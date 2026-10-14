"""Generate bilingual reports and the active English paper from aggregate runs."""
from pathlib import Path
import json,statistics as st,re

HERE=Path(__file__).resolve().parent
def read(name):return json.loads((HERE/'results'/name).read_text())

def render():
    b=read('protocol_method_results.json');g=read('gamenet_adaptation_results.json');l=read('local_harness_results.json')
    m=read('mapping_protocol_audit.json');t=read('verified_labs_audit.json');o=read('order_probe_normalized_results.json')
    bm=b['metrics']['admission_proxy'];runs=[bm['direct_sgd'][s]['all_admissions'] for s in ['17','42','73']]
    gr=[x['test'] for x in g['runs']]
    method_rows=[('Training prevalence',bm['prevalence']['all_admissions'],None),
      ('Case retrieval (30 neighbors)',bm['case_retrieval']['all_admissions'],None),
      ('TF-IDF/SGD (3 seeds)',{k:st.mean(x[k] for x in runs) for k in runs[0]},st.stdev(x['micro_f1_at_5'] for x in runs)),
      ('GAMENet text/single-visit adaptation (3 seeds)',{k:st.mean(x[k] for x in gr) for k in gr[0]},st.stdev(x['micro_f1_at_5'] for x in gr))]
    table='| Method / 方法 | N | Precision@5 | Recall@5 | F1@5 | Seed SD |\n| --- | ---: | ---: | ---: | ---: | ---: |\n'
    for name,metrics,sd in method_rows:
        table+=f"| {name} | 4,000 | {metrics['precision_at_5']:.4f} | {metrics['micro_recall_at_5']:.4f} | {metrics['micro_f1_at_5']:.4f} | {f'{sd:.4f}' if sd is not None else '—'} |\n"
    small='| Method / 方法 | N | Observed F1 | Mean classes | Calls | Valid output |\n| --- | ---: | ---: | ---: | ---: | ---: |\n'
    for key,name in [('prevalence','Prevalence'),('case_retrieval','30-neighbor voting'),('direct_sgd','SGD seed 42')]:
        small+=f"| {name} | 50 | {b['same_50_case_baselines'][key]['micro_f1_at_5']:.4f} | 5.00 | — | — |\n"
    small+=f"| GAMENet adaptation seed 42 | 50 | {g['same_50_case_seed42']['micro_f1_at_5']:.4f} | 5.00 | — | — |\n"
    for key,name in [('direct','Local LLM direct'),('ordinary_repeat','Ordinary repeat'),('case_retrieval','Local LLM + case retrieval'),('bounded_harness','PRISMATIC bounded harness')]:
        r=l['metrics'][key]
        small+=f"| {name} | 50 | {r['observed_micro_f1']:.4f} | {r['mean_predicted_classes']:.2f} | {2 if key in ['ordinary_repeat','bounded_harness'] else 1} | {100*r['valid_json_fraction']:.0f}% |\n"
    coverage=m['order_field_counts']['mapped']/m['order_field_counts']['raw_orders']*100
    timing='| Input / 输入 | Retrieval F1 | SGD mean F1 (3 seeds) |\n| --- | ---: | ---: |\n'
    for view,v in b['metrics'].items():
        timing+=f"| {view} | {v['case_retrieval']['all_admissions']['micro_f1_at_5']:.4f} | {st.mean(v['direct_sgd'][s]['all_admissions']['micro_f1_at_5'] for s in ['17','42','73']):.4f} |\n"
    ordertable='| Arm / 方法 | Cases | Raw schema valid | Normalized valid | Orders in valid bundles | Clinical ratings |\n| --- | ---: | ---: | ---: | ---: | --- |\n'
    for arm,r in o['metrics'].items():ordertable+=f"| {arm} | 10 | {r['raw_complete_schema_valid']}/10 | {r['normalized_schema_valid']}/10 | {r['proposed_orders']} | Pending / 待评 |\n"
    reproduce='''```bash
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
'''
    refs='''
## Artifacts / 证据文件

- [Frozen protocol 中文](PROTOCOL.md) / [English](PROTOCOL.en.md), [machine config](protocol.json), [complete order schema](order_schema.json)
- [Mapping audit](results/mapping_protocol_audit.json), [verified lab audit](results/verified_labs_audit.json)
- [Baselines and sensitivity](results/protocol_method_results.json), [GAMENet adaptation](results/gamenet_adaptation_results.json)
- [Same-case local harness](results/local_harness_results.json), [original order probe](results/order_probe_results.json), [normalization revision](results/order_probe_normalized_results.json)
- [Graph coverage](results/graph_resource_audit.json), [method readiness](method_readiness.json), [run manifest](results/run_manifest.json)
'''
    zh=f'''# PRISMATIC v4 实验交付：真实结果

2026-10-14，执行批次 r1；订单解析修正 r2。[English report](RESULTS.en.md)。本报告从汇总 JSON 生成。所有测试均为开发结果，未完成临床验证。

## 1. 本轮做成了什么

已执行：40k 内回退药物映射、分途径覆盖审计、双时间戳检验过滤、4,000 例基线与输入消融、三种子 GAMENet 入院文本适配、同 50 例四种本地 LLM 方法、10 例完整订单草案与修订、7 项订单协议测试。GAMENet 使用真实作者来源 DDI 图；不是全零占位。

## 2. 主要方法表：同 4,000 例

MIMIC-IV 3.1 + ED 2.2；训练/验证/测试 40,000/4,000/4,000；患者不交叉；同一 admission-proxy 输入、80 类药物空间、每例 5 个预测。均为历史可观察标签重合；不同模型训练计算量未严格配平。

{table}
GAMENet 保留作者图网络与读出，两个输入通道换为主诉/acuity 与既往用药 token，只有单次就诊，没有原始纵向历史读取。三种子均仅 5 epoch，验证分数到预算末尾仍在上升，不能据此断言原始 GAMENet 劣于 SGD。批处理前向与原代码单例前向误差均小于 1e-5。

SafeDrug、SafeRx-Agent 与临床完整 harness 的正式大样本分数仍未获得；不是零分。本轮已运行的 harness 见下一张同病例表。

## 3. 同 50 例：包含本地 harness 的跨方法比较

所有行使用相同的 50 位测试患者、相同目标和至多 5 类预算。前三行及 GAMENet 固定输出 5 类；LLM 可弃权。四个 LLM 方法的底座均为固定 revision 的 Qwen3-4B-Instruct-2507-4bit。本表不能与上一张的 4,000 例数字直接横向混排。

{small}
**本轮 harness 没有提升历史重合 F1。** 它对普通复核的差值为 −0.03634，患者配对 95% 区间 [−0.11168, 0.03931]；对病例检索的差值为 −0.07886，区间 [−0.13372, −0.02355]。harness 的精确率为 0.3511、召回为 0.1480，50% 病例为空输出。结构合法率提高伴随明显召回损失，不写成安全性改善。

普通复核和 harness 都有两次调用及相同每次输出上限，但输入 token 分别为 199,348 和 234,313，未做到严格总 token 等量。实际双调用累计时间分别约 286.44 秒和 324.24 秒。各方法费用不涉及 OpenRouter；受限 MIMIC 全程本地推理。

## 4. 时间与映射的实际发现

- 新映射仅用 40k 训练入院学习回退，共映射 814,254 / 1,788,195 条医嘱（{coverage:.3f}%），比旧版覆盖略低，但去掉了额外训练病例资源。
- IV 覆盖 19.518%，PO/NG 为 81.874%。240,310 条盐水名称代理记录均未映射；这不是 240,310 次盐水适应证判断，也不是可用于临床目的的标注。
- 1,144 个测试病例无窗口内原始医嘱，152 个有医嘱却全未映射，2,704 个有映射标签。各方法保留全部病例评分，同时报告 mapped-label-only 敏感性；该条件子集不是无偏临床评估。
- 入院前 24 小时、同次住院的指定血液检验有 171,455 条符合采样时点。其中 2,127 条在入院后才入库，已排除；最终 33,393 次入院有数值检验满足两种时间约束，筛后越界为 0。这些检验尚未加入本轮模型输入。
- triage 无时间戳、medrecon 无 storetime，无法凭现有源数据补出真实入库时间；主分析明确按 admission proxy 报告。

{timing}
无患者文本是信息消融，不是处方方法。SGD 在该条件存在优化随机性；种子 42 低于单纯流行度，详见逐种子 JSON。未选择最好种子来美化主表。

## 5. 完整订单协议与实际生成结果

订单协议包含成分/剂型/浓度/剂量/途径/频次/疗程/指征/证据/不确定性，以及液体用途、量、速度与复评。未知保留 null；缺临床知识始终输出未验证状态。

{ordertable}
原始生成每臂仅 4/10 完整满足 schema，常见错误是 ATC 级别不符，另有 1 例 JSON 截断。r2 将无法解析的 ATC 值保留在不确定性说明中并置 null，未猜码，规范化可解析率变为 9/10；**这不是模型生成正确率由 40% 提升为 90%**。两个版本结果均保留。harness 有 11 条订单被标记液体信息缺失，另有 1 条无患者证据引用；临床评分仍为空。7 项关键协议测试全部通过。

## 6. 尚未完成与明确原因

1. SafeDrug 自带 112 个 ATC-L3 分子键，不能直接用于本轮 ATC-L4 80 类；缺少经过核对的同药物空间分子/子结构表示。已取得 DDI 资源，但未用零分子冒充完整模型。
2. SafeRx-Agent 的纵向诊断/操作、专家路由、指征与禁忌知识需要同协议适配，尚未确认可执行官方实现；本轮检索复核代码不冒充其复现。[原论文](https://arxiv.org/html/2605.29146v1)使用 MIMIC-III/IV，当前诊断和操作作为输入，与此入院快照不同。
3. 当前 bounded harness 已跑通检索、状态、检查、修订与弃权，但缺成分级临床 DDI/肾调整知识、经审定经验写入和两位评审者评分，仍不是完整临床 harness。
4. 确认集、病例增长、全量临床主表、完整订单能力扩大、真实 FHIR、次级集扩展继续待办。

下一项工程修复应先解决订单编码/截断和过度弃权，并在验证集调节候选保留策略；不根据这 50 例修改后直接声称确认性改进。比较方法资源补齐与临床评审继续独立推进。

## 7. 复跑

{reproduce}
{refs}
'''
    en=f'''# PRISMATIC v4: executed experimental results

14 October 2026, execution batch r1 and order normalization r2. [Chinese report](RESULTS.zh.md). Generated from aggregate JSON. All results are developmental; clinical correctness is unreviewed.

## 1. Completed work

Executed a train-40k-only fallback mapper, route coverage audit, dual-timestamp laboratory filter, 4,000-case baselines and input sensitivity, three-seed GAMENet admission-text adaptation, four local LLM methods on identical 50 cases, and a ten-case complete-order draft/revision probe. Seven critical order-contract tests pass. No restricted MIMIC input went to OpenRouter.

## 2. Main method panel: identical 4,000 admissions

MIMIC-IV 3.1 plus ED 2.2; 40k/4k/4k patient-disjoint samples, the same admission-proxy fields, top-80 training classes and exactly five predictions. These are observed historical-label overlap metrics; training compute differs.

{table}
The GAMENet adaptation retains author graph/readout modules, replacing diagnosis/procedure channels with complaint/acuity and home-medication tokens. Single-visit inputs remove longitudinal dynamic-memory reading. Three seeds ran five epochs, with validation scores still rising at the budget boundary. This does not establish that faithfully reproduced GAMENet is inferior to SGD. Batched inference agrees with the author's single-case computation within 1e-5.

## 3. Same 50 cases, including the local harness

Every row uses the same 50 test patients and targets, with at most five output classes. Traditional methods output five; LLMs may abstain. All four LLM arms use the same pinned Qwen3-4B-Instruct-2507-4bit weights. Do not mix these scores with the 4,000-case panel.

{small}
The bounded harness does not improve observed F1. Its paired difference versus ordinary repeat is −0.03634 (95% patient-bootstrap interval −0.11168 to 0.03931), and versus retrieval is −0.07886 (−0.13372 to −0.02355). Precision is 0.3511, recall 0.1480 and empty-output frequency 50%. Better structural validity accompanies lower recall; this is not evidence of safety improvement.

Repeat and harness share two calls and the same per-call output cap, but consume 199,348 and 234,313 input tokens respectively. Total token budgets are not identical. Their accumulated arm times are approximately 286.44 and 324.24 seconds. Shared first responses are charged to each logical arm in usage reporting.

## 4. Timing and mapping

The revised mapper covers 814,254/1,788,195 orders ({coverage:.3f}%). Coverage is slightly lower than v0.3 after restricting fallback learning to actual training admissions. IV coverage is 19.518%; PO/NG coverage is 81.874%. All 240,310 saline-name proxy rows are unmapped, so ATC overlap cannot evaluate saline behavior. Name matches are not clinical-purpose labels.

The development test retains 1,144 admissions with no recorded window order, 152 with unmapped-only orders and 2,704 with mapped labels. Mapped-label-only sensitivity is conditional on future label availability, not an unbiased clinical evaluation.

Of 171,455 selected same-admission blood-lab rows charted within 24 hours before admission, 2,127 were stored after the decision and excluded. Numeric results satisfying both time constraints cover 33,393 admissions; post-filter violations are zero. They are not added post hoc to this comparison. Triage lacks row timestamps and medrecon lacks storetime, so full availability remains unverifiable.

{timing}
The no-text condition is an information ablation. Optimization variation is retained: seed 42 underperforms prevalence in that condition. The table reports all three seeds rather than selecting the best.

## 5. Complete-order execution

The contract includes ingredient, formulation, concentration, dose/unit, route, frequency, duration, indication, evidence and uncertainty, plus fluid purpose/volume/rate/reassessment. Unknowns remain null and absent clinical knowledge is always disclosed.

{ordertable}
Only 4/10 raw responses per arm satisfy the full schema. Main failures are wrong ATC granularity and one truncated JSON response. In r2, unresolved ATC strings become null with the raw value retained in uncertainty; no code is inferred. Normalized validity is 9/10, not an increase in correct model generation from 40% to 90%. Both versions remain available. The revised harness has 11 fluid-information findings and one order without patient evidence. Clinical correctness remains unscored. Seven contract tests pass.

## 6. Outstanding gates

SafeDrug's bundled 112 molecular keys are ATC-L3 and are not a verified mapping for the common 80-class ATC-L4 space. The DDI resource is now available, but molecular/substructure compatibility remains unresolved; no zero-molecule substitute is called complete SafeDrug.

[SafeRx-Agent](https://arxiv.org/html/2605.29146v1) uses MIMIC-III/IV, current diagnoses/procedures, longitudinal context and clinical knowledge. A compatible admission adapter and confirmed executable reference are outstanding. Our bounded retrieval/critique prototype is not labeled its reproduction.

The current harness implements retrieval, state, structural checks, bounded revision and abstention. Validated ingredient-level DDI/renal knowledge, adjudicated experience updates and clinical ratings remain missing. Confirmatory patients, larger complete-order evaluation, case growth, real FHIR and extended secondary benchmarks remain pending. Repair schema truncation and over-abstention on validation data before claiming improvement on fresh confirmation.

## 7. Reproduce

{reproduce}
{refs}
'''
    (HERE/'RESULTS.zh.md').write_text(zh.rstrip()+'\n');(HERE/'RESULTS.en.md').write_text(en.rstrip()+'\n')
    table_data={'panel_4000':[{'method':n,'metrics':v,'seed_sd_f1':s} for n,v,s in method_rows],
                'panel_50':{'classical':b['same_50_case_baselines'],'gamenet_seed42':g['same_50_case_seed42'],'llm':l['metrics']}}
    (HERE/'results/method_table.json').write_text(json.dumps(table_data,indent=2)+'\n')
    return method_rows,b,g,l,m,t,o,coverage

if __name__=='__main__':render()
