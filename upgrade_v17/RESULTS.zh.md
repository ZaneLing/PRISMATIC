# v0.17：说明书证据与技能进化的完整组件对照

## 设计与主结果

使用未改源码的 GRASP 作者核心（`9d7d125a`）学习技能文件，底层证据工具固定为 openFDA 连续片段。证据/无证据、技能/无技能共用同一答案提示、DeepSeek-V4.1-Flash 和一次 512-token 调用。625 个训练病例分四批；作者核心用训练集平衡探针筛选，并在每个 epoch 结束后用 387 个验证病例选择状态。模型权重、检索代码与说明书快照不变。这是引用已有优化器的处方 harness 集成，不宣称新优化器。

### 同一 988 题 RxSafeBench 衍生任务

| Method | Correct | Accuracy (%) | Calls / case |
|---|---:|---:|---:|
| CoT | 467/988 | 47.27 | 1 |
| Author GRASP core | 502/988 | 50.81 | 1 |
| Fixed grounded harness | 499/988 | 50.51 | 1 |
| Grounded skill evolution | 501/988 | 50.71 | 1 |

### 单独的 300 题 RxQA 迁移

| Method | Correct | Accuracy (%) | Calls / case |
|---|---:|---:|---:|
| CoT | 193/300 | 64.33 | 1 |
| Author GRASP core | 189/300 | 63.00 | 1 |
| Fixed grounded harness | 188/300 | 62.67 | 1 |
| Grounded skill evolution | 183/300 | 61.00 | 1 |

组合后仅比固定证据多答对 2 题，比无证据作者 GRASP 少答对 1 题；迁移比固定证据少答对 5 题。验证集 49.1%→53.2% 不足以证明测试/迁移收益。另报告四格组件交互量，检查组合增益是否超过两个单独增益之和；负结果完整保留。

## 究竟进化了什么，哪一轮改变？

第 1 轮不接受技能；第 2 轮新增 `label_indication_and_caution_parsing`，第 3/4 轮修改它。`artifacts/` 公开每个版本的实际文本，`results/round_artifacts.json` 保存哈希。这些是模型生成的决策指引，不是临床权威资料。测试/迁移标签不参与状态选择；中间版本评价用于已观察开发基准上的过程分析。

| Dataset | Round | Seen cases | Correct | Fixes / regressions |
|---|---:|---:|---:|---:|
| rxsafebench | 0 | 0 | 499/988 | 0 / 0 |
| rxsafebench | 1 | 157 | 499/988 | 0 / 0 |
| rxsafebench | 2 | 314 | 475/988 | 70 / 94 |
| rxsafebench | 3 | 471 | 493/988 | 74 / 56 |
| rxsafebench | 4 | 625 | 501/988 | 76 / 68 |
| rxqa | 0 | 0 | 188/300 | 0 / 0 |
| rxqa | 1 | 157 | 188/300 | 0 / 0 |
| rxqa | 2 | 314 | 175/300 | 19 / 32 |
| rxqa | 3 | 471 | 175/300 | 17 / 17 |
| rxqa | 4 | 625 | 183/300 | 22 / 14 |


已独立核对全部最终预测、病例对应和分数，配对场景/题目区间及修复退化见 `results/summary.json`。推理成本记录逻辑使用量（包括缓存），实际扣费另记本地共享账本。未使用受限患者数据。

![Frozen skill trajectories](round_curves.png)
