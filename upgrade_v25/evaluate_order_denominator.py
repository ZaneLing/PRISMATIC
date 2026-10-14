"""Post-test completeness sensitivity of immutable eICU predictions; no fitting."""
import json
from pathlib import Path
import joblib
import numpy as np
from data_contract import HERE, PRIVATE, FIELDS, sha, save


def read(path):
    return json.loads(path.read_text())


def counts(predictions, truth):
    result = []
    assert len(predictions) == len(truth)
    for pred, gold in zip(predictions, truth):
        emitted = {tuple(o.get(k) for k in FIELDS) for o in pred}
        complete = {t for t in emitted if None not in t}
        reference = {tuple(o.get(k) for k in FIELDS) for o in gold
                     if all(o.get(k) is not None for k in FIELDS)}
        result.append([len(complete & reference), len(complete), len(emitted), len(reference)])
    return np.asarray(result, dtype=np.int64)


def score(total):
    return np.stack([2 * total[..., 0] / np.maximum(1, total[..., 1] + total[..., 3]),
                     2 * total[..., 0] / np.maximum(1, total[..., 2] + total[..., 3])], axis=-1)


def metrics(matrix):
    total = matrix.sum(axis=0)
    old, new = score(total)
    assert 0 <= new <= old <= 1 and total[0] <= min(total[1], total[3])
    assert total[1] <= total[2]
    return dict(zip(['matched_complete_tuples', 'complete_predicted_tuples',
                     'all_predicted_tuples', 'complete_reference_tuples'], map(int, total)),
                original_joint_f1=float(old), all_output_denominator_f1=float(new),
                complete_output_fraction=float(total[1] / max(1, total[2])))


def intervals(matrices, groups, contrasts):
    _, index = np.unique(groups, return_inverse=True)
    n = int(index.max()) + 1
    names = sorted({name for pair in contrasts for name in pair})
    blocks = []
    for name in names:
        grouped = np.zeros((n, 4), dtype=np.int64)
        np.add.at(grouped, index, matrices[name])
        blocks.append(grouped)
    stacked = np.concatenate(blocks, axis=1)
    rng = np.random.default_rng(42)
    weights = np.asarray([np.bincount(rng.integers(0, n, n), minlength=n)
                          for _ in range(2000)], dtype=np.int64)
    bound = n * int(stacked.max())
    assert bound < np.iinfo(np.int64).max // 2
    totals = (weights @ stacked).reshape(2000, len(names), 4)
    assert (totals >= 0).all() and (totals <= bound).all()
    values = score(totals)
    assert np.isfinite(values).all()
    return {left + '__minus__' + right:
            np.quantile(values[:, names.index(left)] - values[:, names.index(right)],
                        [.025, .975], axis=0).tolist()
            for left, right in contrasts}


def main():
    np.seterr(all='raise')
    protocol = read(HERE / 'order_denominator_protocol.json')
    assert all(sha(HERE / p) == h for p, h in protocol['source_sha256'].items())
    assert tuple(protocol['fields']) == FIELDS
    original = read(HERE / 'results/summary.json')
    numeric = read(HERE / 'results/interval_numeric_audit.json')
    source = {**protocol['source_sha256'], 'order_denominator_protocol.json':
              sha(HERE / 'order_denominator_protocol.json')}
    bundle = PRIVATE / 'sealed_evaluation.joblib'
    assert sha(bundle) == numeric['sealed_bundle_sha256']
    data = joblib.load(bundle)
    ids = [c['case_id'] for c in data['cases']]
    result = {'status': 'executed_pending_independent_recount', 'seeds': {},
              'source_sha256': source, 'script_sha256': sha(Path(__file__)),
              'sealed_bundle_sha256': sha(bundle), 'private_prediction_sha256': {},
              'api_calls': 0, 'new_forward_passes': 0, 'original_scores_replaced': False,
              'model_or_threshold_changes': False, 'post_test_descriptive_analysis': True}
    private = {}
    for seed in [42, 137, 2026]:
        path = PRIVATE / f'seed_{seed}/all_test_predictions.joblib'
        assert sha(path) == numeric['artifact_sha256'][f'seed_{seed}/all_test_predictions.joblib']
        result['private_prediction_sha256'][str(seed)] = sha(path)
        saved = joblib.load(path)
        assert saved['case_ids'] == ids
        report = read(HERE / f'results/test_seed_{seed}.json')
        source[f'results/test_seed_{seed}.json'] = sha(HERE / f'results/test_seed_{seed}.json')
        matrices = {name: counts(pred, data['truth']) for name, pred in saved['predictions'].items()}
        private[str(seed)] = matrices
        panels = {}
        for name, matrix in matrices.items():
            m = metrics(matrix)
            if '_round_' in name:
                prefix, r = name.rsplit('_round_', 1)
                arm, kind = prefix.rsplit('_', 1)
                expected = report['accepted_curves' if kind == 'active' else 'raw_curves'][arm][int(r)]['metrics']
            else:
                expected = report['methods'][name]
            assert abs(m['original_joint_f1'] - expected['core_order_micro_f1']) < 1e-12
            assert abs(m['complete_output_fraction'] - expected['predicted_order_completion']) < 1e-12
            panels[name] = m
        left = saved['predictions']['error_prioritized']
        right = saved['predictions']['error_priority_initial_tool']
        assert all({o['drug_code'] for o in p} == {o['drug_code'] for o in q} for p, q in zip(left, right))
        paired = {}
        for a, b in protocol['paired_contrasts']:
            paired[a + '__minus__' + b] = {
                'original_and_sensitivity_difference': (score(matrices[a].sum(0)) - score(matrices[b].sum(0))).tolist(),
                'matched_complete_tuple_change': int(matrices[a][:, 0].sum() - matrices[b][:, 0].sum()),
                'complete_prediction_change': int(matrices[a][:, 1].sum() - matrices[b][:, 1].sum()),
                'emitted_prediction_change': int(matrices[a][:, 2].sum() - matrices[b][:, 2].sum())}
        for cluster in ['patient_hash', 'hospital_hash']:
            name = cluster.removesuffix('_hash') if hasattr(cluster, 'removesuffix') else cluster[:-5]
            bounds = intervals(matrices, [c[cluster] for c in data['cases']], protocol['paired_contrasts'])
            for pair, value in bounds.items():
                previous = original['paired'][str(seed)][pair][name + '_ci95']
                assert np.allclose(np.asarray(value)[:, 0], np.asarray(previous)[:, 1], atol=1e-12, rtol=0)
                paired[pair][name + '_original_and_sensitivity_ci95'] = value
        result['seeds'][str(seed)] = {'states': panels, 'paired': paired,
                                     'tool_contrast_same_drug_sets': True}
        print(json.dumps({'seed': seed, 'states_recounted': len(panels)}), flush=True)
    aggregate = {}
    for name in result['seeds']['42']['states']:
        aggregate[name] = {}
        for field in ['original_joint_f1', 'all_output_denominator_f1', 'complete_output_fraction']:
            values = [r['states'][name][field] for r in result['seeds'].values()]
            aggregate[name][field] = {'mean': float(np.mean(values)), 'seed_sd': float(np.std(values, ddof=1))}
    result['all_states'] = aggregate
    result['final_method_names'] = list(original['methods'])
    result['cases'] = len(ids)
    result['complete_reference_tuples'] = result['seeds']['42']['states']['initial_state']['complete_reference_tuples']
    assert all(sha(HERE / p) == h for p, h in source.items())
    target = PRIVATE / 'order_denominator_counts.joblib'
    joblib.dump(private, target)
    result['private_counts_sha256'] = sha(target)
    save(HERE / 'results/order_denominator_summary.json', result)
    print(json.dumps({'status': result['status'], 'states': len(aggregate), 'seeds': 3}), flush=True)


if __name__ == '__main__':
    main()
