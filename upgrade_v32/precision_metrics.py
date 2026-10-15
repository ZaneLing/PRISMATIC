"""Unselected fixed-eight endpoints for every frozen readout and tie rule."""
import numpy as np

from evaluation_metrics import auc, contrast, direct, evidence, invariance
from rank_diagnostic import alignment, select

READOUTS = ['native', 'fp32_binary', 'fp32_rerounded']


def summarize(probabilities, cases, rank_spec):
    states = list(probabilities)
    panels, changes, stable = {}, {}, {}
    for rule in rank_spec['tie_rules']:
        panels[rule], changes[rule] = {}, {}
        all_predictions = {}
        for kind, group in cases.items():
            panels[rule][kind], all_predictions[kind], evidence_by_readout = {}, {}, {}
            for readout in READOUTS:
                methods, records, predictions = {}, {}, {}
                for state in states:
                    vectors = probabilities[state][kind][readout]
                    predictions[state], ties = select(vectors, group, rule, rank_spec)
                    methods[state], records[state] = evidence(predictions[state], group)
                    values = [auc(case['target_mask'], p) for case, p in zip(group, vectors)]
                    valid = [v for v in values if v is not None]
                    methods[state].update(boundary_tie_cases=ties,
                                          mean_unique_scores=float(np.mean([len(np.unique(p)) for p in vectors])),
                                          within_case_auroc_mean=float(np.mean(valid)) if valid else None,
                                          within_case_auroc_eligible_cases=len(valid), within_case_auroc_excluded_cases=len(values) - len(valid))
                control = rank_spec['control']
                predictions[control] = direct(group, rank_spec['k'])
                methods[control], records[control] = evidence(predictions[control], group)
                panels[rule][kind][readout] = {'methods': methods, 'contrasts_vs_retrieval': {
                    state: contrast([(1, records[state]), (-1, records[control])]) for state in states}}
                all_predictions[kind][readout] = predictions
                evidence_by_readout[readout] = records
            changes[rule][kind] = {state: {
                'fp32_minus_native': contrast([(1, evidence_by_readout['fp32_binary'][state]), (-1, evidence_by_readout['native'][state])]),
                'fp32_minus_rerounded': contrast([(1, evidence_by_readout['fp32_binary'][state]), (-1, evidence_by_readout['fp32_rerounded'][state])]),
                'rerounded_minus_native': contrast([(1, evidence_by_readout['fp32_rerounded'][state]), (-1, evidence_by_readout['native'][state])])}
                for state in states}
        stable[rule] = {kind: {readout: {state: invariance(all_predictions['ranked'][readout][state], methods[state]) for state in methods}
                              for readout, methods in reads.items()} for kind, reads in all_predictions.items() if kind != 'ranked'}
    aligned = {readout: {kind: {state: alignment(probabilities[state]['ranked'][readout], probabilities[state][kind][readout], cases['ranked'], cases[kind])
                               for state in states} for kind in cases if kind != 'ranked'} for readout in READOUTS}
    return {'panels': panels, 'readout_contrasts': changes, 'top8_view_invariance': stable, 'score_rank_alignment': aligned}
