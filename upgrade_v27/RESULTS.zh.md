# v0.27 — 标准处方方法兼容性审计

## 1. 已构建的真实队列

独立历史就诊任务：MIMIC-IV 3.1成人、住院含ICU、诊断/操作/已映射药物各至少一项，每人至少两次合格就诊。输入整次就诊的诊断/操作及既往就诊，不能称为入院时点或六小时新订单预测。

| Split | Patients | Visits | Medication targets | Targets outside train vocabulary |
|---|---:|---:|---:|---:|
| train | 7,115 | 18,429 | 227,151 | 0 |
| proposal | 433 | 1,095 | 13,300 | 3 |
| guard | 467 | 1,231 | 14,878 | 3 |
| test | 890 | 2,422 | 30,004 | 5 |

仅训练集建立词表：10,726个诊断、5,330个操作、271个真正五字符ATC-L4类。测试集词表外标签继续计入召回分母。跨划分患者交集为零。旧公开NDC表仅覆盖所选2,734,635条处方行的 **27.23%**；标签是已映射子集，不是完整处方ground truth。

## 2. 独立核对已通过

从原始文件逐项重建23,177次就诊的诊断、操作、药物集合，检查成人ICU资格、就诊排序、患者划分及训练词表。完整母队列筛选流程来自构建器，没有在本审计中独立再扫描。测试患者与此前v0.9/v0.21已观察测试的交集分别为20/50人，本表将标为探索性实验。

## 3. 分子资源与代码已实际运行

**746/746**个公开CID均取得结构并通过RDKit验证，覆盖399个ATC-L4类；对应本队列训练类的 **219/271**，覆盖测试24,391/30,004个标签。52个未覆盖类别全部列明，没有补造分子。

ARMR-2025、GAMENet、SafeDrug固定作者核心均已通过合成输入的前向/反向执行探针；GAMENet对隐藏的当前药物标签变化不敏感。SafeDrug探针采用真实公开分子和明确标注的合成单位子结构矩阵，仅验证依赖与执行，不是训练结果。正式实验仍需BRICS、相互作用图及相同覆盖药物空间。

## 4. 下一执行关口

解决分子覆盖后登记训练附录：完整ATC-L4非分子方法表与独立披露的共同分子空间表；运行真正作者核心、传统对照和RxRSI处方工具。开发集选版本，冻结后统一计算患者平均及micro指标、覆盖率、处方数量和患者聚类区间。v0.27当前尚无已训练或已评分的方法。

## Artifacts / 交付文件

- [Registered protocol](protocol.json)
- [Cohort manifest](results/cohort_manifest.json)
- [Independent audit and missing classes](results/cohort_audit.json)
- [Public molecule receipts](results/molecular_resource_audit.json)
- [Author-core execution probe](results/author_core_probe.json)
- [Recent-method source audit](../paper/LATEST_METHODS.zh.md)

Restricted cases, fitted artifacts and patient-level outputs remain local. Public reports contain aggregates and hashes.
