# RxRSIAgent：当前主表、进化证据与执行状态

更新：2026-10-14。此文是长期更新的阅读入口；各版本保留协议、失败和结果。本轮用户充值后，之前的 API 缺失均已补齐。**目前仍未证明我们的方法优于最强对照。**

## 1. 方法对比主表在哪、测什么？

### 主表 A：处方药物和订单匹配

同一 MIMIC-IV/ED 预处理、40,000 训练住院、4,000 测试住院（3,440 位患者），三种子；药物为冻结的 128 个原始药名空间。订单为药物、途径、剂量字符串、单位的联合匹配。它不等同于原论文 ATC-L4/RxNorm 协议。这里没有盐水出现 F1。

| Method | Drug micro-F1 | Core-order micro-F1 |
|---|---:|---:|
| Word/character ensemble + tools | 0.40209 ± 0.00058 | 0.28110 ± 0.00062 |
| RxRSI selected state | 0.39920 ± 0.00251 | 0.27865 ± 0.00142 |
| Freeze initial memory | 0.39976 ± 0.00224 | 0.27926 ± 0.00113 |
| Freeze initial order tool | 0.39920 ± 0.00251 | 0.27494 ± 0.00142 |

[完整 12 方法/消融表、逐轮结果](../upgrade_v7/RESULTS.zh.md)。临床历史 GT 可直接自动评分；额外医生标注不是计算这些指标的前提。

### 主表 B：公开处方选择题上的方法比较

RxSafeBench 去重后 2,000 题，按场景组切分为 625/190/197/988 训练/候选选择/退化检查/测试题；这是明确标注的三选项衍生任务。所有行固定 DeepSeek-V4.1-Flash，比较的是方法。± 为三个进化顺序的标准差；固定答案跨顺序复用。作者核心只跑 seed 42。模型调用数不同，开发成本另记，不能声称所有行等预算。

| Method | Accuracy (%) | Calls/case | Evidence |
|---|---:|---:|---|
| Direct LLM | 46.15 ± 0.00 | 1 | [v0.8](../upgrade_v8/RESULTS.en.md) |
| CoT | 47.27 ± 0.00 | 1 | [v0.8](../upgrade_v8/RESULTS.en.md) |
| Self-Refine | 47.57 ± 0.00 | 2 | [v0.8](../upgrade_v8/RESULTS.en.md) |
| Case RAG | 49.09 ± 0.00 | 1 | [v0.8](../upgrade_v8/RESULTS.en.md) |
| Reflexion task adaptation | 47.64 ± 0.64 | 1 | [v0.8](../upgrade_v8/RESULTS.en.md) |
| GRASP task adaptation | 48.01 ± 1.29 | 1 | [v0.8](../upgrade_v8/RESULTS.en.md) |
| EvoTool task adaptation | 47.27 ± 0.00 | 1 | [v0.8](../upgrade_v8/RESULTS.en.md) |
| RxRSI language artifacts | 47.27 ± 0.00 | 1 | [v0.8](../upgrade_v8/RESULTS.en.md) |
| Author GRASP core + task adapter | **50.81** | 1 | [v0.10](../upgrade_v10/RESULTS.en.md) |
| Fixed balanced evidence review | 48.99 | 2 | [v0.11](../upgrade_v11/RESULTS.en.md) |
| Fixed safety evidence review | 49.29 | 2 | [v0.11](../upgrade_v11/RESULTS.en.md) |
| Fixed indication evidence review | 48.38 | 2 | [v0.11](../upgrade_v11/RESULTS.en.md) |
| Outcome verifier: uniform | 49.12 ± 0.23 | 2 | [v0.13](../upgrade_v13/RESULTS.en.md) |
| Outcome verifier: error_prioritized | 49.02 ± 0.06 | 2 | [v0.13](../upgrade_v13/RESULTS.en.md) |
| One-call fixed grounding | 50.51 | 1 | [v0.17](../upgrade_v17/RESULTS.en.md) |
| Grounded skill evolution | 50.71 | 1 | [v0.17](../upgrade_v17/RESULTS.en.md) |

作者 GRASP 核心在当前完整对照中最好。`task adaptation` 是我们的任务适配，不冒充原论文实现；作者核心保持源码不变，但任务适配器由我们编写。跨论文原分数仅在英文论文的独立文献表中引用，不放入本表。

## 2. RSI 到底改变了什么？

| 实验 | 实际改变对象 | 逐轮证据与结论 |
|---|---|---|
| v0.7 | 监督策略参数、病例记忆、联合订单模板 | 三种子五检查点随病例增长改善，但输给同数据静态集成；不能归因为独有 RSI |
| v0.8 | LLM 提议技能文本、记忆、证据关注词 | 三种子四轮全部拒绝完整 RxRSI 的候选；最终未进化，不宣称成功 |
| v0.10 | 作者 GRASP 技能文件 | 在同一衍生任务上提高至 50.81%，RxQA 迁移反而 193→189/300 |
| v0.12–13 | 工具路由/结果核验器系数与阈值 | 权重真实变化，部分更新被接受，但有测试退化；错误优先没有稳定优于普通更新 |
| v0.9 | 本地 Qwen LoRA 参数 | 500 例全检查点测试完成；两臂均低于直接 top-8 工具 |
| v0.15 | 二元纳入/排除监督下的 LoRA 参数 | 为处理过度开药而事先声明的干预，现已开始本地训练 |
| v0.17 | 固定说明书工具上的 GRASP 技能文件 | 完整结果 501/988；固定证据 499、作者核心 502；迁移下降 |

每种对象都有版本哈希，接受/拒绝及修复/退化记录。图：

![处方病例增长轨迹](../upgrade_v7/round_curves.png)

![公开语言进化轨迹](../upgrade_v8/round_curves.png)

## 3. 本次恢复后新增实测

- **适应证证据复核：478/988，48.38%。** HTTP 缺失已全部补齐，原选择协议不变。
- **Gemini 开发预算修复：**同 190 题 CoT 72→105 正确，已收到但无效回答 69→2；证据方法 62→100 正确、无效 85→1。推理强度和完成预算同时变化，不分别归因，也不当作测试集或 RSI 成绩。[完整报告](../upgrade_v16/RESULTS.zh.md)。
- **真实 FHIR：**五项读写/回读/版本/原子失败/清理检查通过。16 题开发试验直接工具 10/16、固定核验 harness 8/16；所有 11 个写入资源回读成功并清理，独立重评分一致。[报告](../upgrade_v14/RESULTS.zh.md)。

## 4. 继续执行的顺序与交付标准

1. v0.9 全检查点测试、独立重算和患者聚类区间已完成，见新增本地参数主表。
2. v0.15 已接续开始训练；保持患者与训练预算一致，检验显式负候选监督是否减少过度选择。
3. v0.16 截断检查已完成，冻结 2,048-token/low 配置。继续 v0.17 固定证据/进化证据与 RxQA；v0.18 随后在 Gemini 上比较四种冻结方法。
4. 根据 FHIR 开发失败改进检索与动作协议，再进行完整同分布/未见任务类型评价；开发 16 题不能替代正式测试。
5. 最终保留没有参与迭代的确认测试、多种子、消融、费用和退化记录。若仍未超过强对照，论文结论如实保留，不能通过挑选方法或修改测试标签获得“第一”。

[英文论文](latex/v0.3/prismatic_v03_en.tex) · [持续执行计划](COMPLETION_PLAN.md) · [版本记录](CHANGELOG.md)。受限患者记录、权重、原始轨迹和密钥始终不进入 GitHub。

## 新增已完成主表：500 例本地参数进化

与上方 4,000 例主表分开：这里是事先保留的 500 次住院、494 位患者，共用初始 8k 候选工具。GT 平均 6.784 个药物，固定目录可覆盖 3.802 个。选择在测试前冻结。

| Method | Drug F1 | Core-order F1 | Mean drugs |
|---|---:|---:|---:|
| base | 0.23399 | 0.13593 | 5.46 |
| uniform_sft | 0.28694 | 0.19115 | 17.42 |
| error_prioritized_sft | 0.28432 | 0.19137 | 18.98 |
| all_20_candidate_tools | 0.28390 | 0.19181 | 20.00 |
| guard_selected_top_k_tools | 0.31169 | 0.20739 | 8.00 |

[Full local results / 完整本地结果](../upgrade_v9/RESULTS.zh.md)

## 时间协议新增审计

全体 1,788,195 条旧目标中，42,005 条 provider 医嘱在入院前已开立，276,269 条开立于原六小时窗口之后。可信时间关联排除 438 条住院编号冲突。药房与 provider 时钟差异尚需追溯源关联，不能挑一个时钟就宣称前瞻有效。[详细结果](../upgrade_v20/RESULTS.zh.md)。
