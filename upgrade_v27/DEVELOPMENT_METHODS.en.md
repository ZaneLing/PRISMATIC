# Cross-method development comparison

All rows use 1,231 guard visits from 467 MIMIC-IV patients. Full ATC-L4 (271 classes) and the molecular subspace (219 classes) are separate. Current-visit diagnosis/procedure inputs define a retrospective task. Models and thresholds are selected on proposal data. Only completed, independently audited methods are recounted here; the final test gate stays closed.

No model call, fit, test prediction or new selection is performed by this analysis. It reconstructs GT and patient ordering from the frozen source, counts the saved predictions separately, verifies published metrics and the prior audited rule-score arrays, then pairs identical patients and matched seeds.

## full

| Method | Completed runs | Patient F1 ± seed SD | Patient Jaccard ± seed SD |
|---|---:|---:|---:|
| prevalence | 1 | 0.45794 | 0.30680 |
| last_visit | 1 | 0.30154 | 0.21585 |
| cosine_knn | 1 | 0.55081 | 0.39614 |
| structured_logistic | 1 | 0.61151 | 0.45742 |
| ARMR | 3 | 0.60864 ± 0.00132 | 0.45327 ± 0.00113 |
| GAMENet | 3 | 0.52708 ± 0.00664 | 0.37087 ± 0.00643 |
| uniform_policy | 3 | 0.61151 ± 0.00000 | 0.45742 ± 0.00000 |
| greedy_error_rules | 3 | 0.61267 ± 0.00066 | 0.45863 ± 0.00064 |
| random_candidate_rules | 3 | 0.61205 ± 0.00031 | 0.45791 ± 0.00027 |
| own_error_rule_agent | 3 | 0.61260 ± 0.00057 | 0.45856 ± 0.00057 |
| shuffled_evidence_rule_agent | 3 | 0.61219 ± 0.00038 | 0.45811 ± 0.00044 |
| matched_proposals_without_witness_gate | 3 | 0.61251 ± 0.00087 | 0.45840 ± 0.00102 |

### Own-error rule agent minus each comparator

| Comparator | Matched seeds | F1 difference (pp) | Patient 95% interval (pp) |
|---|---|---:|---:|
| prevalence | 42, 137, 2026 | +15.466 | [+14.584, +16.331] |
| last_visit | 42, 137, 2026 | +31.107 | [+30.044, +32.159] |
| cosine_knn | 42, 137, 2026 | +6.179 | [+5.547, +6.778] |
| structured_logistic | 42, 137, 2026 | +0.109 | [+0.048, +0.172] |
| ARMR | 42, 137, 2026 | +0.396 | [-0.075, +0.870] |
| GAMENet | 42, 137, 2026 | +8.552 | [+7.882, +9.184] |
| uniform_policy | 42, 137, 2026 | +0.109 | [+0.048, +0.172] |
| greedy_error_rules | 42, 137, 2026 | -0.007 | [-0.020, +0.006] |
| random_candidate_rules | 42, 137, 2026 | +0.055 | [+0.019, +0.093] |
| shuffled_evidence_rule_agent | 42, 137, 2026 | +0.041 | [-0.002, +0.084] |
| matched_proposals_without_witness_gate | 42, 137, 2026 | +0.009 | [-0.038, +0.058] |

## molecular

| Method | Completed runs | Patient F1 ± seed SD | Patient Jaccard ± seed SD |
|---|---:|---:|---:|
| prevalence | 1 | 0.42555 | 0.28089 |
| last_visit | 1 | 0.28971 | 0.20613 |
| cosine_knn | 1 | 0.51751 | 0.36710 |
| structured_logistic | 1 | 0.58113 | 0.42971 |
| GAMENet | 1 | 0.51055 | 0.35689 |
| SafeDrug | 3 | 0.53689 ± 0.00244 | 0.38432 ± 0.00223 |
| uniform_policy | 3 | 0.58113 ± 0.00000 | 0.42971 ± 0.00000 |
| greedy_error_rules | 3 | 0.58230 ± 0.00042 | 0.43084 ± 0.00039 |
| random_candidate_rules | 3 | 0.58220 ± 0.00055 | 0.43078 ± 0.00058 |
| own_error_rule_agent | 3 | 0.58198 ± 0.00014 | 0.43049 ± 0.00014 |
| shuffled_evidence_rule_agent | 3 | 0.58255 ± 0.00029 | 0.43105 ± 0.00027 |
| matched_proposals_without_witness_gate | 3 | 0.58202 ± 0.00067 | 0.43050 ± 0.00070 |

### Own-error rule agent minus each comparator

| Comparator | Matched seeds | F1 difference (pp) | Patient 95% interval (pp) |
|---|---|---:|---:|
| prevalence | 42, 137, 2026 | +15.644 | [+14.663, +16.620] |
| last_visit | 42, 137, 2026 | +29.228 | [+28.076, +30.405] |
| cosine_knn | 42, 137, 2026 | +6.447 | [+5.720, +7.151] |
| structured_logistic | 42, 137, 2026 | +0.086 | [+0.001, +0.171] |
| GAMENet | 42 | +7.142 | [+6.330, +7.980] |
| SafeDrug | 42, 137, 2026 | +4.509 | [+3.828, +5.157] |
| uniform_policy | 42, 137, 2026 | +0.086 | [+0.001, +0.171] |
| greedy_error_rules | 42, 137, 2026 | -0.031 | [-0.062, -0.002] |
| random_candidate_rules | 42, 137, 2026 | -0.022 | [-0.088, +0.044] |
| shuffled_evidence_rule_agent | 42, 137, 2026 | -0.056 | [-0.114, -0.003] |
| matched_proposals_without_witness_gate | 42, 137, 2026 | -0.003 | [-0.055, +0.047] |

## Interpretation

The paired comparison uses only shared completed seeds for neural models. A fixed conventional control is reused for each matched seed. Intervals use 4,000 paired patient-cluster resamples after averaging the observed seeds; they describe patient uncertainty conditional on those seeds and do not include a new-seed population or multiple-comparison correction. This post-training development analysis cannot promote a method or establish untouched-test superiority. A benefit over older neural architectures must also be compared with strong ordinary learning and greedy-memory controls.

[All source hashes, per-run metrics and paired effects](results/development_methods.json) · [Actual compute accounting](../paper/COMPUTE_ACCOUNTING.en.md) · [Final-test execution status](RESULTS.en.md)
