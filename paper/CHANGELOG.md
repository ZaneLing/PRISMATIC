# Manuscript change log / 论文变更记录

## v0.8 first-seed results / v0.10 completed / v0.11 started — 2026-10-14

- Eight public method rows, four checkpoints after initialization, object ablations and RxQA transfer complete for seed 42; all selected RxRSI updates are rejected. 完成首种子，保留持平曲线。
- The unmodified GRASP core scores 502/988 versus CoT 467/988; paired scenario-cluster interval for the gain is [0.91, 6.07] points. Our scoped-skills variant has insufficient coverage and remains unchanged. 补强作者实现对照并记录失败原因。
- Fixed Qwen empty reasoning envelope and cache case binding before any local parameter-study test scoring; original strict-parser failure retained. 修复真实工程问题，统一重算。
- Started public drug-label evidence study: 623/699 names matched; all lookups contain drug names only. 继续根据不足推进 v0.11。

## v0.7 complete; v0.8/v0.9 execution started — 2026-10-14

- Target changed to ACL 2027; official ACL style embedded in the existing English editor file; built-in compilation succeeds. 目标与格式同步到 ACL，英文原路径保留。
- Removed saline-presence endpoint from current scoring/tables. 删除当前盐水出现指标，保留旧版本原始证据。
- Completed new-patient 4k comparisons across three seeds, five checkpoints, 12 method/ablation rows, independent recount and patient-cluster bootstrap. 完成真实多方法主表和轮次审计。
- Conditional tool helps; expanded memory is inconsistent; full state trails the strong equal-data ensemble. 如实保留负结果，继续后续改进。
- Started LLM-authored language-artifact evolution on public RxSafeBench/RxQA and actual local QLoRA updates. v0.8/v0.9 未跑完，不提前填写结果。
- User confirms official RxEval/SafeRx test packages are unavailable; runnable experiments continue.

## v0.6-r1/r2 — 2026-10-14

- Redesigned the current system as **RxRSIAgent**, with explicit prescription workflow and GT-supervised policy/memory/template updates. 新增可读流程图与中英文设计文档。
- Removed clinician review and reimplementation of every published baseline as prerequisites. 有 GT 的字段直接自动评价；原论文分数按协议直接引用。
- Executed 40k/4k/4k raw-order experiments including saline records. Drug F1 0.35841 → 0.40668; selected core-order F1 0.28003. 固定药名空间来自初始 8k，测试订单覆盖 85.34%。
- Executed 32k pre-update error-feedback records and 0/0.25/1 replay ablations. Zero extra weighting wins; same-data ordinary training matches the selected policy. 保留负消融，不把数据增长误称为独有机制收益。
- Executed local LLM planners on 20 validation + 20 test cases; validation selects learned-policy output. LLM 参数未更新，技能自动编辑和 SFT 未伪报为完成。
- Added source-reported GAMENet, SafeDrug, SafeRx, RxEval, MedAgentSim, MedAgentBench and GRASP datasets/results. Main Table 2 is reported protocol panels; Table 3 is actual local method comparison.
- Passed 7 contract tests and independent aggregate recomputation, with patient-disjoint checks and 2,000 patient-cluster bootstrap replicates. Updated the existing English paper in place and compiled with the built-in compiler.

## v0.4 execution r1 / order normalization r2 — 2026-10-14

- Executed train-40k-only mapping and route audit: 814,254/1,788,195 orders mapped; IV coverage 19.518%; all 240,310 saline-name proxy rows unmapped. 执行映射与途径审计，保留未知而不补造药物编码。
- Executed dual-timestamp lab audit: excluded 2,127 post-decision stored rows; 33,393 admissions retain eligible numeric labs. Actual method inputs remain the frozen admission proxy. 完成检验时间过滤，未向本轮模型事后添加新字段。
- Ran 4,000-case baselines and three-seed GAMENet text/single-visit adaptation, with a real TWOSIDES class graph and forward-equivalence check. 已跑真实图方法适配，明确区别于忠实复现。
- Ran the same 50 cases through local direct, ordinary repeat, retrieval and bounded harness: F1 .2445/.2445/.2871/.2082. The harness abstains on 50% and does not improve observed F1. 如实保留负结果。
- Executed ten-case complete-order drafts/revisions. Raw schema validity is 4/10 per arm; explicit-unknown ATC normalization raises parseability to 9/10 without claiming correct generation. Original failures retained; seven protocol tests pass. 临床评分仍待提交。
- Updated the current English paper in place, generated [Chinese](../upgrade_v4/RESULTS.zh.md) and [English](../upgrade_v4/RESULTS.en.md) result reports. Remaining method/resource gates are explicit.

## v0.4-dev — 2026-10-14

- 新增完整 [论文补全执行计划](COMPLETION_PLAN.md)，包括方法矩阵、病例增长、消融、双人盲评、全量公开集、真实 FHIR、统计和验收交付。
- 按用户要求仅维护英文论文；当前已打开英文文件原位切换为原 ZIP 的 AAMAS `sigconf,nonacm` 模板。旧 v0.3 可从提交 `289bf4c0` 恢复；旧中文文件仅归档。
- 完成 P01a 原始医嘱可观测性审计：当前测试集 1,296 个空 ATC 标签中 1,144 个无窗口内记录处方，152 个有处方但全部映射失败。补充时间缺失、实际输入字段与训练映射资源的限制，保留旧 F1 数字作为开发结果。
- 完成 P01b 的时间字段及现有队列检查：已纳入既往用药无 charttime 越界、患者跨切分为零；triage 无时间戳、medrecon 无 storetime，使得入库可用性无法完全验证。论文披露这一区别，时间协议及敏感性实验仍待补全。

## v0.3 — 2026-10-14

- 以中英文 LaTeX 重写论文，并用 Codex 内置编译器分别成功编译。
- 处方主表改为以方法为行，固定受限 MIMIC-IV/ED 入院时点队列、患者切分、ATC-L4 编码与每例五类输出。已运行流行度、病例检索和直接 TF-IDF/SGD；GAMENet、SafeDrug、SafeRx-Agent 及完整 harness 据实留空，不借用原论文分数。
- 重建全部 201,750 次符合急诊入院时间条件的队列，保留零后续口服药病例，消除旧版按未来医嘱筛人的条件。新增公开 NDC 映射与训练患者内 GSN/药名回退覆盖率审计；目前仅 45.652% 的六小时医嘱映射到 ATC-L4。
- 新增 RxSafeBench 去重全量 2,000 题、RxQA OpenFDA 全量 300 题的公开次级直接作答；并登记 RxSafeBench 全量轻量 harness 同题复核。
- 新增共同测试患者 200 例的本地受限临床盲评抽样清单，以及中英文双人评分规程。实际盲评和完整剂量医嘱尚未完成。

## v0.2 — 2026-10-14

- 增加论文式中英文稿、统一表号和明确的主表入口。
- 在 RxSafeBench 固定 60 题上新增同模型、同题、共用首次回答的普通二次复核与证据约束 harness 对照。
- 主表显示 harness 相对直接回答的正确题数变化为 GPT 0、Gemini −5、DeepSeek +3；三个配对区间均包含 0，暂无稳定提升证据。
- 将最新研究的任务与数据集列成复现矩阵，区分已经同题测试、不同任务和尚待复现。

## v0.1 — 2026-10-14

- 归档第一轮中英文研究报告：受限 MIMIC 病例增长、公开 RxSafeBench/RxQA 直接模型测试和后续计划。只调整归档副本的相对链接以适配新目录，正文与数值不变。
- 此版本没有完成 harness 对照主表；旧报告保留供追溯。

## v0.5-r1 — 2026-10-14

Delivered [v0.5 executed results](../upgrade_v5/RESULTS.en.md) and the [architecture diagram](../upgrade_v5/ARCHITECTURE.md).

- **E01 engineering repair:** trace all 50 cases; all 25 empty arrays are valid and 20 erase nonempty proposals. Separate historical predictions from clinical unknowns; preserve valid code members and recover invalid revisions.
- **E01 measurements:** free review F1=0.31130, empty rate=0%, versus v4 0.20820 / 50%. Validation-gated harness F1=0.41015; not a clinically complete order result.
- **E02/E03 conditional memory:** freeze an 8,000-case base, replay 250/1,000/4,000/16,000/32,000 episodes with 30 neighbors and validation-selected updates. Base/final F1=0.34727/0.35281, non-monotonic. Vocabulary/mapping fixed from the common 40k training cohort; not end-to-end low-data learning.
- **Strong baseline and negative ablations:** static ensemble three-seed mean 0.39176; 10% memory fusion 0.39022 is worse than seed-42 static 0.39185. Validation also rejects LLM candidate edits. All failures are retained.
- **Verification:** eight contract tests; independent recalculation of LLM and 4k aggregates; embedded class unchanged; active English source updated in place and checked with the built-in compiler.
- **Outstanding:** clinician-rated experience, supportive/fluid full orders, ingredient-level knowledge, compatible SafeDrug/SafeRx implementations, independent patient confirmation and live FHIR. No claim of surpassing these original methods.

已执行并交付 [v0.5 真实实验结果](../upgrade_v5/RESULTS.zh.md) 与[结构图](../upgrade_v5/ARCHITECTURE.md)。

- **E01 修复完成（工程层）：**逐例追踪 50 例；25 次空输出均为合法数组，20 次删光已有检索候选；缺失临床证据与历史预测状态已分离，解析器增加合法项保留和失败恢复。
- **E01 实测：**自由复核 F1=0.31130，空输出率=0%；旧版 0.20820 / 50%。验证门控 harness F1=0.41015；这行不能替代临床完整订单结果。
- **E02/E03 条件记忆实验完成：**冻结 8,000 例基础模型，经验 250/1,000/4,000/16,000/32,000，固定 30 邻居和验证选择。基础 F1 0.34727，最终 0.35281；曲线非单调。词表/映射预先固定自 40,000 训练例，不是端到端低数据实验。
- **强基线与负消融：**词/字符静态排序三种子均值 0.39176；10% 记忆融合 0.39022 低于 seed-42 静态 0.39185。50 例验证表明 LLM 改写较差，门控保留排序候选。保留所有负结果。
- **工程验证：**8 项契约测试；病例级轨迹与 4,000 例聚合重算；旧版模板内容保持；英文源原位更新并使用内置编译器检查。
- **仍未完成：**医生评审经验、辅助药/盐水完整订单学习、成分级临床知识、SafeDrug/SafeRx 兼容复现、新患者确认及真实 FHIR。没有宣称超过这些原始方法。
