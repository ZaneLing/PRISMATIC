"""Three binary readouts sharing frozen, unchanged backbone hidden states."""
import hashlib

import mlx.core as mx
import numpy as np


def head_rows(model, zero_id, one_id):
    assert model.args.tie_word_embeddings
    head = model.model.embed_tokens
    assert head.bits == 4 and head.group_size == 64 and head.mode == 'affine'
    ids = mx.array([zero_id, one_id])
    packed = head.weight[ids]
    scales = head.scales[ids].astype(mx.float32)
    offsets = head.biases[ids].astype(mx.float32)
    dense = mx.dequantize(packed, scales=scales, biases=offsets, group_size=head.group_size,
                          bits=head.bits, mode=head.mode, dtype=mx.float32)
    mx.eval(packed, scales, offsets, dense)
    return {'packed': packed, 'scales': scales, 'offsets': offsets, 'dense': dense}


def projections(model, hidden, rows, zero_id, one_id):
    wide = model.model.embed_tokens.as_linear(hidden)
    native = wide[..., mx.array([zero_id, one_id])].astype(mx.float32)
    precise = hidden.astype(mx.float32) @ rows['dense'].T
    rounded = precise.astype(mx.bfloat16).astype(mx.float32)
    return {'native': native, 'fp32_binary': precise, 'fp32_rerounded': rounded}, str(wide.dtype)


def unpack_numpy(packed, scales, offsets):
    """Independent scalar affine reconstruction, with float64 arithmetic."""
    packed = np.asarray(packed, dtype=np.uint32)
    shifts = np.arange(8, dtype=np.uint32) * 4
    values = ((packed[..., None] >> shifts) & 15).reshape(packed.shape[0], -1)
    return values.astype(np.float64) * np.repeat(np.asarray(scales, dtype=np.float64), 64, axis=1) + np.repeat(np.asarray(offsets, dtype=np.float64), 64, axis=1)


def round_bfloat16_numpy(values):
    """Round finite float32 values to nearest-even bfloat16, then expand."""
    values = np.asarray(values, dtype=np.float32)
    assert np.isfinite(values).all()
    bits = values.view(np.uint32)
    rounded = (bits + np.uint32(0x7fff) + ((bits >> 16) & 1)) & np.uint32(0xffff0000)
    return rounded.view(np.float32)


def probability_numpy(logits):
    z = np.asarray(logits, dtype=np.float64)
    z = z - z.max(axis=-1, keepdims=True)
    e = np.exp(z)
    return e[..., 1] / e.sum(axis=-1)


def array_digest(arrays):
    h = hashlib.sha256()
    for name, value in sorted(arrays.items()):
        a = np.ascontiguousarray(value)
        h.update(name.encode())
        h.update(str(a.dtype).encode())
        h.update(str(a.shape).encode())
        h.update(a.tobytes())
    return h.hexdigest()
