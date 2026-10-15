"""Actual frozen-model synthetic probe; no clinical cases or target access."""
import gc
import hashlib
import json
import time
from pathlib import Path

import mlx.core as mx
import numpy as np
from mlx_lm import load

from evaluate import state_inventory
from inference import encode
from precision_readout import (array_digest, head_rows, probability_numpy, projections,
                               round_bfloat16_numpy, unpack_numpy)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIVATE = Path.home() / 'Desktop/MedTreeBench/dataset/restricted/prismatic-v32'
MODEL = Path.home() / 'Desktop/PRISMATIC/upgrade_v2/.local/models/qwen3-4b-instruct-2507-4bit'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    public = HERE / 'results/precision_probe.json'
    assert not public.exists(), 'A completed probe must not be silently rerun.'
    protocol = json.loads((HERE / 'precision_protocol.json').read_text())
    tolerance = protocol['tolerances_fixed_before_preflight']
    config = json.loads((PRIVATE / 'decision_config.json').read_text())
    parent = json.loads((PRIVATE / 'evaluation_lock.json').read_text())
    assert sha(PRIVATE / 'decision_config.json') == parent['decision_config_sha256']
    states = state_inventory()
    assert list(states) == protocol['states']
    synthetic = [{'messages': [{'role': 'system', 'content': 'Synthetic numerical probe. No clinical records. Return a JSON inclusion mask with twenty binary values.'},
                               {'role': 'user', 'content': '\n'.join(f'O{i+1}: synthetic item {i+j}; synthetic attribute {(i+j)%5}' for i in range(20))}]}
                 for j in [0, 7]]
    expected_head = None
    records = []
    for name, state in states.items():
        start = time.perf_counter()
        model, tok = load(str(MODEL), adapter_path=str(state['adapter']) if state['adapter'] else None)
        rows = head_rows(model, config['zero_token_id'], config['one_token_id'])
        arrays = {key: np.asarray(value) for key, value in rows.items()}
        head_hash = array_digest({key: value for key, value in arrays.items() if key != 'dense'})
        if expected_head is None:
            expected_head = head_hash
        assert head_hash == expected_head, 'Output embedding rows changed across adapter states.'
        independent_weights = unpack_numpy(arrays['packed'], arrays['scales'], arrays['offsets'])
        weight_delta = float(np.max(np.abs(independent_weights - arrays['dense'])))
        assert weight_delta <= tolerance['dense_weight_max_absolute_delta']
        encoded = [encode(tok, c, config) for c in synthetic]
        length = max(len(x[0]) for x in encoded)
        pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
        tokens = mx.array([x + [pad] * (length - len(x)) for x, _ in encoded], dtype=mx.int32)
        positions = mx.array([p for _, p in encoded], dtype=mx.int32)
        full = model.model(tokens)
        hidden = mx.take_along_axis(full, (positions - 1)[..., None], axis=1)
        logits, native_dtype = projections(model, hidden, rows, config['zero_token_id'], config['one_token_id'])
        probs = {key: mx.softmax(value, axis=-1)[..., 1] for key, value in logits.items()}
        mx.eval(hidden, *logits.values(), *probs.values())
        h = np.asarray(hidden.astype(mx.float32))
        logits_np = {key: np.asarray(value) for key, value in logits.items()}
        probs_np = {key: np.asarray(value) for key, value in probs.items()}
        reference_logits = h.astype(np.float64) @ independent_weights.T
        logit_delta = float(np.max(np.abs(reference_logits - logits_np['fp32_binary'])))
        assert logit_delta <= tolerance['dense_logit_max_absolute_delta'], (name, logit_delta)
        rounded = round_bfloat16_numpy(logits_np['fp32_binary'])
        rounding_delta = float(np.max(np.abs(rounded - logits_np['fp32_rerounded'])))
        assert rounding_delta <= tolerance['rounding_control_max_absolute_delta']
        probability_delta = {key: float(np.max(np.abs(probability_numpy(value) - probs_np[key]))) for key, value in logits_np.items()}
        probability_delta['fp32_against_float64_dot'] = float(np.max(np.abs(probability_numpy(reference_logits) - probs_np['fp32_binary'])))
        assert max(probability_delta.values()) <= tolerance['binary_probability_max_absolute_delta'], (name, probability_delta)
        save_dir = PRIVATE / 'precision/synthetic' / name
        save_dir.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(save_dir / 'readout.npz', hidden=h, **arrays,
                            **{key + '_logits': value for key, value in logits_np.items()},
                            **{key + '_probabilities': value for key, value in probs_np.items()})
        unique = {key: [len(set(vector.tolist())) for vector in value] for key, value in probs_np.items()}
        row = {'state': name, 'state_version': state['version'], 'hidden_dtype': str(hidden.dtype),
               'native_projection_dtype': native_dtype, 'stored_head_rows_sha256': head_hash,
               'max_weight_reconstruction_delta': weight_delta, 'max_dense_logit_delta': logit_delta,
               'max_rounding_control_delta': rounding_delta, 'max_binary_probability_delta': probability_delta,
               'unique_scores_per_synthetic_prompt': unique,
               'native_vs_rerounded_max_probability_delta': float(np.max(np.abs(probs_np['native'] - probs_np['fp32_rerounded']))),
               'private_array_sha256': sha(save_dir / 'readout.npz'), 'seconds_including_model_load': time.perf_counter() - start}
        records.append(row)
        print(json.dumps({'state': name, 'status': 'synthetic_numerics_passed', 'unique_scores': unique}), flush=True)
        del model, tok, rows, arrays, tokens, positions, full, hidden, logits, probs
        gc.collect()
        mx.clear_cache()
    names = ['precision_protocol.json', 'precision_readout.py', 'probe_precision.py', 'inference.py', 'decision_loss.py', 'evaluate.py']
    result = {'status': 'passed', 'synthetic_only': True, 'protocol_sha256': sha(HERE / 'precision_protocol.json'),
              'source_sha256': {str((HERE / n).relative_to(ROOT)): sha(HERE / n) for n in names},
              'decision_config_sha256': sha(PRIVATE / 'decision_config.json'), 'states': records,
              'synthetic_prompts_per_state': 2, 'backbone_case_forwards': len(records) * 2,
              'clinical_case_forwards': 0, 'training_steps': 0, 'api_calls': 0, 'guard_or_test_reads': False,
              'clinical_evaluator_complete': False,
              'scope': 'Engineering preflight on frozen real model states and synthetic inputs. NumPy independently reconstructs stored quantized rows, float64 dense readout, softmax and bfloat16 rounding; no clinical effect is measured.'}
    public.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'status': 'passed', 'synthetic_states': len(records), 'clinical_case_forwards': 0}), flush=True)


if __name__ == '__main__':
    main()
