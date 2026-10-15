# v0.32 frozen readout precision comparison

## 1. What changes

All three readouts share the same frozen backbone hidden states. Native uses the original quantized vocabulary projection. FP32 reconstructs only the two output-token rows from the same stored four-bit weights/scales/offsets and projects in float32. Re-rounded casts those FP32 logits to bfloat16 and back before softmax. Memory, tools, backbone/adapter weights and candidate templates remain unchanged.

FP32 versus re-rounded isolates final-logit rounding within the new dense projection. Native versus FP32 also changes projection arithmetic, so its entire effect cannot be assigned to final rounding. Any benefit is a numerical implementation effect; it does not demonstrate learned RSI. The backbone remains quantized.

[Protocol](precision_protocol.json) · [Frozen clinical implementation](results/precision_execution_lock.json) · [Earlier ranking diagnosis](RANKING_DIAGNOSTIC.en.md)

## 2. Completed engineering preflight

Six actual frozen model states, two synthetic prompts each, twenty binary decisions per prompt. These twelve backbone case-forwards contain no clinical cases or target labels. Distinct-score counts below are numerical diagnostics, not prescription performance.

| State | Native: prompt 1 / 2 | FP32: prompt 1 / 2 | Re-rounded: prompt 1 / 2 |
|---|---:|---:|---:|
| Frozen base | 18/18 | 20/20 | 18/18 |
| Original failed adapter | 16/15 | 20/20 | 16/14 |
| GT prefix / uniform | 16/12 | 20/20 | 16/12 |
| Zero prefix / uniform | 3/4 | 20/20 | 4/4 |
| GT prefix / balanced | 15/13 | 20/20 | 14/13 |
| Zero prefix / balanced | 3/3 | 20/20 | 3/3 |

Independent byte-level extraction of the two embedding rows and NumPy reconstruction pass. Maximum float64-reference logit difference: 8.944e-06; probability difference: 2.713e-06; re-rounding difference: 0.0. All six states have bfloat16 hidden states and native projection outputs. Native versus re-rounded probabilities differ by up to 0.01562, confirming that the two projection implementations are not numerically identical.

This preflight confirms that final-logit rounding can collapse distinct synthetic scores. It does not establish improved medication ranking, prescription F1 or clinical benefit.

[Preflight receipt](results/precision_probe.json) · [Independent raw-weight audit](results/precision_probe_audit.json) · [Synthetic scoring-pipeline audit](results/precision_pipeline_probe.json)

## 3. Clinical comparison: awaiting independent audit

The dedicated evaluator and independent auditor are implemented and frozen. The proposal run has been launched for all six states, ranked/permuted views, three shared-hidden-state readouts and both identity-based tie rules. No independently audited clinical precision score is available yet. Original model/threshold selection and test gates remain unchanged.
