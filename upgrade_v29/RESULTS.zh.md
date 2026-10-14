# v0.29：条件程序记忆与隔离的新witness

## 1. 问题与真实机制

v0.27的记忆收益很小，尚未证明优于贪心编辑。本次登记干预将普通逐药物校准与语言agent规则生成分开，并把每位witness患者永久排除在策略拟合和候选统计之外。使用相同历史MIMIC-IV ATC-L4任务，完整与分子空间分别报告；不生成剂量，不证明入院时点的临床正确性。

7,115位训练患者按与标签无关的哈希划分：5,692位拟合策略，1,423位永久用于witness验证。五轮逐步增加拟合患者，每轮只使用一批新的witness，分别285／285／285／284／284人。任何轮次的模型系数和候选统计都不能使用witness标签；固定v0.27词表早于本划分。每位witness只在所属轮内被最多四项编辑顺序复用，仍属于自适应训练验证，不是独立确认。

共同校准对照从拟合患者的交叉拟合预测中学习逐类别阈值。语言agent只接收有足够支持的聚合特征／药物错误上下文，生成一到两个条件组成的新增或删除程序；再用真实归纳收益和新witness核验。贪心对照穷举包含肯定与否定条件的组合，随机和打乱证据方法同时保留。打乱仅改变数值支持／收益的对应关系，错误驱动的药类及特征筛选仍固定。取消witness方法使用相同agent提议，不冒充独立反事实学习轨迹。

**实际进化对象：可执行条件规则记忆。** 校准和系数重新拟合属于普通监督更新；语言模型权重、工具代码保持固定。原始基础／折模型、提议、拒绝和全部原始轮次均本地保存。本版不运行测试集推断。

## 2. 真实运行状态

**API中断：** 新HTTP402后，未完成模型调用等待补充额度；已完成状态和独立核验保留。

| Panel | Seed | Completed rounds /5 | Own-agent rules | Status |
|---|---:|---:|---:|---|
| full | 137 | 5 | 11 | selection_frozen |
| full | 2026 | 4 | 4 | training |
| full | 42 | 5 | 6 | selection_frozen |
| molecular | 137 | 5 | 8 | selection_frozen |
| molecular | 2026 | 5 | 9 | selection_frozen |
| molecular | 42 | 5 | 5 | selection_frozen |

合成执行探针已覆盖患者角色隔离、组合条件语义、目标字段拒绝、实际支持度、接纳／拒绝与校准变化；它们不是临床性能分数。

## 3. 独立核验后的guard比较

相同1,231次就诊／467人，仅报告guard。每个纳入种子均完成原始数据重建及所选基础／全部折模型的独立重新拟合；未完成或未审计的单元保持待完成。

| Panel | Method | Audited seeds | Patient F1 ± SD | Patient Jaccard ± SD |
|---|---|---:|---:|---:|
| full | raw_policy | 2 | 0.60554 ± 0.00058 | 0.45116 ± 0.00064 |
| full | calibrated_policy | 2 | 0.60758 ± 0.00056 | 0.45361 ± 0.00052 |
| full | greedy_conditional_memory | 2 | 0.60775 ± 0.00079 | 0.45365 ± 0.00083 |
| full | random_conditional_memory | 2 | 0.60715 ± 0.00040 | 0.45317 ± 0.00043 |
| full | own_error_program_agent | 2 | 0.60771 ± 0.00026 | 0.45355 ± 0.00033 |
| full | shuffled_evidence_program_agent | 2 | 0.60761 ± 0.00061 | 0.45367 ± 0.00061 |
| full | matched_proposals_no_witness | 2 | 0.60720 ± 0.00036 | 0.45289 ± 0.00039 |
| molecular | raw_policy | 3 | 0.57564 ± 0.00053 | 0.42407 ± 0.00070 |
| molecular | calibrated_policy | 3 | 0.57989 ± 0.00088 | 0.42804 ± 0.00064 |
| molecular | greedy_conditional_memory | 3 | 0.58094 ± 0.00060 | 0.42903 ± 0.00059 |
| molecular | random_conditional_memory | 3 | 0.57930 ± 0.00168 | 0.42723 ± 0.00154 |
| molecular | own_error_program_agent | 3 | 0.58021 ± 0.00105 | 0.42827 ± 0.00095 |
| molecular | shuffled_evidence_program_agent | 3 | 0.57956 ± 0.00097 | 0.42769 ± 0.00070 |
| molecular | matched_proposals_no_witness | 3 | 0.58010 ± 0.00106 | 0.42801 ± 0.00102 |

| Panel | Own agent minus comparator | F1 difference (pp) | Patient interval (pp) |
|---|---|---:|---:|
| full | raw_policy | +0.217 | [-0.024, +0.461] |
| full | calibrated_policy | +0.013 | [-0.047, +0.078] |
| full | greedy_conditional_memory | -0.005 | [-0.060, +0.051] |
| full | random_conditional_memory | +0.056 | [-0.010, +0.127] |
| full | shuffled_evidence_program_agent | +0.009 | [-0.054, +0.075] |
| full | matched_proposals_no_witness | +0.051 | [-0.007, +0.113] |
| molecular | raw_policy | +0.457 | [+0.177, +0.750] |
| molecular | calibrated_policy | +0.032 | [-0.037, +0.100] |
| molecular | greedy_conditional_memory | -0.073 | [-0.148, +0.002] |
| molecular | random_conditional_memory | +0.091 | [+0.003, +0.182] |
| molecular | shuffled_evidence_program_agent | +0.065 | [-0.017, +0.146] |
| molecular | matched_proposals_no_witness | +0.011 | [-0.054, +0.078] |

区间先平均已有种子再按患者重采样，不估计新种子的变化，属于未作多重比较校正的描述性区间。相对原策略的提升必须分解为普通校准收益与语言agent额外贡献。

| Panel | Round | Raw proposal F1 | Calibrated proposal F1 | Own-agent proposal F1 | Rules / conjunctions by seed |
|---|---:|---:|---:|---:|---|
| full | 1 | 0.56255 | 0.56797 | 0.56866 | 2/0, 3/0 |
| full | 2 | 0.57991 | 0.58543 | 0.58543 | 3/0, 3/0 |
| full | 3 | 0.58750 | 0.59412 | 0.59365 | 3/1, 7/0 |
| full | 4 | 0.59385 | 0.59807 | 0.59755 | 5/1, 10/0 |
| full | 5 | 0.59706 | 0.60191 | 0.60157 | 6/1, 11/1 |
| molecular | 1 | 0.53803 | 0.54189 | 0.54214 | 2/0, 0/0, 1/1 |
| molecular | 2 | 0.55354 | 0.55899 | 0.55957 | 3/0, 0/0, 3/1 |
| molecular | 3 | 0.56260 | 0.57181 | 0.57188 | 4/0, 2/0, 4/2 |
| molecular | 4 | 0.57198 | 0.57727 | 0.57716 | 6/0, 5/0, 6/2 |
| molecular | 5 | 0.57429 | 0.58165 | 0.58178 | 5/0, 8/0, 9/2 |

| Panel | Method | Logical model calls | Logical response USD | Enumerated programs | Proposal seconds |
|---|---|---:|---:|---:|---:|
| full | raw_policy | 0 | 0.00000 | 0 | 0.0 |
| full | calibrated_policy | 0 | 0.00000 | 0 | 0.0 |
| full | greedy_conditional_memory | 0 | 0.00000 | 50897 | 139.3 |
| full | random_conditional_memory | 0 | 0.00000 | 50892 | 141.9 |
| full | own_error_program_agent | 10 | 0.01283 | 30756 | 129.2 |
| full | shuffled_evidence_program_agent | 10 | 0.01290 | 30725 | 146.3 |
| full | matched_proposals_no_witness | 0 | 0.00000 | 0 | 0.1 |
| molecular | raw_policy | 0 | 0.00000 | 0 | 0.0 |
| molecular | calibrated_policy | 0 | 0.00000 | 0 | 0.0 |
| molecular | greedy_conditional_memory | 0 | 0.00000 | 76354 | 214.1 |
| molecular | random_conditional_memory | 0 | 0.00000 | 76374 | 214.0 |
| molecular | own_error_program_agent | 15 | 0.02775 | 46116 | 167.9 |
| molecular | shuffled_evidence_program_agent | 15 | 0.02504 | 46111 | 162.3 |
| molecular | matched_proposals_no_witness | 0 | 0.00000 | 0 | 0.1 |

## 4. 已执行的旧记忆与新编辑诊断

本登记回放在早期开发成绩已观察后进行，只用proposal病例；不改训练决定、不拟合新模型、不新增API调用。每轮不同记忆使用同一个当前策略与校准。

| Audited run | Accepted edits with positive proposal transfer | Negative transfer | Zero transfer |
|---|---:|---:|---:|
| full-seed42 | 4 | 4 | 0 |
| full-seed137 | 7 | 4 | 0 |
| molecular-seed42 | 4 | 3 | 0 |
| molecular-seed137 | 5 | 3 | 0 |
| molecular-seed2026 | 6 | 3 | 0 |

| Audited run | Round | Prior-memory effect (F1 pp) | New-edit effect (F1 pp) |
|---|---:|---:|---:|
| full-seed42 | 1 | +0.0000 | +0.0203 |
| full-seed42 | 2 | -0.0182 | -0.0296 |
| full-seed42 | 3 | -0.1099 | +0.0249 |
| full-seed42 | 4 | -0.0077 | -0.0201 |
| full-seed42 | 5 | -0.0421 | +0.0185 |
| full-seed137 | 1 | +0.0000 | +0.1175 |
| full-seed137 | 2 | +0.0462 | +0.0000 |
| full-seed137 | 3 | -0.0277 | +0.0176 |
| full-seed137 | 4 | -0.0640 | -0.0109 |
| full-seed137 | 5 | -0.0371 | -0.0089 |
| molecular-seed42 | 1 | +0.0000 | +0.0574 |
| molecular-seed42 | 2 | +0.1709 | -0.0036 |
| molecular-seed42 | 3 | +0.0263 | -0.0153 |
| molecular-seed42 | 4 | +0.0202 | -0.0056 |
| molecular-seed42 | 5 | -0.0099 | +0.0101 |
| molecular-seed137 | 1 | +0.0000 | +0.0000 |
| molecular-seed137 | 2 | +0.0000 | +0.0000 |
| molecular-seed137 | 3 | +0.0000 | +0.0037 |
| molecular-seed137 | 4 | +0.0209 | +0.0476 |
| molecular-seed137 | 5 | +0.0458 | +0.0282 |
| molecular-seed2026 | 1 | +0.0000 | +0.0203 |
| molecular-seed2026 | 2 | +0.0002 | +0.0059 |
| molecular-seed2026 | 3 | -0.0184 | +0.0252 |
| molecular-seed2026 | 4 | -0.0485 | -0.0661 |
| molecular-seed2026 | 5 | -0.0428 | +0.0088 |

新witness上有益的编辑仍可能损害proposal表现；基础策略／校准改变后，旧规则的作用也会变化。这为重新核验规则兼容性提供依据，但不是已经执行的新改进agent，也不是独立学习的反事实轨迹。

## Artifacts / 交付

- [Registered protocol](protocol.json)
- [Actual pre-training probes](results/runtime_probe.json)
- [Audit-gated aggregate results](results/summary.json)
- [Registered memory diagnosis](diagnostic_addendum.json) and [actual replay effects](results/memory_diagnostic.json)
- [Historical round-selection metadata correction](../paper/round_selection_metadata_audit.json)

滚动导出的共享字典会使旧轮次嵌套`round.best`显示较晚选择。不可变逐轮回执与各方法`best_round`已独立核对，历史选择修正在上方链接；分数、规则和最终模型选择没有变化。受限病例、预测与权重保持本地。
