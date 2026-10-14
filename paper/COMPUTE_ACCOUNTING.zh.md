# 共同处方方法实验：实际计算预算账本

## 1. 哪些条件已经对齐

每个 ATC-L4 分组内使用相同患者划分与药物空间。作者神经方法均训练 50 整轮，每轮 18,429 次就诊，合计 921,450 次就诊曝光。各方法的批量、优化步数、参数数量和设备不同；50 轮对应相同病例曝光，具体步数与已记录耗时另列。

每组神经方法在每个训练轮次上评价 6 个全局阈值，共 300 个轮次／阈值候选，均由同一 proposal 集选择。作者神经方法之间使用相同选择预算。

v27 六种规则方法共享每轮监督拟合。v29 七种方法也共享拟合，其中 5,692 人用于策略训练，1,423 人永久独立作为 witness。v30 的 14 种记忆轨迹原样复用 v29 模型。执行账本对共享拟合只计一次；单独复现实验中的某一种方法时，仍需完成其基础策略拟合。

## 2. 已完成并独立核验的作者模型

10/15 组已登记运行在此快照中完成并通过核验。逐组将 50 条训练轮次记录与原执行日志对齐。拟合秒数不包含 proposal／guard 预测、检查点写入和核验重跑。

| Panel | Method | Seed | Device | Parameters | Steps | Visit exposures | Fit minutes |
|---|---|---:|---|---:|---:|---:|---:|
| full | ARMR | 42 | mps | 12,141,073 | 29,750 | 921,450 | 51.39 |
| full | ARMR | 137 | mps | 12,141,073 | 29,750 | 921,450 | 53.14 |
| full | ARMR | 2026 | mps | 12,141,073 | 29,750 | 921,450 | 183.58 |
| full | GAMENet | 42 | cpu | 1,295,952 | 921,450 | 921,450 | 69.76 |
| full | GAMENet | 137 | cpu | 1,295,952 | 921,450 | 921,450 | 75.84 |
| full | GAMENet | 2026 | cpu | 1,295,952 | 921,450 | 921,450 | 83.87 |
| molecular | GAMENet | 42 | cpu | 1,282,588 | 921,450 | 921,450 | 65.20 |
| molecular | SafeDrug | 42 | cpu | 1,379,598 | 921,450 | 921,450 | 67.86 |
| molecular | SafeDrug | 137 | cpu | 1,379,598 | 921,450 | 921,450 | 72.12 |
| molecular | SafeDrug | 2026 | cpu | 1,379,598 | 921,450 | 921,450 | 81.21 |

### 对应的开发集结果

| Panel / method | Audited seeds | Guard patient F1 ± seed SD | Guard patient Jaccard ± seed SD |
|---|---|---:|---:|
| full/ARMR | 42, 137, 2026 | 0.60864 ± 0.00132 | 0.45327 ± 0.00113 |
| full/GAMENet | 42, 137, 2026 | 0.52708 ± 0.00664 | 0.37087 ± 0.00643 |
| molecular/GAMENet | 42 | 0.51055 (one seed) | 0.35689 (one seed) |
| molecular/SafeDrug | 42, 137, 2026 | 0.53689 ± 0.00244 | 0.38432 ± 0.00223 |

以上均来自同一 1,231 次 guard 就诊／467 位患者，检查点只由 proposal 选择。未完成种子不补零；这些开发结果不会替代等待全部方法完成后的统一测试主表。

## 3. 共享监督拟合的实际开销

| Study | Panel | Seed | Fit events / unique labels | Input-row participations | Fit minutes | Final fit patients / visits | Shared arms |
|---|---|---:|---:|---:|---:|---:|---:|
| v27 | full | 42 | 30/30 | 277,995 | 6.68 | 7,115/18,429 | 6 |
| v27 | full | 137 | 30/30 | 277,255 | 6.63 | 7,115/18,429 | 6 |
| v27 | full | 2026 | 30/30 | 275,445 | 6.41 | 7,115/18,429 | 6 |
| v29 | full | 42 | 30/30 | 220,615 | 5.03 | 5,692/14,728 | 7 |
| v29 | full | 137 | 30/30 | 220,720 | 5.08 | 5,692/14,665 | 7 |
| v29 | full | 2026 | 30/30 | 220,475 | 5.07 | 5,692/14,643 | 7 |
| v27 | molecular | 42 | 30/30 | 277,995 | 5.27 | 7,115/18,429 | 6 |
| v27 | molecular | 137 | 30/30 | 277,255 | 5.26 | 7,115/18,429 | 6 |
| v27 | molecular | 2026 | 30/30 | 275,445 | 5.08 | 7,115/18,429 | 6 |
| v29 | molecular | 42 | 30/30 | 220,615 | 4.06 | 5,692/14,728 | 7 |
| v29 | molecular | 137 | 30/30 | 220,720 | 4.03 | 5,692/14,665 | 7 |
| v29 | molecular | 2026 | 30/30 | 220,475 | 4.08 | 5,692/14,643 | 7 |

每个五轮源实验，每轮拟合 3 个正则化候选和 3 个交叉拟合模型。每项拟合记录表示一整套逐类分类器；目标恒定的类别可能无需优化。输入行参与次数统计传入这些拟合的数据行数，不代表求解器内部迭代数或 epoch 曝光。重复拟合事件如有发生仍计入总数。规则搜索、校准、生成、预测和审计不在这些拟合计时之内。

| Reuse study | Panel | Seed | Frozen fit source | Additional policy fits | Shared arms |
|---|---|---:|---|---:|---:|
| v30 | full | 42 | v29/full/42 | 0 | 14 |
| v30 | molecular | 42 | v29/molecular/42 | 0 | 14 |

新增策略拟合为零表示原样复用；记忆归纳与验证仍消耗计算和逻辑模型调用。

## 4. 已核验运行的提议调用

| Study | Panel | Seed | Arm | Logical calls | Known logical response USD | Unpriced calls |
|---|---|---:|---|---:|---:|---:|
| v27 | full | 42 | own_error_rule_agent | 5 | 0.00232 | 0 |
| v27 | full | 42 | shuffled_evidence_rule_agent | 5 | 0.00194 | 0 |
| v27 | full | 137 | own_error_rule_agent | 5 | 0.00218 | 0 |
| v27 | full | 137 | shuffled_evidence_rule_agent | 5 | 0.00207 | 0 |
| v27 | full | 2026 | own_error_rule_agent | 5 | 0.00265 | 0 |
| v27 | full | 2026 | shuffled_evidence_rule_agent | 5 | 0.00272 | 0 |
| v29 | full | 42 | own_error_program_agent | 5 | 0.00983 | 0 |
| v29 | full | 42 | shuffled_evidence_program_agent | 5 | 0.00890 | 0 |
| v29 | full | 137 | own_error_program_agent | 5 | 0.00300 | 0 |
| v29 | full | 137 | shuffled_evidence_program_agent | 5 | 0.00399 | 0 |
| v29 | full | 2026 | own_error_program_agent | 5 | 0.01146 | 0 |
| v29 | full | 2026 | shuffled_evidence_program_agent | 5 | 0.00965 | 0 |
| v27 | molecular | 42 | own_error_rule_agent | 5 | 0.00210 | 0 |
| v27 | molecular | 42 | shuffled_evidence_rule_agent | 5 | 0.00198 | 0 |
| v27 | molecular | 137 | own_error_rule_agent | 5 | 0.00200 | 0 |
| v27 | molecular | 137 | shuffled_evidence_rule_agent | 5 | 0.00155 | 0 |
| v27 | molecular | 2026 | own_error_rule_agent | 5 | 0.00141 | 0 |
| v27 | molecular | 2026 | shuffled_evidence_rule_agent | 5 | 0.00229 | 0 |
| v29 | molecular | 42 | own_error_program_agent | 5 | 0.00846 | 0 |
| v29 | molecular | 42 | shuffled_evidence_program_agent | 5 | 0.00757 | 0 |
| v29 | molecular | 137 | own_error_program_agent | 5 | 0.00924 | 0 |
| v29 | molecular | 137 | shuffled_evidence_program_agent | 5 | 0.00839 | 0 |
| v29 | molecular | 2026 | own_error_program_agent | 5 | 0.01005 | 0 |
| v29 | molecular | 2026 | shuffled_evidence_program_agent | 5 | 0.00908 | 0 |
| v30 | full | 42 | own_C0P0 | 5 | 0.00782 | 0 |
| v30 | full | 42 | own_C0P1 | 5 | 0.00623 | 0 |
| v30 | full | 42 | own_C1P0 | 5 | 0.00623 | 0 |
| v30 | full | 42 | own_C1P1 | 5 | 0.00623 | 0 |
| v30 | full | 42 | shuffled_C0P0 | 5 | 0.00616 | 0 |
| v30 | full | 42 | shuffled_C0P1 | 5 | 0.00589 | 0 |
| v30 | full | 42 | shuffled_C1P0 | 5 | 0.00589 | 0 |
| v30 | full | 42 | shuffled_C1P1 | 5 | 0.00589 | 0 |
| v30 | molecular | 42 | own_C0P0 | 5 | 0.00934 | 0 |
| v30 | molecular | 42 | own_C0P1 | 5 | 0.00934 | 0 |
| v30 | molecular | 42 | own_C1P0 | 5 | 0.00877 | 0 |
| v30 | molecular | 42 | own_C1P1 | 5 | 0.00881 | 0 |
| v30 | molecular | 42 | shuffled_C0P0 | 5 | 0.00831 | 0 |
| v30 | molecular | 42 | shuffled_C0P1 | 5 | 0.00836 | 0 |
| v30 | molecular | 42 | shuffled_C1P0 | 5 | 0.00827 | 0 |
| v30 | molecular | 42 | shuffled_C1P1 | 5 | 0.00827 | 0 |

此处统计方法层面的逻辑请求，以及保存的成功响应对应价格。相同响应可能跨组合复用，不能把表中价格相加当作新增账户扣款。失败尝试、账户级用量和等待充值时间不在此表覆盖范围内；实际计费请求仍以物理请求账本为准。

## 5. 传统方法计时范围

| Panel | Method | Recorded block seconds | Configurations × thresholds | Shared feature seconds |
|---|---|---:|---:|---:|
| full | prevalence | not measured | 1 × 6 = 6 | 3.062 |
| full | last_visit | not measured | 1 × 6 = 6 | 3.062 |
| full | cosine_knn | 2.574 | 3 × 6 = 18 | 3.062 |
| full | structured_logistic | 92.086 | 3 × 6 = 18 | 3.062 |
| molecular | prevalence | not measured | 1 × 6 = 6 | 3.283 |
| molecular | last_visit | not measured | 1 × 6 = 6 | 3.283 |
| molecular | cosine_knn | 3.893 | 3 × 6 = 18 | 3.283 |
| molecular | structured_logistic | 87.223 | 3 × 6 = 18 | 3.283 |

余弦检索和逻辑回归计时包含 proposal 搜索及 guard 预测，范围宽于神经模型的纯拟合计时。历史频率／上次就诊方法保存的零值表示未计时。特征构建按每个药物分组共享一次。现有记录不支持推算 FLOPs、能耗、独占设备延迟或峰值内存。

## 6. 如何解释这些数字

CPU 与 Apple MPS 上有多个任务并行运行。各方法计时之和反映共享硬件下的活动时间，不是连续经过的墙钟时间，也不能作为独占设备速度排名。本次核算没有新增拟合、模型请求或测试预测；它重建已有回执并绑定源哈希，不是独立计算性能剖析。每个已登记干预内部按其协议匹配预算，异构方法之间分别披露搜索与拟合开销。

[Machine-readable receipts and source hashes](compute_accounting.json) · [Common method study](../upgrade_v27/RESULTS.zh.md) · [Common test extension](../upgrade_v30/COMMON_TEST.zh.md)
