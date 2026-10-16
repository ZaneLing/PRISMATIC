# Protocol correction / 协议纠错

16 October2026.

**RxSafeBench's original paper already defines a three-option multiple-choice task** (SectionII-C). Earlier local reports incorrectly called the source protocol free generation. See the [original paper](https://arxiv.org/html/2511.04328v1).

Our local deduplication, option ordering, scenario-group split, prompts and evaluation subset still differ from the source protocol. Published paper scores therefore do not become same-protocol main-table results. This correction changes the task description, not saved predictions, labels or scores. Legacy hash-bound audit fields mentioning a generation protocol remain historical; this note supersedes that wording.

**RxSafeBench原论文已经是三选一MCQ，不是自由生成。** 此前文字描述有误。本地去重、选项顺序、场景分组切分、提示词和评测子集仍与原协议不同，因此不能直接复制原论文分数到同协议主表。此次纠正描述，不改变保存的预测、标签或分数；旧哈希绑定档案保留，并由本纠错说明覆盖其错误表述。

Current evidence: [English](CURRENT_RESULTS.en.md) / [中文](CURRENT_RESULTS.zh.md).
