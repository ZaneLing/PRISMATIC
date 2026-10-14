# PRISMATIC v4 实验交付：真实结果

2026-10-14，执行批次 r1；订单解析修正 r2。[English report](RESULTS.en.md)。本报告从汇总 JSON 生成。所有测试均为开发结果，未完成临床验证。

## 1. 本轮做成了什么

已执行：40k 内回退药物映射、分途径覆盖审计、双时间戳检验过滤、4,000 例基线与输入消融、三种子 GAMENet 入院文本适配、同 50 例四种本地 LLM 方法、10 例完整订单草案与修订、7 项订单协议测试。GAMENet 使用真实作者来源 DDI 图；不是全零占位。

## 2. 主要方法表：同 4,000 例

MIMIC-IV 3.1 + ED 2.2；训练/验证/测试 40,000/4,000/4,000；患者不交叉；同一 admission-proxy 输入、80 类药物空间、每例 5 个预测。均为历史可观察标签重合；不同模型训练计算量未严格配平。

| Method / 方法 | N | Precision@5 | Recall@5 | F1@5 | Seed SD |
| --- | ---: | ---: | ---: | ---: | ---: |
| Training prevalence | 4,000 | 0.2432 | 0.3408 | 0.2839 | — |
| Case retrieval (30 neighbors) | 4,000 | 0.2812 | 0.3940 | 0.3281 | — |
| TF-IDF/SGD (3 seeds) | 4,000 | 0.3310 | 0.4639 | 0.3864 | 0.0007 |
| GAMENet text/single-visit adaptation (3 seeds) | 4,000 | 0.2944 | 0.4125 | 0.3436 | 0.0022 |

GAMENet 保留作者图网络与读出，两个输入通道换为主诉/acuity 与既往用药 token，只有单次就诊，没有原始纵向历史读取。三种子均仅 5 epoch，验证分数到预算末尾仍在上升，不能据此断言原始 GAMENet 劣于 SGD。批处理前向与原代码单例前向误差均小于 1e-5。

SafeDrug、SafeRx-Agent 与临床完整 harness 的正式大样本分数仍未获得；不是零分。本轮已运行的 harness 见下一张同病例表。

## 3. 同 50 例：包含本地 harness 的跨方法比较

所有行使用相同的 50 位测试患者、相同目标和至多 5 类预算。前三行及 GAMENet 固定输出 5 类；LLM 可弃权。四个 LLM 方法的底座均为固定 revision 的 Qwen3-4B-Instruct-2507-4bit。本表不能与上一张的 4,000 例数字直接横向混排。

| Method / 方法 | N | Observed F1 | Mean classes | Calls | Valid output |
| --- | ---: | ---: | ---: | ---: | ---: |
| Prevalence | 50 | 0.3763 | 5.00 | — | — |
| 30-neighbor voting | 50 | 0.3721 | 5.00 | — | — |
| SGD seed 42 | 50 | 0.4271 | 5.00 | — | — |
| GAMENet adaptation seed 42 | 50 | 0.4144 | 5.00 | — | — |
| Local LLM direct | 50 | 0.2445 | 4.70 | 1 | 94% |
| Ordinary repeat | 50 | 0.2445 | 4.70 | 2 | 94% |
| Local LLM + case retrieval | 50 | 0.2871 | 4.04 | 1 | 90% |
| PRISMATIC bounded harness | 50 | 0.2082 | 1.88 | 2 | 100% |

**本轮 harness 没有提升历史重合 F1。** 它对普通复核的差值为 −0.03634，患者配对 95% 区间 [−0.11168, 0.03931]；对病例检索的差值为 −0.07886，区间 [−0.13372, −0.02355]。harness 的精确率为 0.3511、召回为 0.1480，50% 病例为空输出。结构合法率提高伴随明显召回损失，不写成安全性改善。

普通复核和 harness 都有两次调用及相同每次输出上限，但输入 token 分别为 199,348 和 234,313，未做到严格总 token 等量。实际双调用累计时间分别约 286.44 秒和 324.24 秒。各方法费用不涉及 OpenRouter；受限 MIMIC 全程本地推理。

## 4. 时间与映射的实际发现

- 新映射仅用 40k 训练入院学习回退，共映射 814,254 / 1,788,195 条医嘱（45.535%），比旧版覆盖略低，但去掉了额外训练病例资源。
- IV 覆盖 19.518%，PO/NG 为 81.874%。240,310 条盐水名称代理记录均未映射；这不是 240,310 次盐水适应证判断，也不是可用于临床目的的标注。
- 1,144 个测试病例无窗口内原始医嘱，152 个有医嘱却全未映射，2,704 个有映射标签。各方法保留全部病例评分，同时报告 mapped-label-only 敏感性；该条件子集不是无偏临床评估。
- 入院前 24 小时、同次住院的指定血液检验有 171,455 条符合采样时点。其中 2,127 条在入院后才入库，已排除；最终 33,393 次入院有数值检验满足两种时间约束，筛后越界为 0。这些检验尚未加入本轮模型输入。
- triage 无时间戳、medrecon 无 storetime，无法凭现有源数据补出真实入库时间；主分析明确按 admission proxy 报告。

| Input / 输入 | Retrieval F1 | SGD mean F1 (3 seeds) |
| --- | ---: | ---: |
| admission_proxy | 0.3281 | 0.3864 |
| home_meds_only | 0.3139 | 0.3695 |
| no_patient_text | 0.2653 | 0.2772 |

无患者文本是信息消融，不是处方方法。SGD 在该条件存在优化随机性；种子 42 低于单纯流行度，详见逐种子 JSON。未选择最好种子来美化主表。

## 5. 完整订单协议与实际生成结果

订单协议包含成分/剂型/浓度/剂量/途径/频次/疗程/指征/证据/不确定性，以及液体用途、量、速度与复评。未知保留 null；缺临床知识始终输出未验证状态。

| Arm / 方法 | Cases | Raw schema valid | Normalized valid | Orders in valid bundles | Clinical ratings |
| --- | ---: | ---: | ---: | ---: | --- |
| direct | 10 | 4/10 | 9/10 | 13 | Pending / 待评 |
| retrieval_harness | 10 | 4/10 | 9/10 | 13 | Pending / 待评 |

原始生成每臂仅 4/10 完整满足 schema，常见错误是 ATC 级别不符，另有 1 例 JSON 截断。r2 将无法解析的 ATC 值保留在不确定性说明中并置 null，未猜码，规范化可解析率变为 9/10；**这不是模型生成正确率由 40% 提升为 90%**。两个版本结果均保留。harness 有 11 条订单被标记液体信息缺失，另有 1 条无患者证据引用；临床评分仍为空。7 项关键协议测试全部通过。

## 6. 尚未完成与明确原因

1. SafeDrug 自带 112 个 ATC-L3 分子键，不能直接用于本轮 ATC-L4 80 类；缺少经过核对的同药物空间分子/子结构表示。已取得 DDI 资源，但未用零分子冒充完整模型。
2. SafeRx-Agent 的纵向诊断/操作、专家路由、指征与禁忌知识需要同协议适配，尚未确认可执行官方实现；本轮检索复核代码不冒充其复现。[原论文](https://arxiv.org/html/2605.29146v1)使用 MIMIC-III/IV，当前诊断和操作作为输入，与此入院快照不同。
3. 当前 bounded harness 已跑通检索、状态、检查、修订与弃权，但缺成分级临床 DDI/肾调整知识、经审定经验写入和两位评审者评分，仍不是完整临床 harness。
4. 确认集、病例增长、全量临床主表、完整订单能力扩大、真实 FHIR、次级集扩展继续待办。

下一项工程修复应先解决订单编码/截断和过度弃权，并在验证集调节候选保留策略；不根据这 50 例修改后直接声称确认性改进。比较方法资源补齐与临床评审继续独立推进。

## 7. 复跑

```bash
# Use the research Python environment with upgrade_v4/requirements.txt.
python upgrade_v4/build_protocol_data.py
python upgrade_v4/build_verified_labs.py
python upgrade_v4/run_protocol_methods.py
python upgrade_v4/fetch_ddi_resource.py
python upgrade_v4/build_graph_resources.py
python upgrade_v4/run_gamenet_adaptation.py
# Use the separate local MLX environment for the following two commands.
python upgrade_v4/run_local_harness.py
python upgrade_v4/run_order_probe.py
# Return to the research environment.
python upgrade_v4/evaluate_order_probe.py
python -m unittest discover -s upgrade_v4 -p 'test_order_protocol.py' -v
python upgrade_v4/render_results.py
```
The graph script requires the author-linked `drug-DDI.csv` and pinned author checkouts. The local model must already exist. Resume logs must match protocol and input hashes; use a new private output directory for a new experiment.


## Artifacts / 证据文件

- [Frozen protocol 中文](PROTOCOL.md) / [English](PROTOCOL.en.md), [machine config](protocol.json), [complete order schema](order_schema.json)
- [Mapping audit](results/mapping_protocol_audit.json), [verified lab audit](results/verified_labs_audit.json)
- [Baselines and sensitivity](results/protocol_method_results.json), [GAMENet adaptation](results/gamenet_adaptation_results.json)
- [Same-case local harness](results/local_harness_results.json), [original order probe](results/order_probe_results.json), [normalization revision](results/order_probe_normalized_results.json)
- [Graph coverage](results/graph_resource_audit.json), [method readiness](method_readiness.json), [run manifest](results/run_manifest.json)
