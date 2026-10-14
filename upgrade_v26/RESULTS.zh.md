# v0.26：候选位置依赖的开发集诊断

## 设计

v0.15暴露前缀选择与检查点退化后，在其既有200例／197人guard上固定诊断；不评价训练/测试病例。冻结原模型及两臂已选第2轮适配器。比较重新生成的原提示，以及明确提供原始检索名次的顺序、确定性打乱、逆序候选。后三条件保留同样患者信息、全部药物/订单字段及原始名次，按展示顺序解释掩码，因此不是暗中删除有效排序信息。额外名次提示的影响另与原提示比较。

这是由已见测试诊断启发的开发敏感性实验，不是未触碰确认。没有重新训练，也不据此接纳任何模型、提示或检查点。生成全在本地，相同输入只生成一次，每例保存不可变回执。

## 冻结方法结果

| Frozen method | Display condition | Drug F1 | Order F1 | Empty (%) | Invalid | Nontrivial display-prefix (%) |
|---|---|---:|---:|---:|---:|---:|
| base | original | 0.19211 | 0.12091 | 3.0 | 0 | 1.0 |
| base | ranked_explicit | 0.21480 | 0.13843 | 3.0 | 0 | 4.1 |
| base | permuted_rank_explicit | 0.19417 | 0.12603 | 1.0 | 0 | 1.5 |
| base | reversed_rank_explicit | 0.10402 | 0.06915 | 5.5 | 0 | 0.5 |
| uniform_sft_round2 | original | 0.27561 | 0.19212 | 10.5 | 0 | 99.4 |
| uniform_sft_round2 | ranked_explicit | 0.22125 | 0.14351 | 10.0 | 0 | 99.4 |
| uniform_sft_round2 | permuted_rank_explicit | 0.10492 | 0.07377 | 9.0 | 0 | 100.0 |
| uniform_sft_round2 | reversed_rank_explicit | 0.03301 | 0.02120 | 28.5 | 0 | 100.0 |
| error_prioritized_sft_round2 | original | 0.32043 | 0.22181 | 3.5 | 0 | 99.4 |
| error_prioritized_sft_round2 | ranked_explicit | 0.27471 | 0.19207 | 4.5 | 0 | 100.0 |
| error_prioritized_sft_round2 | permuted_rank_explicit | 0.17441 | 0.12645 | 1.0 | 0 | 100.0 |
| error_prioritized_sft_round2 | reversed_rank_explicit | 0.21980 | 0.15146 | 0.0 | 0 | 100.0 |

Direct original-rank controls (drug/order F1): direct_original_rank_top8 0.32027/0.22434, direct_original_rank_top20 0.27382/0.19522.

## Reordering contrasts / 重排比较

| Frozen method | Contrast | Drug/order Δ | Medication-set agreement (%) | Mean Jaccard |
|---|---|---:|---:|---:|
| base | ranked_explicit__minus__original | +0.02269/+0.01751 | 18.5 | 0.537 |
| base | permuted_rank_explicit__minus__ranked_explicit | -0.02062/-0.01240 | 0.0 | 0.198 |
| base | reversed_rank_explicit__minus__ranked_explicit | -0.11078/-0.06927 | 0.5 | 0.090 |
| uniform_sft_round2 | ranked_explicit__minus__original | -0.05436/-0.04861 | 42.5 | 0.671 |
| uniform_sft_round2 | permuted_rank_explicit__minus__ranked_explicit | -0.11633/-0.06974 | 1.0 | 0.091 |
| uniform_sft_round2 | reversed_rank_explicit__minus__ranked_explicit | -0.18824/-0.12231 | 3.0 | 0.030 |
| error_prioritized_sft_round2 | ranked_explicit__minus__original | -0.04573/-0.02974 | 21.5 | 0.522 |
| error_prioritized_sft_round2 | permuted_rank_explicit__minus__ranked_explicit | -0.10030/-0.06562 | 11.0 | 0.238 |
| error_prioritized_sft_round2 | reversed_rank_explicit__minus__ranked_explicit | -0.05491/-0.04061 | 26.5 | 0.355 |

## 这对“进化”意味着什么

明确保留原检索名次后，只打乱展示位置，错误优先模型药物F1仍从0.27471降到0.17441，差值−0.10030，患者聚类区间[−0.13508,−0.06646]。普通适配器从0.22125降至0.10492。两种适配器在打乱条件下的非平凡合法输出100%选展示前缀，原模型仅1.5%。原提示下优先模型0.32043也几乎等于固定top8的0.32027，不能据此说学会了更好的临床选择。2,400个病例/状态/条件输出全部解析成功，因此不是JSON格式失败。

下一干预应随机化训练展示位置、保留原名次，并直接检验逐药决策，在相同步数/token预算下比较普通更新、自身错误、打乱反馈及固定排序对照；逐轮报告原始和接纳状态。本诊断支持该修复方向，但没有识别完整因果机制，也不能用这个已使用的guard直接挑胜者。

全部预测、候选集合/GT一致性和逐例回执哈希通过独立核对。完整患者聚类配对区间见 `results/summary.json`。顺序敏感性不能直接证明临床思路，也不能单独解释训练退化的因果机制；本诊断不宣称改进或最佳方法。
