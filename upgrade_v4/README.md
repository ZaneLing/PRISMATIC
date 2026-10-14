# P00/P01a 与 P01b 时间审计交付

> **最新批次：真实方法比较已完成一轮。** 请先看 [中文结果](RESULTS.zh.md) / [English results](RESULTS.en.md) 和 [执行协议](PROTOCOL.md) / [English protocol](PROTOCOL.en.md)。下文保留此前 P00/P01a 的初始交付记录。英文论文表 2 已加入 GAMENet 独立适配和同 50 例 bounded harness 比较；完整临床 harness、SafeDrug/SafeRx 与临床评审仍未完成。

对应 [完整执行计划](../paper/COMPLETION_PLAN.md)，2026-10-14。

P00 已把当前打开的英文稿原位切换为用户 ZIP 内的 AAMAS 英文双栏模板。原 class 没有修改；嵌入 LaTeX 的 `filecontents` 是为了满足编辑器单文件编译。模板与 ZIP 的哈希在 [来源记录](../paper/latex/v0.3/template_provenance.json)。仅维护英文稿，旧中文版本保留供追溯。

P01a 的 [审计脚本](audit_label_observability.py) 扫描原始 MIMIC-IV 处方，按相同六小时窗口复核空 ATC 标签。受限逐例派生文件只写入本地 `restricted/prismatic-v4`，此处只发布 [汇总 JSON](results/label_observability_audit.json)。

| 标签可观测性 | 全队列入院数 | 当前 4,000 测试病例 |
| --- | ---: | ---: |
| 六小时内无记录的原始处方 | 58,982 | 1,144 |
| 有原始处方但没有映射 ATC 类别 | 8,004 | 152 |
| 至少一个映射 ATC 类别 | 134,764 | 2,704 |
| 总计 | 201,750 | 4,000 |

全队列另有 497 次入院关联无法解析 starttime 的处方行，共 2,364 行；这些行是否属于六小时窗口未知。当前测试样本中有 11 次入院存在这类记录。至少有一个映射类别的病例也可能有部分药物未映射。

**对论文的影响：**原来的“空 ATC 集合”不能直接作为“无须用药”的临床金标准。旧 F1 数字暂不改变，仍作为旧协议开发结果；下一步 P01b/P02 确定缺失标签处理、输入可用时间和药物映射后，才运行新版主表。

正文还修正两项资源说明：当前已完成预测器实际只使用 chiefcomplaint、acuity、home_meds；训练内药名/GSN 回退映射用到了完整训练患者池，超出了模型抽取的 40,000 次入院，因此病例增长实验必须控制这项资源。

复跑（在授权本地环境）：

```bash
python upgrade_v4/audit_label_observability.py
```

run_id: `P01a-label-observability-v1`。输入 cohort SHA-256 与各切分计数见 JSON。脚本验证入院唯一性、无原始医嘱却有映射标签的矛盾，并沿用 v0.3 完全相同的哈希抽样，以保证 4,000 测试病例一致。

## P01b：时间信息能验证到哪一步

[时间审计脚本](audit_input_timing.py)读取原始表头及当前队列，产出[汇总报告](results/input_timing_audit.json)。全部 201,750 次入院中，决策时间缺失、已纳入 home-med 的 charttime 超过决策时刻、重复入院、跨切分患者均为 0。

但 triage 无逐行时间戳；medrecon 与 vitalsign 只有 charttime，没有 storetime。因此主诉/acuity 的入院时可用性尚属假设，既往用药的入库时间也不可验证。labevents 有 charttime 和 storetime，但尚未进入当前模型，下一版接入时须同时约束。prescriptions 的 starttime/stoptime 不等于下单时间。

这些结果已写入英文稿。仍需完成分层映射审计、输入政策及排除不可验证字段的敏感性实验、完整订单 schema 与确认集冻结；本报告没有宣布 P01b/P02 全部完成。

```bash
python upgrade_v4/audit_input_timing.py
```

## English delivery summary

The active English manuscript now uses the supplied ZIP's unmodified AAMAS class and has compiled with the desktop editor. See the [English completion plan](../paper/COMPLETION_PLAN.en.md) and [compilation record](../paper/latex/v0.3/compile_check.json).

The raw-order audit separates two previously conflated empty-label conditions. Across all 201,750 admissions, 58,982 have no recorded six-hour order, 8,004 have orders but no mapped ATC class, and 134,764 have at least one mapped class. The identical 4,000-case pilot contains 1,144, 152 and 2,704 admissions respectively. At least one mapped class does not imply complete mapping. Unparseable starttimes affect 497 admissions and 2,364 prescription rows, whose window membership is unknown.

The timing audit reports zero missing decision times, included home-medication charttime violations, duplicate admissions and cross-split patients. However, triage has no per-row timestamp and medrecon has no storetime. Admission-time availability is therefore not fully verified. Laboratory records have both charttime and storetime but have not entered the current predictors. The paper now distinguishes these limits from checked constraints.

No new method superiority or clinical safety result is claimed. Previous F1 values remain developmental evidence. P01b/P02 still require mapping strata, input and unknown-label policies, complete-order schema, sensitivity experiments and a locked confirmatory split before the formal method table is expanded. Restricted per-case derivatives stay local; only aggregates are published.
