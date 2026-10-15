"""Aggregate adjudicated research ratings; never infer clinical labels.

Inputs contain a frozen, method-independent requirement inventory and one
blinded arm's output inventory and ratings. Missing assessments remain unknown.
These measures are a proposed research rubric, not a validated clinical scale.
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path


def indexed(rows, key):
    result = {}
    for row in rows:
        if row[key] in result:
            raise ValueError('Duplicate ' + key)
        result[row[key]] = row
    return result


def binary(value):
    if value is not None and type(value) is not bool:
        raise ValueError('Ratings must be true, false or null')
    return value


def summarize(values, unknown_applicability=0):
    n = len(values)
    rated = sum(x is not None for x in values)
    passed = sum(x is True for x in values)
    return {'eligible': n, 'rated': rated, 'pass': passed,
            'fail': sum(x is False for x in values), 'unrated': n-rated,
            'unknown_applicability': unknown_applicability,
            'assessment_coverage': rated/n if n else None,
            'pass_rate_among_rated': passed/rated if rated else None,
            'confirmed_pass_lower_bound': passed/n if n else None,
            'complete_for_declared_scope': rated == n and unknown_applicability == 0}


def events(values):
    r = summarize(values)
    return {'eligible': r['eligible'], 'rated': r['rated'], 'events': r['pass'],
            'known_non_events': r['fail'], 'unrated': r['unrated'],
            'assessment_coverage': r['assessment_coverage'],
            'event_rate_among_rated': r['pass_rate_among_rated'],
            'confirmed_event_lower_bound': r['confirmed_pass_lower_bound']}


def score(bundle):
    if bundle.get('status') != 'adjudicated':
        raise ValueError('Only adjudicated bundles produce research aggregates')
    cases = indexed(bundle['references'], 'case_id')
    outputs = indexed(bundle['outputs'], 'case_id')
    reviews = indexed(bundle['reviews'], 'case_id')
    if set(outputs) != set(cases) or not set(reviews) <= set(cases):
        raise ValueError('Outputs must cover the frozen case inventory; reviews cannot add cases')
    domains, unknown = defaultdict(list), defaultdict(int)
    case_domain_rates = defaultdict(list)
    critical, major_errors, unnecessary, ordered = [], [], [], []
    critical_unknown = 0
    for cid, case in cases.items():
        required = indexed(case['requirements'], 'id')
        review = reviews.get(cid, {})
        ratings = review.get('requirements', {})
        if not set(ratings) <= set(required):
            raise ValueError('Unknown requirement ID')
        case_values = defaultdict(list)
        unresolved_critical = False
        for rid, req in required.items():
            applicable = binary(req['applicable'])
            domain = req['domain']
            value = binary(ratings.get(rid))
            if applicable is None:
                if value is not None:
                    raise ValueError('Unknown applicability cannot receive a satisfaction rating')
                unknown[domain] += 1
                unresolved_critical |= bool(req.get('critical'))
                critical_unknown += int(bool(req.get('critical')))
                continue
            if not applicable:
                if value is not None:
                    raise ValueError('Non-applicable requirements must not receive a rating')
                continue
            domains[domain].append(value)
            case_values[domain].append(value)
            if req.get('critical'):
                critical.append(value)
                unresolved_critical |= value is None
        for domain, values in case_values.items():
            # A macro average is only defined on completely rated cases;
            # its coverage must be reported alongside it.
            case_domain_rates[domain].append(
                sum(x is True for x in values)/len(values) if all(x is not None for x in values) else None)
        major = binary(review.get('major_error'))
        if major is False and unresolved_critical:
            raise ValueError('Unassessed critical items cannot receive no-major-error clearance')
        major_errors.append(major)
        order_ids = outputs[cid]['order_ids']
        if len(order_ids) != len(set(order_ids)):
            raise ValueError('Duplicate output order ID')
        order_ratings = review.get('unnecessary_orders', {})
        if not set(order_ratings) <= set(order_ids):
            raise ValueError('Unknown output order ID')
        unnecessary.extend(binary(order_ratings.get(oid)) for oid in order_ids)
        ordered.append(bool(order_ids))
    result = {}
    for domain in sorted(set(domains) | set(unknown)):
        result[domain] = summarize(domains[domain], unknown[domain])
        vals = case_domain_rates[domain]
        complete = [v for v in vals if v is not None]
        result[domain].update(case_macro_rate=sum(complete)/len(complete) if complete else None,
            complete_cases=len(complete), eligible_cases=len(vals))
    return {'status': 'computed_from_adjudication', 'arm_id': bundle['arm_id'],
            'n_cases': len(cases), 'n_reviewed_cases': len(reviews), 'domains': result,
            'critical_requirement_coverage': summarize(critical, critical_unknown),
            'major_error_cases': events(major_errors),
            'unnecessary_orders': events(unnecessary),
            'cases_with_orders': sum(ordered), 'order_action_coverage': sum(ordered)/len(ordered) if ordered else None,
            'interpretation': 'Higher requirement satisfaction and lower event rates are desirable, conditional on assessment and action coverage. Unknowns remain explicit; no pooled quality or safety score.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('ratings_json')
    parser.add_argument('output_json')
    args = parser.parse_args()
    result = score(json.loads(Path(args.ratings_json).read_text()))
    Path(args.output_json).write_text(json.dumps(result, indent=2)+'\n')
