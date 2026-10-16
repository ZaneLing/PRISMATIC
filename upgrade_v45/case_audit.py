"""Recount observed trace patterns and release no case/source prose."""
import collections
import json
from common45 import HERE, RUN, OLD_RUN, digest, save, sha
from evidence45 import entity_groups, homeopathic


def main():
    data = json.loads((OLD_RUN / 'data.json').read_text())
    cases = {c['id']: c for c in data['train']}
    old = RUN.parent / 'rxrsi-v44'
    rows = json.loads((old / 'learning/feedback.json').read_text())
    roots = [json.loads(p.read_text()) for p in (old / 'roots').glob('r*/*.json')]
    full = {}
    for path in (RUN / 'full_labels').glob('*.json'):
        for label in json.loads(path.read_text()).get('labels', []):
            full[label['id']] = label
    patterns = collections.defaultdict(list)
    for row in rows:
        case = cases[row['case_id']]
        groups = entity_groups(case, row['plan'], {})
        labels = [x['label_id'] for x in row['evidence']['products']]
        home = [lid for lid in labels if lid in full and homeopathic(full[lid])]
        if home:
            patterns['selected_homeopathic_product_verified_from_full_source'].append(row['case_id'])
        if any(g['scope'] == 'combination' for g in groups):
            patterns['multi_component_option_without_regimen_level_source_in_old_tool'].append(row['case_id'])
        expected = collections.defaultdict(set)
        for group in groups:
            if group['scope'] == 'component' and group['option'] != 'context':
                expected[group['name']].add(group['option'])
        if any(len(v) > 1 for v in expected.values()):
            patterns['shared_component_with_multiple_option_roles'].append(row['case_id'])
    by = {r['case_id']: r for r in rows}
    out = {'population': 'All400 prior training traces; never main/independent test traces',
           'n': len(rows), 'wrong': sum(r['prediction'] != ([cases[r['case_id']]['gold']] if isinstance(cases[r['case_id']]['gold'], str) else sorted(cases[r['case_id']]['gold'])) for r in rows),
           'root_stage_hypotheses_not_causal_counts': dict(collections.Counter(r['root'].get('earliest_stage') for r in roots)),
           'reference_judgments_are_model_hypotheses': dict(collections.Counter(r['root'].get('reference_status') for r in roots)),
           'patterns': {}, 'feedback_sha256': sha(old / 'learning/feedback.json'),
           'metadata_coverage_note': 'Homeopathic counts are lower bounds among original selected labels recovered in new full-source requests; old trimmed metadata cannot establish absence.',
           'clinical_note': 'Pattern co-occurrence with an error is not proof of its causal contribution. Aggregate paired interventions and case traces test the repair.'}
    for name, ids in patterns.items():
        out['patterns'][name] = {'n': len(ids), 'wrong': sum(by[i]['prediction'] != [cases[i]['gold']] for i in ids), 'case_ids': ids}
    save(HERE / 'results/training_patterns.json', out)
    protocol = json.loads((HERE / 'protocol.json').read_text())
    illustrations = []
    for i in protocol['illustration_ids']:
        case = cases[i]; original = by[i]
        item = {'case_id': i, 'gold': case['gold'], 'baseline': original['prediction'], 'options': case['options'],
                'baseline_trace_sha256': digest(original), 'candidate': {}}
        for arm in ('tools', 'tools_contract'):
            path = RUN / 'runs' / arm / 'train' / (digest(i) + '.json')
            if not path.exists():
                continue
            row = json.loads(path.read_text())
            item['candidate'][arm] = {'prediction': row['prediction'], 'trace_sha256': sha(path),
                                      'source_labels': [x['label_id'] for x in row['evidence']['products']],
                                      'source_flags': row['evidence']['flags'],
                                      'final_explanation': row['final'].get('evidence') if isinstance(row['final'], dict) else None}
        illustrations.append(item)
    save(HERE / 'results/case_studies.json', illustrations)
    print(json.dumps({k: {x:y for x,y in v.items() if x != 'case_ids'} for k,v in out['patterns'].items()}))


if __name__ == '__main__':
    main()
