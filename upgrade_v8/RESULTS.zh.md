# RxRSIAgent v0.8：真实语言技能进化实验

已完整完成的训练顺序种子：42。未完成种子不计入汇总。固定 DeepSeek-V4.1-Flash，所有方法共用 625 训练 / 190 候选选择 / 197 退化检查 / 988 测试。这里是 RxSafeBench 衍生选药题，不能与原论文自由生成分数混排。

## 同数据方法主表

| Method | Accuracy (%) | Seed SD (pp) | Invalid outputs |
|---|---:|---:|---:|
| Direct | 46.15 | — | 1 |
| CoT | 47.27 | — | 0 |
| Self-Refine | 47.57 | — | 0 |
| Case RAG | 49.09 | — | 0 |
| Reflexion adaptation | 47.27 | — | 0 |
| GRASP adaptation | 47.27 | — | 0 |
| EvoTool adaptation | 47.27 | — | 0 |
| RxRSI | 47.27 | — | 0 |

Reflexion、GRASP、EvoTool 为独立任务适配，未称官方复现。每轮都有四个候选评价名额，提议 token 成本可能不同。无效输出计错；跨种子标准差衡量训练顺序敏感性。

## 每一轮到底变了什么

![固定测试集逐轮曲线](round_curves.png)

| Round | Accepted | Changed artifacts | Guard fixes / regressions | Test accuracy (%) |
|---|---|---|---:|---:|
| 0 | True | none | 0 / 0 | 47.27 |
| 1 | False | none | 12 / 19 | 47.27 |
| 2 | False | none | 11 / 16 | 47.27 |
| 3 | False | none | 12 / 18 | 47.27 |
| 4 | False | none | 13 / 14 | 47.27 |

上表为第一个完整种子。版本文件保存完整修改文本及被拒绝候选；拒绝后继续使用原状态。模型权重与工具源代码固定，关注词只修改证据工具配置。

## 对象消融

| Variant | Accuracy (%) |
|---|---:|
| without_memory | 47.27 |
| without_skills | 47.27 |
| without_tool_update | 47.27 |

## RxQA 迁移：公开 OpenFDA 全量 300 题

CoT：193/300（64.33%）；RxRSI：193/300（64.33%）。修复/退化：0/0。RxQA 答案没有用于修改技能。

## 核验与解释边界

预测已独立重算、核对逐例对齐及版本哈希。场景组聚类的配对区间见 `results/summary.json`；区间为描述性结果，未作多重比较修正。方法成本统计逻辑推理用量，实际账本另记包含演化的真实请求。反复使用的退化检查集属于开发资源。上升、持平、退化均原样保留，不把选择题收益解释成完整临床处方能力。
