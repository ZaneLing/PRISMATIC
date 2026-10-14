# 同一数据上的跨方法开发集比较

所有行均使用 MIMIC-IV 同一 1,231 次 guard 就诊／467 位患者。完整 ATC-L4（271 类）与分子子空间（219 类）分别报告。输入含本次完整就诊的诊断／操作，属于回顾性任务。模型和阈值由 proposal 选择。这里只重算已经完成并独立核验的方法；最终测试仍等待全部方法完成。

本次分析没有模型调用、拟合、测试预测或新的版本选择。它从冻结源数据重建 GT 与患者顺序，独立计数已保存预测，核对已发布指标及既有规则方法审计数组，再按相同患者和匹配种子做配对比较。

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

### 自身错误规则 agent 相对各对照的差值

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
| GAMENet | 2 | 0.50709 ± 0.00490 | 0.35366 ± 0.00456 |
| SafeDrug | 3 | 0.53689 ± 0.00244 | 0.38432 ± 0.00223 |
| uniform_policy | 3 | 0.58113 ± 0.00000 | 0.42971 ± 0.00000 |
| greedy_error_rules | 3 | 0.58230 ± 0.00042 | 0.43084 ± 0.00039 |
| random_candidate_rules | 3 | 0.58220 ± 0.00055 | 0.43078 ± 0.00058 |
| own_error_rule_agent | 3 | 0.58198 ± 0.00014 | 0.43049 ± 0.00014 |
| shuffled_evidence_rule_agent | 3 | 0.58255 ± 0.00029 | 0.43105 ± 0.00027 |
| matched_proposals_without_witness_gate | 3 | 0.58202 ± 0.00067 | 0.43050 ± 0.00070 |

### 自身错误规则 agent 相对各对照的差值

| Comparator | Matched seeds | F1 difference (pp) | Patient 95% interval (pp) |
|---|---|---:|---:|
| prevalence | 42, 137, 2026 | +15.644 | [+14.663, +16.620] |
| last_visit | 42, 137, 2026 | +29.228 | [+28.076, +30.405] |
| cosine_knn | 42, 137, 2026 | +6.447 | [+5.720, +7.151] |
| structured_logistic | 42, 137, 2026 | +0.086 | [+0.001, +0.171] |
| GAMENet | 42, 137 | +7.497 | [+6.724, +8.263] |
| SafeDrug | 42, 137, 2026 | +4.509 | [+3.828, +5.157] |
| uniform_policy | 42, 137, 2026 | +0.086 | [+0.001, +0.171] |
| greedy_error_rules | 42, 137, 2026 | -0.031 | [-0.062, -0.002] |
| random_candidate_rules | 42, 137, 2026 | -0.022 | [-0.088, +0.044] |
| shuffled_evidence_rule_agent | 42, 137, 2026 | -0.056 | [-0.114, -0.003] |
| matched_proposals_without_witness_gate | 42, 137, 2026 | -0.003 | [-0.055, +0.047] |

## 解释边界

神经方法之间只比较共同完成的种子；固定传统对照在各匹配种子中复用。区间先平均已有种子，再做 4,000 次患者聚类配对重采样，反映给定这些种子的患者不确定性，不包含新种子总体波动或多重比较校正。这项训练后的开发集分析不用于升级方法，不能证明未触碰测试集上的领先。即使超过较早神经方法，也必须同时对照强普通学习和贪心记忆方法。

[All source hashes, per-run metrics and paired effects](results/development_methods.json) · [Actual compute accounting](../paper/COMPUTE_ACCOUNTING.zh.md) · [Final-test execution status](RESULTS.zh.md)
