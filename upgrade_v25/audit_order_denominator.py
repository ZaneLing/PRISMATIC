"""Independent per-stay source recount for the post-test denominator sensitivity."""
import json
from pathlib import Path
import joblib
import numpy as np
from data_contract import HERE, PRIVATE, sha, save


def independently_count(pred, reference):
    # Canonical serialized fields and explicit dictionaries instead of evaluator tuple sets.
    observed = {}
    for order in reference:
        values = [order.get('drug_code'), order.get('route'), order.get('dosage'), order.get('frequency')]
        if all(v is not None for v in values):
            observed[json.dumps(values, ensure_ascii=False)] = True
    emitted = {}
    for order in pred:
        values = [order.get('drug_code'), order.get('route'), order.get('dosage'), order.get('frequency')]
        emitted[json.dumps(values, ensure_ascii=False)] = all(v is not None for v in values)
    matched = sum(1 for text, complete in emitted.items() if complete and text in observed)
    return [matched, sum(emitted.values()), len(emitted), len(observed)]


def main():
    path = HERE / 'results/order_denominator_summary.json'
    report = json.loads(path.read_text())
    assert report['status'] == 'executed_pending_independent_recount'
    assert report['script_sha256'] == sha(HERE / 'evaluate_order_denominator.py')
    assert all(sha(HERE / p) == h for p, h in report['source_sha256'].items())
    assert sha(PRIVATE / 'sealed_evaluation.joblib') == report['sealed_bundle_sha256']
    assert sha(PRIVATE / 'order_denominator_counts.joblib') == report['private_counts_sha256']
    gold = joblib.load(PRIVATE / 'sealed_evaluation.joblib')
    counts = joblib.load(PRIVATE / 'order_denominator_counts.joblib')
    total_states = 0
    for seed, panel in report['seeds'].items():
        source = PRIVATE / f'seed_{seed}/all_test_predictions.joblib'
        assert sha(source) == report['private_prediction_sha256'][seed]
        saved = joblib.load(source)
        assert saved['case_ids'] == [c['case_id'] for c in gold['cases']]
        for name, predictions in saved['predictions'].items():
            matrix = np.asarray([independently_count(p, g) for p, g in zip(predictions, gold['truth'])], dtype=np.int64)
            assert np.array_equal(matrix, counts[seed][name])
            m = panel['states'][name]
            hit, complete, emitted, reference = map(int, matrix.sum(0))
            assert [hit, complete, emitted, reference] == [m[k] for k in [
                'matched_complete_tuples', 'complete_predicted_tuples', 'all_predicted_tuples', 'complete_reference_tuples']]
            assert abs(2 * hit / max(1, complete + reference) - m['original_joint_f1']) < 1e-12
            assert abs(2 * hit / max(1, emitted + reference) - m['all_output_denominator_f1']) < 1e-12
            total_states += 1
        print(json.dumps({'seed': seed, 'independent_source_recount': 'passed'}), flush=True)
    assert total_states == 129
    proof = {'status': 'passed', 'auditor_sha256': sha(Path(__file__)), 'summary_sha256': sha(path),
             'states_recounted': total_states, 'per_stay_count_vectors_recounted': total_states * len(gold['truth']),
             'maximum_count_difference': 0, 'original_scoring_unchanged': True,
             'scope': 'Independent canonical-serialization source count reconstruction and both denominator formulas for every saved state. Original interval endpoints are checked by the evaluator against the previous integer audit; the new sensitivity intervals use those same integer cluster draws, not a second independently executed bootstrap. No model forward or optimizer replay.',
             'api_calls': 0}
    save(HERE / 'results/order_denominator_audit.json', proof)
    print(json.dumps({'status': 'passed', 'states_recounted': total_states}), flush=True)


if __name__ == '__main__':
    main()
