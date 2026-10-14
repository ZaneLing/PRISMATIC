# v0.27 — 标准处方方法兼容性审计

## 1. 已构建的真实队列

独立历史就诊任务：MIMIC-IV 3.1成人、住院含ICU、诊断/操作/已映射药物各至少一项，每人至少两次合格就诊。输入整次就诊的诊断/操作及既往就诊，不能称为入院时点或六小时新订单预测。

| Panel | Method | Patient-average F1 | Patient-average Jaccard | Mean medications |
|---|---|---:|---:|---:|
| full | prevalence | 0.45794 | 0.30680 | 11.00 |
| full | last_visit | 0.30154 | 0.21585 | 7.26 |
| full | cosine_knn | 0.55081 | 0.39614 | 13.10 |
| full | structured_logistic | 0.61151 | 0.45742 | 12.48 |
| molecular | prevalence | 0.42555 | 0.28089 | 15.00 |
| molecular | last_visit | 0.28971 | 0.20613 | 5.81 |
| molecular | cosine_knn | 0.51751 | 0.36710 | 10.43 |
| molecular | structured_logistic | 0.58113 | 0.42971 | 9.86 |

仅训练集建立词表：10,726个诊断、5,330个操作、271个真正五字符ATC-L4类。测试集词表外标签继续计入召回分母。跨划分患者交集为零。旧公开NDC表仅覆盖所选2,734,635条处方行的 **27.23%**；标签是已映射子集，不是完整处方ground truth。

## 2. 独立核对已通过

从原始文件逐项重建23,177次就诊的诊断、操作、药物集合，检查成人ICU资格、就诊排序、患者划分及训练词表。完整母队列筛选流程来自构建器，没有在本审计中独立再扫描。测试患者与此前v0.9/v0.21已观察测试的交集分别为20/50人，本表将标为探索性实验。

## 3. 分子资源与代码已实际运行

**746/746**个公开CID均取得结构并通过RDKit验证，覆盖399个ATC-L4类；对应本队列训练类的 **219/271**，覆盖测试24,391/30,004个标签。52个未覆盖类别全部列明，没有补造分子。

ARMR-2025、GAMENet、SafeDrug固定作者核心均已通过合成输入的前向/反向执行探针；GAMENet对隐藏的当前药物标签变化不敏感。SafeDrug探针采用真实公开分子和明确标注的合成单位子结构矩阵，仅验证依赖与执行，不是训练结果。后续已构建正式资源：627个真实分子图、863个BRICS片段、326种指纹，投影无缺失行；合成探针矩阵不会用于训练。

## 4. 已登记并启动真实方法训练

完整271类与共同分子219类两表保留相同患者/就诊；分子表明确排除5,613个测试标签，保留3次空目标就诊，不能和完整表混算。每种神经架构训练50整轮，种子42/137/2026；ARMR与GAMENet跑两种空间，SafeDrug跑分子空间。proposal按患者平均Jaccard选择轮次/阈值，guard只报告；相同病例曝光不等于相同步数/FLOPs。全部基线和之后登记的RxRSI状态冻结前，不推断测试集。

SafeDrug稀疏图、固定分子嵌入的检查点保存，以及ARMR的CPU/GPU执行都通过数值/梯度/恢复探针。当前公开SafeDrug脚本的`min`与论文式19的`max`冲突，本独立适配复现采用论文公式并披露差异。[原论文](https://arxiv.org/pdf/2105.02711)。不冒充原文精确复现成绩。

| Panel | Method | Seed | Finished epochs / 50 | Status |
|---|---|---:|---:|---|
| full | ARMR | 42 | 13 | training |
| full | GAMENet | 42 | 10 | training |
| molecular | SafeDrug | 42 | 10 | training |

Queued seeds/panels are not counted as completed. Snapshot of saved epoch receipts; no provisional neural test score.

## 5. 已完成的传统方法比较：仅开发guard

以下是真实拟合后的方法比较：1,231次开发就诊／467人。四种方法均由另一proposal集选定；从原就诊源独立重建特征、保存预测、集合指标，核查通过。这还不是最终测试主表。

| Panel | Method | Patient-average F1 | Patient-average Jaccard | Mean medications |
|---|---|---:|---:|---:|
| full | prevalence | 0.45794 | 0.30680 | 11.00 |
| full | last_visit | 0.30154 | 0.21585 | 7.26 |
| full | cosine_knn | 0.55081 | 0.39614 | 13.10 |
| full | structured_logistic | 0.61151 | 0.45742 | 12.48 |
| molecular | prevalence | 0.42555 | 0.28089 | 15.00 |
| molecular | last_visit | 0.28971 | 0.20613 | 5.81 |
| molecular | cosine_knn | 0.51751 | 0.36710 | 10.43 |
| molecular | structured_logistic | 0.58113 | 0.42971 | 9.86 |

## Artifacts / 交付文件

- [Registered protocol](protocol.json) and [training addendum](training_addendum.json)
- [Implementation details](implementation_notes.json)
- [Cohort manifest](results/cohort_manifest.json)
- [Independent audit and missing classes](results/cohort_audit.json)
- [Public molecule receipts](results/molecular_resource_audit.json)
- [Actual molecular/graph resources](results/model_resource_manifest.json)
- [Author-core execution probe](results/author_core_probe.json) and [training runtime equivalence](results/training_runtime_probe.json)
- [Independent control audit](results/control_audit.json)
- [Recent-method source audit](../paper/LATEST_METHODS.zh.md)

Restricted cases, fitted artifacts and patient-level outputs remain local. Public reports contain aggregates and hashes.
