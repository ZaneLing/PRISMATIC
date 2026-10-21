# 历史病例使用记录与冻结测试子集

## eICU 暴露记录 — 2026-10-21

v52的576位患者（192反思、64提案、64守门、256审计）现已暴露；他们与v25患者均不重叠。下一次独立验证须同时排除v25和v52患者。审计医院并非历史上从未使用过。成员文件哈希和位置记录于 `exposure_registry.json`。

## 1. 已实际完成的独立成员核验

在当前统一测试尚未开始时，独立重建 **11类实验／38种数据角色**，得到 **69,839位历史使用或保守预留患者**。原890位测试患者中，**572位**出现在该并集中；冻结的补充子集保留 **318位患者／801次就诊**，保留每位患者全部原测试就诊，与历史并集交叉为零。

原完整测试主表保持不变；排除只依赖身份和历史角色，不使用成绩或预测。两个药物空间使用完全相同的患者子集。源协议的全部合格重复就诊患者已经分配（8,905/8,905），重新命名已有划分不会产生新数据。

| Recorded family | Patients overlapping the890 current test patients | Membership evidence |
|---|---:|---|
| v2_6h | 367 | Original deterministic sampler reconstructed; public per-role admission/patient counts match. No original membership hash was recorded. |
| v2_24h | 371 | Original deterministic sampler reconstructed; public per-role admission/patient counts match. No original membership hash was recorded. |
| v2_legacy_support | 138 | Original deterministic sampler; historical membership only, no legacy endpoint recomputed. |
| v3 | 323 | Original deterministic sampler; recorded role counts match. |
| v4_v5_v6 | 323 | Source cohort hash and original admission membership hashes match; v5/v6 use the same deterministic selection. |
| v7 | 178 | All original role membership hashes and patient counts match. |
| prepared_review | 36 | Read saved manifest; conservatively exclude despite no completed clinician ratings. |
| v9 | 20 | Exact saved local parameter-case patient membership; all listed roles excluded. |
| v15 | 20 | Exact saved local parameter-case patient membership; all listed roles excluded. |
| v21_v22_v23 | 50 | Stored source IDs reconstruct all original case membership hashes. |
| current_v27_v29_v30 | 0 | Current fitting/development membership included; reserved unexecuted test handled separately. |

各行有交叉，不能相加。早期确定性样本有源文件／代码哈希及匹配计数，但未保存当年的成员摘要；后期样本与原始成员摘要或实际存储身份一致。已预留审核病例也保守排除，即使尚无医生标注；这属于使用记录，不要求医生审核后才能计算GT指标。

## 2. 证据范围与后续对照

登记册覆盖列出的PRISMATIC MIMIC-IV实验历史，不能证明患者从未进入基础模型预训练、未留记录的实验或外部使用。总体数据审计与模型使用记录不同。本子集是预先登记的历史记录排除敏感性分析，不是全球完全未触碰的确认集，也不是新外部数据；两组患者构成不同，成绩差异不能解释为“接触过病例”的因果效应。

**模型成绩待执行。** 两套共同测试核验完成后，评估器对相同不可变预测分别计算保留组与排除组结果，报告所有已选择方法、种子波动和描述性患者聚类区间，不新增拟合、API调用或检查点选择。

[Registered protocol](prior_case_exclusion_protocol.json) · [Registry aggregates](exposure_registry.json) · [Independent membership audit](exposure_registry_audit.json)
