"""Independent CPU readout replay and all fixed-eight clinical metric recounts."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from audit_evaluation import compare, metrics, paired, transformed
from audit_precision_probe import MODEL as MODEL_FILE, model_rows
from audit_rank_diagnostic import case_auc, rank_alignment, selected, set_agreement

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIVATE = Path.home() / 'Desktop/MedTreeBench/dataset/restricted/prismatic-v32'
READOUTS = ['native', 'fp32_binary', 'fp32_rerounded']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def independently_summarize(probabilities, cases, spec):
    states = list(probabilities)
    panels, changes, stable = {}, {}, {}
    for rule in spec['tie_rules']:
        panels[rule], changes[rule], predictions = {}, {}, {}
        for kind, group in cases.items():
            panels[rule][kind], predictions[kind], evidence = {}, {}, {}
            for readout in READOUTS:
                methods, records, preds = {}, {}, {}
                for state in states:
                    vectors = probabilities[state][kind][readout]
                    picks = [selected(p, c, rule, spec) for p, c in zip(vectors, group)]
                    preds[state] = [p[0] for p in picks]
                    methods[state], records[state] = metrics(preds[state], group)
                    values = [case_auc(p, c) for p, c in zip(vectors, group)]
                    eligible = [v for v in values if v is not None]
                    methods[state].update(boundary_tie_cases=sum(int(p[1]) for p in picks),
                        mean_unique_scores=sum(len(set(p.tolist())) for p in vectors)/len(vectors),
                        within_case_auroc_mean=sum(eligible)/len(eligible) if eligible else None,
                        within_case_auroc_eligible_cases=len(eligible), within_case_auroc_excluded_cases=len(values)-len(eligible))
                control = spec['control']
                preds[control] = [[o for o,r in zip(c['catalogue'].values(),c['original_rank_by_position']) if r <= 8] for c in group]
                methods[control], records[control] = metrics(preds[control], group)
                panels[rule][kind][readout] = {'methods': methods, 'contrasts_vs_retrieval': {
                    state: paired([(1,records[state]),(-1,records[control])]) for state in states}}
                predictions[kind][readout], evidence[readout] = preds, records
            changes[rule][kind] = {state: {
                'fp32_minus_native': paired([(1,evidence['fp32_binary'][state]),(-1,evidence['native'][state])]),
                'fp32_minus_rerounded': paired([(1,evidence['fp32_binary'][state]),(-1,evidence['fp32_rerounded'][state])]),
                'rerounded_minus_native': paired([(1,evidence['fp32_rerounded'][state]),(-1,evidence['native'][state])])}
                for state in states}
        stable[rule] = {kind: {readout: {state: set_agreement(predictions['ranked'][readout][state], methods[state]) for state in methods}
                              for readout, methods in reads.items()} for kind, reads in predictions.items() if kind != 'ranked'}
    aligned = {readout: {kind: {state: rank_alignment(probabilities[state]['ranked'][readout], probabilities[state][kind][readout], cases['ranked'], cases[kind])
                               for state in states} for kind in cases if kind != 'ranked'} for readout in READOUTS}
    return {'panels': panels, 'readout_contrasts': changes, 'top8_view_invariance': stable, 'score_rank_alignment': aligned}


def main(split):
    path = HERE / f'results/{split}_precision.json'
    report = json.loads(path.read_text())
    lock_path = HERE / 'results/precision_execution_lock.json'
    lock = json.loads(lock_path.read_text())
    assert report['execution_lock_sha256'] == sha(lock_path)
    assert all(sha(ROOT / n) == value for n, value in lock['source_sha256'].items())
    protocol = json.loads((HERE / 'precision_protocol.json').read_text())
    tolerance = protocol['tolerances_fixed_before_preflight']
    spec = json.loads((HERE / 'rank_diagnostic_protocol.json').read_text())
    parent = json.loads((HERE / f'results/{split}_summary.json').read_text())
    parent_audit = json.loads((HERE / f'results/{split}_audit.json').read_text())
    assert parent_audit['status'] == 'passed' and parent_audit['summary_sha256'] == sha(HERE / f'results/{split}_summary.json') == report['parent_summary_sha256']
    assert report['parent_audit_sha256'] == sha(HERE / f'results/{split}_audit.json')
    assert parent_audit['auditor_sha256'] == sha(HERE / 'audit_evaluation.py')
    parent_lock = json.loads((PRIVATE / 'evaluation_lock.json').read_text())
    assert sha(MODEL_FILE) == parent_lock['state_versions']['frozen_base']
    assert all(sha(ROOT / n) == value for n, value in parent_lock['source_sha256'].items())
    assert report['state_versions'] == parent_lock['state_versions']
    source = PRIVATE.parent / 'prismatic-v31/cases.json'
    assert sha(source) == parent_lock['source_cases_sha256']
    original = json.loads(source.read_text())['validation' if split == 'proposal' else 'guard']
    cases = {kind: [transformed(c, kind) for c in original] for kind in parent['views']}
    assert report['cases'] == len(original) and report['patients'] == len({c['subject_hash'] for c in original})
    config = json.loads((PRIVATE / 'decision_config.json').read_text())
    assert sha(PRIVATE / 'decision_config.json') == parent_lock['decision_config_sha256']
    raw_rows = model_rows([config['zero_token_id'], config['one_token_id']])
    weights = np.empty((2, 2560), dtype=np.float64)
    for row in range(2):
        for column in range(2560):
            value = (int(raw_rows['packed'][row, column//8]) >> (4*(column%8))) & 15
            weights[row,column] = value*float(raw_rows['scales'][row,column//64])+float(raw_rows['offsets'][row,column//64])
    probabilities = {}
    max_dot = max_probability = 0.
    count = 0
    total_completed_forwards = unresolved = 0
    for state, version in report['state_versions'].items():
        probabilities[state] = {}
        cache = PRIVATE / 'precision/inference' / state
        for kind, group in cases.items():
            binding_path = cache / f'{split}-{kind}-bindings.json'
            assert sha(binding_path) == report['binding_sha256'][state][kind]
            bindings = json.loads(binding_path.read_text())
            old_path = PRIVATE / 'inference' / state / 'bindings' / f'{split}-{kind}.json'
            assert sha(old_path) == parent['binding_sha256'][state][kind]
            old_bindings = json.loads(old_path.read_text())
            assert len(bindings) == len(group) == len(old_bindings)
            result = {key: [] for key in READOUTS}
            delta_replay, changed, seconds = 0., 0, 0.
            for row, old, c in zip(bindings, old_bindings, group):
                assert row['case_id'] == old['case_id'] == c['case_id'] and row['subject_hash'] == old['subject_hash'] == c['subject_hash']
                signature = digest([version, sha(lock_path), c['messages'], config, 'shared_precision_hidden_v1'])
                assert row['signature'] == signature
                meta_path = cache / f'{signature}.json'
                meta = json.loads(meta_path.read_text())
                assert sha(meta_path) == row['metadata_sha256']
                assert meta['execution_lock_sha256'] == sha(lock_path) and meta['state_version'] == version
                assert meta['stored_head_rows_sha256'] == lock['stored_head_rows_sha256'] and meta['prompt_sha256'] == digest(c['messages'])
                old_meta_path = PRIVATE / 'inference' / state / 'raw' / f"{old['signature']}.json"
                assert sha(old_meta_path) == old['raw_sha256']
                old_meta = json.loads(old_meta_path.read_text())
                assert meta['input_tokens'] == old_meta['input_tokens'] and meta['decision_positions'] == old_meta['decision_positions']
                arrays_path = meta_path.with_suffix('.npz')
                assert sha(arrays_path) == row['array_sha256'] == meta['array_sha256']
                with np.load(arrays_path) as data:
                    assert data['hidden'].shape == (20,2560) and all(np.isfinite(data[n]).all() for n in data.files)
                    exact = np.einsum('th,kh->tk',data['hidden'].astype(np.float64),weights)
                    dot_delta = float(np.max(np.abs(exact-data['fp32_binary_logits'])))
                    assert dot_delta <= tolerance['dense_logit_max_absolute_delta']
                    max_dot = max(max_dot,dot_delta)
                    bits = data['fp32_binary_logits'].astype(np.float32).view(np.uint32)
                    upper, lower = bits>>16, bits&65535
                    extra = (lower>32768)|((lower==32768)&((upper&1)==1))
                    rounded = ((upper+extra.astype(np.uint32))<<16).view(np.float32)
                    assert np.array_equal(rounded,data['fp32_rerounded_logits'])
                    for readout in READOUTS:
                        logits = data[readout+'_logits'].astype(np.float64)
                        p = data[readout+'_probabilities']
                        assert logits.shape == (20,2) and p.shape == (20,) and ((p>=0)&(p<=1)).all()
                        expected = 1./(1.+np.exp(logits[:,0]-logits[:,1]))
                        error = float(np.max(np.abs(expected-p)))
                        assert error <= tolerance['binary_probability_max_absolute_delta']
                        max_probability = max(max_probability,error)
                        result[readout].append(p.astype(float))
                    p_exact = 1./(1.+np.exp(exact[:,0]-exact[:,1]))
                    error = float(np.max(np.abs(p_exact-data['fp32_binary_probabilities'])))
                    assert error <= tolerance['binary_probability_max_absolute_delta']
                    max_probability = max(max_probability,error)
                    error = float(np.max(np.abs(data['native_probabilities']-np.asarray(old['conditional_probabilities']))))
                    assert error <= tolerance['native_parent_probability_replay_max_absolute_delta']
                    delta_replay = max(delta_replay,error)
                    first = selected(old['conditional_probabilities'],c,spec['primary_tie_rule'],spec)[0]
                    second = selected(data['native_probabilities'],c,spec['primary_tie_rule'],spec)[0]
                    changed += {o['drug_name'] for o in first}!={o['drug_name'] for o in second}
                seconds += meta['seconds_per_prompt']
                count += 1
            probabilities[state][kind] = {k:np.asarray(v) for k,v in result.items()}
            compare(report['native_replay'][state][kind],{'max_native_probability_difference_from_parent':delta_replay,'native_top8_changed_from_parent_cases':changed})
            accounting = report['inference_accounting'][state][kind]
            assert abs(accounting['shared_backbone_forward_seconds']-seconds)<1e-8 and accounting['logical_case_forwards']==len(group)
            attempt_dir = cache/f'{split}-{kind}-attempts'
            assert all(sha(attempt_dir/n)==h for n,h in accounting['attempt_ledger_sha256'].items())
            starts = sorted(attempt_dir.glob('*-started.json'))
            completes = sorted(attempt_dir.glob('*-completed.json'))
            attempts = []
            for p in completes:
                done=json.loads(p.read_text());started=json.loads(p.with_name(p.name.replace('-completed','-started')).read_text())
                assert {k:v for k,v in done.items() if k!='seconds'}==started and done['execution_lock_sha256']==sha(lock_path)
                assert len(done['signatures'])==done['batch_size'] and done['seconds']>=0
                attempts.append(done)
            assert accounting['completed_forward_batches']==len(completes)
            assert accounting['completed_actual_case_forwards']==sum(a['batch_size'] for a in attempts)
            assert abs(accounting['completed_actual_forward_seconds']-sum(a['seconds'] for a in attempts))<1e-8
            assert accounting['unresolved_forward_attempts']==len(starts)-len(completes)
            total_completed_forwards+=accounting['completed_actual_case_forwards'];unresolved+=accounting['unresolved_forward_attempts']
    expected = independently_summarize(probabilities,cases,spec)
    for key,value in expected.items():compare(report[key],value)
    assert report['api_calls']==report['training_steps']==0 and report['test_predictions_read'] is False
    receipt={'status':'passed','split':split,'auditor_sha256':sha(Path(__file__)),'summary_sha256':sha(path),
             'execution_lock_sha256':sha(lock_path),'shared_hidden_state_receipts_replayed':count,
             'binary_logit_values_checked':count*20*2*3,'completed_actual_case_forwards':total_completed_forwards,
             'unresolved_forward_attempts':unresolved,'maximum_fp32_dot_residual':max_dot,'maximum_probability_residual':max_probability,
             'scope':'Independent source/permutation and cached binding reconstruction, direct safetensors-row unpacking, float64 readout replay, bfloat16 rounding, all fixed-eight selections, drug/order metrics, both tie rules, rank statistics and paired patient intervals. Native projection is source-bound and checked against parent probabilities; its kernel and the backbone are not independently replayed.'}
    (HERE/f'results/{split}_precision_audit.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('split',choices=['proposal','guard']);main(parser.parse_args().split)
