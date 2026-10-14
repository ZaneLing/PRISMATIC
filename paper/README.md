# PRISMATIC 2 论文式研究记录 / Versioned research manuscript

**当前版本 / Current version: v0.2（2026-10-14）**

这里是持续更新的论文入口。每次新增实验发布一个独立的中英文版本文件，保留旧版，更新下方索引与变更记录。统计表只写入已经完成并可追溯到结果文件的实验；尚未完成的跨论文对照在“待跑”栏，不填借用分数。

This is the durable manuscript index. Each release adds separate Chinese and English files; previous versions remain available. Result tables contain completed, traceable runs only.

## 从哪里看主表 / Main comparison table

- **当前 harness 主表：**[v0.2 中文论文 §4.1](versions/v0.2-2026-10-14.zh.md#41-主表同题配对的-rxsafebench-结果) / [v0.2 English paper §4.1](versions/v0.2-2026-10-14.en.md#41-primary-table-paired-rxsafebench-results)
- **主表数据集：**RxSafeBench 公开模拟会诊题的固定 **60 题**，禁忌 30、相互作用 30。它测三选一药物安全选择，尚未测完整处方生成。
- **比较对象：**相同三个 OpenRouter 模型各自的单次直接作答、两次调用普通复核、两次调用证据约束 harness。三组使用完全相同的 60 道题和第一次回答。
- **当前结论：**harness 相对直接作答在 GPT、Gemini、DeepSeek 上分别为 0、−5、+3 道正确题；三个配对区间均包含 0，尚无稳定提升证据。
- **病例增长表：**[v0.2 中文论文 §4.3](versions/v0.2-2026-10-14.zh.md#43-病例增长与辅助医嘱) / [English §4.3](versions/v0.2-2026-10-14.en.md#43-case-growth-and-supportive-orders)。数据为本地受限 MIMIC-IV + MIMIC-IV-ED，只发布汇总。

## 版本 / Releases

| 版本 | 日期 | 中文 | English | 新内容 |
| --- | --- | --- | --- | --- |
| v0.2 | 2026-10-14 | [论文](versions/v0.2-2026-10-14.zh.md) | [Paper](versions/v0.2-2026-10-14.en.md) | 明确主表、配对 harness 初试、论文结构、下一步外部方法复现 |
| v0.1 | 2026-10-14 | [初版归档](versions/v0.1-2026-10-14.zh.md) | [First report archive](versions/v0.1-2026-10-14.en.md) | 病例增长、直接模型测试、研究计划；当时尚无 harness 主表 |

## 固定的更新规则 / Update contract

1. 新实验先提交代码、样本定义、逐题或汇总结果、统计脚本，再增加 `vX.Y-YYYY-MM-DD.zh.md` 和同名 `.en.md`。受限逐例数据留在本地受限目录。
2. 每版写清数据集版本与哈希、样本量、切分、模型/提示版本、预算、主要指标、置信区间、失败与费用。
3. 旧版只允许修复断链或明显笔误，并在 [变更记录](CHANGELOG.md) 注明；数值或结论改变必须发新版。
4. 跨论文比较必须在**同一数据、输入、药物编码、指标与预算**下重跑；无法重跑的工作只放相关研究表。

## 结果与代码 / Results and code

- [RxSafeBench harness 汇总](../upgrade_v2/results/openrouter_rxsafe_harness_pilot.json) 和 [逐题预测](../upgrade_v2/results/openrouter_rxsafe_harness_pilot_predictions.json)
- [RxSafeBench 直接作答](../upgrade_v2/results/openrouter_rxsafe_pilot.json)、[RxQA 直接作答](../upgrade_v2/results/openrouter_rxqa_pilot.json)
- [病例增长汇总](../upgrade_v2/results/evolution_curve.json)、[实验代码与复现说明](../upgrade_v2/README.md)
