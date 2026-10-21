"""Bilingual aggregate results and in-place English manuscript update."""
import json,re
from common53 import *
def main():
    r=json.loads((HERE/'results/audit.json').read_text());cost=json.loads((HERE/'results/compute.json').read_text());review=json.loads((HERE/'results/review_package.json').read_text());dev=json.loads((HERE/'results/development_bottleneck.json').read_text())
    def m(model,name='rxrsi_library_53'):return r['metrics'][model][name]['metrics']
    def fmt(v):return f'{v:.3f}'
    methodnames={'fixed':'Frozen LLM agent','contract_fallback':'Fixed contract fallback (not RSI)','rxrsi_library_53':'RxRSIAgent / order53','rxrsi_library_153':'RxRSIAgent / order153','rxrsi_library_253':'RxRSIAgent / order253','supervised_draft':'Frozen supervised draft','library_feedback_replay':'Raw feedback correction replay','unscoped_53':'Learned actions without conditions','rxrsi_library_53-shuffled':'Shuffled reflection feedback'}
    table=['| Backbone / method | Drug F1 % | Native4 F1 % | Missed / patient ↓ | Extra / patient ↓ | Joint discrepancy / patient ↓ |','|---|---:|---:|---:|---:|---:|']
    for model in ['qwen','llama']:
        for name,label in methodnames.items():
            z=m(model,name);table.append(f'| {model} / {label} | {100*z["drug_f1"]:.2f} | {100*z["joint_f1"]:.2f} | {fmt(z["missed_drugs_per_patient"])} | {fmt(z["extra_drugs_per_patient"])} | {fmt(z["joint_errors_per_patient"])} |')
    rounds=['| Round | Feedback cases | Rules | Exceptions | Qwen drug F1 % | Missed | Extra | Joint |','|---:|---:|---:|---:|---:|---:|---:|---:|']
    seq=r['trajectories']['qwen']['library_53']
    for x in seq:
        z=x['metrics'];rounds.append(f'| {x["round"]} | {x["feedback"]} | {x["rules"]} | {x["exception_rules"]} | {100*z["drug_f1"]:.2f} | {fmt(z["missed_drugs_per_patient"])} | {fmt(z["extra_drugs_per_patient"])} | {fmt(z["joint_errors_per_patient"])} |')
    intervals=['| Model / order | Δ missed [95% CI] | Δ extra [95% CI] | Δ joint [95% CI] | Patients with any worsened component |','|---|---|---|---|---:|']
    for model in ['qwen','llama']:
        for seed in [53,153,253]:
            p=r['metrics'][model]['rxrsi_library_'+str(seed)]['paired']
            cols=[f'{v:+.4f} [{ci[0]:+.4f}, {ci[1]:+.4f}]' for v,ci in zip(p['error_delta'],p['error_ci95'])]
            intervals.append('| '+model+' / '+str(seed)+' | '+' | '.join(cols)+f' | {p["component_harmed_patients"]} |')
    strata=['| Model / stratum | Baseline → final drug F1 % | Baseline → final missed | Baseline → final extra | Baseline → final joint |','|---|---:|---:|---:|---:|']
    for model in ['qwen','llama']:
        for group in ['one_system','multiple_systems']:
            a=r['metrics'][model]['fixed']['strata'][group];b=r['metrics'][model]['rxrsi_library_53']['strata'][group]
            vals=[f'{100*a["drug_f1"]:.2f} → {100*b["drug_f1"]:.2f}']+[f'{a[k]:.3f} → {b[k]:.3f}' for k in ['missed_drugs_per_patient','extra_drugs_per_patient','joint_errors_per_patient']]
            strata.append('| '+model+' / '+group+' | '+' | '.join(vals)+' |')
    c=r['ceiling'];q0=m('qwen','fixed');q1=m('qwen');l0=m('llama','fixed');l1=m('llama')
    def endpointtext(z):return ', '.join(fmt(z[k]) for k in ['missed_drugs_per_patient','extra_drugs_per_patient','joint_errors_per_patient'])
    decoder_table=['| Backbone | Syntax failure | Responses with unknown IDs | Empty output | Empty with nonempty target |','|---|---:|---:|---:|---:|']
    for model,d in r['decoding'].items():decoder_table.append(f'| {model} | {d["syntax_failure"]}/{d["cases"]} | {d["any_unknown_ids"]}/{d["cases"]} | {d["empty_outputs"]}/{d["cases"]} | {d["empty_with_nonempty_target"]}/{d["cases"]} |')
    common='\n'.join(table)+'\n\n## Frozen round trajectory / 冻结的逐轮轨迹\n\n'+'\n'.join(rounds)+'\n\n![All frozen streams](results/retention.png)\n\n## Paired uncertainty / 配对不确定性\n\n'+'\n'.join(intervals)+'\n\n## Recorded disease-system strata / 记录的疾病系统分层\n\n'+'\n'.join(strata)+'\n\n## Output contract / 输出协议\n\n'+'\n'.join(decoder_table)+'\n'
    en=f'''# RxRSIAgent: order-specific memory on256 new patients

**The full hypothesis remains unsupported.** This is a completed experiment, not a promised result. Three case orders retain5,4,4 rules, all deletions and none with empirical exception clauses. The first prespecified stream changes Qwen drug F1 from {100*q0['drug_f1']:.2f}% to {100*q1['drug_f1']:.2f}%; Llama changes from {100*l0['drug_f1']:.2f}% to {100*l1['drug_f1']:.2f}%. A gain in F1 or fewer extra tuples does not establish simultaneous improvement in all three errors.

## Design and scope

- Audit256 new patients, disjoint from all prior v25/v52 members. Both backbones run on all256. Reuse192 reflection/64 proposal/64 guard patients for development; those sets were already exposed.
- Six cumulative32-case rounds under seeds53/153/253. Qwen-derived programs transfer unchanged to Llama. This is not independent learning under two backbones or an estimate across arbitrary models.
- Frozen prompt, catalogue, actor weights, output cap and complete-JSON decoder. All local actors use one256-token call; postprocessing controls reuse exactly the same responses. Equal LLM generation does not mean identical information, extra tool work or supervision.
- New/changed **recorded** orders at hours6–12, not the full treatment plan. Native4 is HICL/route/dosage-string/frequency-string; exact mismatches do not establish clinical errors.
- The learner induces drug-specific programs over diagnostic paths and prior-record status. Statistical conditions require clinical review; removal means omitting a predicted future event, not stopping a patient's medication.
- Templates initially require3 reflection patients. A pre-outcome amendment uses3,815 old-training templates with at least3 distinct-patient support,125 encountered in reflection. Fourteen new field-repair candidates pass reflection but do not reduce aggregate proposal errors; retained programs are unchanged. No support/gate threshold was relaxed.

## Completed comparison

{common}
All round states were frozen before audit outcomes. These are repeated measurements of the same256 patients, not independent256-patient experiments per round. The displayed95% intervals are marginal; `results/audit.json` also reports one-sided Bonferroni bounds over36 error/design/order/model tests. No favorable stream or checkpoint was selected. The static contract fallback raises Llama drug F1 from4.58% to6.72%, but increases extra and joint discrepancies; it also slightly worsens Qwen. It remains opt-in, with no experimental memory, and is not counted as RSI or promoted by its F1 gain.

## What changed, and what did not

- External memory grew; no LLM weights, pharmacological knowledge or executable interpreter code evolved autonomously.
- The two template-bank designs retain identical programs. The shuffled-reflection control keeps true proposal/guard labels, so any gain there can be supplied by development selection.
- Actor catalogue coverage is {c['catalogue_target_drugs']}/{c['target_drugs']} drug targets ({100*c['catalogue_target_drugs']/max(1,c['target_drugs']):.2f}%) and {c['catalogue_target_complete_tuples']}/{c['target_complete_tuples']} complete reference tuples ({100*c['catalogue_target_complete_tuples']/max(1,c['target_complete_tuples']):.2f}%). Added template access is not proof of useful template selection.
- Qwen shared-drug field mismatches: {q0['wrong_shared_tuples']}/{q0['shared_reference_tuples']} before, {q1['wrong_shared_tuples']}/{q1['shared_reference_tuples']} after. A changed denominator must be read with omissions; removing identities is not a dose repair.
- Two fixed local backbones, three orders, sparse labels and reused gates do not establish stable model-independent prescribing improvement. Multiple-system membership is not validated chronic multimorbidity.

## Appropriateness and deliverables

Three source-backed partial label tools now preserve unknown facts and distinguish initiation from continuation. Only1/1,836 final Qwen order rows receives partial checks, with all3 findings unknown. This very low coverage does not satisfy a full appropriateness audit. They run as preflight findings in `runtime.py`; they do not modify the frozen benchmark orders or certify clinical safety. See [sources and research](RESEARCH.en.md).

A local two-reviewer, method-blinded package contains32 random stratified patients and {review['unique_skills']} unique rules. Sources are masked, presentation randomized, identical plans deduplicated; original recorded orders are also reviewed. **Completed annotations:0.** The [rubric](REVIEW_PROTOCOL.en.md) reports assessable denominators and missing-context rates. Case-level illustrations and all patient-derived rules remain restricted in `prismatic-v53/CASE_STUDIES.md` and `review/`.

New API spend: **USD0**. New local calls: {cost['new_calls']}; input/output tokens {cost['input_tokens']:,}/{cost['output_tokens']:,}. Local compute is unpriced. The standing USD10 budget has USD0.085203 spent on the earlier aggregate-only proposer and USD9.914797 remaining; historical located response costs of approximately USD89.53 precede that cap.

## Next evidence needed

The observed failure has narrowed: template access improves, but condition-to-action transfer and productive repairs do not follow. Next work must obtain defensible treatment intent and active disease evidence; learn additions/field repairs that actually execute on independent cases; compare them against raw feedback memory; and complete blinded appropriateness/skill review. Do not tune further on these now-exposed256 patients or call rule accumulation clinical RSI.
'''
    zh=f'''# RxRSIAgent：256位新患者的订单级记忆实验

**完整命题仍未得到支持。** 本轮已经跑完实验。三种病例顺序分别保留5、4、4条规则，全部是删除，没有保留带实证反例的规则。首个预设顺序下，Qwen 药物F1从 {100*q0['drug_f1']:.2f}% 变为 {100*q1['drug_f1']:.2f}%；Llama 从 {100*l0['drug_f1']:.2f}% 变为 {100*l1['drug_f1']:.2f}%。F1提高或多余订单减少，均不能替代三类错误同时可靠下降的证据。

## 做了什么

- 新增256位患者，与此前v25/v52所有患者无重叠；两个模型均跑完整256位。开发复用192位反馈、64位proposal、64位guard，明确属于已暴露开发集。
- 六轮，每轮累计新增32个反馈病例；三种顺序53/153/253。把Qwen学到的程序原样迁移到Llama，没有针对Llama测试结果调参。
- 固定prompt、候选目录、权重、完整JSON解析器；每个模型每个患者一次256-token上限调用。后处理复用同一输出；相同LLM调用量不等于监督信息和工具计算完全相同。
- 目标是入ICU后第6—12小时实际记录的新增/修改订单，不是患者全部治疗方案。Native4为HICL、途径、剂量字符串、频次字符串；字符串不匹配不直接等于临床错误。
- 学习内容由粗疾病类别改成具体诊断路径、目标药物、既往记录状态与增补/删除/字段替换。删除操作只是取消预测的未来订单，不能解释为临床停药建议。
- 发现反馈稀疏后，在看测试指标之前，引入3815种旧训练集重复联合模板；当前反馈可使用的模板由2增至125。新增14个字段修复候选均未降低proposal集的汇总错误数，因此保留状态不变。没有放宽验证门槛。

## 完整对比

{common}
上述轮次共享同一256位独立患者，不是每轮新增256位独立实验。表中为边际95%配对区间；JSON另含36项错误/方案/顺序/模型检验的Bonferroni单侧上界。所有状态在读取测试指标前冻结，未选择测试分数最好的一轮。固定解析回退使Llama药物F1从4.58%升至6.72%，但多开和联合差异增加，Qwen也略有退步；因此保持显式可选，不默认推广，也不计作RSI。

## 这轮能证明什么

1. 外部规则记忆确实发生了变化；但没有自主修改LLM权重、发现药理知识或生成新的工具代码。
2. 扩充联合模板没有改变最终规则；问题从“拿不到模板”进一步定位到“条件能否迁移并触发正确修复”。
3. 首个顺序Qwen的三类错误/患者是 `{endpointtext(q0)}` → `{endpointtext(q1)}`，Llama为 `{endpointtext(l0)}` → `{endpointtext(l1)}`。不能只挑下降的一项。
4. 候选目录覆盖 {c['catalogue_target_drugs']}/{c['target_drugs']} 个GT药物（{100*c['catalogue_target_drugs']/max(1,c['target_drugs']):.2f}%）、{c['catalogue_target_complete_tuples']}/{c['target_complete_tuples']} 个完整GT订单（{100*c['catalogue_target_complete_tuples']/max(1,c['target_complete_tuples']):.2f}%）。
5. Qwen共同药物上的字段错误从 {q0['wrong_shared_tuples']}/{q0['shared_reference_tuples']} 变为 {q1['wrong_shared_tuples']}/{q1['shared_reference_tuples']}；分母变化须与漏开一起看，不能把删药当作剂量修复。
6. 打乱反馈对照仍使用真实proposal/guard标签，其收益可能来自开发集筛选。两个小模型、三种顺序不能证明任意模型稳定受益；多系统分组也不等于经过验证的慢性多病共存。

## 适当性审查与交付

已接入三种带说明书来源的局部核验工具：保留信息未知状态，区分首次与继续用药，并由 `runtime.py` 返回预筛记录。实际仅覆盖Qwen最终1836条订单中的1条，三个核验项全部返回未知，远未达到完整适当性审查。这是固定工具工程，不计入学习收益；没有改变已冻结实验订单，也不构成临床安全认证。详见[调研与设计](RESEARCH.zh.md)。

双人盲评包包含32位分层随机患者和 {review['unique_skills']} 条唯一规则，隐藏方法来源、随机展示、合并相同方案，并纳入实际记录订单。**已完成临床标注：0。** [评分规程](REVIEW_PROTOCOL.zh.md)明确可评估分母与信息缺失比例。真实失败案例位于本地受限目录 `prismatic-v53/CASE_STUDIES.md`；病例包和规则正文未上传GitHub。

本轮新增API费用 **$0**；本地新推理 {cost['new_calls']} 次，输入/输出token为 {cost['input_tokens']:,}/{cost['output_tokens']:,}，本地算力未折算价格。当前$10额度此前已用$0.085203，剩余$9.914797；此前全部研究可定位响应费用约$89.53另计，不能把本地推理说成零总成本。

## 下一步应该补的证据

需要具有时间依据的治疗意图与活跃疾病证据，使补漏和字段修复能在独立病例真正执行；需要超过原始反馈回放；需要两位评审者完成技能与处方适当性标注。上述256位测试患者现已暴露，后续调优不能继续把它们称为独立确认集。当前默认研究运行时仍不推广实验技能库。
'''
    (HERE/'RESULTS.en.md').write_text(en);(HERE/'RESULTS.zh.md').write_text(zh)
    paper=ROOT/'paper/latex/v0.3/prismatic_v03_en.tex';source=paper.read_text()
    tabletex=[]
    for model in ['qwen','llama']:
        for name,label in [('fixed','Frozen actor'),('rxrsi_library_53','RxRSIAgent'),('library_feedback_replay','Feedback replay'),('supervised_draft','Supervised tool')]:
            z=m(model,name);tabletex.append(f'{model.capitalize()} / {label} & {100*z["drug_f1"]:.2f} & {100*z["joint_f1"]:.2f} & {z["missed_drugs_per_patient"]:.3f} & {z["extra_drugs_per_patient"]:.3f} & {z["joint_errors_per_patient"]:.3f}'+r'\\')
    roundtex=[]
    for x in seq:
        z=x['metrics'];roundtex.append(f'{x["round"]} & {x["feedback"]} & {x["rules"]} & {x["exception_rules"]} & {100*z["drug_f1"]:.2f} & {z["missed_drugs_per_patient"]:.3f} & {z["extra_drugs_per_patient"]:.3f} & {z["joint_errors_per_patient"]:.3f}'+r'\\')
    robust=[]
    for model in ['qwen','llama']:
        for seed in [53,153,253]:
            p=r['metrics'][model]['rxrsi_library_'+str(seed)]['paired'];a=p['error_delta'];robust.append(f'{model.capitalize()} / {seed} & {a[0]:+.4f} & {a[1]:+.4f} & {a[2]:+.4f} & {p["component_harmed_patients"]}'+r'\\')
    section=r'''\subsection{Order-specific memory and retention on new patients}\label{sec:conditional-memory}
We test a bounded prescription-memory learner on256 new eICU patients, excluded from the frozen tool-development cohort and the preceding conditional-memory study. Both local backbones run on every patient. Learning reuses192 feedback,64 proposal and64 guard patients that were previously exposed during development; this is not a new development split. Audit patients come from an old development-hospital partition and therefore do not establish unseen-institution generalization.

\paragraph{Clinical observability and task.} Inputs include diagnoses entered by ICU hour6, prior orders and laboratory results revised by the cutoff. Active/resolved disease status, treatment intent and a complete allergy history are unavailable. Targets are recorded orders entered at hours6--12, including zero-target stays, not all clinically necessary treatment. Native4 denotes HICL identity, route, dosage string and frequency string; exact discrepancies are reference-relative. Half the audit has multiple disease-system categories, an operational stratum rather than validated chronic multimorbidity.

\paragraph{Feedback-induced programs.} Six cumulative32-case rounds are run under three randomized case orders. The fixed symbolic learner induces a target drug, a diagnostic-path condition, optional prior-record status, an add/remove/replace action, and empirical exceptions. Paths use at least two diagnostic hierarchy levels. Missing prior documentation is not evidence of no therapy. Harmful examples are applications worsening any error component; exceptions require at least two such feedback examples. Programs execute without reference access. This is supervised external program-memory induction, not LLM weight adaptation or autonomous invention of clinical tool code.

Each candidate requires at least4 applicable and3 helped feedback patients. Reflection and proposal must reduce total discrepancy without increasing any primary component. The separate guard rejects any aggregate increase and any individual increase in missed drugs, and requires an actual changed order. At most3 candidates reach the guard and one is retained per round; rejected state--program pairs are cached. These statistical gates do not certify clinical suitability. Every round freezes before audit outcomes, and Qwen-derived programs transfer unchanged to Llama.

\paragraph{Template bottleneck and development amendment.} Only2 complete tuples recur in at least3 reflection patients. Before audit outcomes were read, an amendment supplies3,815 old-training templates supported by at least3 distinct patients;125 have appeared in reflection. No gate is relaxed, and a replay comparator has the same template resource. Fourteen additional field-repair candidates qualify on reflection but do not reduce aggregate proposal errors. Across896 candidate--case checks,787 fail the condition,97 lack the target drug in the draft, and12 alter a tuple without changing any primary error count. The retained programs are identical under both template banks. The amendment follows the start of audit generation but precedes outcome inspection.

\begin{figure*}[t]\centering
\begin{tikzpicture}[x=1cm,y=1cm,>=Stealth,b/.style={draw,rounded corners,align=center,text width=2.55cm,minimum height=1.1cm,font=\small}]
\node[b](a) at(0,0){Hour6 context\\diagnosis paths\\prior records + labs};
\node[b](b) at(3.4,0){Frozen local actor\\training-only retrieval\\joint-order draft};
\node[b](c) at(6.8,0){Executable memory\\drug + when / unless\\add / remove / replace};
\node[b](d) at(10.2,0){Source-based preflight\\typed facts / unknowns\\research output};
\draw[->](a)--(b);\draw[->](b)--(c);\draw[->](c)--(d);
\node[b](e) at(0,-2){Feedback discrepancies\\missing / extra drugs\\joint-field mismatch};
\node[b](f) at(3.4,-2){Error-pattern induction\\support + countercases\\candidate programs};
\node[b](g) at(6.8,-2){Proposal + guard\\component constraints\\retain / reject};
\node[b](h) at(10.2,-2){Frozen-state audit\\new patients / orders\\backbones + reviewers};
\draw[->](e)--(f);\draw[->](f)--(g);\draw[->](g)--(h);\draw[->](g.north)--(c.south);
\end{tikzpicture}
\caption{RxRSIAgent's executed order-memory workflow. The interpreter and clinical preflight are fixed engineering; external programs are learned. Human review is prepared but pending. Audit outcomes never select programs.}\label{fig:conditional-memory}
\end{figure*}

\begin{table*}[t]\centering\small
\caption{Same256 new patients for both backbones. RxRSIAgent uses the first prespecified case order; no best-stream selection. F1 is a percentage; errors are counts/patient. All postprocessing controls reuse identical actor responses, but their supervision and computation differ.}\label{tab:conditional-memory}
\begin{tabular}{@{}lrrrrr@{}}\toprule
Method & Drug F1 & Native4 F1 & Missed & Extra & Joint errors\\\midrule
'''+ '\n'.join(tabletex)+r'''
\bottomrule\end{tabular}\end{table*}
\begin{table*}[t]\centering\small
\caption{Frozen Qwen trajectory for the first prespecified stream. All rows reuse the same audit patients.}\label{tab:conditional-rounds}
\begin{tabular}{@{}rrrrrrrr@{}}\toprule
Round & Feedback & Rules & Exceptions & Drug F1 & Missed & Extra & Joint\\\midrule
'''+ '\n'.join(roundtex)+r'''
\bottomrule\end{tabular}\end{table*}
\begin{table*}[t]\centering\small
\caption{Final changes relative to each frozen actor across all prespecified case orders; negative error changes are better. Harmed means any primary component increased, not adjudicated clinical harm.}\label{tab:order-retention}
\begin{tabular}{@{}lrrrr@{}}\toprule
Backbone / order & $\Delta$ missed & $\Delta$ extra & $\Delta$ joint & Harmed patients\\\midrule
'''+ '\n'.join(robust)+r'''
\bottomrule\end{tabular}\end{table*}

\paragraph{Growth versus retained capability.} The three streams retain5,4,4 programs, all removals; no empirical exception survives. Consequently, this study does not demonstrate learned additions, joint-field repairs or clinically valid counterexamples. Removing an extra tuple can lower joint symmetric difference without improving the fields of any correctly chosen drug. Conditions refer to recorded disease paths, but their relationship to a medication's indication has not been established. The raw-feedback replay and scope-removal controls distinguish memory accumulation from useful conditional consolidation; shuffled reflection retains true development labels and cannot isolate learning from gate selection.

'''+f'Catalogue reachability is {c["catalogue_target_drugs"]}/{c["target_drugs"]} target drugs and {c["catalogue_target_complete_tuples"]}/{c["target_complete_tuples"]} complete target tuples. Qwen shared-identity field mismatches are {q0["wrong_shared_tuples"]}/{q0["shared_reference_tuples"]} before and {q1["wrong_shared_tuples"]}/{q1["shared_reference_tuples"]} after; denominator changes must be interpreted with omissions. '+r'''The aggregate release includes all rounds, single/multiple-system strata,4,000 paired patient-bootstrap draws, marginal95\% intervals and conservative one-sided Bonferroni bounds across36 error/design/order/backbone comparisons. The strong claim requires all three errors to reliably decrease, meaningful learned exceptions and completed clinical review; it is not supported. Small models, reused gates and the sparse event-forecasting target limit generalization.

\paragraph{Appropriateness remains a separate endpoint.} A fixed preflight implements partial metformin, enoxaparin and eplerenone label checks with typed, time-qualified measurements\citep{labelchecks}. Unknown measurements never imply normal function; treatment initiation is not inferred from an absent prior record. Only1 of1,836 final Qwen order rows is covered by these partial checks, and all three resulting findings are unknown;1,835 rows are not covered. These checks do not alter the frozen benchmark predictions or certify full safety. Sixteen synthetic boundary tests verify implementation only. A two-reviewer, method-blinded review package contains32 randomly stratified patients and unique retained rules, following a WHO/MAI-informed research rubric\citep{whoprescribing,mai}. It hides method identity, deduplicates identical plans and includes recorded orders. No clinical annotations have been returned. A separate fixed contract fallback increases Llama F1 but also increases extra and joint discrepancies; it remains opt-in and is not an RSI gain. Experimental memory is not promoted to the default runtime. New paid API spend is USD0; local compute is unpriced.

'''
    start=source.index(r'\subsection{Conditional executable memory on new patients}') if r'\subsection{Conditional executable memory on new patients}' in source else source.index(r'\subsection{Order-specific memory and retention on new patients}')
    end=source.index(r'\section{Clinical Scope and Limitations}',start)
    source=source[:start]+section+source[end:]
    abstract=f'''Can prescription agents learn conditional executable skills from case feedback and reduce omissions, extras and joint-order errors on new patients? We study this question with RxRSIAgent, task-specific workflows combining evidence tools, frozen language models and external program memory. Public-question results and local MIMIC-IV experiments do not establish superiority to the strongest controls. A new eICU audit evaluates256 previously unused patients with two local backbones and three six-round feedback orders. The learner retains5,4,4 drug-specific conditional programs, all deletions and none with retained empirical exceptions. In the first prespecified stream, Qwen drug F1 changes from {100*q0['drug_f1']:.2f}\\% to {100*q1['drug_f1']:.2f}\\%, and Llama from {100*l0['drug_f1']:.2f}\\% to {100*l1['drug_f1']:.2f}\\%. Expanding supported joint templates from2 to125 produces additional development candidates but no retained field repair. We separate missing drugs, extra drugs and complete-tuple discrepancies, include feedback-memory controls, and preserve uncertain clinical facts in source-based preflight tools. The experiments identify limits of sparse order-event feedback and conditional transfer, while leaving sustained, clinically appropriate prescription self-improvement unproved.'''
    source=re.sub(r'\\begin\{abstract\}.*?\\end\{abstract\}',lambda _:r'\begin{abstract}'+'\n'+abstract+'\n'+r'\end{abstract}',source,flags=re.S)
    marker='These mechanisms motivate experience-based prescription agents, but a stored reflection or a larger memory does not itself demonstrate transferable improvement.'
    addition=r' GuideSkill compiles and evolves executable diagnostic criteria, while SkillLearnBench and ContinualSkillBench distinguish skill quality, execution and outcomes and test benefits beyond retained feedback\citep{guideskill,skilllearn,continualskill}. These diagnostic and general-task results motivate our controls but are not prescription scores.'
    if addition not in source:source=source.replace(marker,marker+addition)
    refs=r'''
\bibitem[Cao et al.(2026)]{guideskill} Lang Cao et al. 2026. GuideSkill: Evolving Executable LLM Agent Skills for Guideline-Grounded Clinical Reasoning. \emph{arXiv:2607.26160}. \url{https://arxiv.org/abs/2607.26160}.
\bibitem[Zhong et al.(2026)]{skilllearn} Shanshan Zhong et al. 2026. SkillLearnBench: Benchmarking Continual Learning Methods for Agent Skill Generation on Real-World Tasks. \emph{arXiv:2604.20087}. \url{https://arxiv.org/abs/2604.20087}.
\bibitem[Guan et al.(2026)]{continualskill} Tianyi Guan et al. 2026. ContinualSkillBench: Can LLM Agents Truly Evolve Their Capabilities? \emph{arXiv:2608.03874}, version3. \url{https://arxiv.org/abs/2608.03874v3}.
\bibitem[WHO(2001)]{whoprescribing} World Health Organization. 2001. Teacher's Guide to Good Prescribing. WHO/EDM/PAR/2001.2. \url{https://iris.who.int/handle/10665/67010}.
\bibitem[DailyMed(2026)]{labelchecks} DailyMed. 2026. Product labels for metformin, enoxaparin and eplerenone. Accessed October21,2026. Source set identifiers and implemented scope are recorded in the released clinical-check module. \url{https://dailymed.nlm.nih.gov/}.
'''
    if '{guideskill}' not in source:source=source.replace(r'\end{thebibliography}',refs+r'\end{thebibliography}')
    # The citation command also contains {guideskill,...}, so exact bibitem key remains unambiguous.
    conclusion="RxRSIAgent connects reference discrepancies to executable programs and inspectable conditions. The completed experiments do not establish sustained prescription self-improvement or superiority to the strongest controls. On new patients, external memory grows, but retained updates remain deletions without learned empirical exceptions. Expanding supported joint templates does not produce retained additions or field repairs. Source-grounded preflight and blinded review preparation strengthen the evaluation contract; they are not evidence of autonomous clinical learning. Further claims require productive, clinically grounded updates, robust retention across patients and backbones, and completed appropriateness review. The present audit is now exposed and cannot serve as unseen confirmation for further tuning."
    source=re.sub(r'\\section\{Conclusion\}.*?(?=\\section\*\{Ethics and Reproducibility\})',lambda _:r'\section{Conclusion}'+'\n'+conclusion+'\n\n',source,flags=re.S)
    paper.write_text(source)
    for lang,text in [('en',en),('zh',zh)]:
        status=ROOT/'paper'/('RXRSI_PROOF_STATUS.'+lang+'.md')
        title='# Current prescription RSI evidence\n' if lang=='en' else '# 当前处方RSI证据\n'
        status.write_text(title+'\n'+('\n'.join(text.splitlines()[2:5]))+'\n\n'+f'[Full results / 完整结果](../upgrade_v53/RESULTS.{lang}.md) · [Research / 调研](../upgrade_v53/RESEARCH.{lang}.md) · [Review / 评审](../upgrade_v53/REVIEW_PROTOCOL.{lang}.md)\n\n'+'\n'.join(table)+'\n')
    print('Wrote bilingual results and updated the existing English ACL source in place.')
if __name__=='__main__':main()
