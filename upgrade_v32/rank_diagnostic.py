"""Post-proposal, fixed-cardinality diagnosis from immutable parent probabilities."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIVATE = Path.home() / 'Desktop/MedTreeBench/dataset/restricted/prismatic-v32'
sys.path.insert(0, str(ROOT / 'upgrade_v31'))
from views import view
from evaluation_metrics import auc, contrast, direct, evidence, invariance


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def immutable(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=2, allow_nan=False) + '\n'
    if path.exists():
        assert path.read_text() == text, 'Immutable diagnostic artifact differs: ' + path.name
    else:
        tmp = path.with_suffix('.tmp')
        tmp.write_text(text)
        tmp.replace(path)


def select(probabilities, cases, rule, spec):
    predictions = []
    boundary_ties = 0
    for vector, case in zip(probabilities, cases):
        orders = list(case['catalogue'].values())
        names = [o['drug_name'] for o in orders]
        assert len(names) == len(set(names)) == 20
        assert len(vector) == 20 and np.isfinite(vector).all()
        if rule == 'drug_sha256':
            keys = [hashlib.sha256((spec['tie_hash_prefix'] + n).encode()).hexdigest() for n in names]
        else:
            assert rule == 'drug_lexical'
            keys = names
        indices = sorted(range(20), key=lambda i: (-float(vector[i]), keys[i], names[i]))
        boundary_ties += float(vector[indices[spec['k'] - 1]]) == float(vector[indices[spec['k']]])
        predictions.append([orders[i] for i in indices[:spec['k']]])
    return predictions, int(boundary_ties)


def midranks(values):
    values = np.asarray(values)
    return np.asarray([np.sum(values < x) + (np.sum(values == x) + 1) / 2 for x in values], dtype=float)


def rho(first, second):
    a, b = midranks(first), midranks(second)
    a -= a.mean()
    b -= b.mean()
    denominator = float(np.sqrt(np.sum(a * a) * np.sum(b * b)))
    return float(np.sum(a * b) / denominator) if denominator else None


def correlation_summary(values):
    valid = [v for v in values if v is not None]
    return {'mean_spearman': float(np.mean(valid)) if valid else None,
            'eligible_cases': len(valid), 'constant_vector_cases': len(values) - len(valid)}


def alignment(ranked_prob, other_prob, ranked_cases, other_cases):
    identity, position = [], []
    for a, b, first, second in zip(ranked_prob, other_prob, ranked_cases, other_cases):
        names = [o['drug_name'] for o in first['catalogue'].values()]
        other_names = [o['drug_name'] for o in second['catalogue'].values()]
        assert set(names) == set(other_names)
        mapping = dict(zip(other_names, b))
        identity.append(rho(a, [mapping[n] for n in names]))
        position.append(rho(a, b))
    return {'drug_identity_aligned': correlation_summary(identity),
            'same_display_slots_unaligned': correlation_summary(position)}


def main(split):
    spec = json.loads((HERE / 'rank_diagnostic_protocol.json').read_text())
    lock_path = HERE / 'results/rank_diagnostic_lock.json'
    lock = json.loads(lock_path.read_text())
    assert lock['protocol_sha256'] == sha(HERE / 'rank_diagnostic_protocol.json')
    assert all(sha(ROOT / name) == digest for name, digest in lock['source_sha256'].items())
    parent_path = HERE / f'results/{split}_summary.json'
    audit_path = HERE / f'results/{split}_audit.json'
    parent = json.loads(parent_path.read_text())
    audit = json.loads(audit_path.read_text())
    assert audit['status'] == 'passed' and audit['summary_sha256'] == sha(parent_path)
    assert audit['auditor_sha256'] == sha(HERE / 'audit_evaluation.py')
    assert sha(HERE / 'results/proposal_summary.json') == spec['known_parent_proposal_summary_sha256']
    source = PRIVATE.parent / 'prismatic-v31/cases.json'
    parent_lock = json.loads((PRIVATE / 'evaluation_lock.json').read_text())
    assert sha(source) == parent_lock['source_cases_sha256']
    assert parent['evaluation_lock_sha256'] == sha(PRIVATE / 'evaluation_lock.json')
    assert all(sha(ROOT / name) == digest for name, digest in parent_lock['source_sha256'].items())
    original = json.loads(source.read_text())['validation' if split == 'proposal' else 'guard']
    cases = {kind: [view(c, kind) for c in original] for kind in parent['views']}
    probabilities = {}
    for name in spec['neural_states']:
        probabilities[name] = {}
        for kind, group in cases.items():
            path = PRIVATE / 'inference' / name / 'bindings' / f'{split}-{kind}.json'
            assert sha(path) == parent['binding_sha256'][name][kind]
            rows = json.loads(path.read_text())
            assert len(rows) == len(group)
            for row, case in zip(rows, group):
                assert row['case_id'] == case['case_id'] and row['subject_hash'] == case['subject_hash']
            probabilities[name][kind] = np.asarray([r['conditional_probabilities'] for r in rows], dtype=float)
    definitions = {name + '_minus_retrieval': [(1, name), (-1, spec['control'])] for name in spec['neural_states']}
    for name in spec['neural_states'][2:]:
        for control in spec['neural_states'][:2]:
            definitions[name + '_minus_' + control] = [(1, name), (-1, control)]
    panels, stored_predictions, stability = {}, {}, {}
    for rule in spec['tie_rules']:
        panels[rule], stored_predictions[rule] = {}, {}
        for kind, group in cases.items():
            predictions = {}
            scores, records = {}, {}
            for name in spec['neural_states']:
                predictions[name], ties = select(probabilities[name][kind], group, rule, spec)
                scores[name], records[name] = evidence(predictions[name], group)
                within = [auc(c['target_mask'], p) for c, p in zip(group, probabilities[name][kind])]
                valid = [x for x in within if x is not None]
                scores[name].update(boundary_tie_cases=ties, within_case_auroc_mean=float(np.mean(valid)) if valid else None,
                                    within_case_auroc_eligible_cases=len(valid), within_case_auroc_excluded_cases=len(within) - len(valid))
            predictions[spec['control']] = direct(group, spec['k'])
            scores[spec['control']], records[spec['control']] = evidence(predictions[spec['control']], group)
            for metric in ['drug_micro_f1', 'core_order_micro_f1', 'mean_predicted_drugs']:
                assert scores[spec['control']][metric] == parent['endpoints']['fixed_half'][kind]['methods'][spec['control']][metric]
            panels[rule][kind] = {'methods': scores, 'contrasts': {name: contrast([(weight, records[method]) for weight, method in terms]) for name, terms in definitions.items()}}
            stored_predictions[rule][kind] = predictions
        stability[rule] = {kind: {name: invariance(stored_predictions[rule]['ranked'][name], preds[name]) for name in preds}
                           for kind, preds in stored_predictions[rule].items() if kind != 'ranked'}
    aligned = {kind: {name: alignment(probabilities[name]['ranked'], probabilities[name][kind], cases['ranked'], cases[kind])
                     for name in spec['neural_states']} for kind in cases if kind != 'ranked'}
    selections_path = PRIVATE / 'ranking' / f'{split}_selections.json'
    immutable(selections_path, {'case_ids': [c['case_id'] for c in original], 'predictions': stored_predictions})
    result = {'status': 'executed_pending_independent_audit', 'split': split, 'cases': len(original),
              'patients': len({c['subject_hash'] for c in original}), 'diagnostic_lock_sha256': sha(lock_path),
              'parent_summary_sha256': sha(parent_path), 'parent_audit_sha256': sha(audit_path),
              'private_selections_sha256': sha(selections_path), 'panels': panels,
              'top8_view_invariance': stability, 'score_rank_alignment': aligned,
              'new_model_inference': 0, 'api_calls': 0, 'test_predictions_read': False,
              'scope': spec['selection_effect']}
    immutable(HERE / f'results/{split}_rank_diagnostic.json', result)
    print(json.dumps({'status': result['status'], 'split': split, 'cases': len(original), 'methods': 7, 'tie_rules': 2}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('split', choices=['proposal', 'guard'])
    main(parser.parse_args().split)
