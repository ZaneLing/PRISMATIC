# v0.18：跨基座的冻结技能迁移

## 研究问题与协议

在 DeepSeek 上学到的技能，直接交给 Gemini 后是否仍有帮助？四种方法共用 Gemini-3.8-Flash、同一 988 题 RxSafeBench 衍生任务、每题一次调用、低 reasoning 和 2,048-token 上限。调用设置在测试前用开发集冻结。技能和 openFDA 说明书快照沿用 v0.10/v0.17，前后核对文件哈希。没有用 Gemini 测试标签改技能或提示。

## 同一基座的方法主表

| Method | Correct / 988 | Accuracy (%) | Invalid | Logical inference USD |
|---|---:|---:|---:|---:|
| CoT | 532 | 53.85 | 4 | 1.9454 |
| Frozen author-GRASP skills | 527 | 53.34 | 5 | 2.6209 |
| Fixed grounded harness | 538 | 54.45 | 5 | 2.5229 |
| Frozen grounded skills | 510 | 51.62 | 24 | 3.9129 |

## Paired contrasts / 配对差异

| Contrast | Difference (pp) | Scenario-cluster 95% interval (pp) | Fixes / regressions |
|---|---:|---:|---:|
| frozen_author_grasp__minus__cot | -0.51 | [-2.23, 1.21] | 34 / 39 |
| fixed_grounded__minus__cot | 0.61 | [-2.13, 3.24] | 99 / 93 |
| frozen_grounded_grasp__minus__cot | -2.23 | [-5.26, 0.81] | 108 / 130 |
| frozen_grounded_grasp__minus__fixed_grounded | -2.83 | [-4.85, -0.81] | 38 / 66 |
| frozen_grounded_grasp__minus__frozen_author_grasp | -1.72 | [-4.86, 1.32] | 112 / 129 |

## 事后失败诊断

证据技能相对固定证据下降2.83个百分点，配对区间[-4.85,-0.81]。24个无效技能输出中23个以长度截断结束；10个原本正确病例变为无效。但在双方输出都有效的961题中，正确数仍从528降到508，不能只归因于截断。这个条件子集用于诊断，不替换主表。平均输入长度从1,666.81增至2,831.81 token。本轮冻结比较未根据测试结果改动。

## 如何解读与核验

本轮验证持久技能的迁移能力；测试时没有修改模型权重、工具代码或技能文本。表内调用数和输出上限相同，输入长度和返回用量不同。费用按成功返回的逻辑请求计算，包含缓存复用，并非已经与供应商账单对账的实付总额；超时或重试可能产生未返回用量的额外收费。DeepSeek 源实验的输出上限不同，因此跨模型原始分数不属于等算力比较。这里只有一条冻结技能学习轨迹，不能替代多种子稳健性实验。

所有预测已逐例对齐并独立重算。收到但格式不合格的答案计错；未完成的网络请求不得填表。配对区间按源场景聚类重采样 4,000 次，属于描述性区间，没有做多重比较校正。保留负迁移和退化。仓库发布代码与汇总；请求未使用受限患者数据。
