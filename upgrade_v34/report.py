"""Generate bilingual reports only from independently audited completed runs."""
import json
import numpy as np
from run_comparators import HERE,save
from public_client import ledger_total


def main():
    a=json.loads((HERE/'results/audit.json').read_text())
    required=('proposal','test','rxqa','medqa')
    assert all(all(s in a['author_methods'][m] for s in required) for m in ('medagents','mdagents'))
    assert len(a['transfer'])==3
    old=json.loads((HERE.parent/'upgrade_v17/results/summary.json').read_text())
    main_rows=[]
    for method,label in [('medagents','MedAgents (author workflow adapter)'),('mdagents','MDAgents (author workflow adapter)')]:
        x=a['author_methods'][method]['test'];y=a['author_methods'][method]['rxqa']
        main_rows.append(f"| {label} | {x['correct']}/988 ({100*x['accuracy']:.2f}%) | {y['correct']}/300 ({100*y['accuracy']:.2f}%) | {x['mean_calls']:.2f} / {y['mean_calls']:.2f} |")
    for method,label in [('cot','CoT'),('author_grasp','GRASP author core'),('evolving_grounded','RxRSIAgent retained checkpoint')]:
        x=old['datasets']['rxsafebench']['methods'][method];y=old['datasets']['rxqa']['methods'][method]
        main_rows.append(f"| {label} | {x['correct']}/988 ({100*x['accuracy']:.2f}%) | {y['correct']}/300 ({100*y['accuracy']:.2f}%) | 1 / 1 |")
    main_table='\n'.join(['| Method | RxSafeBench | RxQA | Mean calls: RxSafe / RxQA |','|---|---:|---:|---:|']+main_rows)
    rows=[]
    for r in range(5):
        entries=[]
        for seed in ('42','137','2026'):
            t=a['transfer'][seed][r];entries.append(f"{t['skills']} / {t['metrics']['correct']}")
        rows.append(f"| {r} | {[0,156,312,468,625][r]} | "+' | '.join(entries)+' |')
    curve='\n'.join(['| Round | Unique training cases | Seed42: skills / MedQA correct | Seed137 | Seed2026 |','|---:|---:|---:|---:|---:|']+rows)
    rows=[]
    for method,label in [('medagents','MedAgents'),('mdagents','MDAgents')]:
        d=a['author_methods'][method]['medqa'];rows.append(f"| {label} | {d['correct']}/200 | {100*d['accuracy']:.2f}% | {d['mean_calls']:.2f} |")
    rows.append('| Empty memory control | 166/200 | 83.00% | 1 |')
    for seed in ('42','137','2026'):
        t=a['transfer'][seed][-1];m=t['metrics'];rows.append(f"| Scoped-memory candidate, seed{seed} | {m['correct']}/200 | {100*m['correct']/200:.2f}% | {m['calls']/200:.2f} |")
    transfer_table='\n'.join(['| Method | MedQA correct | Accuracy | Mean calls |','|---|---:|---:|---:|']+rows)
    effects=[]
    for seed in ('42','137','2026'):
        t=a['transfer'][seed][-1]['versus_initial'];effects.append(f"| {seed} | {100*t['difference']:+.2f} | [{100*t['ci95'][0]:+.2f}, {100*t['ci95'][1]:+.2f}] | {t['fixes']} / {t['regressions']} |")
    effect_table='\n'.join(['| Seed | Transfer gain (pp) | Paired95% interval (pp) | Fixes / regressions |','|---:|---:|---:|---:|']+effects)
    protocol=json.loads((HERE/'protocol.json').read_text());spend=ledger_total()-protocol['ledger_start_usd']
    mean_gain=100*np.mean([a['transfer'][s][-1]['versus_initial']['difference'] for s in ('42','137','2026')])
    summary={'status':'complete_audited','engineering_target_pp':10,'target_met':False,
        'mean_transfer_gain_pp':float(mean_gain),'new_task_n':200,'training_unique_cases':625,'learning_seeds':[42,137,2026],
        'incremental_successful_response_ledger_usd':spend,
        'baseline_source':'Author workflow adapters with explicitly documented task/transport/parser and MDAgents corrections; not official-paper score reproduction',
        'uncompleted':['SafeRx-Agent same-task reproduction','matched-total-budget medical-agent comparison','equal-data retrieval/shuffled-feedback controls','clinical prescription quality annotation'],
        'selected_main_profile_changed':False}
    save(HERE/'results/summary.json',summary)
    en=f'''# Medical-agent comparisons and counterexample-scoped skill learning

Date:2026-10-16. Completed and independently audited. **The +10 percentage-point engineering target is not met.** No large-gain or mature-RSI claim is made.

## 1. Executed named methods

{main_table}

All rows share the DeepSeek V4.1 Flash identifier and question identities. Budgets differ. MedAgents uses its author five-stage syn_verif workflow, original stage limits and up to3 voting rounds. MDAgents uses its author adaptive workflow,1024 output tokens/call and zero demonstrations on these new tasks. Both have explicit80-call/24000-output-token per-case ceilings. Legacy controls use one512-token call. Therefore this table supplies missing method measurements, not an equal-compute superiority test. SafeRx-Agent remains unexecuted under this protocol; its ATC medication-set task must not be conflated with QA.

Sources: [MedAgents author repository](https://github.com/gersteinlab/MedAgents), [MDAgents author repository](https://github.com/mitmedialab/MDAgents). Pins, source hashes and all adaptations are in [protocol.json](protocol.json). Source repositories remain unmodified; the adapter loads pinned functions and applies declared repairs. This is an author-workflow task adaptation, not reproduction of an original paper's score.

Development preflight fixed quoted-answer parsing, MDAgents recruitment formatting and missing initial/final report handling. The same medication-choice task instruction was added to both author adapters for raw RxSafe consultations. Original debug runs and protocol hashes are retained; official test scoring starts only after [comparison freeze](comparison_freeze.json). Invalid/budget-exhausted received trajectories are included in the denominator; transport failures cannot be scored as model errors.

Development inspection also identifies explicit claims that no listed option is appropriate. These are not empty API outputs. The audit distinguishes empty final text from no-valid-option assertions; a model assertion does not establish that the reference is wrong. Both remain scored under the frozen forced-choice protocol, with clinical adjudication still needed for disputed items.

## 2. What actually evolved?

Only procedural memory cards changed. Model weights, source tools and optimizer code stayed fixed. Each card has observable positive conditions, exclusion conditions, a procedure, training-error support IDs and distinct successful counterexample IDs. At inference, a TF-IDF shortlist feeds a semantic router; at most2 cards can activate, each with an exact input quotation. The model checks exclusion conditions; this is not a proven clinical-rule validator. Activated cards include one training support and one contrasting example.

Four rounds expose156/312/468/625 unique training cases. Proposal190 and guard197 must both improve correct count without increasing invalid outputs. Every rejection is retained. Three seeds change training order; they are not three independent test cohorts. A development-only schema repair clarified case roles and allows one failed-schema correction. All three trajectories were restarted under the same repaired implementation before any MedQA inference; initial trajectories remain in development_history.

{curve}

Identical retained states reuse identical responses; flat repeated points are not new stochastic replications. The retained artifacts contain one general interaction/contraindication procedure in seed42, none in137, and two selection procedures in2026. One2026 procedure prefers a named active ingredient when relevant; this presents a shortcut-learning concern despite its exclusions and must not be treated as validated medical guidance.

## 3. Independent-task transfer

Two hundred MedQA questions were frozen by question-text hash before learning, excluding normalized exact overlap with the existing public cases. No answer, difficulty or method outcome selected them. They are general medical-reasoning questions, not a full-prescription benchmark; model pretraining exposure and semantic duplication are not ruled out. All three final trajectories were frozen before evaluation, and no test-selected seed replaces the main method.

{transfer_table}

{effect_table}

Mean gain across the three observed training orders is **{mean_gain:.2f}pp**. These gains are too small for the declared target. The active-memory arm also adds a router call; equal-data retrieval and matched-budget refinement/shuffled-feedback controls are still required for a causal learning claim. We do not promote the candidate or replace the incumbent main-table checkpoint based on these scores.

## 4. Large-gain acceptance and next work

The engineering objective is +10 absolute points over the strongest fully executed same-task comparator, with a matched-budget analysis, independent-task confirmation, paired intervals and three training seeds. It is a target, not a promised outcome. A large gain over a weak or broken adapter is not sufficient.

The next mechanism should address missing evidence and executable clinical actions: candidate-balanced and formulation-aware evidence, explicit patient-fact requirements, and source-backed calculations/verification. Updates need support/counterexample execution tests and separate measurements for autonomous changes and researcher fixes. Further unconstrained textual-card growth is not supported by this experiment. Complete the missing compute/data controls and clinical endpoints before a superiority or prescribing-safety claim. Neither an unavailable resource nor an unassessed safety dimension is counted as a pass.

## 5. Artifacts and cost

[Runner](run_comparators.py) · [Author adapters](medical_agents.py) · [Memory implementation](scoped_memory.py) · [Learning runner](run_memory.py) · [Independent audit](results/audit.json) · [Summary](results/summary.json).

Incremental successful-response ledger: approximately **USD{spend:.3f}**, including development/debug runs; this is not a reconciled provider bill. Logical per-method usage includes exact cache reuse. Only public QA was sent. Restricted records and raw receipts remain local. Earlier paused queues were not resumed.
'''
    zh=f'''# 医学 agent 实测对照与带反例的技能进化

日期：2026-10-16。状态：本轮已完成并独立复核。**尚未达到相对最强基线+10个绝对百分点的工程目标，不能作为成熟RSI成果交付。**

## 1. 不再只有 GRASP：新增真实方法结果

{main_table}

相同DeepSeek V4.1 Flash标识、相同题目，但调用预算不同。MedAgents保留作者五阶段流程和最多3轮投票；MDAgents保留作者自适应流程，每次最多1024输出token，新任务不提供示例。两者均有每题80次调用／24000输出token上限。旧对照每题一次512-token调用。因此这里补齐了两个医学方法的实测数据，尚未完成严格等计算预算比较。SafeRx-Agent仍未在同协议运行，其ATC药物集合任务不能直接当作问答结果。

[MedAgents作者代码](https://github.com/gersteinlab/MedAgents) · [MDAgents作者代码](https://github.com/mitmedialab/MDAgents)。提交、哈希和适配说明见[协议](protocol.json)。调用固定作者函数，明确记录适配器修改；不把这些数值称为原论文分数复现。

开发接入阶段修复了带引号的答案解析、团队招募格式，以及MDAgents初始／最终报告传递问题；为两种作者方法的RxSafe原始对话补上与我们相同的药物选择任务说明。旧调试结果和协议哈希全部保留，[正式测试前冻结](comparison_freeze.json)。收到的无效答案和预算耗尽记入分母；传输失败不当作模型答错。

开发检查还发现部分无效答案是在明确表达“这些选项都不适合”，并非空输出。审计分别记录空文本与此类回答；模型质疑不证明参考标签错误，仍按冻结的强制选择协议计分。争议项需要另行核验临床合理性，不能仅凭标签一致性作出临床结论。

## 2. 进化了哪些东西？

本轮只更新**程序性技能记忆**；没有更新模型权重、工具源代码或学习算法。每张卡有适用条件、排除条件、处理步骤、训练错误支持案例和不同的成功反例。运行时先按文本相似度取最多4张卡，再由语义路由器选择最多2张；激活必须引用当前输入中的真实原文。排除条件仍由模型判断，不是已验证的临床规则引擎。

三种训练顺序各四轮，累计156／312／468／625个唯一训练病例；190题proposal与197题guard都必须提高正确数且不增加无效输出，才能保留更新。提案器曾混淆支持／反例角色，已在开发阶段增加明确角色与一次格式修复，并在独立评测前用统一修复重新运行三个种子。初始失败记录保留在development_history。

{curve}

表中后面三列为“保留技能数／MedQA正确题数”。未改变的状态复用相同答案，不是重复独立采样。种子42保留一条交互／禁忌检查程序，137没有更新通过门槛，2026保留两条选择程序。2026中的“优先考虑对话中已提到的成分”存在利用题目线索的风险；即使带排除条件，也不能视为已验证医学知识。

## 3. 独立任务验证：有小幅收益，但不够

MedQA的200题在学习前按题干哈希冻结，排除与既有公开题的标准化全文完全重复；选择不使用标签或方法表现。它评估一般医学推理，不等于完整处方能力，也无法排除模型预训练见过这些题或语义重复。三个种子的完整状态冻结后才开始测试，不按测试结果挑最好种子。

{transfer_table}

{effect_table}

三个训练顺序平均提升 **{mean_gain:.2f}个百分点**。这不满足大幅提升目标。带技能运行还增加了一次路由调用，等数据检索、等预算反思、打乱反馈对照仍需补充，不能把全部差异归因于学习。此次候选不替换原主表配置。

## 4. 怎样判定下一次是真正有价值的升级？

- 主任务相对最强完整实测方法，争取**+10个绝对百分点**；不是只超过一个较弱对照。
- 同时报告等预算结果、配对区间、三种训练顺序和独立任务迁移。
- 处方错误与安全相关终点不能用问答准确率替代；未知项目不能算通过。
- 下一步着重补充可用证据和可执行的处方操作：候选药均衡检索、剂型／途径核验、患者事实前提、带来源的计算和核验工具；每次更新必须用支持病例和反例验证，并分开报告自主更新与人工工程修复。

本轮结果不支持继续无限增加通用文字技能。上述大幅提升仍是研究目标，不能承诺必然达到。

## 5. 交付

[作者方法运行器](run_comparators.py) · [适配器](medical_agents.py) · [技能实现](scoped_memory.py) · [逐轮学习](run_memory.py) · [独立审计](results/audit.json) · [汇总](results/summary.json)。

新增成功响应费用账本约 **${spend:.3f}**，包含接入调试，未与供应商账单对账。方法逻辑费用包含缓存复用。只发送公开问答，受限病例和原始响应未提交GitHub，旧长期队列仍暂停。
'''
    (HERE/'RESULTS.en.md').write_text(en)
    (HERE/'RESULTS.zh.md').write_text(zh)
    print(json.dumps(summary))


if __name__=='__main__':main()
