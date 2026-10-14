# v0.29：条件程序记忆与隔离的新witness

## 1. 问题与真实机制

v0.27的记忆收益很小，尚未证明优于贪心编辑。本次登记干预将普通逐药物校准与语言agent规则生成分开，并把每位witness患者永久排除在策略拟合和候选统计之外。使用相同历史MIMIC-IV ATC-L4任务，完整与分子空间分别报告；不生成剂量，不证明入院时点的临床正确性。

7,115位训练患者按与标签无关的哈希划分：5,692位拟合策略，1,423位永久用于witness验证。五轮逐步增加拟合患者，每轮只使用一批新的witness，分别285／285／285／284／284人。任何轮次的模型系数和候选统计都不能使用witness标签；固定v0.27词表早于本划分。每位witness只在所属轮内被最多四项编辑顺序复用，仍属于自适应训练验证，不是独立确认。

共同校准对照从拟合患者的交叉拟合预测中学习逐类别阈值。语言agent只接收有足够支持的聚合特征／药物错误上下文，生成一到两个条件组成的新增或删除程序；再用真实归纳收益和新witness核验。贪心对照穷举包含肯定与否定条件的组合，随机和打乱证据方法同时保留。打乱仅改变数值支持／收益的对应关系，错误驱动的药类及特征筛选仍固定。取消witness方法使用相同agent提议，不冒充独立反事实学习轨迹。

**实际进化对象：可执行条件规则记忆。** 校准和系数重新拟合属于普通监督更新；语言模型权重、工具代码保持固定。原始基础／折模型、提议、拒绝和全部原始轮次均本地保存。本版不运行测试集推断。

## 2. 真实运行状态

| Panel | Seed | Completed rounds /5 | Own-agent rules | Status |
|---|---:|---:|---:|---|
| full | 137 | 4 | 10 | training |
| full | 42 | 5 | 6 | selection_frozen |
| molecular | 137 | 5 | 8 | selection_frozen |
| molecular | 2026 | 2 | 3 | training |
| molecular | 42 | 5 | 5 | selection_frozen |

合成执行探针已覆盖患者角色隔离、组合条件语义、目标字段拒绝、实际支持度、接纳／拒绝与校准变化；它们不是临床性能分数。

## 3. 独立核验后的guard比较

相同1,231次就诊／467人，仅报告guard。每个纳入种子均完成原始数据重建及所选基础／全部折模型的独立重新拟合；未完成或未审计的单元保持待完成。

| Panel | Method | Audited seeds | Patient F1 ± SD | Patient Jaccard ± SD |
|---|---|---:|---:|---:|
| full | raw_policy | 1 | 0.60594 (one seed) | 0.45161 (one seed) |
| full | calibrated_policy | 1 | 0.60719 (one seed) | 0.45324 (one seed) |
| full | greedy_conditional_memory | 1 | 0.60719 (one seed) | 0.45306 (one seed) |
| full | random_conditional_memory | 1 | 0.60687 (one seed) | 0.45287 (one seed) |
| full | own_error_program_agent | 1 | 0.60789 (one seed) | 0.45379 (one seed) |
| full | shuffled_evidence_program_agent | 1 | 0.60719 (one seed) | 0.45324 (one seed) |
| full | matched_proposals_no_witness | 1 | 0.60694 (one seed) | 0.45262 (one seed) |
| molecular | raw_policy | 1 | 0.57623 (one seed) | 0.42480 (one seed) |
| molecular | calibrated_policy | 1 | 0.57911 (one seed) | 0.42750 (one seed) |
| molecular | greedy_conditional_memory | 1 | 0.58026 (one seed) | 0.42835 (one seed) |
| molecular | random_conditional_memory | 1 | 0.57984 (one seed) | 0.42805 (one seed) |
| molecular | own_error_program_agent | 1 | 0.57908 (one seed) | 0.42721 (one seed) |
| molecular | shuffled_evidence_program_agent | 1 | 0.57877 (one seed) | 0.42715 (one seed) |
| molecular | matched_proposals_no_witness | 1 | 0.57887 (one seed) | 0.42683 (one seed) |

| Panel | Own agent minus comparator | F1 difference (pp) | Patient interval (pp) |
|---|---|---:|---:|
| full | raw_policy | +0.195 | [-0.099, +0.487] |
| full | calibrated_policy | +0.070 | [-0.005, +0.160] |
| full | greedy_conditional_memory | +0.070 | [+0.020, +0.123] |
| full | random_conditional_memory | +0.102 | [+0.015, +0.202] |
| full | shuffled_evidence_program_agent | +0.070 | [-0.005, +0.160] |
| full | matched_proposals_no_witness | +0.095 | [-0.006, +0.197] |
| molecular | raw_policy | +0.285 | [-0.073, +0.667] |
| molecular | calibrated_policy | -0.003 | [-0.111, +0.116] |
| molecular | greedy_conditional_memory | -0.118 | [-0.232, -0.002] |
| molecular | random_conditional_memory | -0.076 | [-0.236, +0.092] |
| molecular | shuffled_evidence_program_agent | +0.031 | [-0.095, +0.169] |
| molecular | matched_proposals_no_witness | +0.021 | [-0.098, +0.138] |

区间先平均已有种子再按患者重采样，不估计新种子的变化，属于未作多重比较校正的描述性区间。相对原策略的提升必须分解为普通校准收益与语言agent额外贡献。

| Panel | Round | Raw proposal F1 | Calibrated proposal F1 | Own-agent proposal F1 | Rules / conjunctions by seed |
|---|---:|---:|---:|---:|---|
| full | 1 | 0.56351 | 0.56919 | 0.56939 | 2/0 |
| full | 2 | 0.57951 | 0.58630 | 0.58582 | 3/0 |
| full | 3 | 0.58569 | 0.59365 | 0.59280 | 3/1 |
| full | 4 | 0.59183 | 0.59920 | 0.59892 | 5/1 |
| full | 5 | 0.59570 | 0.60234 | 0.60210 | 6/1 |
| molecular | 1 | 0.53828 | 0.54199 | 0.54256 | 2/0 |
| molecular | 2 | 0.55363 | 0.55621 | 0.55789 | 3/0 |
| molecular | 3 | 0.56000 | 0.57210 | 0.57221 | 4/0 |
| molecular | 4 | 0.56934 | 0.57732 | 0.57747 | 6/0 |
| molecular | 5 | 0.57055 | 0.58171 | 0.58171 | 5/0 |

| Panel | Method | Logical model calls | Logical response USD | Enumerated programs | Proposal seconds |
|---|---|---:|---:|---:|---:|
| full | raw_policy | 0 | 0.00000 | 0 | 0.0 |
| full | calibrated_policy | 0 | 0.00000 | 0 | 0.0 |
| full | greedy_conditional_memory | 0 | 0.00000 | 25448 | 67.5 |
| full | random_conditional_memory | 0 | 0.00000 | 25446 | 68.7 |
| full | own_error_program_agent | 5 | 0.00983 | 15373 | 65.9 |
| full | shuffled_evidence_program_agent | 5 | 0.00890 | 15363 | 88.6 |
| full | matched_proposals_no_witness | 0 | 0.00000 | 0 | 0.1 |
| molecular | raw_policy | 0 | 0.00000 | 0 | 0.0 |
| molecular | calibrated_policy | 0 | 0.00000 | 0 | 0.0 |
| molecular | greedy_conditional_memory | 0 | 0.00000 | 25451 | 70.2 |
| molecular | random_conditional_memory | 0 | 0.00000 | 25452 | 70.0 |
| molecular | own_error_program_agent | 5 | 0.00846 | 15375 | 53.2 |
| molecular | shuffled_evidence_program_agent | 5 | 0.00757 | 15372 | 52.6 |
| molecular | matched_proposals_no_witness | 0 | 0.00000 | 0 | 0.0 |

## 4. 已执行的旧记忆与新编辑诊断

本登记回放在早期开发成绩已观察后进行，只用proposal病例；不改训练决定、不拟合新模型、不新增API调用。每轮不同记忆使用同一个当前策略与校准。

| Audited run | Accepted edits with positive proposal transfer | Negative transfer | Zero transfer |
|---|---:|---:|---:|
| full-seed42 | 4 | 4 | 0 |
| molecular-seed42 | 4 | 3 | 0 |

| Audited run | Round | Prior-memory effect (F1 pp) | New-edit effect (F1 pp) |
|---|---:|---:|---:|
| full-seed42 | 1 | +0.0000 | +0.0203 |
| full-seed42 | 2 | -0.0182 | -0.0296 |
| full-seed42 | 3 | -0.1099 | +0.0249 |
| full-seed42 | 4 | -0.0077 | -0.0201 |
| full-seed42 | 5 | -0.0421 | +0.0185 |
| molecular-seed42 | 1 | +0.0000 | +0.0574 |
| molecular-seed42 | 2 | +0.1709 | -0.0036 |
| molecular-seed42 | 3 | +0.0263 | -0.0153 |
| molecular-seed42 | 4 | +0.0202 | -0.0056 |
| molecular-seed42 | 5 | -0.0099 | +0.0101 |

新witness上有益的编辑仍可能损害proposal表现；基础策略／校准改变后，旧规则的作用也会变化。这为重新核验规则兼容性提供依据，但不是已经执行的新改进agent，也不是独立学习的反事实轨迹。

## Artifacts / 交付

- [Registered protocol](protocol.json)
- [Actual pre-training probes](results/runtime_probe.json)
- [Audit-gated aggregate results](results/summary.json)
- [Registered memory diagnosis](diagnostic_addendum.json) and [actual replay effects](results/memory_diagnostic.json)
- [Historical round-selection metadata correction](../paper/round_selection_metadata_audit.json)

滚动导出的共享字典会使旧轮次嵌套`round.best`显示较晚选择。不可变逐轮回执与各方法`best_round`已独立核对，历史选择修正在上方链接；分数、规则和最终模型选择没有变化。受限病例、预测与权重保持本地。
