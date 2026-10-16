"""Generate bilingual reports only from completed local experimental artifacts."""
import json
from common import *
LABELS={'rxrsi_base':'RxRSIAgent, initial state','rxrsi_selected':'RxRSIAgent, retained state','direct':'Direct self-refinement',
 'saferx':'SafeRx-Agent task adaptation','skemex':'SkeMex author memory core + common actor','flame_list':'FLAME released list-policy transfer',
 'candidate_top8':'Frozen supervised top-8 + order tool'}
def main():
    audit=json.loads((HERE/'results/audit.json').read_text());learning=json.loads((HERE/'results/learning_scope.json').read_text())
    comparison=json.loads((HERE/'results/comparison.json').read_text());transfer=json.loads((HERE/'results/transfer.json').read_text())
    assert comparison['complete'] and learning['complete'] and transfer['complete']
    methods=audit['methods'];rounds=learning['rounds'];fmt=lambda x:f'{100*x:.2f}'
    lines=['| Method | Drug P | Drug R | Drug F1 | Core4 F1 | Core5 F1 | Empty |', '|---|---:|---:|---:|---:|---:|---:|---:|']
    for name in ['direct','saferx','skemex','rxrsi_base','rxrsi_selected']:
        if name in methods:
            m=methods[name]['metrics'];lines.append('| '+LABELS[name]+' | '+' | '.join(fmt(m[k]) for k in ['drug_precision','drug_recall','drug_micro_f1','core_order_micro_f1','core5_micro_f1','empty_fraction'])+' |')
    table='\n'.join(lines)
    separate=['| Separate component / initializer | Drug F1 | Core4 F1 | Core5 F1 |', '|---|---:|---:|---:|']
    for name in ['candidate_top8','flame_list']:
        if name in methods:
            m=methods[name]['metrics'];separate.append('| '+LABELS[name]+' | '+' | '.join(fmt(m[k]) for k in ['drug_micro_f1','core_order_micro_f1','core5_micro_f1'])+' |')
    table+='\n\n'+ '\n'.join(separate)
    curve=json.loads((HERE/'results/round_curve.json').read_text())['trajectory']
    trajectory=['| Round | New cases processed | Retained rules | Proposal drug / Core4 F1 | Guard drug / Core4 F1 | Test drug / Core4 F1 | Accepted |','|---:|---:|---:|---:|---:|---:|---|']
    for r,t in zip(rounds,curve):trajectory.append(f"| {r['round']} | {r['cases_seen']} | {len(r['state']['cards'])} | {fmt(r['proposal']['drug_micro_f1'])} / {fmt(r['proposal']['core_order_micro_f1'])} | {fmt(r['guard']['drug_micro_f1'])} / {fmt(r['guard']['core_order_micro_f1'])} | {fmt(t['metrics']['drug_micro_f1'])} / {fmt(t['metrics']['core_order_micro_f1'])} | {r['accepted']} |")
    tr='\n'.join(trajectory);a=transfer['methods']['rxrsi_base'];b=transfer['methods']['rxrsi_selected'];main=methods['rxrsi_selected']['metrics'];counts=methods['rxrsi_selected']['counts']
    en=f'''# MIMIC-IV prescription experiment: executed results

## 1. Main result and task

**RxRSIAgent: drug F1 {fmt(main['drug_micro_f1'])}%; Core4 F1 {fmt(main['core_order_micro_f1'])}% on all 1,082 test admissions.**

This is a local Qwen3-4B prescription-task adaptation, not the frozen hosted DeepSeek QA agent. Predict the full set of new/change orders in hours 6–12 after admission, using observations available at hour 6. Output comprises joint drug/route/dose/unit/frequency templates selected from a common 24-drug catalogue; it is not unrestricted prescribing or the entire hospital-stay regimen. The cohort is retrospectively restricted to admissions with nonempty future targets, complete 12-hour follow-up and no ambiguous candidate target rows. Provider order time and pharmacy entry time must both fall in hours 6–12, with verification by hour 12; prior-order and lab availability use recorded clocks. Released data lack complete field-version histories. This is not an all-admission evaluation. The 128-name vocabulary and 40,000-admission supervised candidate tool are frozen. Out-of-vocabulary GT remains scored.

## 2. Measured comparison

All numbers below are percentages. The first five local rows use the same cases, candidate catalogue, offline label resource, Qwen backbone and maximum 128+128+96 output tokens. Actual token use and offline learning compute differ. **SafeRx and SkeMex are explicitly limited task/subsystem adaptations. FLAME uses a released trained list-policy checkpoint with a different backbone and initializer; its row is a separate transfer experiment, not a full-method, equal-information comparison. These measurements do not establish superiority over the original papers.**

{table}

Candidate coverage ceiling: **{fmt(main['catalogue_drug_recall_ceiling'])}% of GT drugs**. Complete Core5 reference coverage: **{fmt(main['core5_gt_field_coverage'])}%**. Missing frequency does not become a match. No saline-presence metric is used.

## 3. Sequential experience updates

{tr}

Six rounds process 24 new training admissions each (144 total, disjoint from the previous 144 training admissions). The local reflector receives full available-input, plan, evidence, checker and reference traces for discrepant examples and a comparatively better example; better does not mean correct. A researcher-defined interface permits conditional procedure text and selected/all-observed fact scope. It cannot change weights, executable tool code, vocabulary, templates or descriptive output schemas. Each proposed rule requires an observable trigger and counterexample. Numeric dose rules and unsupported copied drug actions are rejected. Explicit {{}} means no proposed update. Retention requires a strictly higher proposal mean of drug/Core4 F1 and no decrease in either guard endpoint. Proposal/guard subsets (48/64) are reused. All states freeze before new test inference; earlier literal-schema test scores had already been observed. A flat trajectory is not successful RSI. The available trigger language contains only five observation-presence predicates (or a two-predicate conjunction), and the only tool configuration is fact scope; this does not yet express a broad clinical indication/dose skill library.

## 4. Frozen-memory transfer

On Llama-3.2-3B, all 1,082 cases: initial drug/Core4 F1 **{fmt(a['drug_micro_f1'])}/{fmt(a['core_order_micro_f1'])}%**; retained memory **{fmt(b['drug_micro_f1'])}/{fmt(b['core_order_micro_f1'])}%**. Drug-F1 change **{100*(b['drug_micro_f1']-a['drug_micro_f1']):+.2f} percentage points**. No Llama-specific rule selection or retraining. Since the retained memory is empty, this is a second-backbone baseline check; it does not test transfer of a learned rule or establish model-independent benefit.

## 5. Failure findings and cases

- Initial protocol diagnostic, 48 proposal cases: drug/Core4 F1 9.59/4.26%; 25 parseable plans, zero parseable assessments and zero verified-fact cases. Fact-ID binding and concise intermediate JSON repair this contract. This is a researcher repair, not autonomous RSI; syntax improvement alone did not establish accuracy improvement.
- Training observability audit: 1,722/40,000 admissions belong to 144 groups with identical visible context and differing reference drug sets. This supports an information/variation limitation, not a claim that every error is unavoidable.
- Selected test predictions miss {counts['selection_missing']} targets already inside the catalogue; {counts['catalogue_missing']} targets are outside it. These distinguish selection and candidate-generation bottlenecks.
- Case-level GT/prediction differences and before/after interventions are saved locally as `failure_case_studies.json` in the restricted experiment directory. No patient-level content is published.
- Recorded actions are not unique clinical optima. No clinical-safety, DDI, allergy or renal-dose success is inferred from F1 or source quotation.

## 6. Cost, provenance and limitations

**New paid API cost: USD 0; authorization cap: USD 10.** All patient inference and reflection are local. Public checkpoint downloads do not call paid inference APIs. Local compute is not monetized. Earlier located response expenditure remains approximately USD 89.53 and is not charged to this new cap.

The test has historical exposure from earlier supervised studies; the result is exploratory. Source pins, exact predictor hashes, costs, denominators and patient-bootstrap contrasts are in `results/audit.json`, `results/*`, and `test_freeze_scope.json`. See the README for comparator fidelity and runnable commands. Publication-quality claims still require complete author-workflow controls and a new untouched clinical evaluation.
'''
    zh=f'''# MIMIC-IV 完整窗口处方实验：真实结果

## 一、这次实际测了什么

**RxRSIAgent 在全量 1,082 例上的药物 F1：{fmt(main['drug_micro_f1'])}%；四字段订单 F1：{fmt(main['core_order_micro_f1'])}%。**

这是本地 Qwen3-4B 的处方任务适配，不是把原来 DeepSeek 选择题分数改名。使用入院第 6 小时已可用的信息，预测随后 6 小时内全部新增/变更订单；不是预测整个住院期的所有药物。模型从共享的 24 药物候选订单库选择多项，编译出药物、途径、剂量、单位和频次。队列只包含未来窗口非空、12小时随访完整且目标记录时序一致的入院病例：医生开单时间和药房录入时间均须位于6–12小时，且12小时内完成核验；既往订单和检验按记录的可用时间过滤。原始发布数据没有完整字段版本史，不能声称是全部入院人群的结果。128 药物词表与 4 万例训练得到的候选工具保持冻结；库外 GT 仍计入漏开。

## 二、对比主表

数值单位均为百分比。共同本地对照使用相同病例、候选库、说明书资源、Qwen 底座和最多 128+128+96 输出 token；实际输入量、训练与记忆计算量不同。**SafeRx 是独立任务适配，SkeMex 使用作者记忆子系统与共同处方执行器。FLAME 是已发布训练检查点的列表策略迁移，底座及初始化信息不同。这些都不能冒充完整原方法复现，也不能据此声称超过原论文。**

{table}

候选库最多覆盖 **{fmt(main['catalogue_drug_recall_ceiling'])}%** 的 GT 药物；五字段均已知的参考订单覆盖率为 **{fmt(main['core5_gt_field_coverage'])}%**。缺失频次不算匹配，不计算盐水出现 F1。

## 三、逐轮进化

{tr}

六轮各处理24例新训练病例，共144例，与此前144例训练病例不重叠。反思器读取可用输入、计划、证据、核验与参考订单的完整追踪，包括失败例和相对较好例；后者不一定完全正确。研究者预先定义可更新的程序文本、可观察触发条件、反例和所选/全部观察事实配置；底座、工具代码、词表、订单模板和描述性输出协议在轨迹内固定。数字剂量规则与未独立验证的药名动作被拒绝；明确输出 {{}} 代表不提案。候选集药物/订单 F1 均值须严格提高，守门集两个端点均不得下降。复用48/64例开发子集，全部状态冻结后才开始新测试；此前含编号示例的测试分数已被观察，属于探索性实验。**没有保留变化就不能声称成功 RSI。** 当前条件语言仅有五个观察是否存在的谓词及至多两个谓词的合取，工具配置也只支持事实范围；它尚不足以表达广泛的适应证和剂量技能库。

## 四、跨模型迁移

将冻结的规则直接交给 Llama-3.2-3B，不在该模型上再挑规则。全量 1,082 例：初始药物/四字段 F1 **{fmt(a['drug_micro_f1'])}/{fmt(a['core_order_micro_f1'])}%**；迁移后 **{fmt(b['drug_micro_f1'])}/{fmt(b['core_order_micro_f1'])}%**。药物 F1 变化 **{100*(b['drug_micro_f1']-a['drug_micro_f1']):+.2f} pp**。保留记忆为空，因此这里只能作为第二底座的基线检查，没有可迁移的学习规则；不能称为已证明跨模型进化收益。

## 五、从失败中得到什么

1. 初始 48 例开发实验药物/订单 F1 为 9.59/4.26%，只有 25 例计划可解析，评估可解析与事实核验均为零。事实编号绑定和简短输出修复了工程协议；这不是自主 RSI，也不代表准确率随之提高。
2. 训练集中有 1,722/40,000 例属于 144 组“可见上下文相同、GT 药物集合不同”的记录。低分也受信息缺失、治疗差异或记录过程影响，不能直接推断模型不理解医生。
3. 最终测试中，已有候选却漏选的 GT 共 {counts['selection_missing']} 个；候选库外 GT 共 {counts['catalogue_missing']} 个。前者针对决策，后者针对候选检索，不能混成一种错误。
4. 真实训练失败病例、GT、前后预测及字段差异保存在受限目录的 `failure_case_studies.json`，不向 GitHub 发布病例内容。
5. GT 是记录到的医生行为，不能直接当作唯一临床最优方案；F1 和引用有效不等于 DDI、过敏、肾剂量或处方适宜性已经验证。

## 六、费用与可复现性

**本次新增付费 API 支出 0 美元，用户授权上限 10 美元。** 病例推理和反思均在本地；公开模型下载不产生模型推理 API 费用。本地计算成本没有折算。历史已找到的响应费用仍约 89.53 美元，不重复计入此次预算。

当前测试集有历史监督实验暴露，结果属于探索性评估。聚合结果、患者级 bootstrap、预测哈希、模型/代码版本与冻结状态见 `results/` 和 `test_freeze_scope.json`。完整原方法对照和新的未触碰临床评估仍是论文定稿条件。
'''
    more_en,more_zh=details(audit,learning)
    en+=more_en;zh+=more_zh
    e,z=schema_details(audit);en+=e;zh+=z
    (HERE/'RESULTS.en.md').write_text(en);(HERE/'RESULTS.zh.md').write_text(zh)
    for lang,text in [('en',en),('zh',zh)]:
        (ROOT/f'paper/versions/v0.50-2026-10-17.{lang}.md').write_text(text)
    print('Wrote bilingual executed-result reports')

def details(audit,learning):
    """Mechanism results and implementation boundaries, all linked to measured data."""
    fmt=lambda x:f'{100*x:.2f}'
    comparison=audit['paired_patient_bootstrap']['rxrsi_base_to_rxrsi']
    ci=comparison['drug_delta_ci95'];ci4=comparison['core4_delta_ci95']
    base=audit['methods']['rxrsi_base']['metrics'];final=audit['methods']['rxrsi_selected']['metrics']
    delta=100*(final['drug_micro_f1']-base['drug_micro_f1'])
    cards=learning['selected_state']['cards']
    lines=['| Module | Initial | Retained |','|---|---:|---:|',f'| Procedural cards | 0 | {len(cards)} |',
      f"| Cards enabling all-observed verification | 0 | {sum(c.get('fact_scope')=='all_observed' for c in cards)} |",
      '| Model-weight updates | 0 | 0 |','| New executable tool code | 0 | 0 |','| Candidate model / vocabulary changes | 0 | 0 |']
    module='\n'.join(lines)
    learned='\n'.join('- Trigger / 条件: `'+c['condition']+'`; scope / 范围: `'+c.get('fact_scope','selected')+'`; SHA-256: `'+c['card_sha256']+'`.' for c in cards) or 'No retained rule / 未保留规则。'
    learned+='\n\nFull generated text remains in restricted local learning.json; public cards expose hashes and structural fields only. / 完整生成文本保留在受限目录，公开卡片仅含哈希及结构字段。'
    ab=json.loads((HERE/'results/evidence_ablation.json').read_text());a=ab['baseline'];b=ab['without_label_excerpts']
    trace=json.loads((HERE/'results/training_trace_audit.json').read_text())['counts']
    semantic=json.loads((HERE/'results/skemex_learning.json').read_text())
    sr=['| Round | Cases | Created | Active skills | Schema/materialization errors |','|---:|---:|---:|---:|---:|']
    for r in semantic['rounds']:sr.append(f"| {r['round']} | {r['cases_seen']} | {r['created']} | {r['active']} | {len(r.get('adapter_errors',[]))} |")
    sk='\n'.join(sr)
    comp_path=HERE/'results/component_ablation.json';comp='Component diagnostic is still pending; no result is implied.'
    if comp_path.exists():
        d=json.loads(comp_path.read_text());ls=['| Component, 128 fixed test cases | Drug F1 | Core4 F1 | Mean checked facts |','|---|---:|---:|---:|']
        for name,entry in d['arms'].items():ls.append(f"| {name} | {fmt(entry['metrics']['drug_micro_f1'])} | {fmt(entry['metrics']['core_order_micro_f1'])} | {entry['mean_checked_facts']:.2f} |")
        comp='\n'.join(ls)
        replay=d.get('cached_full_cohort_to_fresh_replay',{}).get('initial',{})
        if replay:comp+=f"\n\nNo-edit replay control / 无改动重放对照: {replay['changed_cases']}/128 semantic order sets differ between the cached full-cohort run and the fresh fixed-layout subset run. All four component arms use the same case order/chunks and fresh per-batch generation. / 四个消融臂采用相同病例顺序与分批方式，逐批重新生成。"
    de=audit['methods']['rxrsi_selected']['descriptive_endpoints']
    per_path=HERE/'results/catalogue_permutation.json';position_en=position_zh=''
    if per_path.exists():
        per=json.loads(per_path.read_text());same=per['same_drug_set_cases']
        position_en=f"Catalogue permutation preserves the drug set in {same}/128 cases. Drug F1 changes from {fmt(per['original']['drug_micro_f1'])}% to {fmt(per['permuted']['drug_micro_f1'])}%. This tests position sensitivity, not absence of pretrained drug priors."
        position_zh=f"只打乱候选编号和顺序后，{same}/128例仍选择相同药物集合；药物 F1 从 {fmt(per['original']['drug_micro_f1'])}% 变为 {fmt(per['permuted']['drug_micro_f1'])}%。这检验位置敏感性，不能证明预训练药名先验已被排除。"
    en=f'''
## 7. Retention is not the same as verified improvement

Full-test initial-to-retained drug-F1 change: **{delta:+.2f} pp**, patient-cluster 95% interval **[{100*ci[0]:+.2f}, {100*ci[1]:+.2f}] pp**; Core4 interval **[{100*ci4[0]:+.2f}, {100*ci4[1]:+.2f}] pp**. There are {comparison['changed_cases']} changed cases, {comparison['case_f1_improved']} with higher per-case drug F1 and {comparison['case_f1_regressed']} with lower per-case drug F1. These exploratory intervals do not adjust for repeated development. A positive point estimate alone does not establish reliable improvement.

{module}

Retained state identifiers:

{learned}

The executable trigger is the declared condition enum. Natural-language counterexamples are recorded but not formally enforced as separate predicates. The model's root description remains a hypothesis. The fact-scope interface was written by the researcher before this trajectory; its selection was made by the updater.

{comp}

The subset and component arms were fixed before the corrected-interface test, after earlier literal-schema test scores had been observed. They are diagnostic only, and do not choose a new main-table method.

{position_en}

For retained RxRSIAgent, mean drug Jaccard is {fmt(de['mean_drug_jaccard'])}%, exact drug-set agreement {fmt(de['drug_exact_set_accuracy'])}%; reference-relative omissions/extras average {de['missed_drugs_per_admission']:.2f}/{de['extra_drugs_per_admission']:.2f} per admission. Recall is {fmt(de['prior_target_recall'])}% for target drugs present in prior orders and {fmt(de['new_target_recall'])}% for other target drugs. The shared catalogue covers {fmt(de['catalogue_core4_recall_ceiling'])}% of complete reference Core4 tuples. Order fields are supplied by the frozen joint-template tool, not independently generated by the LLM. Core4/Core5 tuples are complete in {fmt(de['core4_prediction_field_coverage'])}%/{fmt(de['core5_prediction_field_coverage'])}% of predicted orders. Tuple F1 scores only tuples whose fields are observed; completeness is therefore a separate endpoint.

## 8. Evidence-removal intervention and comparator learning

Training-only trace audit (144 admissions): {trace['reference_drugs_in_catalogue']}/{trace['reference_drugs']} reference drugs enter the catalogue; {trace['reference_candidate_drugs_with_cached_label']} of those have an exact-name cached label, but only {trace['reference_drugs_with_excerpt']} reference drugs receive a selected excerpt. Conversely, {trace['predicted_drugs_with_excerpt']}/{trace['predicted_drugs']} predicted drugs have an excerpt. Only two sentences are allocated globally per case. This exposes uneven evidence availability/selection; it does not establish its causal effect. The checker covers {trace['checked_unique_facts']}/{trace['observed_facts']} supplied facts; the LLM still sees the complete supplied input. No extra clinical context is created by expanding checker scope.

On the same 48 proposal cases, with label excerpts: drug/Core4 F1 **{fmt(a['drug_micro_f1'])}/{fmt(a['core_order_micro_f1'])}%**; without excerpts: **{fmt(b['drug_micro_f1'])}/{fmt(b['core_order_micro_f1'])}%**. This changes information and input length, and is an exploratory development ablation. It does not prove that drug labels are intrinsically harmful or that their clinical use is unnecessary.

SkeMex author-memory training, with all 144 training admissions:

{sk}

The author core is pinned; the actor, embedding backend and continuous prescription reward are adaptations. The source's original ReAct/tool benchmark is not reproduced. RxRSIAgent additionally uses 48 proposal and 64 guard labels; SkeMex directly updates on 144 training admissions. Validation supervision and offline update compute are not matched. FLAME executes the actual released trained list policy after merging 224 adapter layers; all adapter tensors are consumed. Its source classifier and patient/diagnosis/procedure embeddings are absent, so only component transfer is claimed.

An engine-only prefill-batch probe changed 2/16 development outputs. That optimization was rejected; the main run retains prefill batch 2 and completion batch 8. Quantized greedy decoding is still batch-sensitive, and cached requests reuse their first recorded output.

Primary method sources: [SafeRx-Agent](https://arxiv.org/html/2605.29146v1), [FLAME paper](https://arxiv.org/html/2505.20218v1) and [author code](https://github.com/cxfann/Flame), [SkeMex paper](https://arxiv.org/html/2606.09365v4) and [author code](https://github.com/manglu097/SkeMex). Published numbers are preserved separately in `published_reference_scores.json`, never inserted as matched local rows.
'''
    zh=f'''
## 七、通过守门不等于已经证明提高

全量测试初始→最终药物 F1 变化 **{delta:+.2f} pp**，按患者聚类 bootstrap 的95%区间为 **[{100*ci[0]:+.2f}, {100*ci[1]:+.2f}] pp**；四字段 F1 变化区间为 **[{100*ci4[0]:+.2f}, {100*ci4[1]:+.2f}] pp**。共 {comparison['changed_cases']} 例输出变化，其中单例药物 F1 改善 {comparison['case_f1_improved']} 例、下降 {comparison['case_f1_regressed']} 例。区间未校正重复开发，正的点估计不能单独证明可靠收益。

{module}

保留状态的可公开标识如下：

{learned}

可执行触发条件是枚举条件；自然语言反例被保存，但尚未形式化为额外排除谓词。模型写出的根因仍是假设。事实范围配置接口由研究者预先实现，更新器决定是否及在何种条件下启用。

{comp}

子集和消融臂在修复后测试开始前冻结；此前编号示例版本的测试结果已被观察；仅用于解释组件，不据此改选主表方法。

{position_zh}

最终 RxRSIAgent 的平均药物 Jaccard 为 {fmt(de['mean_drug_jaccard'])}%，整套药物完全匹配率 {fmt(de['drug_exact_set_accuracy'])}%；每例相对于GT平均漏 {de['missed_drugs_per_admission']:.2f} 个药、多 {de['extra_drugs_per_admission']:.2f} 个药。此前已出现药物的目标召回率 {fmt(de['prior_target_recall'])}%，新药目标召回率 {fmt(de['new_target_recall'])}%。共享候选模板最多覆盖 {fmt(de['catalogue_core4_recall_ceiling'])}% 的完整四字段 GT。剂量等联合字段由冻结模板工具提供，不是 LLM 自由生成的剂量。预测订单的四/五字段完整率分别为{fmt(de['core4_prediction_field_coverage'])}%/{fmt(de['core5_prediction_field_coverage'])}%；字段F1只比较字段均已知的元组，须与完整率一起读。

## 八、证据检索干预与对照学习过程

144例训练追踪：{trace['reference_drugs_in_catalogue']}/{trace['reference_drugs']}个GT药物进入候选库，其中{trace['reference_candidate_drugs_with_cached_label']}个有精确药名匹配的缓存说明书，但最终只有{trace['reference_drugs_with_excerpt']}个GT药物获得摘录；相对地，预测药物有{trace['predicted_drugs_with_excerpt']}/{trace['predicted_drugs']}个获得摘录。当前每例只在全局分配两个句子，证据覆盖明显不均衡；这还不是它造成错选的因果证明。核验器检查{trace['checked_unique_facts']}/{trace['observed_facts']}条输入事实，LLM仍能看见完整输入，扩大核验范围不会增加原始临床信息。

相同48例候选集：有说明书片段时药物/订单 F1 为 **{fmt(a['drug_micro_f1'])}/{fmt(a['core_order_micro_f1'])}%**；去掉片段后为 **{fmt(b['drug_micro_f1'])}/{fmt(b['core_order_micro_f1'])}%**。这是同时改变信息量和输入长度的探索性开发消融，不能推断药品说明书本身有害或临床上不需要它。

SkeMex 作者记忆核心处理全部144例训练病例：

{sk}

使用了固定版本的作者记忆代码；处方执行器、向量模型与连续奖励属于适配，未执行原论文完整 ReAct 工具任务。RxRSIAgent另用了48例候选集和64例守门集标签；SkeMex直接在144例训练病例上更新。因此验证监督量和离线更新算力不等同。FLAME 使用真实发布的训练后列表策略，融合224个适配器层、全部适配器张量均已使用；缺少源分类器和患者/诊断/操作嵌入，只能称组件迁移。

预填充批次加速探针使16例中的2例输出变化，因此未采用；主实验保留预填充批次2、生成批次8。量化贪心解码仍可能随批次布局变化，缓存复用第一次记录的输出。

原始来源：[SafeRx-Agent](https://arxiv.org/html/2605.29146v1)、[FLAME论文](https://arxiv.org/html/2505.20218v1)与[作者代码](https://github.com/cxfann/Flame)、[SkeMex论文](https://arxiv.org/html/2606.09365v4)与[作者代码](https://github.com/manglu097/SkeMex)。原论文分数另存 `published_reference_scores.json`，没有混入同条件实测主表。
'''
    return en,zh
def schema_details(audit):
    probe=json.loads((ROOT/'upgrade_v49/results/schema_probe.json').read_text())
    rows=['| Format intervention, 48 training cases | Drug F1 | A1 selections | A23 selections |','|---|---:|---:|---:|']
    for name,arm in probe['arms'].items():
        ids=arm['order_identifier_counts'];rows.append(f"| {name} | {100*arm['metrics']['drug_micro_f1']:.2f}% | {ids.get('A1',0)} | {ids.get('A23',0)} |")
    table='\n'.join(rows);fix=audit['engineering_schema_repair'];old=fix['old_metrics'];new=fix['new_metrics']
    paired=fix['paired'];ci=paired['drug_delta_ci95']
    summary=f"{100*old['drug_micro_f1']:.2f}% → {100*new['drug_micro_f1']:.2f}% (95% CI of difference: [{100*ci[0]:+.2f}, {100*ci[1]:+.2f}] pp)"
    attempts=[x for r in json.loads((HERE/'results/learning_scope.json').read_text())['rounds'] for x in r.get('attempts',[])]
    from collections import Counter
    reasons=dict(Counter(x.get('rejection') or ('explicit_no_edit' if x.get('no_edit') else 'valid_candidate') for x in attempts))
    en=f"""
## 9. Controlled format-example intervention and failed updates

{table}

Patients, catalogue contents and batch layout remain fixed; only valid identifier examples are changed or removed. Moving the example from A1 to A23 moves selections from A1 (36→0 cases) to A23 (5→46), confirming format-example anchoring in this local adapter. Descriptive schemas remove this shortcut and are applied to all common local controls. This is a researcher interface repair, **not an accepted RSI update**. Full-test initial actor comparison: {summary}. Earlier literal-schema tests are exposed, so this is exploratory.

The earlier bounded-scope learner passed development but failed on all 1,082 test cases: drug F1 7.34→7.27%; +3 correct drugs accompanied by +138 extras. This negative result is preserved. Corrected-trajectory proposal dispositions: `{reasons}`. Disallowed rules, empty proposals, unchanged predictions and failed gates are distinct failure modes; none is successful evolution. The two valid candidates activate only when both prior orders and labs are absent. In each development subset they trigger on just two cases containing only one observed fact, so all-observed scope adds no checked facts and changes no orders. This is a measured condition/action mismatch, not successful tool improvement; see learning_diagnostics.json.
"""
    zh=f"""
## 九、格式示例因果干预与更新失败

{table}

患者、候选内容和分批布局保持相同，只改或删除合法编号示例。示例从A1换成A23，A1入选36→0例，A23入选5→46例，确认本地适配器存在格式示例锚定。描述性协议去掉该捷径，并共同应用于所有本地对照。这是研究者工程修复，**不是接受的 RSI 更新**。全量初始执行器对照：{summary}。此前测试已经暴露，仍属探索性结果。

此前扩大事实范围的规则通过开发集，但全量测试药物F1从7.34降至7.27%；仅多命中3个药，同时多出138个药。负结果保留。修复后轨迹的提案处理统计：`{reasons}`。非法规则、明确不提案、输出不变与未通过开发门槛需要分别解释，不能统称成功进化。两个合法候选都要求“既无既往订单又无实验室信息”；在各开发子集中仅触发2例，这些病例本来就只有1条观察事实，扩大至全部事实没有增加核验信息，订单也完全不变。这是实测的条件与动作不匹配，见 learning_diagnostics.json。
"""
    full=json.loads((PRIVATE/'test_freeze.json').read_text())
    (PRIVATE/'LEARNED_STATE.bilingual.md').write_text('# Local learned state / 本地学习状态\n\n```json\n'+json.dumps(full['state'],ensure_ascii=False,indent=2)+'\n```\n')
    return en,zh
if __name__=='__main__':main()
