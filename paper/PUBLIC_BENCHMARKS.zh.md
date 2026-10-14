# 公开基准覆盖范围与实际评价口径

## RxQA：公开OpenFDA部分全部300题

官方公开的是 **300道OpenFDA题目**，迁移实验覆盖全部300题，没有从这份公开文件中抽样。BNF来源题目因许可限制未公开，本项目没有评测这部分。[官方发布与范围说明](https://github.com/Google-Health/rxqa)。

本次独立核验检查固定CSV哈希、300个唯一题号、完整迁移成员、原选项顺序及每道题标签；并逐题复算v17四种匹配方法的保存预测：

| Method | Correct / all public questions | Accuracy |
|---|---:|---:|
| cot | 193/300 | 64.33% |
| author_grasp | 189/300 | 63.00% |
| fixed_grounded | 188/300 | 62.67% |
| evolving_grounded | 183/300 | 61.00% |

这里是对已有结果的独立复算，不是新跑出的提升；技能进化在这组迁移对照中没有获益。历史v3直接提示为186/300，属于不同提示／预算的快照，不能替换本表匹配的CoT对照。

## RxSafeBench：原始发布、去重与进化划分

固定的两个源文件共 **2,443条记录**，与官方说明一致；按任务类型、完全相同对话及正确药物去重后，得到 **2,000道三选一衍生题**。历史直接回答／重新考虑／轻量复核覆盖全部2,000题。该任务转换与原论文的药物生成评价不同，不能同官方排行榜数值直接排名。[官方基准](https://github.com/CAS-SIAT-XinHai/RxSafeBench)。

| Historical fixed method | Correct / unique cases | Accuracy | Fixes / regressions vs direct |
|---|---:|---:|---:|
| direct | 924/2000 | 46.20% | reference |
| repeat | 878/2000 | 43.90% | 72 / 118 |
| harness | 952/2000 | 47.60% | 338 / 310 |

后续进化实验将同一2,000题划为625训练、190 proposal、197 guard、988测试，题目及场景组不跨划分。进化方法统一比较 **同一988道测试题**；不能把参与进化的数据也算作未见测试。因此，历史全量表与后续冻结测试表分别报告。

## 元数据修正与核验局限

历史v3完整harness报告的样本说明误沿用了“30+30”，但源身份与保存预测逐项核验均证实 **每方法2,000题**。原始报告保留，本说明与核验记录修正其文字；英文论文也改为明确称RxQA公开OpenFDA部分全量。分数和原始预测没有变化。

本核验确认覆盖范围、转换和保存答案计数，不证明临床安全、与官方原任务等价，或新方法取得提升。

[Coverage audit and hashes](public_benchmark_coverage.json) · [Current public method comparison](../upgrade_v17/RESULTS.en.md)
