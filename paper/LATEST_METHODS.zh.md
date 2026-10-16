# 最新方法：原文、数据协议与代码核对

更新于 **2026年10月15日**。本页补充[持续结果总表](CURRENT_RESULTS.zh.md)。`(R)` 表示原作者报告；本地实验另列，跨协议分数不排名。

## 1. 应加入论文的近期工作

| 方法 / 论文 | 数据与预测任务 | 原文结果 (R) | 在我们论文中的作用 |
|---|---|---|---|
| [ARMR，IJCAI 2025](https://www.ijcai.org/proceedings/2025/0871.pdf)，表2–3 | MIMIC-III：6,350患者 / 15,032次就诊；MIMIC-IV：9,036 / 20,616；131个ATC-L3类；当前诊断、操作与历史就诊 | 患者平均F1分别为0.6959 / 0.6712 | 近期结构化处方基线；分段历史编码、新旧药物注意力及组件消融。[作者代码](https://github.com/seucoin/armr2)。 |
| [HADRec，2026年10月预印本](https://arxiv.org/html/2610.00984v1)，表4、8 | MIMIC-III / IV；药物层级和分子特征；具体编码层级存在下述代码问题 | III的F1为0.7010；IV为0.6408；III→IV迁移为0.5901 | 可以直接引用原分数；同协议运行前须澄清药物空间。迁移不等于准确率全面提升。 |
| [LT3，CL4Health 2025](https://aclanthology.org/2025.cl4health-1.17/)，表2 | n2c2-2018 / MIMIC-III；输入已有药物属性，生成处方文本 | BLEU 78.52；ROUGE-L 77.55 | 可比较文字表达能力，不能当患者到药物选择基线。其96–98%为下游实体识别F1。官方训练集按9:1分训练/验证，保留官方测试集。 |

## 2. 已实际核对的代码问题

- **ARMR身份：**2025年作者仓库固定为 `750480158e94ed5be37011e05fe1212d9ba60705`，包含分段/Mamba历史编码及新旧药物模块，使用普通PyTorch即可执行该实现，不依赖仅CUDA可用的Mamba包。未检出作者上传的患者记录。
- **DREAM标注不一致：**固定版本 `a9851583a4b90904e7aa697f6bd6cddb89b03d33` 的[README](https://github.com/novzyg/DREAM)把ARMR链接到2021年对抗模型，但实现含类似2025年方法的分段/Mamba组件。因此不能仅凭表中同名行确认版本或直接沿用其排行；本地运行优先使用2025年作者代码。
- **HADRec层级不一致：**固定版本 `93d8e171bb028a54a7a81a384e80d1b8f58ed0d3` 的 `construction.py:107`、`data_process.py:117` 截断为四字符；后者176–177行对第3、4层使用相同前缀，其他编码器却期望五字符子类。[代码证据](https://github.com/wjk78623-cell/HADRec/blob/93d8e171bb028a54a7a81a384e80d1b8f58ed0d3/data_process.py)。标准ATC-L3为四字符，L4为五字符，如A10B与A10BA。[WHO合作中心](https://atcddd.fhi.no/atc/structure_and_principles/)。这说明公开实现需要澄清，不能据此反推论文全部分数实际用了哪套未公开产物。

## 3. 正在落实的跨方法主表

[v0.27数据协议](../upgrade_v27/protocol.json)定义独立的历史就诊药物集合任务：本地授权 MIMIC-IV 3.1、患者互斥划分、真正五字符 ATC-L4、仅训练集拟合词表。后续[训练附录](../upgrade_v27/training_addendum.json)正式登记 ARMR-2025、GAMENet、SafeDrug 作者核心、四种传统方法及另行定义的 RxRSI 机制。RETAIN 仍是数据阶段的候选，尚未执行，不出现在实测表中。输入使用整次就诊诊断／操作，与六小时可用时间受控任务分别报告。

公开分子资源已完成：**746/746 个 CID 全部返回并通过 RDKit 验证，覆盖 399 个 ATC-L4 类**。[公开资源审计](../upgrade_v27/results/molecular_resource_audit.json)保留原始哈希。队列专用资源也已补齐：覆盖 **219/271** 个训练药类，包含 **627** 个分子图、**863** 个 BRICS 片段。完整与分子空间分别比较，并明确排除标签和保留的空目标病例。SafeDrug 三个已登记种子均已完成 50 轮并通过检查点／预测独立核验；完整空间 ARMR 和 GAMENet 各三个种子均已完成，分子空间 GAMENet 三个种子也均已核验。其他已登记作者运行继续。[实际执行和成绩](../upgrade_v27/RESULTS.zh.md)。

[跨方法开发集复算](../upgrade_v27/DEVELOPMENT_METHODS.zh.md)使用相同 1,231 次就诊／467 人，按共同完成的种子做配对。[计算账本](COMPUTE_ACCOUNTING.zh.md)列出实际拟合、病例曝光与提议预算。[最终共同测试扩展](../upgrade_v30/COMMON_TEST.zh.md)等待已登记方法及核验全部完成。HADRec 继续保留原作者报告结果，其层级和完整执行协议仍需明确的兼容适配。缺失分数不填零，已复用开发／测试人群均明确标注。

## 2026-10-16 update

[Expanded comparator families, verified code availability, task compatibility and mechanism hypotheses](RESEARCH_ASSESSMENT.zh.md#4-审稿人应看到哪些外部方法). FLAME, SafeRx-Agent, RareAgents and SkeMex are priority additions; no new local method scores are claimed.
