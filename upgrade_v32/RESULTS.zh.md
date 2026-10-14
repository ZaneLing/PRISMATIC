# v0.32：二元处方决策受控修复——执行与结果

## 1. 本实验回答什么

v31 首次更新生成了格式合法、内容全零的处方。本试验用相同 400 例、每组 100 步，交叉检验训练前缀和类别不平衡。四个新适配器、基础模型和原失败适配器均采用不含标签的全零前缀评分；另保留原检索前 8 个和全部 20 个候选的直接对照。

固定 0.5 阈值反映未经校准的决策表现。另一组结果在 100 例 proposal 上选择一个全局阈值，两种候选排序共享该值；六个模型状态接受相同校准。单纯调阈值的收益与更新权重的收益分别报告。

## 2. 真实完成情况

- 已完成训练: **1/4**
- 已独立复算成绩分组: **暂无**
- API 请求: **0**

| Arm | Steps | Fit seconds | Adapter SHA-256 (prefix) |
|---|---:|---:|---|
| teacher_uniform | 100 | 1739.2 | 03e345d3b72d |
| zero_uniform | pending | — | — |
| teacher_balanced | pending | — | — |
| zero_balanced | pending | — | — |

训练完成状态与原始适配器哈希逐项核对。独立核验重建全部 8,000 个二元标签，并在四组训练回执均通过后开放 proposal 评分。评分预检已通过 120 个合成病例／概率绑定、完整阈值选择、源数据复算及逐字节一致的断点恢复；这些合成检查不属于临床实验成绩。

## 3. proposal

尚无通过独立复算的成绩。当前前置条件：all_four_training_audits.

## 4. guard

尚无通过独立复算的成绩。当前前置条件：all_four_training_audits, frozen_thresholds, proposal_summary, proposal_audit, v31_seed42_frozen_selection.

## 5. 结论边界

本版是单种子、单轮的监督修复，不能单独证明递归自进化。候选检索工具与剂量模板保持固定。四组训练状态和普通校准阈值冻结后，guard 仍须等待原 v31 seed42 全部选择冻结；guard 成绩不能用于挑选优胜修复。后续仍需多轮自身错误、打乱错误和普通训练对照。

[Protocol](protocol.json) · [Evaluation addendum](evaluation_addendum.json) · [Execution progress](results/progress.json) · [Synthetic scoring preflight](results/evaluation_probe.json) · [Earlier collapse diagnosis](../upgrade_v31/COLLAPSE.zh.md)
