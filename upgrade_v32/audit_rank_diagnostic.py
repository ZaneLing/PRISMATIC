"""Independent fixed-cardinality selection, source alignment and score recount."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from audit_evaluation import compare, metrics, paired, transformed

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIVATE = Path.home() / 'Desktop/MedTreeBench/dataset/restricted/prismatic-v32'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def selected(vector, case, rule, spec):
    table = []
    for value, order in zip(vector, case['catalogue'].values()):
        name = order['drug_name']
        key = hashlib.sha256((spec['tie_hash_prefix'] + name).encode()).hexdigest() if rule == 'drug_sha256' else name
        table.append((float(value), key, name, order))
    assert len(table) == 20 and len({row[2] for row in table}) == 20
    table.sort(key=lambda row: (-row[0], row[1], row[2]))
    return [row[3] for row in table[:8]], table[7][0] == table[8][0]


def case_auc(prob, case):
    positive = [float(p) for p, y in zip(prob, case['target_mask']) if y]
    negative = [float(p) for p, y in zip(prob, case['target_mask']) if not y]
    if not positive or not negative:
        return None
    return sum((a > b) + .5 * (a == b) for a in positive for b in negative) / (len(positive) * len(negative))


def tied_ranks(values):
    order = np.argsort(values, kind='stable')
    ranks = np.empty(len(order), dtype=float)
    start = 0
    while start < len(order):
        stop = start + 1
        while stop < len(order) and values[order[stop]] == values[order[start]]:
            stop += 1
        ranks[order[start:stop]] = (start + stop - 1) / 2
        start = stop
    return ranks


def correlation(a, b):
    a, b = tied_ranks(a), tied_ranks(b)
    if a.max() == a.min() or b.max() == b.min():
        return None
    return float(np.corrcoef(a, b)[0, 1])


def rank_alignment(first, second, cases_a, cases_b):
    a_values, b_values = [], []
    for a, b, ca, cb in zip(first, second, cases_a, cases_b):
        left = list(ca['catalogue'].values())
        right = list(cb['catalogue'].values())
        b_index = {o['drug_name']: i for i, o in enumerate(right)}
        a_values.append(correlation(a, [b[b_index[o['drug_name']]] for o in left]))
        b_values.append(correlation(a, b))
    result = {}
    for name, values in [('drug_identity_aligned', a_values), ('same_display_slots_unaligned', b_values)]:
        present = [x for x in values if x is not None]
        result[name] = {'mean_spearman': sum(present) / len(present) if present else None,
                        'eligible_cases': len(present), 'constant_vector_cases': len(values) - len(present)}
    return result


def set_agreement(first, second):
    same = 0
    total = 0.
    for a, b in zip(first, second):
        left = {o['drug_name'] for o in a}
        right = {o['drug_name'] for o in b}
        assert len(left) == len(right) == 8
        same += left == right
        total += len(left.intersection(right)) / len(left.union(right))
    n = len(first)
    return {'cases': n, 'drug_set_agreement': same / n, 'mean_jaccard': total / n,
            'nonempty_union_cases': n, 'nonempty_union_mean_jaccard': total / n}


def main(split):
    spec = json.loads((HERE / 'rank_diagnostic_protocol.json').read_text())
    assert spec['k'] == 8 and spec['tie_rules'] == ['drug_sha256', 'drug_lexical']
    path = HERE / f'results/{split}_rank_diagnostic.json'
    result = json.loads(path.read_text())
    lock = json.loads((HERE / 'results/rank_diagnostic_lock.json').read_text())
    assert result['diagnostic_lock_sha256'] == sha(HERE / 'results/rank_diagnostic_lock.json')
    assert lock['protocol_sha256'] == sha(HERE / 'rank_diagnostic_protocol.json')
    assert all(sha(ROOT / name) == value for name, value in lock['source_sha256'].items())
    parent_path = HERE / f'results/{split}_summary.json'
    parent_audit_path = HERE / f'results/{split}_audit.json'
    parent = json.loads(parent_path.read_text())
    parent_audit = json.loads(parent_audit_path.read_text())
    assert parent_audit['status'] == 'passed' and parent_audit['summary_sha256'] == sha(parent_path)
    assert result['parent_summary_sha256'] == sha(parent_path) and result['parent_audit_sha256'] == sha(parent_audit_path)
    assert parent_audit['auditor_sha256'] == sha(HERE / 'audit_evaluation.py')
    source = PRIVATE.parent / 'prismatic-v31/cases.json'
    parent_lock = json.loads((PRIVATE / 'evaluation_lock.json').read_text())
    assert sha(source) == parent_lock['source_cases_sha256']
    assert parent['evaluation_lock_sha256'] == sha(PRIVATE / 'evaluation_lock.json')
    assert all(sha(ROOT / name) == value for name, value in parent_lock['source_sha256'].items())
    original = json.loads(source.read_text())['validation' if split == 'proposal' else 'guard']
    cases = {kind: [transformed(case, kind) for case in original] for kind in parent['views']}
    assert result['cases'] == len(original) and result['patients'] == len({c['subject_hash'] for c in original})
    private_path = PRIVATE / 'ranking' / f'{split}_selections.json'
    assert result['private_selections_sha256'] == sha(private_path)
    recorded = json.loads(private_path.read_text())
    assert recorded['case_ids'] == [c['case_id'] for c in original]
    probs = {}
    bindings = 0
    for name in spec['neural_states']:
        probs[name] = {}
        for kind, group in cases.items():
            binding = PRIVATE / 'inference' / name / 'bindings' / f'{split}-{kind}.json'
            assert sha(binding) == parent['binding_sha256'][name][kind]
            rows = json.loads(binding.read_text())
            assert len(rows) == len(group)
            for row, case in zip(rows, group):
                assert row['case_id'] == case['case_id'] and row['subject_hash'] == case['subject_hash']
                raw = PRIVATE / 'inference' / name / 'raw' / (row['signature'] + '.json')
                assert sha(raw) == row['raw_sha256']
                assert json.loads(raw.read_text())['conditional_probabilities'] == row['conditional_probabilities']
                bindings += 1
            probs[name][kind] = np.asarray([r['conditional_probabilities'] for r in rows])
    definitions = {name + '_minus_retrieval': [(1, name), (-1, spec['control'])] for name in spec['neural_states']}
    for name in spec['neural_states'][2:]:
        for baseline in spec['neural_states'][:2]:
            definitions[name + '_minus_' + baseline] = [(1, name), (-1, baseline)]
    panels, predictions, invariant = {}, {}, {}
    selections = 0
    for rule in spec['tie_rules']:
        panels[rule], predictions[rule] = {}, {}
        for kind, group in cases.items():
            scores, evidences, preds = {}, {}, {}
            for name in spec['neural_states']:
                pairs = [selected(p, c, rule, spec) for p, c in zip(probs[name][kind], group)]
                preds[name] = [x[0] for x in pairs]
                scores[name], evidences[name] = metrics(preds[name], group)
                aucs = [case_auc(p, c) for p, c in zip(probs[name][kind], group)]
                available = [x for x in aucs if x is not None]
                scores[name].update(boundary_tie_cases=sum(int(x[1]) for x in pairs),
                                    within_case_auroc_mean=sum(available) / len(available) if available else None,
                                    within_case_auroc_eligible_cases=len(available), within_case_auroc_excluded_cases=len(aucs) - len(available))
            preds[spec['control']] = [[order for order, rank in zip(c['catalogue'].values(), c['original_rank_by_position']) if rank <= 8] for c in group]
            scores[spec['control']], evidences[spec['control']] = metrics(preds[spec['control']], group)
            panels[rule][kind] = {'methods': scores, 'contrasts': {name: paired([(w, evidences[m]) for w, m in terms]) for name, terms in definitions.items()}}
            predictions[rule][kind] = preds
            selections += len(preds) * len(group)
        invariant[rule] = {kind: {name: set_agreement(predictions[rule]['ranked'][name], pred[name]) for name in pred}
                           for kind, pred in predictions[rule].items() if kind != 'ranked'}
    aligned = {kind: {name: rank_alignment(probs[name]['ranked'], probs[name][kind], cases['ranked'], cases[kind])
                     for name in spec['neural_states']} for kind in cases if kind != 'ranked'}
    compare(recorded['predictions'], predictions)
    compare(result['panels'], panels)
    compare(result['top8_view_invariance'], invariant)
    compare(result['score_rank_alignment'], aligned)
    assert result['new_model_inference'] == result['api_calls'] == 0 and result['test_predictions_read'] is False
    receipt = {'status': 'passed', 'split': split, 'auditor_sha256': sha(Path(__file__)),
               'summary_sha256': sha(path), 'diagnostic_lock_sha256': result['diagnostic_lock_sha256'],
               'parent_audit_sha256': sha(parent_audit_path), 'case_probability_bindings_recounted': bindings,
               'case_selections_recounted': selections, 'methods_per_view_and_tie_rule': 7, 'tie_rules': 2,
               'scope': 'Independent source/permutation, raw-probability binding, fixed-eight selection, within-case AUROC, identity/slot rank correlation, order metrics and 4000-draw paired patient interval recount. No neural forward or optimizer replay. Post-proposal descriptive diagnostic.'}
    (HERE / f'results/{split}_rank_diagnostic_audit.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('split', choices=['proposal', 'guard'])
    main(parser.parse_args().split)
