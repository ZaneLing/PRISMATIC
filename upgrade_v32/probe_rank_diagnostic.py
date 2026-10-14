"""Synthetic checks for drug-identity ties, alignment and independent score arithmetic."""
import hashlib
import json
from pathlib import Path

import numpy as np

from rank_diagnostic import alignment, select
from evaluation_metrics import contrast, evidence
from audit_rank_diagnostic import case_auc, compare, metrics, paired, rank_alignment, selected

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def main():
    spec = json.loads((HERE / 'rank_diagnostic_protocol.json').read_text())
    cases = []
    for j in range(3):
        orders = [{'drug_name': 'synthetic-' + str(i), 'route': 'test', 'dose_value': str(i),
                   'dose_unit': 'test', 'frequency_per_24h': None} for i in range(20)]
        gold = [] if j == 0 else orders[:j + 2]
        cases.append({'catalogue': {str(i): o for i, o in enumerate(orders)}, 'gold': gold,
                      'subject_hash': str(j // 2), 'target_mask': [int(o in gold) for o in orders]})
    probability = np.asarray([[.5] * 20, [.8] * 5 + [.5] * 10 + [.2] * 5, np.linspace(.1, .9, 20)])
    reverse = [{**c, 'catalogue': dict(reversed(list(c['catalogue'].items()))), 'target_mask': list(reversed(c['target_mask']))} for c in cases]
    for rule in spec['tie_rules']:
        first, ties = select(probability, cases, rule, spec)
        second, ties_b = select(probability[:, ::-1], reverse, rule, spec)
        assert first == second and ties == ties_b == 2
        independently = [selected(p, c, rule, spec)[0] for p, c in zip(probability, cases)]
        assert first == independently
        actual, ev = evidence(first, cases)
        expected, independent_ev = metrics(first, cases)
        compare(actual, expected)
        alternative = [list(c['catalogue'].values())[-8:] for c in cases]
        _, control_ev = evidence(alternative, cases)
        _, independent_control = metrics(alternative, cases)
        compare(contrast([(1, ev), (-1, control_ev)]), paired([(1, independent_ev), (-1, independent_control)]))
        altered_targets = [{**c, 'gold': [], 'target_mask': [0] * 20} for c in cases]
        assert select(probability, altered_targets, rule, spec)[0] == first
    scores = alignment(probability, probability[:, ::-1], cases, reverse)
    compare(scores, rank_alignment(probability, probability[:, ::-1], cases, reverse))
    assert scores['drug_identity_aligned']['mean_spearman'] == 1.
    assert scores['drug_identity_aligned']['constant_vector_cases'] == 1
    assert case_auc(probability[0], cases[0]) is None
    duplicate = {**cases[0], 'catalogue': dict(cases[0]['catalogue'])}
    duplicate['catalogue']['19'] = duplicate['catalogue']['0']
    rejected = False
    try:
        select(probability[:1], [duplicate], 'drug_sha256', spec)
    except AssertionError:
        rejected = True
    assert rejected
    names = ['rank_diagnostic.py', 'audit_rank_diagnostic.py', 'probe_rank_diagnostic.py',
             'rank_diagnostic_protocol.json', 'evaluation_metrics.py', 'audit_evaluation.py']
    hashes = {str((HERE / name).relative_to(ROOT)): hashlib.sha256((HERE / name).read_bytes()).hexdigest() for name in names}
    receipt = {'status': 'passed', 'synthetic_only': True, 'case_probability_pairs': 3,
               'source_sha256': hashes, 'checks': ['identity_ties_do_not_depend_on_display_order', 'cutoff_tie_count',
               'independent_selection', 'independent_order_metrics', 'paired_patient_interval_arithmetic',
               'identity_alignment_vs_slot_alignment', 'constant_correlation_undefined', 'absent_class_auroc_undefined',
               'duplicate_drug_rejected', 'selection_ignores_targets']}
    (HERE / 'results/rank_diagnostic_probe.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'status': 'passed', 'synthetic_only': True, 'checks': len(receipt['checks'])}))


if __name__ == '__main__':
    main()
