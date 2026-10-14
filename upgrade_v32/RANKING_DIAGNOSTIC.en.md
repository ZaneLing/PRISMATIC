# v0.32 fixed-cardinality ranking diagnosis

## 1. Question and scope

Does calibration hide useful medication ranking? Every state selects exactly eight of the same twenty candidate order templates using its saved probabilities. The original retrieval top-eight receives the same eight-drug output budget. Targets are used only for scoring. No training, model forward pass, API request, checkpoint/threshold selection, or test access is added.

This diagnosis was specified and committed after the parent proposal outcomes were known, before computing these new endpoints. It is a post-proposal development analysis, not an original preregistered endpoint or independent confirmation. The original fixed-0.5 and calibrated results remain intact. Fixed eight-drug output is a diagnostic, not a clinical prescription-count rule.

Exact ties use a SHA-256 key derived solely from drug identity. Lexical drug-name order is a declared sensitivity analysis. Neither rule uses target labels, display position, or retrieval rank. Both are invariant to candidate permutation when scores are identical.

[Protocol](rank_diagnostic_protocol.json) · [Frozen implementation](results/rank_diagnostic_lock.json) · [Original repair experiment](RESULTS.en.md)

## 2. proposal: 100 admissions / 97 patients

**Finding:** no neural state exceeds retrieval in drug or core-order F1 in any reported view under either tie rule. Fixing the number of emitted drugs does not recover a winning repair.

### Primary: drug-identity hash ties

| View | Method | Drug F1 | Core-order F1 | Within-case AUROC (eligible n) | Cutoff ties / cases |
|---|---|---:|---:|---:|---:|
| ranked | Frozen base | 0.27096 | 0.18111 | 0.68006 (67) | 14/100 |
| ranked | Original failed adapter | 0.28571 | 0.19405 | 0.70017 (67) | 13/100 |
| ranked | GT prefix / uniform | 0.28706 | 0.19405 | 0.69818 (67) | 9/100 |
| ranked | Zero prefix / uniform | 0.23877 | 0.16171 | 0.56853 (67) | 93/100 |
| ranked | GT prefix / balanced | 0.28437 | 0.19405 | 0.68927 (67) | 12/100 |
| ranked | Zero prefix / balanced | 0.22401 | 0.14877 | 0.56036 (67) | 84/100 |
| ranked | Original retrieval top-8 | 0.28706 | 0.20181 | — | — |
| permuted | Frozen base | 0.21462 | 0.14489 | 0.55057 (67) | 8/100 |
| permuted | Original failed adapter | 0.20926 | 0.14101 | 0.53655 (67) | 14/100 |
| permuted | GT prefix / uniform | 0.20389 | 0.13713 | 0.51945 (67) | 12/100 |
| permuted | Zero prefix / uniform | 0.23877 | 0.16041 | 0.54811 (67) | 89/100 |
| permuted | GT prefix / balanced | 0.20523 | 0.13842 | 0.54082 (67) | 15/100 |
| permuted | Zero prefix / balanced | 0.20255 | 0.14618 | 0.49068 (67) | 80/100 |
| permuted | Original retrieval top-8 | 0.28706 | 0.20181 | — | — |

AUROC compares positive and negative candidates within each admission, with half credit for ties. Cases without both classes are excluded only from AUROC; their prescriptions remain in F1. The machine-readable summary retains eligible/excluded counts, precision, recall and all paired contrasts. F1 retains reference medications absent from the twenty candidates. Core-order F1 matches drug, route, dose value and dose unit, using the parent complete-tuple denominator.

### Sensitivity: lexical drug-name ties

| View | Method | Drug F1 | Core-order F1 | Within-case AUROC (eligible n) | Cutoff ties / cases |
|---|---|---:|---:|---:|---:|
| ranked | Frozen base | 0.26962 | 0.17982 | 0.68006 (67) | 14/100 |
| ranked | Original failed adapter | 0.28303 | 0.19146 | 0.70017 (67) | 13/100 |
| ranked | GT prefix / uniform | 0.28571 | 0.19276 | 0.69818 (67) | 9/100 |
| ranked | Zero prefix / uniform | 0.20255 | 0.13972 | 0.56853 (67) | 93/100 |
| ranked | GT prefix / balanced | 0.28706 | 0.19534 | 0.68927 (67) | 12/100 |
| ranked | Zero prefix / balanced | 0.19852 | 0.13325 | 0.56036 (67) | 84/100 |
| ranked | Original retrieval top-8 | 0.28706 | 0.20181 | — | — |
| permuted | Frozen base | 0.21462 | 0.14489 | 0.55057 (67) | 8/100 |
| permuted | Original failed adapter | 0.20791 | 0.14101 | 0.53655 (67) | 14/100 |
| permuted | GT prefix / uniform | 0.20389 | 0.13713 | 0.51945 (67) | 12/100 |
| permuted | Zero prefix / uniform | 0.21060 | 0.14101 | 0.54811 (67) | 89/100 |
| permuted | GT prefix / balanced | 0.20657 | 0.13972 | 0.54082 (67) | 15/100 |
| permuted | Zero prefix / balanced | 0.17975 | 0.12678 | 0.49068 (67) | 80/100 |
| permuted | Original retrieval top-8 | 0.28706 | 0.20181 | — | — |

AUROC compares positive and negative candidates within each admission, with half credit for ties. Cases without both classes are excluded only from AUROC; their prescriptions remain in F1. The machine-readable summary retains eligible/excluded counts, precision, recall and all paired contrasts. F1 retains reference medications absent from the twenty candidates. Core-order F1 matches drug, route, dose value and dose unit, using the parent complete-tuple denominator.

### Score identity and display position

| Changed view | Model | Identity-aligned Spearman | Same-slot Spearman | Exact top-8 set agreement | Top-8 Jaccard |
|---|---|---:|---:|---:|---:|
| permuted | Frozen base | 0.24291 | 0.72743 | 0.0% | 0.37712 |
| permuted | Original failed adapter | 0.21228 | 0.79617 | 0.0% | 0.34197 |
| permuted | GT prefix / uniform | 0.19792 | 0.81688 | 0.0% | 0.33767 |
| permuted | Zero prefix / uniform | 0.12379 | 0.18125 | 0.0% | 0.35949 |
| permuted | GT prefix / balanced | 0.24096 | 0.76418 | 0.0% | 0.34778 |
| permuted | Zero prefix / balanced | -0.00186 | 0.15051 | 0.0% | 0.27992 |

Correlations are within-case averages. Identity alignment compares the same medications; same-slot alignment compares the same displayed positions, usually containing different drugs. The latter is a diagnostic of positional dependence, not proof of its causal origin. Undefined constant-vector correlations are counted in the summary. Top-eight set agreement cannot be inflated by all-empty or all-twenty outputs.

### Paired differences: drug_sha256

| View | Contrast | Drug Δ [95% CI] | Core-order Δ [95% CI] |
|---|---|---:|---:|
| ranked | frozen_base_minus_retrieval | -0.01610 [-0.03274, +0.00133] | -0.02070 [-0.03686, -0.00395] |
| ranked | original_failed_adapter_minus_retrieval | -0.00134 [-0.01516, +0.01240] | -0.00776 [-0.01969, +0.00411] |
| ranked | teacher_uniform_minus_retrieval | +0.00000 [-0.01184, +0.01159] | -0.00776 [-0.01759, +0.00249] |
| ranked | zero_uniform_minus_retrieval | -0.04829 [-0.07728, -0.01862] | -0.04010 [-0.06547, -0.01518] |
| ranked | teacher_balanced_minus_retrieval | -0.00268 [-0.01533, +0.01029] | -0.00776 [-0.01888, +0.00377] |
| ranked | zero_balanced_minus_retrieval | -0.06304 [-0.09080, -0.03552] | -0.05304 [-0.07792, -0.02642] |
| ranked | teacher_uniform_minus_frozen_base | +0.01610 [+0.00263, +0.02941] | +0.01294 [+0.00131, +0.02461] |
| ranked | teacher_uniform_minus_original_failed_adapter | +0.00134 [-0.00755, +0.01004] | +0.00000 [-0.00908, +0.00896] |
| ranked | zero_uniform_minus_frozen_base | -0.03219 [-0.06010, -0.00282] | -0.01940 [-0.04065, +0.00297] |
| ranked | zero_uniform_minus_original_failed_adapter | -0.04695 [-0.07351, -0.01802] | -0.03234 [-0.05292, -0.00946] |
| ranked | teacher_balanced_minus_frozen_base | +0.01341 [+0.00000, +0.02658] | +0.01294 [+0.00000, +0.02598] |
| ranked | teacher_balanced_minus_original_failed_adapter | -0.00134 [-0.00935, +0.00667] | +0.00000 [-0.00645, +0.00633] |
| ranked | zero_balanced_minus_frozen_base | -0.04695 [-0.07542, -0.01911] | -0.03234 [-0.05629, -0.00750] |
| ranked | zero_balanced_minus_original_failed_adapter | -0.06170 [-0.08892, -0.03296] | -0.04528 [-0.06671, -0.02094] |
| permuted | frozen_base_minus_retrieval | -0.07243 [-0.09826, -0.04536] | -0.05692 [-0.08275, -0.03003] |
| permuted | original_failed_adapter_minus_retrieval | -0.07780 [-0.10609, -0.04798] | -0.06080 [-0.08784, -0.03214] |
| permuted | teacher_uniform_minus_retrieval | -0.08317 [-0.11155, -0.05409] | -0.06468 [-0.09170, -0.03649] |
| permuted | zero_uniform_minus_retrieval | -0.04829 [-0.07450, -0.02060] | -0.04140 [-0.06376, -0.01867] |
| permuted | teacher_balanced_minus_retrieval | -0.08182 [-0.11053, -0.05307] | -0.06339 [-0.09172, -0.03472] |
| permuted | zero_balanced_minus_retrieval | -0.08451 [-0.11097, -0.05799] | -0.05563 [-0.08090, -0.02959] |
| permuted | teacher_uniform_minus_frozen_base | -0.01073 [-0.02183, +0.00000] | -0.00776 [-0.01826, +0.00262] |
| permuted | teacher_uniform_minus_original_failed_adapter | -0.00537 [-0.01289, +0.00139] | -0.00388 [-0.01065, +0.00261] |
| permuted | zero_uniform_minus_frozen_base | +0.02414 [+0.00000, +0.04759] | +0.01552 [-0.00257, +0.03246] |
| permuted | zero_uniform_minus_original_failed_adapter | +0.02951 [+0.00630, +0.05111] | +0.01940 [+0.00000, +0.03730] |
| permuted | teacher_balanced_minus_frozen_base | -0.00939 [-0.02001, +0.00125] | -0.00647 [-0.01613, +0.00272] |
| permuted | teacher_balanced_minus_original_failed_adapter | -0.00402 [-0.01117, +0.00269] | -0.00259 [-0.00889, +0.00359] |
| permuted | zero_balanced_minus_frozen_base | -0.01207 [-0.03408, +0.01049] | +0.00129 [-0.02032, +0.02202] |
| permuted | zero_balanced_minus_original_failed_adapter | -0.00671 [-0.03094, +0.01787] | +0.00517 [-0.01747, +0.02708] |

### Paired differences: drug_lexical

| View | Contrast | Drug Δ [95% CI] | Core-order Δ [95% CI] |
|---|---|---:|---:|
| ranked | frozen_base_minus_retrieval | -0.01744 [-0.03405, +0.00000] | -0.02199 [-0.03788, -0.00525] |
| ranked | original_failed_adapter_minus_retrieval | -0.00402 [-0.01743, +0.00959] | -0.01035 [-0.02199, +0.00126] |
| ranked | teacher_uniform_minus_retrieval | -0.00134 [-0.01321, +0.01016] | -0.00906 [-0.01844, +0.00000] |
| ranked | zero_uniform_minus_retrieval | -0.08451 [-0.11222, -0.05585] | -0.06210 [-0.08759, -0.03634] |
| ranked | teacher_balanced_minus_retrieval | +0.00000 [-0.01303, +0.01340] | -0.00647 [-0.01819, +0.00520] |
| ranked | zero_balanced_minus_retrieval | -0.08853 [-0.11666, -0.06195] | -0.06856 [-0.09362, -0.04381] |
| ranked | teacher_uniform_minus_frozen_base | +0.01610 [+0.00262, +0.02989] | +0.01294 [+0.00124, +0.02495] |
| ranked | teacher_uniform_minus_original_failed_adapter | +0.00268 [-0.00442, +0.01040] | +0.00129 [-0.00640, +0.00925] |
| ranked | zero_uniform_minus_frozen_base | -0.06707 [-0.09174, -0.04087] | -0.04010 [-0.06279, -0.01657] |
| ranked | zero_uniform_minus_original_failed_adapter | -0.08048 [-0.10625, -0.05296] | -0.05175 [-0.07325, -0.03001] |
| ranked | teacher_balanced_minus_frozen_base | +0.01744 [+0.00418, +0.03026] | +0.01552 [+0.00265, +0.02811] |
| ranked | teacher_balanced_minus_original_failed_adapter | +0.00402 [-0.00267, +0.01095] | +0.00388 [-0.00132, +0.00979] |
| ranked | zero_balanced_minus_frozen_base | -0.07109 [-0.09980, -0.04396] | -0.04657 [-0.07059, -0.02348] |
| ranked | zero_balanced_minus_original_failed_adapter | -0.08451 [-0.11175, -0.05815] | -0.05821 [-0.07927, -0.03682] |
| permuted | frozen_base_minus_retrieval | -0.07243 [-0.09826, -0.04536] | -0.05692 [-0.08275, -0.03003] |
| permuted | original_failed_adapter_minus_retrieval | -0.07914 [-0.10674, -0.05014] | -0.06080 [-0.08668, -0.03312] |
| permuted | teacher_uniform_minus_retrieval | -0.08317 [-0.11155, -0.05409] | -0.06468 [-0.09170, -0.03649] |
| permuted | zero_uniform_minus_retrieval | -0.07646 [-0.10408, -0.04701] | -0.06080 [-0.08754, -0.03366] |
| permuted | teacher_balanced_minus_retrieval | -0.08048 [-0.10912, -0.05142] | -0.06210 [-0.09001, -0.03315] |
| permuted | zero_balanced_minus_retrieval | -0.10731 [-0.13470, -0.07828] | -0.07503 [-0.10187, -0.04776] |
| permuted | teacher_uniform_minus_frozen_base | -0.01073 [-0.02183, +0.00000] | -0.00776 [-0.01826, +0.00262] |
| permuted | teacher_uniform_minus_original_failed_adapter | -0.00402 [-0.01088, +0.00266] | -0.00388 [-0.01049, +0.00256] |
| permuted | zero_uniform_minus_frozen_base | -0.00402 [-0.02823, +0.02185] | -0.00388 [-0.02384, +0.01529] |
| permuted | zero_uniform_minus_original_failed_adapter | +0.00268 [-0.02038, +0.02648] | +0.00000 [-0.01921, +0.01893] |
| permuted | teacher_balanced_minus_frozen_base | -0.00805 [-0.01919, +0.00283] | -0.00517 [-0.01548, +0.00528] |
| permuted | teacher_balanced_minus_original_failed_adapter | -0.00134 [-0.00820, +0.00539] | -0.00129 [-0.00790, +0.00521] |
| permuted | zero_balanced_minus_frozen_base | -0.03488 [-0.05974, -0.01039] | -0.01811 [-0.04110, +0.00372] |
| permuted | zero_balanced_minus_original_failed_adapter | -0.02817 [-0.05260, -0.00520] | -0.01423 [-0.03763, +0.00764] |

Intervals use 4,000 paired patient resamples, without multiplicity correction. They describe this one-seed development sample; they do not include training-seed uncertainty. All states and both tie rules are retained without selecting a new winner.

**Independent audit:** 1,200 probability bindings and 2,800 case selections; order metrics, within-case AUROC, rank alignment and paired intervals independently recounted. No optimizer or neural-forward replay.

[Machine-readable results](results/proposal_rank_diagnostic.json) · [Independent audit](results/proposal_rank_diagnostic_audit.json)

## 3. Next implementation decision

Threshold tuning alone has not resolved the ranking failure. Frequent exact cutoff ties also require a separate numerical-readout precision check before attributing them to the learned representation. A future candidate-specific readout should preserve drug identity across permutations and be compared with the same retrieval evidence and output budget. These are next investigations, not implemented or validated repairs. Existing multi-round studies and their selection gates continue unchanged.

The original guard is still closed or awaiting its parent audit. No guard score is available for this diagnostic.
