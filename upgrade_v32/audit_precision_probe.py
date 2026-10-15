"""Reconstruct frozen output rows directly from the safetensors byte ranges."""
import hashlib
import json
import struct
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIVATE = Path.home() / 'Desktop/MedTreeBench/dataset/restricted/prismatic-v32'
MODEL = Path.home() / 'Desktop/PRISMATIC/upgrade_v2/.local/models/qwen3-4b-instruct-2507-4bit/model.safetensors'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def model_rows(ids):
    """Read only the declared rows; no tensor-library unpacker is used."""
    with MODEL.open('rb') as handle:
        length = struct.unpack('<Q', handle.read(8))[0]
        header = json.loads(handle.read(length))
        base = 8 + length
        result = {}
        for short, suffix in [('packed', 'weight'), ('scales', 'scales'), ('offsets', 'biases')]:
            entry = header['model.embed_tokens.' + suffix]
            width = entry['shape'][1]
            dtype = '<u4' if short == 'packed' else '<u2'
            assert entry['dtype'] == ('U32' if short == 'packed' else 'BF16')
            row_bytes = width * np.dtype(dtype).itemsize
            values = []
            for index in ids:
                handle.seek(base + entry['data_offsets'][0] + index * row_bytes)
                row = np.frombuffer(handle.read(row_bytes), dtype=dtype).copy()
                if short != 'packed':
                    row = (row.astype(np.uint32) << 16).view(np.float32)
                values.append(row)
            result[short] = np.asarray(values)
    return result


def main():
    path = HERE / 'results/precision_probe.json'
    report = json.loads(path.read_text())
    protocol = json.loads((HERE / 'precision_protocol.json').read_text())
    parent = json.loads((PRIVATE / 'evaluation_lock.json').read_text())
    assert report['status'] == 'passed' and report['synthetic_only']
    assert report['protocol_sha256'] == sha(HERE / 'precision_protocol.json')
    assert all(sha(ROOT / name) == h for name, h in report['source_sha256'].items())
    assert sha(MODEL) == parent['state_versions']['frozen_base']
    assert {row['state']: row['state_version'] for row in report['states']} == parent['state_versions']
    config = json.loads((PRIVATE / 'decision_config.json').read_text())
    assert sha(PRIVATE / 'decision_config.json') == report['decision_config_sha256'] == parent['decision_config_sha256']
    rows = model_rows([config['zero_token_id'], config['one_token_id']])
    dense = np.empty((2, 2560), dtype=np.float64)
    for i in range(2):
        for j in range(2560):
            integer = (int(rows['packed'][i, j // 8]) >> (4 * (j % 8))) & 15
            dense[i, j] = integer * float(rows['scales'][i, j // 64]) + float(rows['offsets'][i, j // 64])
    tolerance = protocol['tolerances_fixed_before_preflight']
    maxima = {'weight': 0., 'dense_logit': 0., 'binary_probability': 0., 'rounding': 0.}
    logits_count = 0
    for state in report['states']:
        private = PRIVATE / 'precision/synthetic' / state['state'] / 'readout.npz'
        assert sha(private) == state['private_array_sha256']
        with np.load(private) as data:
            assert data['hidden'].shape == (2, 20, 2560)
            assert all(np.isfinite(data[n]).all() for n in data.files)
            for name, value in rows.items():
                assert np.array_equal(data[name], value), (state['state'], name)
            weight_delta = float(np.max(np.abs(data['dense'] - dense)))
            exact = np.einsum('bth,kh->btk', data['hidden'].astype(np.float64), dense)
            logit_delta = float(np.max(np.abs(exact - data['fp32_binary_logits'])))
            bits = data['fp32_binary_logits'].astype(np.float32).view(np.uint32)
            upper = bits >> 16
            lower = bits & 65535
            increment = (lower > 32768) | ((lower == 32768) & ((upper & 1) == 1))
            rounded = ((upper + increment.astype(np.uint32)) << 16).view(np.float32)
            round_delta = float(np.max(np.abs(rounded - data['fp32_rerounded_logits'])))
            probability_delta = 0.
            for name in ['native', 'fp32_binary', 'fp32_rerounded']:
                z = data[name + '_logits'].astype(np.float64)
                expected = 1. / (1. + np.exp(z[..., 0] - z[..., 1]))
                p = data[name + '_probabilities']
                probability_delta = max(probability_delta, float(np.max(np.abs(expected - p))))
                assert [len(np.unique(vector)) for vector in p] == state['unique_scores_per_synthetic_prompt'][name]
                logits_count += z.size
            exact_probability = 1. / (1. + np.exp(exact[..., 0] - exact[..., 1]))
            probability_delta = max(probability_delta, float(np.max(np.abs(exact_probability - data['fp32_binary_probabilities']))))
            assert weight_delta <= tolerance['dense_weight_max_absolute_delta']
            assert logit_delta <= tolerance['dense_logit_max_absolute_delta']
            assert probability_delta <= tolerance['binary_probability_max_absolute_delta']
            assert round_delta <= tolerance['rounding_control_max_absolute_delta']
            for name, value in [('weight', weight_delta), ('dense_logit', logit_delta), ('binary_probability', probability_delta), ('rounding', round_delta)]:
                maxima[name] = max(maxima[name], value)
    result = {'status': 'passed', 'synthetic_only': True, 'auditor_sha256': sha(Path(__file__)),
              'probe_sha256': sha(path), 'model_sha256': sha(MODEL), 'states': len(report['states']),
              'source_binary_rows_read': 2, 'readout_logit_values_recounted': logits_count,
              'maximum_numeric_residuals': maxima, 'clinical_case_forwards': 0,
              'scope': 'Independent raw-safetensors row extraction, scalar four-bit affine reconstruction, float64 hidden-state projection, alternate nearest-even bfloat16 rounding, probability and tie-count recount. Does not reexecute the backbone or establish clinical performance.'}
    (HERE / 'results/precision_probe_audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
