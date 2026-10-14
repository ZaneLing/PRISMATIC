"""Replay completed development checkpoints without opening the sealed test bundle.

This retrospective diagnostic adds no fitting or state selection.  It executes the
saved policy/tool artifacts, independently counts outputs, and checks the original
proposal choice and guard decision before publishing any curve.
"""
import os
for name in ['OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS']:
    os.environ.setdefault(name, '1')
import json
from pathlib import Path
import joblib
import numpy as np
from scipy.special import expit
from data_contract import HERE, PRIVATE, FIELDS, sha, digest, save

METRICS = ['drug_micro_f1', 'core_order_micro_f1', 'drug_precision',
           'drug_recall', 'empty_fraction', 'mean_predicted_drugs']


def read(path):
    return json.loads(path.read_text())


def recount(predictions, truth):
    totals = np.zeros(6, dtype=np.int64)
    empty = agreement = total_orders = 0
    case_counts = []
    for pred, gold in zip(predictions, truth):
        p = {o['drug_code'] for o in pred}
        g = {o['drug_code'] for o in gold}
        pt = {tuple(o[k] for k in FIELDS) for o in pred
              if all(o.get(k) is not None for k in FIELDS)}
        gt = {tuple(o[k] for k in FIELDS) for o in gold
              if all(o.get(k) is not None for k in FIELDS)}
        counts = [len(p & g), len(p), len(g), len(pt & gt), len(pt), len(gt)]
        totals += counts
        case_counts.append(counts)
        empty += not pred
        agreement += bool(pred) == bool(gold)
        total_orders += len(pred)
    assert len(predictions) == len(truth) and truth
    n = len(truth)
    d = 2 * totals[0] / max(1, totals[1] + totals[2])
    o = 2 * totals[3] / max(1, totals[4] + totals[5])
    scores = dict(cases=n, drug_micro_f1=float(d), core_order_micro_f1=float(o),
                  promotion_score=float((d + o) / 2),
                  drug_precision=float(totals[0] / max(1, totals[1])),
                  drug_recall=float(totals[0] / max(1, totals[2])),
                  empty_fraction=empty / n, mean_predicted_drugs=float(totals[1] / n),
                  complete_predicted_orders=int(totals[4]), complete_gold_orders=int(totals[5]),
                  predicted_order_completion=float(totals[4] / max(1, total_orders)),
                  empty_decision_agreement=agreement / n)
    return scores, np.asarray(case_counts, dtype=np.int64)


def equal_scores(actual, expected):
    assert set(actual) == set(expected)
    for key in actual:
        assert abs(actual[key] - expected[key]) <= 1e-12, (key, actual[key], expected[key])


def main():
    spec = read(HERE / 'protocol.json')
    manifest = read(HERE / 'results/feature_manifest.json')
    assert read(HERE / 'results/cohort_audit.json')['status'] == 'passed'
    assert sha(PRIVATE / 'development.joblib') == manifest['development_sha256']
    development = joblib.load(PRIVATE / 'development.joblib')
    assert set(development) == {'train', 'proposal', 'guard', 'classes', 'y'}
    classes = development['classes']
    assert digest(classes) == manifest['class_space_sha256']
    core = {name: sha(HERE / name) for name in ['train.py', 'learning.py', 'data_contract.py']}
    source_names = ['protocol.json', 'results/feature_manifest.json', 'results/cohort_audit.json',
                    'results/cohort_manifest.json'] + list(core)
    source_names += [f'results/journal_seed_{s}_{a}.json' for s in spec['seeds'] for a in spec['arms']]
    source_hashes = {name: sha(HERE / name) for name in source_names}
    people = [c['patient_hash'] for c in development['guard']['cases']]
    hospitals = [c['hospital_hash'] for c in development['guard']['cases']]
    truth = development['guard']['truth']
    assert len(truth) == 2000 and len(set(people)) == 1912 and len(set(hospitals)) == 17
    counts_path = PRIVATE / 'development_recount_counts.joblib'
    private_counts = {'case_ids': [c['case_id'] for c in development['guard']['cases']], 'states': {}}
    results, artifacts = {}, {}
    completed = 0
    for seed in spec['seeds']:
        folder = PRIVATE / f'seed_{seed}'
        lock = read(folder / 'execution_lock.json')
        assert lock == {'protocol_sha256': source_hashes['protocol.json'], 'code_sha256': core}
        sequence = joblib.load(folder / 'case_order.joblib')
        expected = np.r_[np.arange(8000), np.random.default_rng(seed).permutation(np.arange(8000, 40000))]
        assert np.array_equal(sequence, expected)
        artifacts[f'seed_{seed}/execution_lock.json'] = sha(folder / 'execution_lock.json')
        artifacts[f'seed_{seed}/case_order.joblib'] = sha(folder / 'case_order.joblib')
        results[str(seed)] = {}
        for arm in spec['arms']:
            journal = read(HERE / f'results/journal_seed_{seed}_{arm}.json')
            assert len(journal) == len(spec['round_sizes']) == 5
            states, active = [], None
            for r, entry in enumerate(journal):
                state = entry['candidate']
                assert entry['round'] == state['round'] == r and state['arm'] == arm
                n = spec['round_sizes'][r]
                assert state['training_cases'] == entry['training_cases'] == n
                ids = [development['train']['cases'][i]['case_id'] for i in sequence[:n]]
                assert digest(ids) == entry['training_membership_sha256']
                model = joblib.load(folder / state['policy_file'])
                assert digest([model.coef_.tolist(), model.intercept_.tolist()]) == state['policy_sha256']
                assert model.iterations == [60] * len(classes)
                assert entry['logical_training_case_exposures'] == n * 60 * len(classes)
                assert sha(folder / state['tool_file']) == state['tool_sha256']
                tool = joblib.load(folder / state['tool_file'])
                seen_truth = [development['train']['truth'][i] for i in sequence[:n]]
                assert tool.membership_sha256 == digest(seen_truth) == entry['tool_membership_sha256']
                seen = {tuple(o[k] for k in FIELDS) for rows in seen_truth for o in rows}
                assert all(tuple(o[k] for k in FIELDS) in seen for o in tool.defaults.values())
                assert all(tuple(o) in seen for labels in tool.labels.values() for o in labels)
                for name in [state['policy_file'], state['tool_file']]:
                    artifacts[f'seed_{seed}/{name}'] = sha(folder / name)
                scores = {}
                for split in ['proposal', 'guard']:
                    b = development[split]
                    probabilities = expit(b['x'] @ model.coef_.T + model.intercept_)
                    indices = np.argsort(-probabilities, axis=1, kind='stable')[:, :20]
                    values = np.take_along_axis(probabilities, indices, axis=1)
                    # Reexecute the original frozen tool; scoring below does not
                    # call learning.score, ranked_rows, choose, or assess.
                    rows = tool.compile([[classes[j] for j in row] for row in indices], b['word'])
                    options = {}
                    thresholds = spec['thresholds'] if split == 'proposal' else [state['threshold']]
                    for threshold in thresholds:
                        pred = [[o for o, p in zip(row, probs) if p >= threshold]
                                for row, probs in zip(rows, values)]
                        metric, matrix = recount(pred, b['truth'])
                        options[threshold] = metric
                        if split == 'guard':
                            private_counts['states'][f'{seed}/{arm}/{r}'] = matrix
                    chosen = max(thresholds, key=lambda t: options[t]['promotion_score'])
                    assert chosen == state['threshold']
                    scores[split] = options[chosen]
                equal_scores(scores['proposal'], entry['proposal'])
                equal_scores(scores['guard'], entry['raw_guard'])
                before = states[active]['raw'] if active is not None else None
                accept = before is None or (scores['guard']['promotion_score'] > before['promotion_score']
                         and all(scores['guard'][k] >= before[k] - .002
                                 for k in ['drug_micro_f1', 'core_order_micro_f1']))
                if accept:
                    active = r
                assert accept == entry['accepted'] and entry['active'] == journal[active]['candidate']
                active_scores = scores['guard'] if active == r else states[active]['raw']
                equal_scores(active_scores, entry['active_guard'])
                states.append({'round': r, 'training_cases_encountered': n,
                               'raw': scores['guard'], 'accepted': active_scores,
                               'accepted_update': accept, 'active_round': active,
                               'threshold': state['threshold']})
                completed += 1
                print(json.dumps({'recounted_development_states': completed, 'seed': seed,
                                  'arm': arm, 'round': r}), flush=True)
            results[str(seed)][arm] = states
    assert completed == 45
    assert all(sha(HERE / name) == value for name, value in source_hashes.items())
    joblib.dump(private_counts, counts_path)
    aggregate = {}
    for kind in ['raw', 'accepted']:
        aggregate[kind] = {}
        for arm in spec['arms']:
            rows = []
            for r in range(5):
                row = {'round': r, 'training_cases_encountered': spec['round_sizes'][r]}
                for metric in METRICS:
                    v = [results[str(s)][arm][r][kind][metric] for s in spec['seeds']]
                    row[metric] = {'mean': float(np.mean(v)), 'seed_sd': float(np.std(v, ddof=1))}
                rows.append(row)
            aggregate[kind][arm] = rows
    contrasts = {}
    for kind in ['raw', 'accepted']:
        contrasts[kind] = {}
        for control in ['uniform', 'permuted_priority']:
            differences = {str(s): {k: results[str(s)]['error_prioritized'][4][kind][k] -
                                    results[str(s)][control][4][kind][k] for k in METRICS[:2]}
                           for s in spec['seeds']}
            contrasts[kind][control] = {'seeds': differences,
                'mean': {k: float(np.mean([v[k] for v in differences.values()])) for k in METRICS[:2]}}
    regression_counts = {}
    for arm in spec['arms']:
        regression_counts[arm] = {k: sum(results[str(s)][arm][r]['raw'][k] <
                                         results[str(s)][arm][r-1]['raw'][k] - 1e-12
                                         for s in spec['seeds'] for r in range(1, 5))
                                  for k in METRICS[:2]}
    save(HERE / 'results/development_curves.json', {
        'status': 'passed', 'analysis': 'Retrospective development replay after seeing completed journals; no new selection.',
        'development_states_reexecuted': completed, 'proposal_thresholds_checked_per_state': len(spec['thresholds']),
        'guard_stays': len(truth), 'guard_patients': len(set(people)), 'guard_hospitals': len(set(hospitals)),
        'guard_zero_target_stays': sum(not g for g in truth), 'seeds': spec['seeds'],
        'source_sha256': source_hashes, 'artifact_sha256': artifacts,
        'development_bundle_sha256': manifest['development_sha256'], 'script_sha256': sha(Path(__file__)),
        'private_counts_sha256': sha(counts_path), 'states': results, 'aggregate': aggregate,
        'final_own_error_minus_control': contrasts, 'raw_regressions_among_12_transitions': regression_counts,
        'sealed_test_bundle_opened': False, 'new_fits': 0, 'api_calls': 0,
        'checks': ['saved_parameter_hashes_and_epochs', 'seen_only_tool_membership_and_labels',
                   'frozen_policy_and_tool_forward_execution', 'independent_output_set_counts',
                   'all_original_proposal_thresholds', 'original_guard_accept_reject_decisions'],
        'limits': ['Guard selected accepted states; its smoother curves do not prove generalization.',
                   'Tool execution uses the original implementation; no independent optimizer replay.',
                   'No new feedback-weight audit here; the registered final audit retains that responsibility.',
                   'Three-seed SD describes these seeds, not a confidence interval or clinical safety.']})


if __name__ == '__main__':
    main()
