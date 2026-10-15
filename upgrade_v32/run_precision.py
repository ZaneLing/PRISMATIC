"""Source-locked clinical precision replay with private shared hidden-state receipts."""
import argparse
import fcntl
import gc
import hashlib
import json
import sys
import time
import uuid
from pathlib import Path

import mlx.core as mx
import numpy as np
from mlx_lm import load

from evaluate import state_inventory
from inference import digest, encode
from precision_metrics import READOUTS, summarize
from precision_readout import array_digest, head_rows, projections
from rank_diagnostic import immutable, select

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIVATE = Path.home() / 'Desktop/MedTreeBench/dataset/restricted/prismatic-v32'
MODEL = Path.home() / 'Desktop/PRISMATIC/upgrade_v2/.local/models/qwen3-4b-instruct-2507-4bit'
sys.path.insert(0, str(ROOT / 'upgrade_v31'))
from views import view


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(split):
    (PRIVATE / 'precision').mkdir(parents=True, exist_ok=True)
    lease = (PRIVATE / 'precision/execution-process.lock').open('a')
    fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
    lock_path = HERE / 'results/precision_execution_lock.json'
    lock = json.loads(lock_path.read_text())
    assert all(sha(ROOT / name) == value for name, value in lock['source_sha256'].items())
    assert sha(HERE / 'results/precision_probe.json') == lock['numeric_probe_sha256']
    proof = json.loads((HERE / 'results/precision_probe_audit.json').read_text())
    assert proof['status'] == 'passed' and sha(HERE / 'results/precision_probe_audit.json') == lock['numeric_probe_audit_sha256']
    assert proof['auditor_sha256'] == sha(HERE / 'audit_precision_probe.py')
    pipeline = json.loads((HERE / 'results/precision_pipeline_probe.json').read_text())
    assert pipeline['status'] == 'passed' and sha(HERE / 'results/precision_pipeline_probe.json') == lock['pipeline_probe_sha256']
    output = HERE / f'results/{split}_precision.json'
    if output.exists():
        previous = json.loads(output.read_text())
        assert previous['execution_lock_sha256'] == sha(lock_path)
        print(json.dumps({'status': 'already_complete', 'split': split}), flush=True)
        return
    protocol = json.loads((HERE / 'precision_protocol.json').read_text())
    ranking = json.loads((HERE / 'rank_diagnostic_protocol.json').read_text())
    parent_path = HERE / f'results/{split}_summary.json'
    parent_audit_path = HERE / f'results/{split}_audit.json'
    parent = json.loads(parent_path.read_text())
    parent_audit = json.loads(parent_audit_path.read_text())
    assert parent_audit['status'] == 'passed' and parent_audit['summary_sha256'] == sha(parent_path)
    assert parent_audit['auditor_sha256'] == sha(HERE / 'audit_evaluation.py')
    parent_lock = json.loads((PRIVATE / 'evaluation_lock.json').read_text())
    assert all(sha(ROOT / name) == value for name, value in parent_lock['source_sha256'].items())
    assert parent['evaluation_lock_sha256'] == sha(PRIVATE / 'evaluation_lock.json')
    config = json.loads((PRIVATE / 'decision_config.json').read_text())
    assert sha(PRIVATE / 'decision_config.json') == parent_lock['decision_config_sha256']
    source = PRIVATE.parent / 'prismatic-v31/cases.json'
    assert sha(source) == parent_lock['source_cases_sha256']
    original = json.loads(source.read_text())['validation' if split == 'proposal' else 'guard']
    cases = {kind: [view(c, kind) for c in original] for kind in parent['views']}
    states = state_inventory()
    assert {name: state['version'] for name, state in states.items()} == parent_lock['state_versions']
    probabilities, binding_hashes, replay, accounting = {}, {}, {}, {}
    for name, state in states.items():
        probabilities[name], binding_hashes[name], replay[name], accounting[name] = {}, {}, {}, {}
        model = tok = None
        cache = PRIVATE / 'precision/inference' / name
        cache.mkdir(parents=True, exist_ok=True)
        try:
            for kind, group in cases.items():
                old_path = PRIVATE / 'inference' / name / 'bindings' / f'{split}-{kind}.json'
                assert sha(old_path) == parent['binding_sha256'][name][kind]
                old_bindings = json.loads(old_path.read_text())
                assert len(old_bindings) == len(group)
                bindings, vectors = [], {key: [] for key in READOUTS}
                seconds, new_prompts, replay_delta, changed = 0., 0, 0., 0
                for start in range(0, len(group), 4):
                    chunk = group[start:start + 4]
                    signatures = [digest([state['version'], sha(lock_path), c['messages'], config, 'shared_precision_hidden_v1']) for c in chunk]
                    paths = [cache / f'{signature}.json' for signature in signatures]
                    # Replay the original four-case batch if any receipt is missing.
                    # Complete receipts are validated and never overwritten.
                    if not all(path.exists() for path in paths):
                        if model is None:
                            model, tok = load(str(MODEL), adapter_path=str(state['adapter']) if state['adapter'] else None)
                            rows = head_rows(model, config['zero_token_id'], config['one_token_id'])
                            head_hash = array_digest({key: np.asarray(value) for key, value in rows.items() if key != 'dense'})
                            assert head_hash == lock['stored_head_rows_sha256']
                        encoded = [encode(tok, c, config) for c in chunk]
                        length = max(len(x) for x, _ in encoded)
                        pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
                        tokens = mx.array([x + [pad] * (length - len(x)) for x, _ in encoded], dtype=mx.int32)
                        positions = mx.array([p for _, p in encoded], dtype=mx.int32)
                        attempt_dir = cache / f'{split}-{kind}-attempts'
                        attempt_id = uuid.uuid4().hex
                        attempt = {'signatures': signatures, 'batch_size': len(chunk), 'execution_lock_sha256': sha(lock_path)}
                        immutable(attempt_dir / f'{attempt_id}-started.json', attempt)
                        begin = time.perf_counter()
                        body = model.model(tokens)
                        hidden = mx.take_along_axis(body, (positions - 1)[..., None], axis=1)
                        logits, native_dtype = projections(model, hidden, rows, config['zero_token_id'], config['one_token_id'])
                        probs = {key: mx.softmax(value, axis=-1)[..., 1] for key, value in logits.items()}
                        mx.eval(hidden, *logits.values(), *probs.values())
                        elapsed = time.perf_counter() - begin
                        immutable(attempt_dir / f'{attempt_id}-completed.json', {**attempt, 'seconds': elapsed})
                        hidden_np = np.asarray(hidden.astype(mx.float32))
                        logits_np = {key: np.asarray(value) for key, value in logits.items()}
                        probs_np = {key: np.asarray(value) for key, value in probs.items()}
                        for offset, (c, signature, path, encoded_one) in enumerate(zip(chunk, signatures, paths, encoded)):
                            if path.exists():
                                continue
                            arrays = {'hidden': hidden_np[offset], **{key + '_logits': value[offset] for key, value in logits_np.items()},
                                      **{key + '_probabilities': value[offset] for key, value in probs_np.items()}}
                            array_path = path.with_suffix('.npz')
                            with array_path.with_suffix('.npz.tmp').open('wb') as handle:
                                np.savez_compressed(handle, **arrays)
                            array_path.with_suffix('.npz.tmp').replace(array_path)
                            immutable(path, {'signature': signature, 'state_version': state['version'], 'execution_lock_sha256': sha(lock_path),
                                             'prompt_sha256': digest(c['messages']), 'array_sha256': sha(array_path),
                                             'decision_positions': encoded_one[1], 'input_tokens': len(encoded_one[0]),
                                             'actual_batch_size': len(chunk), 'seconds_per_prompt': elapsed / len(chunk),
                                             'hidden_dtype': str(hidden.dtype), 'native_projection_dtype': native_dtype,
                                             'stored_head_rows_sha256': head_hash})
                            new_prompts += 1
                        del tokens, positions, body, hidden, logits, probs
                        mx.clear_cache()
                    for offset, (c, signature, path) in enumerate(zip(chunk, signatures, paths)):
                        old = old_bindings[start + offset]
                        assert old['case_id'] == c['case_id'] and old['subject_hash'] == c['subject_hash']
                        old_raw = PRIVATE / 'inference' / name / 'raw' / f"{old['signature']}.json"
                        assert sha(old_raw) == old['raw_sha256']
                        old_meta = json.loads(old_raw.read_text())
                        meta = json.loads(path.read_text())
                        assert meta['signature'] == signature and meta['state_version'] == state['version']
                        assert meta['execution_lock_sha256'] == sha(lock_path) and meta['prompt_sha256'] == digest(c['messages'])
                        assert meta['input_tokens'] == old_meta['input_tokens'] and meta['decision_positions'] == old_meta['decision_positions']
                        assert meta['array_sha256'] == sha(path.with_suffix('.npz'))
                        with np.load(path.with_suffix('.npz')) as data:
                            assert data['hidden'].shape == (20, 2560) and all(np.isfinite(data[key]).all() for key in data.files)
                            for key in READOUTS:
                                vectors[key].append(data[key + '_probabilities'].astype(float).tolist())
                            delta = float(np.max(np.abs(data['native_probabilities'] - np.asarray(old['conditional_probabilities']))))
                            assert delta <= protocol['tolerances_fixed_before_preflight']['native_parent_probability_replay_max_absolute_delta'], (name, kind, delta)
                            replay_delta = max(replay_delta, delta)
                            first = select([old['conditional_probabilities']], [c], ranking['primary_tie_rule'], ranking)[0][0]
                            second = select([data['native_probabilities']], [c], ranking['primary_tie_rule'], ranking)[0][0]
                            changed += {o['drug_name'] for o in first} != {o['drug_name'] for o in second}
                        seconds += meta['seconds_per_prompt']
                        bindings.append({'case_id': c['case_id'], 'subject_hash': c['subject_hash'], 'signature': signature,
                                         'metadata_sha256': sha(path), 'array_sha256': meta['array_sha256']})
                    print(json.dumps({'state': name, 'view': kind, 'completed_cases': start + len(chunk), 'total': len(group)}), flush=True)
                binding_path = cache / f'{split}-{kind}-bindings.json'
                immutable(binding_path, bindings)
                probabilities[name][kind] = {key: np.asarray(value) for key, value in vectors.items()}
                binding_hashes[name][kind] = sha(binding_path)
                replay[name][kind] = {'max_native_probability_difference_from_parent': replay_delta, 'native_top8_changed_from_parent_cases': changed}
                accounting[name][kind] = {'logical_case_forwards': len(group), 'shared_backbone_forward_seconds': seconds,
                                          'new_prompt_receipts_this_invocation': new_prompts,
                                          'scope': 'One shared backbone pass for three readouts; time includes all three projections, excludes loading/tokenization. The attempt ledger separately counts completed repeated batches and unresolved attempts.'}
                attempt_dir = cache / f'{split}-{kind}-attempts'
                starts = sorted(attempt_dir.glob('*-started.json'))
                completed_attempts = sorted(attempt_dir.glob('*-completed.json'))
                completed_values = [json.loads(p.read_text()) for p in completed_attempts]
                accounting[name][kind].update(completed_forward_batches=len(completed_attempts),
                    completed_actual_case_forwards=sum(v['batch_size'] for v in completed_values),
                    completed_actual_forward_seconds=sum(v['seconds'] for v in completed_values),
                    unresolved_forward_attempts=len(starts)-len(completed_attempts),
                    attempt_ledger_sha256={p.name:sha(p) for p in starts+completed_attempts})
        finally:
            if model is not None:
                del model, tok, rows
                gc.collect()
                mx.clear_cache()
    result = {'status': 'executed_pending_independent_audit', 'split': split, 'cases': len(original),
              'patients': len({c['subject_hash'] for c in original}), 'execution_lock_sha256': sha(lock_path),
              'parent_summary_sha256': sha(parent_path), 'parent_audit_sha256': sha(parent_audit_path),
              'state_versions': parent_lock['state_versions'], 'binding_sha256': binding_hashes,
              'native_replay': replay, 'inference_accounting': accounting,
              **summarize(probabilities, cases, ranking), 'api_calls': 0, 'training_steps': 0,
              'test_predictions_read': False, 'scope': protocol['statistical_scope']}
    immutable(output, result)
    print(json.dumps({'status': result['status'], 'split': split, 'cases': len(original)}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('split', choices=['proposal', 'guard'])
    main(parser.parse_args().split)
