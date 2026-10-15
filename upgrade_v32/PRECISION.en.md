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

## 3. proposal: 100 admissions / 97 patients

Post-proposal descriptive development diagnosis, one training seed. Each scored policy selects eight candidate templates. All reference drugs are retained. No new threshold, checkpoint, arm or promotion is selected. Case-level AUROC omits only admissions without both positive and negative candidates; their F1 remains included.

### Main comparison: fixed eight medications

Cells show drug/core-order micro-F1. The primary drug-identity-hash tie rule is used here; the complete tables below retain the re-rounded readout, both tie rules and paired intervals.

| State | Ranked native | Ranked FP32 | Permuted native | Permuted FP32 |
|---|---:|---:|---:|---:|
| Frozen base | 0.27096/0.18111 | 0.26962/0.17982 | 0.21462/0.14489 | 0.21462/0.14489 |
| Original failed adapter | 0.28571/0.19405 | 0.28571/0.19405 | 0.20926/0.14101 | 0.20926/0.14101 |
| GT prefix / uniform | 0.28706/0.19405 | 0.28840/0.19534 | 0.20389/0.13713 | 0.20389/0.13583 |
| Zero prefix / uniform | 0.23877/0.16171 | 0.24011/0.15653 | 0.23877/0.16041 | 0.20657/0.12807 |
| GT prefix / balanced | 0.28437/0.19405 | 0.28571/0.19405 | 0.20523/0.13842 | 0.20255/0.13583 |
| Zero prefix / balanced | 0.22401/0.14877 | 0.22401/0.15006 | 0.20255/0.14618 | 0.18779/0.12807 |
| Original retrieval top-8 | 0.28706/0.20181 | 0.28706/0.20181 | 0.28706/0.20181 | 0.28706/0.20181 |

The retrieval row is unchanged across readouts. These are shared-case implementation contrasts; a higher F1 here is not evidence that an agent learned or evolved.

**Interpretation:** FP32 removes every cutoff tie in this panel, but the six neural states still have 0% exact drug-set agreement after candidate permutation. Only teacher-prefix/uniform loss in the ranked view has a drug-F1 point estimate above retrieval: 0.28840 versus 0.28706, paired difference +0.00134 [-0.01058, +0.01313]. Its order F1 remains lower (0.19534 versus 0.20181). Every permuted-view neural configuration remains below retrieval in both endpoints. These exploratory intervals do not establish superiority. Higher readout precision does not resolve the candidate-position failure.

### Position dependence after the precision change

Spearman correlations compare drug-identity alignment with unchanged display slots. Agreement is the fraction of admissions whose complete top-eight drug set is identical after candidate permutation; the primary tie rule is used.

| State | Readout | Drug-identity ρ | Display-slot ρ | Exact set agreement |
|---|---|---:|---:|---:|
| Frozen base | native | 0.24291 | 0.72743 | 0.0% |
| Frozen base | fp32_binary | 0.24402 | 0.72654 | 0.0% |
| Frozen base | fp32_rerounded | 0.24278 | 0.72749 | 0.0% |
| Original failed adapter | native | 0.21228 | 0.79617 | 0.0% |
| Original failed adapter | fp32_binary | 0.21455 | 0.79702 | 0.0% |
| Original failed adapter | fp32_rerounded | 0.21275 | 0.79818 | 0.0% |
| GT prefix / uniform | native | 0.19792 | 0.81688 | 0.0% |
| GT prefix / uniform | fp32_binary | 0.20132 | 0.81675 | 0.0% |
| GT prefix / uniform | fp32_rerounded | 0.19940 | 0.81728 | 0.0% |
| Zero prefix / uniform | native | 0.12379 | 0.18125 | 0.0% |
| Zero prefix / uniform | fp32_binary | 0.14749 | 0.27008 | 0.0% |
| Zero prefix / uniform | fp32_rerounded | 0.12176 | 0.18721 | 0.0% |
| GT prefix / balanced | native | 0.24096 | 0.76418 | 0.0% |
| GT prefix / balanced | fp32_binary | 0.23991 | 0.76183 | 0.0% |
| GT prefix / balanced | fp32_rerounded | 0.24014 | 0.76465 | 0.0% |
| Zero prefix / balanced | native | -0.00186 | 0.15051 | 0.0% |
| Zero prefix / balanced | fp32_binary | 0.01705 | 0.44851 | 0.0% |
| Zero prefix / balanced | fp32_rerounded | 0.02690 | 0.15732 | 0.0% |

### drug_sha256

| View | State | Readout | Drug F1 | Core-order F1 | AUROC (n) | Mean distinct scores | Cutoff tie cases |
|---|---|---|---:|---:|---:|---:|---:|
| ranked | Frozen base | native | 0.27096 | 0.18111 | 0.68006 (67) | 18.29 | 14 |
| ranked | Frozen base | fp32_binary | 0.26962 | 0.17982 | 0.68062 (67) | 20.00 | 0 |
| ranked | Frozen base | fp32_rerounded | 0.27096 | 0.18111 | 0.68012 (67) | 18.30 | 13 |
| ranked | Original failed adapter | native | 0.28571 | 0.19405 | 0.70017 (67) | 16.95 | 13 |
| ranked | Original failed adapter | fp32_binary | 0.28571 | 0.19405 | 0.70007 (67) | 20.00 | 0 |
| ranked | Original failed adapter | fp32_rerounded | 0.28706 | 0.19534 | 0.69933 (67) | 16.96 | 12 |
| ranked | GT prefix / uniform | native | 0.28706 | 0.19405 | 0.69818 (67) | 16.17 | 9 |
| ranked | GT prefix / uniform | fp32_binary | 0.28840 | 0.19534 | 0.69802 (67) | 20.00 | 0 |
| ranked | GT prefix / uniform | fp32_rerounded | 0.28706 | 0.19405 | 0.69781 (67) | 16.17 | 8 |
| ranked | Zero prefix / uniform | native | 0.23877 | 0.16171 | 0.56853 (67) | 3.73 | 93 |
| ranked | Zero prefix / uniform | fp32_binary | 0.24011 | 0.15653 | 0.60723 (67) | 20.00 | 0 |
| ranked | Zero prefix / uniform | fp32_rerounded | 0.23474 | 0.15524 | 0.56200 (67) | 3.75 | 97 |
| ranked | GT prefix / balanced | native | 0.28437 | 0.19405 | 0.68927 (67) | 16.83 | 12 |
| ranked | GT prefix / balanced | fp32_binary | 0.28571 | 0.19405 | 0.68985 (67) | 20.00 | 0 |
| ranked | GT prefix / balanced | fp32_rerounded | 0.28571 | 0.19405 | 0.68926 (67) | 16.77 | 14 |
| ranked | Zero prefix / balanced | native | 0.22401 | 0.14877 | 0.56036 (67) | 2.52 | 84 |
| ranked | Zero prefix / balanced | fp32_binary | 0.22401 | 0.15006 | 0.58629 (67) | 20.00 | 0 |
| ranked | Zero prefix / balanced | fp32_rerounded | 0.22669 | 0.15006 | 0.55852 (67) | 2.58 | 95 |
| ranked | Original retrieval top-8 | — | 0.28706 | 0.20181 | — | — | — |
| permuted | Frozen base | native | 0.21462 | 0.14489 | 0.55057 (67) | 18.38 | 8 |
| permuted | Frozen base | fp32_binary | 0.21462 | 0.14489 | 0.55156 (67) | 20.00 | 0 |
| permuted | Frozen base | fp32_rerounded | 0.21462 | 0.14489 | 0.54991 (67) | 18.37 | 6 |
| permuted | Original failed adapter | native | 0.20926 | 0.14101 | 0.53655 (67) | 16.46 | 14 |
| permuted | Original failed adapter | fp32_binary | 0.20926 | 0.14101 | 0.53812 (67) | 19.99 | 0 |
| permuted | Original failed adapter | fp32_rerounded | 0.20926 | 0.14101 | 0.53608 (67) | 16.60 | 15 |
| permuted | GT prefix / uniform | native | 0.20389 | 0.13713 | 0.51945 (67) | 16.14 | 12 |
| permuted | GT prefix / uniform | fp32_binary | 0.20389 | 0.13583 | 0.52049 (67) | 20.00 | 0 |
| permuted | GT prefix / uniform | fp32_rerounded | 0.20389 | 0.13713 | 0.52032 (67) | 16.09 | 12 |
| permuted | Zero prefix / uniform | native | 0.23877 | 0.16041 | 0.54811 (67) | 3.92 | 89 |
| permuted | Zero prefix / uniform | fp32_binary | 0.20657 | 0.12807 | 0.55003 (67) | 20.00 | 0 |
| permuted | Zero prefix / uniform | fp32_rerounded | 0.24413 | 0.17206 | 0.55346 (67) | 3.94 | 95 |
| permuted | GT prefix / balanced | native | 0.20523 | 0.13842 | 0.54082 (67) | 16.84 | 15 |
| permuted | GT prefix / balanced | fp32_binary | 0.20255 | 0.13583 | 0.54022 (67) | 20.00 | 0 |
| permuted | GT prefix / balanced | fp32_rerounded | 0.20389 | 0.13713 | 0.54059 (67) | 16.89 | 13 |
| permuted | Zero prefix / balanced | native | 0.20255 | 0.14618 | 0.49068 (67) | 2.61 | 80 |
| permuted | Zero prefix / balanced | fp32_binary | 0.18779 | 0.12807 | 0.48628 (67) | 20.00 | 0 |
| permuted | Zero prefix / balanced | fp32_rerounded | 0.20791 | 0.15136 | 0.50848 (67) | 2.68 | 90 |
| permuted | Original retrieval top-8 | — | 0.28706 | 0.20181 | — | — | — |

| View | State | Contrast | Drug Δ [95% CI] | Core-order Δ [95% CI] |
|---|---|---|---:|---:|
| ranked | Frozen base | fp32_minus_native | -0.00134 [-0.00423, +0.00000] | -0.00129 [-0.00407, +0.00000] |
| ranked | Frozen base | fp32_minus_rerounded | -0.00134 [-0.00423, +0.00000] | -0.00129 [-0.00407, +0.00000] |
| ranked | Frozen base | rerounded_minus_native | +0.00000 [+0.00000, +0.00000] | +0.00000 [+0.00000, +0.00000] |
| ranked | Original failed adapter | fp32_minus_native | +0.00000 [-0.00534, +0.00543] | +0.00000 [-0.00511, +0.00526] |
| ranked | Original failed adapter | fp32_minus_rerounded | -0.00134 [-0.00758, +0.00431] | -0.00129 [-0.00723, +0.00419] |
| ranked | Original failed adapter | rerounded_minus_native | +0.00134 [+0.00000, +0.00429] | +0.00129 [+0.00000, +0.00416] |
| ranked | GT prefix / uniform | fp32_minus_native | +0.00134 [-0.00282, +0.00581] | +0.00129 [-0.00273, +0.00563] |
| ranked | GT prefix / uniform | fp32_minus_rerounded | +0.00134 [-0.00282, +0.00581] | +0.00129 [-0.00273, +0.00563] |
| ranked | GT prefix / uniform | rerounded_minus_native | +0.00000 [+0.00000, +0.00000] | +0.00000 [+0.00000, +0.00000] |
| ranked | Zero prefix / uniform | fp32_minus_native | +0.00134 [-0.01707, +0.01856] | -0.00517 [-0.02030, +0.00931] |
| ranked | Zero prefix / uniform | fp32_minus_rerounded | +0.00537 [-0.01282, +0.02304] | +0.00129 [-0.01491, +0.01723] |
| ranked | Zero prefix / uniform | rerounded_minus_native | -0.00402 [-0.01517, +0.00639] | -0.00647 [-0.01621, +0.00244] |
| ranked | GT prefix / balanced | fp32_minus_native | +0.00134 [-0.00284, +0.00614] | +0.00000 [-0.00380, +0.00384] |
| ranked | GT prefix / balanced | fp32_minus_rerounded | +0.00000 [-0.00397, +0.00398] | +0.00000 [-0.00380, +0.00384] |
| ranked | GT prefix / balanced | rerounded_minus_native | +0.00134 [+0.00000, +0.00417] | +0.00000 [+0.00000, +0.00000] |
| ranked | Zero prefix / balanced | fp32_minus_native | +0.00000 [-0.02240, +0.02164] | +0.00129 [-0.01864, +0.01987] |
| ranked | Zero prefix / balanced | fp32_minus_rerounded | -0.00268 [-0.02420, +0.01920] | +0.00000 [-0.02018, +0.01922] |
| ranked | Zero prefix / balanced | rerounded_minus_native | +0.00268 [-0.00686, +0.01233] | +0.00129 [-0.00691, +0.00967] |
| permuted | Frozen base | fp32_minus_native | +0.00000 [+0.00000, +0.00000] | +0.00000 [+0.00000, +0.00000] |
| permuted | Frozen base | fp32_minus_rerounded | +0.00000 [+0.00000, +0.00000] | +0.00000 [+0.00000, +0.00000] |
| permuted | Frozen base | rerounded_minus_native | +0.00000 [+0.00000, +0.00000] | +0.00000 [+0.00000, +0.00000] |
| permuted | Original failed adapter | fp32_minus_native | +0.00000 [+0.00000, +0.00000] | +0.00000 [+0.00000, +0.00000] |
| permuted | Original failed adapter | fp32_minus_rerounded | +0.00000 [+0.00000, +0.00000] | +0.00000 [+0.00000, +0.00000] |
| permuted | Original failed adapter | rerounded_minus_native | +0.00000 [+0.00000, +0.00000] | +0.00000 [+0.00000, +0.00000] |
| permuted | GT prefix / uniform | fp32_minus_native | +0.00000 [+0.00000, +0.00000] | -0.00129 [-0.00404, +0.00000] |
| permuted | GT prefix / uniform | fp32_minus_rerounded | +0.00000 [+0.00000, +0.00000] | -0.00129 [-0.00404, +0.00000] |
| permuted | GT prefix / uniform | rerounded_minus_native | +0.00000 [+0.00000, +0.00000] | +0.00000 [+0.00000, +0.00000] |
| permuted | Zero prefix / uniform | fp32_minus_native | -0.03219 [-0.05205, -0.01149] | -0.03234 [-0.04952, -0.01475] |
| permuted | Zero prefix / uniform | fp32_minus_rerounded | -0.03756 [-0.05667, -0.01863] | -0.04398 [-0.06037, -0.02705] |
| permuted | Zero prefix / uniform | rerounded_minus_native | +0.00537 [-0.00687, +0.01835] | +0.01164 [+0.00131, +0.02292] |
| permuted | GT prefix / balanced | fp32_minus_native | -0.00268 [-0.00683, +0.00000] | -0.00259 [-0.00661, +0.00000] |
| permuted | GT prefix / balanced | fp32_minus_rerounded | -0.00134 [-0.00426, +0.00000] | -0.00129 [-0.00415, +0.00000] |
| permuted | GT prefix / balanced | rerounded_minus_native | -0.00134 [-0.00426, +0.00000] | -0.00129 [-0.00410, +0.00000] |
| permuted | Zero prefix / balanced | fp32_minus_native | -0.01476 [-0.03404, +0.00416] | -0.01811 [-0.03909, +0.00252] |
| permuted | Zero prefix / balanced | fp32_minus_rerounded | -0.02012 [-0.04135, +0.00140] | -0.02329 [-0.04503, -0.00139] |
| permuted | Zero prefix / balanced | rerounded_minus_native | +0.00537 [-0.00750, +0.01844] | +0.00517 [-0.00653, +0.01667] |

### drug_lexical

| View | State | Readout | Drug F1 | Core-order F1 | AUROC (n) | Mean distinct scores | Cutoff tie cases |
|---|---|---|---:|---:|---:|---:|---:|
| ranked | Frozen base | native | 0.26962 | 0.17982 | 0.68006 (67) | 18.29 | 14 |
| ranked | Frozen base | fp32_binary | 0.26962 | 0.17982 | 0.68062 (67) | 20.00 | 0 |
| ranked | Frozen base | fp32_rerounded | 0.26962 | 0.17982 | 0.68012 (67) | 18.30 | 13 |
| ranked | Original failed adapter | native | 0.28303 | 0.19146 | 0.70017 (67) | 16.95 | 13 |
| ranked | Original failed adapter | fp32_binary | 0.28571 | 0.19405 | 0.70007 (67) | 20.00 | 0 |
| ranked | Original failed adapter | fp32_rerounded | 0.28437 | 0.19276 | 0.69933 (67) | 16.96 | 12 |
| ranked | GT prefix / uniform | native | 0.28571 | 0.19276 | 0.69818 (67) | 16.17 | 9 |
| ranked | GT prefix / uniform | fp32_binary | 0.28840 | 0.19534 | 0.69802 (67) | 20.00 | 0 |
| ranked | GT prefix / uniform | fp32_rerounded | 0.28571 | 0.19276 | 0.69781 (67) | 16.17 | 8 |
| ranked | Zero prefix / uniform | native | 0.20255 | 0.13972 | 0.56853 (67) | 3.73 | 93 |
| ranked | Zero prefix / uniform | fp32_binary | 0.24011 | 0.15653 | 0.60723 (67) | 20.00 | 0 |
| ranked | Zero prefix / uniform | fp32_rerounded | 0.20523 | 0.13583 | 0.56200 (67) | 3.75 | 97 |
| ranked | GT prefix / balanced | native | 0.28706 | 0.19534 | 0.68927 (67) | 16.83 | 12 |
| ranked | GT prefix / balanced | fp32_binary | 0.28571 | 0.19405 | 0.68985 (67) | 20.00 | 0 |
| ranked | GT prefix / balanced | fp32_rerounded | 0.28706 | 0.19534 | 0.68926 (67) | 16.77 | 14 |
| ranked | Zero prefix / balanced | native | 0.19852 | 0.13325 | 0.56036 (67) | 2.52 | 84 |
| ranked | Zero prefix / balanced | fp32_binary | 0.22401 | 0.15006 | 0.58629 (67) | 20.00 | 0 |
| ranked | Zero prefix / balanced | fp32_rerounded | 0.18913 | 0.12937 | 0.55852 (67) | 2.58 | 95 |
| ranked | Original retrieval top-8 | — | 0.28706 | 0.20181 | — | — | — |
| permuted | Frozen base | native | 0.21462 | 0.14489 | 0.55057 (67) | 18.38 | 8 |
| permuted | Frozen base | fp32_binary | 0.21462 | 0.14489 | 0.55156 (67) | 20.00 | 0 |
| permuted | Frozen base | fp32_rerounded | 0.21462 | 0.14489 | 0.54991 (67) | 18.37 | 6 |
| permuted | Original failed adapter | native | 0.20791 | 0.14101 | 0.53655 (67) | 16.46 | 14 |
| permuted | Original failed adapter | fp32_binary | 0.20926 | 0.14101 | 0.53812 (67) | 19.99 | 0 |
| permuted | Original failed adapter | fp32_rerounded | 0.20791 | 0.14101 | 0.53608 (67) | 16.60 | 15 |
| permuted | GT prefix / uniform | native | 0.20389 | 0.13713 | 0.51945 (67) | 16.14 | 12 |
| permuted | GT prefix / uniform | fp32_binary | 0.20389 | 0.13583 | 0.52049 (67) | 20.00 | 0 |
| permuted | GT prefix / uniform | fp32_rerounded | 0.20255 | 0.13713 | 0.52032 (67) | 16.09 | 12 |
| permuted | Zero prefix / uniform | native | 0.21060 | 0.14101 | 0.54811 (67) | 3.92 | 89 |
| permuted | Zero prefix / uniform | fp32_binary | 0.20657 | 0.12807 | 0.55003 (67) | 20.00 | 0 |
| permuted | Zero prefix / uniform | fp32_rerounded | 0.21194 | 0.14618 | 0.55346 (67) | 3.94 | 95 |
| permuted | GT prefix / balanced | native | 0.20657 | 0.13972 | 0.54082 (67) | 16.84 | 15 |
| permuted | GT prefix / balanced | fp32_binary | 0.20255 | 0.13583 | 0.54022 (67) | 20.00 | 0 |
| permuted | GT prefix / balanced | fp32_rerounded | 0.20523 | 0.13842 | 0.54059 (67) | 16.89 | 13 |
| permuted | Zero prefix / balanced | native | 0.17975 | 0.12678 | 0.49068 (67) | 2.61 | 80 |
| permuted | Zero prefix / balanced | fp32_binary | 0.18779 | 0.12807 | 0.48628 (67) | 20.00 | 0 |
| permuted | Zero prefix / balanced | fp32_rerounded | 0.17975 | 0.13066 | 0.50848 (67) | 2.68 | 90 |
| permuted | Original retrieval top-8 | — | 0.28706 | 0.20181 | — | — | — |

| View | State | Contrast | Drug Δ [95% CI] | Core-order Δ [95% CI] |
|---|---|---|---:|---:|
| ranked | Frozen base | fp32_minus_native | +0.00000 [+0.00000, +0.00000] | +0.00000 [+0.00000, +0.00000] |
| ranked | Frozen base | fp32_minus_rerounded | +0.00000 [+0.00000, +0.00000] | +0.00000 [+0.00000, +0.00000] |
| ranked | Frozen base | rerounded_minus_native | +0.00000 [+0.00000, +0.00000] | +0.00000 [+0.00000, +0.00000] |
| ranked | Original failed adapter | fp32_minus_native | +0.00268 [-0.00260, +0.00837] | +0.00259 [-0.00249, +0.00814] |
| ranked | Original failed adapter | fp32_minus_rerounded | +0.00134 [-0.00427, +0.00752] | +0.00129 [-0.00412, +0.00726] |
| ranked | Original failed adapter | rerounded_minus_native | +0.00134 [+0.00000, +0.00429] | +0.00129 [+0.00000, +0.00416] |
| ranked | GT prefix / uniform | fp32_minus_native | +0.00268 [+0.00000, +0.00672] | +0.00259 [+0.00000, +0.00648] |
| ranked | GT prefix / uniform | fp32_minus_rerounded | +0.00268 [+0.00000, +0.00672] | +0.00259 [+0.00000, +0.00648] |
| ranked | GT prefix / uniform | rerounded_minus_native | +0.00000 [+0.00000, +0.00000] | +0.00000 [+0.00000, +0.00000] |
| ranked | Zero prefix / uniform | fp32_minus_native | +0.03756 [+0.01834, +0.05661] | +0.01682 [-0.00132, +0.03401] |
| ranked | Zero prefix / uniform | fp32_minus_rerounded | +0.03488 [+0.01611, +0.05310] | +0.02070 [+0.00263, +0.03882] |
| ranked | Zero prefix / uniform | rerounded_minus_native | +0.00268 [-0.00824, +0.01372] | -0.00388 [-0.01325, +0.00498] |
| ranked | GT prefix / balanced | fp32_minus_native | -0.00134 [-0.00744, +0.00418] | -0.00129 [-0.00595, +0.00274] |
| ranked | GT prefix / balanced | fp32_minus_rerounded | -0.00134 [-0.00744, +0.00418] | -0.00129 [-0.00595, +0.00274] |
| ranked | GT prefix / balanced | rerounded_minus_native | +0.00000 [+0.00000, +0.00000] | +0.00000 [+0.00000, +0.00000] |
| ranked | Zero prefix / balanced | fp32_minus_native | +0.02549 [+0.00280, +0.04743] | +0.01682 [-0.00255, +0.03556] |
| ranked | Zero prefix / balanced | fp32_minus_rerounded | +0.03488 [+0.01208, +0.05797] | +0.02070 [+0.00000, +0.04180] |
| ranked | Zero prefix / balanced | rerounded_minus_native | -0.00939 [-0.02063, +0.00149] | -0.00388 [-0.01393, +0.00587] |
| permuted | Frozen base | fp32_minus_native | +0.00000 [+0.00000, +0.00000] | +0.00000 [+0.00000, +0.00000] |
| permuted | Frozen base | fp32_minus_rerounded | +0.00000 [+0.00000, +0.00000] | +0.00000 [+0.00000, +0.00000] |
| permuted | Frozen base | rerounded_minus_native | +0.00000 [+0.00000, +0.00000] | +0.00000 [+0.00000, +0.00000] |
| permuted | Original failed adapter | fp32_minus_native | +0.00134 [-0.00276, +0.00645] | +0.00000 [-0.00382, +0.00395] |
| permuted | Original failed adapter | fp32_minus_rerounded | +0.00134 [-0.00276, +0.00645] | +0.00000 [-0.00382, +0.00395] |
| permuted | Original failed adapter | rerounded_minus_native | +0.00000 [+0.00000, +0.00000] | +0.00000 [+0.00000, +0.00000] |
| permuted | GT prefix / uniform | fp32_minus_native | +0.00000 [+0.00000, +0.00000] | -0.00129 [-0.00404, +0.00000] |
| permuted | GT prefix / uniform | fp32_minus_rerounded | +0.00134 [+0.00000, +0.00425] | -0.00129 [-0.00404, +0.00000] |
| permuted | GT prefix / uniform | rerounded_minus_native | -0.00134 [-0.00425, +0.00000] | +0.00000 [+0.00000, +0.00000] |
| permuted | Zero prefix / uniform | fp32_minus_native | -0.00402 [-0.02387, +0.01600] | -0.01294 [-0.03177, +0.00669] |
| permuted | Zero prefix / uniform | fp32_minus_rerounded | -0.00537 [-0.02841, +0.01715] | -0.01811 [-0.03617, +0.00003] |
| permuted | Zero prefix / uniform | rerounded_minus_native | +0.00134 [-0.01227, +0.01452] | +0.00517 [-0.00647, +0.01689] |
| permuted | GT prefix / balanced | fp32_minus_native | -0.00402 [-0.00900, +0.00000] | -0.00388 [-0.00866, +0.00000] |
| permuted | GT prefix / balanced | fp32_minus_rerounded | -0.00268 [-0.00692, +0.00000] | -0.00259 [-0.00662, +0.00000] |
| permuted | GT prefix / balanced | rerounded_minus_native | -0.00134 [-0.00426, +0.00000] | -0.00129 [-0.00410, +0.00000] |
| permuted | Zero prefix / balanced | fp32_minus_native | +0.00805 [-0.00933, +0.02547] | +0.00129 [-0.01863, +0.02131] |
| permuted | Zero prefix / balanced | fp32_minus_rerounded | +0.00805 [-0.01186, +0.02798] | -0.00259 [-0.02202, +0.01819] |
| permuted | Zero prefix / balanced | rerounded_minus_native | +0.00000 [-0.01153, +0.01209] | +0.00388 [-0.00637, +0.01447] |

Native replay maximum probability difference from the parent cache: 0.0000000; changed native top-eight sets: 0. Independently replayed shared hidden states: 1200; completed actual case-forwards: 1200; unresolved forward attempts: 0. All three readouts share each backbone forward. The auditor reexecutes the dense readout, rounding and metric arithmetic, not the backbone/native projection kernel.

All intervals use 4,000 paired patient draws without multiplicity adjustment or seed-population uncertainty. Full retrieval contrasts, identity alignment, set agreement, source hashes and costs remain in the machine-readable summary.

[Full scores and costs](results/proposal_precision.json) · [Independent recount](results/proposal_precision_audit.json)
