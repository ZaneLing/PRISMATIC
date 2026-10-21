"""Publish aggregate evidence only; private clinical case studies remain restricted."""
import datetime
from common52 import *
LABELS={'frozen_predictor':'Frozen supervised predictor','fixed_qwen':'Fixed Qwen prescription agent','qwen-52':'RxRSIAgent (case order A)','qwen-152':'RxRSIAgent (case order B)','qwen-52-shuffle':'Shuffled-feedback learner','tool-52':'Conditional repair of predictor (no LLM)','qwen_unscoped':'Learned repairs without scopes/exceptions','static_all_repairs':'Static all-repair bundle','llama_fixed_128':'Fixed Llama (128 patients)','llama_transfer_128':'Llama + frozen Qwen memory (128 patients)'}
def replace_block(path,block,marker):
 text=path.read_text();begin=f'<!-- {marker}:START -->';end=f'<!-- {marker}:END -->'
 if begin in text:text=text[:text.index(begin)]+text[text.index(end)+len(end):]
 lines=text.splitlines();lines.insert(2,begin+'\n'+block+'\n'+end+'\n');path.write_text('\n'.join(lines)+'\n')
def table(e):
 rows=['| Method | N | Drug F1 % | Native4 F1 % | Missed/patient ↓ | Extra/patient ↓ | Joint errors/patient ↓ |','|---|---:|---:|---:|---:|---:|---:|']
 for name,r in e['arms'].items():
  m=r['all'];rows.append(f"| {LABELS[name]} | {m['cases']} | {100*m['drug_f1']:.2f} | {100*m['joint_f1']:.2f} | {m['missed_drugs_per_patient']:.3f} | {m['extra_drugs_per_patient']:.3f} | {m['joint_errors_per_patient']:.3f} |")
 return '\n'.join(rows)
def curve(e):
 rows=['| Round | Feedback cases | Retained rules | Exception clauses | Drug F1 % | Native4 F1 % | Missed | Extra | Joint errors |','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
 for r in e['curves']['qwen-52']:
  m=r['metrics'];rows.append(f"| {r['round']} | {r['seen']} | {r['skills']} | {r['exception_clauses']} | {100*m['drug_f1']:.2f} | {100*m['joint_f1']:.2f} | {m['missed_drugs_per_patient']:.3f} | {m['extra_drugs_per_patient']:.3f} | {m['joint_errors_per_patient']:.3f} |")
 return '\n'.join(rows)
def figures(e):
 import matplotlib;matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 fig,ax=plt.subplots(1,3,figsize=(12,3.6))
 for name,style in [('qwen-52','-o'),('qwen-152','--s'),('qwen-52-shuffle',':^')]:
  rows=e['curves'][name];x=[r['seen'] for r in rows]
  ax[0].plot(x,[100*r['metrics']['drug_f1'] for r in rows],style,label={'qwen-52':'Case order A','qwen-152':'Case order B','qwen-52-shuffle':'Reflection labels shuffled'}[name])
  ax[1].plot(x,[100*r['metrics']['joint_f1'] for r in rows],style)
  ax[2].plot(x,[r['skills'] for r in rows],style)
 from matplotlib.ticker import MaxNLocator
 for a,title in zip(ax,['Drug F1 (%)','Complete native4 F1 (%)','Retained executable rules']):
  a.set(title=title,xlabel='Feedback patients seen');a.set_ylim(0,max(max(line.get_ydata()) for line in a.lines)*1.15);a.set_xticks([0,64,128,192]);a.grid(alpha=.2)
 ax[2].yaxis.set_major_locator(MaxNLocator(integer=True));ax[0].legend(fontsize=8,loc='lower left');fig.tight_layout();fig.savefig(HERE/'results/trajectory.png',dpi=180);plt.close(fig)
def main():
 e=json.loads((HERE/'results/evaluation.json').read_text());m=e['arms']['qwen-52']['all'];b=e['arms']['fixed_qwen']['all'];r=e['arms']['qwen-52'];state=json.loads((PRIVATE/'qwen-52-states.json').read_text())[-1];second=e['arms']['qwen-152']['all'];ll=e['arms']['llama_transfer_128'];lb=e['arms']['llama_fixed_128']['all']
 ci=r['paired95'];changed=r['changed_patients'];skilltext='\n'.join(f"- `{s['operator']}` when `{s['when']}`, unless `{', '.join(s['unless']) or 'none established'}`; round {s['round']}, {s['training_cases_seen']} feedback patients, {s['support_training']} scope-positive training cases, {s['empirical_harmful_exceptions']} observed harmful training exceptions." for s in state) or '- No retained rules.'
 interval='\n'.join(f'- {k}: [{lo:.4f}, {hi:.4f}]' for k,(lo,hi) in ci.items())
 strata=[]
 for name in ['single','multi','zero_target','nonzero_target']:
  a=e['arms']['fixed_qwen']['strata'][name];z=r['strata'][name];strata.append(f"| {name} | {z['cases']} | {100*a['drug_f1']:.2f} → {100*z['drug_f1']:.2f} | {a['missed_drugs_per_patient']:.3f} → {z['missed_drugs_per_patient']:.3f} | {a['extra_drugs_per_patient']:.3f} → {z['extra_drugs_per_patient']:.3f} | {a['joint_errors_per_patient']:.3f} → {z['joint_errors_per_patient']:.3f} |")
 stratum='| Stratum | N | Drug F1 % | Missed/patient | Extra/patient | Joint errors/patient |\n|---|---:|---:|---:|---:|---:|\n'+'\n'.join(strata)
 costrows=[json.loads(x) for x in (PRIVATE/'usage.jsonl').read_text().splitlines()]
 cost={'new_api_cost_usd':0,'local_successful_calls':len(costrows),'input_tokens':sum(x['input_tokens'] for x in costrows),'output_tokens':sum(x['output_tokens'] for x in costrows),'sum_amortized_batch_seconds':sum(x['seconds'] for x in costrows),'local_compute_priced':False,'prior_current_budget_spend_usd':.085203,'current_authorized_budget_usd':10}
 save(HERE/'results/cost.json',cost)
 caveats="The operator implementations and hypotheses are researcher specified. The learner automatically selects scopes, exception clauses and retained compositions from feedback; it does not discover arbitrary new medical tools. No drug-name predicate or newly fitted drug score is allowed, but frozen supervised and pretrained drug priors remain. Scope removal and shuffled-feedback controls test narrower alternatives; they cannot eliminate every shortcut. Native4 completeness is syntactic availability of HICL, route, dosage string and frequency, not clinical correctness or all required order fields."
 en=f'''# RxRSIAgent: conditional executable memory on new eICU patients

## 1. Research question and completed experiment

Can feedback induce conditional prescription-repair procedures that reduce omissions, extras and joint-order discrepancies on new patients? This delivery completes **6 rounds × 32 feedback patients**, two stream orders, **64 proposal + 64 guard patients**, a frozen **256-patient audit**, and **128-patient Llama transfer**. Every selected patient is absent from all v25 training/development/test membership. Source hospitals separate reflection, development and audit; audit hospitals had been used previously for other patients' development.

**Main result:** drug F1 {100*b['drug_f1']:.2f}% → {100*m['drug_f1']:.2f}%; native4 F1 {100*b['joint_f1']:.2f}% → {100*m['joint_f1']:.2f}%. The learner retains {len(state)} rules and changes {changed}/256 patients; {r['pareto_improved_patients']} improve without increasing another primary error, while {r['any_primary_worsened_patients']} worsen on at least one primary component. This is a bounded procedural-memory experiment; improvements in every endpoint, every round, or every model must be checked below rather than presumed.

## 2. What is predicted?

Input: demographics, recorded prior orders, available/revised labs and diagnosis entries by ICU hour6. Target: new/changed order records entered in hours6–12. Zero-target patients remain. Native HICL identity is used; no direct pooling with MIMIC raw-name/Core4 scores. The multisystem stratum means at least 2 recorded disease-system categories, not confirmed chronic multimorbidity. The [official source contract](https://github.com/MIT-LCP/eicu-code/blob/main/website/content/eicutables/diagnosis.md) supplies diagnosis entry timing but not resolution/ruled-out state. Diagnosis discharge activity is excluded. Storage-time and complete medication revision histories remain unavailable.

Common catalogue covers {100*e['candidate_drug_coverage']:.2f}% of target drug instances and {100*e['candidate_complete_joint_coverage']:.2f}% of complete target joint tuples. Complete target field coverage is {100*m['target_complete_field_coverage']:.2f}%. Missing/out-of-catalogue drugs stay in the drug denominator. Complete-joint scoring excludes incomplete GT and prediction tuples; its coverage must accompany its score. Qwen has {e['invalid_outputs']['qwen']}/256 invalid audit outputs; Llama has {e['invalid_outputs']['llama']}/128.

## 3. Method and controls

Every actor sees the same frozen predictor draft and training-only diagnosis-aware retrieval catalogue. All order IDs are stable hashes of joint tuples. Qwen/Llama use1 call with256 output tokens; repair programs add no LLM calls. Actual input length and backbone compute differ; the predictor-only arm uses no LLM. Static all-repair executes4 operators; retained programs execute according to their scopes.

Failure-guided symbolic induction searches observable predicates and empirical exceptions. Minimum4 active and2 negative training cases; an empirical exception needs2 harmful training applications. Training, proposal and guard must each show strict total discrepancy reduction and no aggregate increase in any of the3 primary components. At most 3 proposal-ranked candidates reach the guard and at most1 is retained per round. Learned states freeze before audit inference. No audit score selects a checkpoint.

{caveats}

## 4. Comparison table

{table(e)}

These are matched local controls and ablations. Original medical-agent paper scores are not inserted here. Previous MIMIC and public-QA comparisons remain unchanged; this eICU study is additional evidence, not a replacement claim of superiority.

## 5. Actual round-by-round updates

{curve(e)}

![Frozen round trajectories](results/trajectory.png)

Retained programs:

{skilltext}

Second stream final drug/native4 F1: {100*second['drug_f1']:.2f}% / {100*second['joint_f1']:.2f}%. Full proposal/guard outcomes and rejection counts are in `results/qwen-52-learning.json` and `results/qwen-152-learning.json`. Frozen same-state evaluations are not independent replications.

## 6. Transfer, strata and uncertainty

{stratum}

Paired patient-bootstrap 95% intervals for final minus initial; negative primary-error differences favor the learner, positive F1-point differences favor it:

{interval}

Llama drug F1 {100*lb['drug_f1']:.2f}% → {100*ll['all']['drug_f1']:.2f}%, joint F1 {100*lb['joint_f1']:.2f}% → {100*ll['all']['joint_f1']:.2f}%; its full intervals are in `results/evaluation.json`. Intervals use2000 draws and are exploratory, without multiple-testing adjustment. These observations do not guarantee monotonic progress or transfer to arbitrary LLMs.

## 7. Case studies and mechanism limits

Actual improvement, regression and unchanged-failure cases are stored **locally** in the restricted `prismatic-v52/case_studies.json` and `CASE_STUDIES.md`. They contain the recorded inputs, GT, before/after orders and active rules. They are not copied into GitHub. Scope-negative examples and empirically harmful exceptions are recorded separately. Audit exception activation and counterfactual harm/help counts appear in `results/evaluation.json`.

Four hypotheses distinguish missing identities, unsupported additions, wrong joint fields and copying prior therapy into the next time window. They are procedural failure hypotheses, not adjudicated clinical causes. Correct drug identity with wrong route/dose/frequency contributes a missing and an extra joint tuple. A gain from removing extras alone does not demonstrate better treatment coverage. Neither a fuller skill store nor a successful gate proves independent usefulness.

## 8. What is still unproved?

The requested strong claim requires reproducible reductions in all3 error types, clinically meaningful disease-specific exceptions, retained benefits across streams/models and clinician adjudication of appropriateness. Model weights, tool code and the update algorithm did not evolve. The experiment therefore does not establish recursive improvement of the optimizer, invention of new pharmacological knowledge, unrestricted prescribing competence, or superiority over the strongest published agents.

## 9. Cost and artifacts

New API spend **USD 0**. Successful local calls: {cost['local_successful_calls']}; input/output tokens: {cost['input_tokens']:,}/{cost['output_tokens']:,}. Local hardware time is unpriced. The current USD10 authorization still has only the previous USD 0.085203 API receipts charged; historical located study receipts remain approximately USD89.53 separately.

See `protocol.json`, `results/cohort.json`, `results/contract_audit.json`, `results/selection_lock.json`, `results/evaluation.json` and executable source files. The English ACL manuscript is updated in place. No restricted patient data or credentials are exported.
'''
 zh=f'''# RxRSIAgent：新患者上的条件化可执行技能实验

## 1. 本轮到底验证什么

验证“病例反馈是否能自动诱导带适用条件、例外条件的处方修复程序，并在新患者上减少漏开、多开和完整订单错误”。已完成 **6轮×32例反馈、两种病例顺序、64例提案集＋64例守门集、256例独立患者审计，以及128例 Llama 迁移**。全部患者排除既往 v25 所有训练、开发、测试患者。测试医院曾用于其他患者的开发，不能声称从未见过这些机构。

**真实结果：药物F1 {100*b['drug_f1']:.2f}% → {100*m['drug_f1']:.2f}%；原生四字段订单F1 {100*b['joint_f1']:.2f}% → {100*m['joint_f1']:.2f}%。** 保留{len(state)}条规则，改变{changed}/256例输出；按分项差错统计，{r['pareto_improved_patients']}例改善且其他项不增加，{r['any_primary_worsened_patients']}例至少一项变差。是否同时减少三类错误、是否逐轮改善，必须看下面的分项结果。

## 2. 数据、任务和评分

这次用 eICU 的新患者。输入是 ICU 前6小时已记录的诊断、既往订单和可用化验；预测第6—12小时新录入的药物订单。不是出院处方，也不是把所有既往药物再开一遍。保留没有新订单的患者，避免模型多开却被忽略。

“多病”操作定义是6小时前记录了至少两个疾病系统类别；可能有急性、暂定或已缓解的诊断，不能等同于已确诊慢性多病共存。[官方字段说明](https://github.com/MIT-LCP/eicu-code/blob/main/website/content/eicutables/diagnosis.md)明确了诊断录入时间，也说明缺乏已排除/缓解状态。未使用出院时诊断状态。药物完整修订历史仍缺失。

药物使用 HICL 编码；订单使用“药物、途径、剂量字符串、频次字符串”四字段。与 MIMIC 的 Core4 不是同一指标，不能横向拼分。候选目录覆盖{100*e['candidate_drug_coverage']:.2f}%的GT药物、{100*e['candidate_complete_joint_coverage']:.2f}%的完整GT订单。GT四字段完整率{100*m['target_complete_field_coverage']:.2f}%。目录外药物仍计入漏开；完整订单指标只统计字段齐全的元组，因此必须同时看字段覆盖率。四字段齐全不等于临床处方完整、正确。

## 3. 我们实际让什么成长了

不是重新拟合药物概率。所有组从开始就有相同的冻结预测草稿和训练病例检索。模型权重、工具实现固定；算法从失败反馈中选择操作、学习`when`条件、`unless`例外和保留的规则组合。可执行操作有：检索共识补漏、删除缺少多方支持的预测、修改联合订单字段、核对既往订单。药名不作为规则谓词，但底层模型和预测器仍可能含药物先验。

反例分两种：条件不满足的病例；实际执行操作会变差的病例。后者至少出现2例才可诱导例外条件。每条候选至少4例适用、2例不适用。训练、提案、守门三处都必须总错误严格减少，且漏开、多开、完整元组错误分别不增加。每轮最多3条进入守门、最多保留1条；测试结果不参与选规则。

**这里是有边界的程序记忆学习。四种工具的代码和初始假设由研究者写好，规则的条件和组合由反馈选择；不能包装成模型已经自动发明新药学知识或升级了自己的学习算法。**

## 4. 同患者真实对照表

{table(e)}

Missed=漏开的唯一药物数/患者；Extra=GT外药物数/患者；Joint errors=完整GT与预测订单元组的对称差/患者。三项越低越好。固定 Qwen、RxRSIAgent 和静态组合共享1次调用/256输出token；程序修复不增加LLM调用，但工具执行量不同。冻结预测器不调用LLM。Qwen无效输出{e['invalid_outputs']['qwen']}/256；Llama无效输出{e['invalid_outputs']['llama']}/128。

这是新的同设置机制实验，不能冒充 SafeRx-Agent、MedAgents 等原论文完整复现。已有 MIMIC、RxSafe 和 RxQA 对比保留，未把不同任务的分数混为一张排名表。

## 5. 六轮到底更新了什么

{curve(e)}

![逐轮冻结状态](results/trajectory.png)

实际保留规则（operator=操作，when=条件，unless=例外）：

{skilltext}

第二病例顺序最终药物/订单F1：{100*second['drug_f1']:.2f}% / {100*second['joint_f1']:.2f}%。完整候选、通过和拒绝记录见 `results/qwen-52-learning.json`、`results/qwen-152-learning.json`。重复评估未变化状态不算独立重复实验。

## 6. 多疾病系统、无新订单及跨模型表现

{stratum}

single=单疾病系统；multi=多疾病系统；zero_target=无新目标药物；nonzero_target=有新目标药物。特别检查有新订单患者，避免只靠减少输出获利。

最终减初始的配对患者bootstrap 95%区间（错误差小于0有利；F1百分点差大于0有利）：

{interval}

同一冻结技能迁移到 Llama：药物F1 {100*lb['drug_f1']:.2f}% → {100*ll['all']['drug_f1']:.2f}%；订单F1 {100*lb['joint_f1']:.2f}% → {100*ll['all']['joint_f1']:.2f}%。完整区间在结果JSON。所有区间是2000次重采样的探索性分析，未作多重检验校正。

## 7. 失败病例与机制结论的边界

真实改善、退步、仍失败病例连同GT及前后处方，保存在受限目录的 `case_studies.json` 和 `CASE_STUDIES.md`，不上传GitHub。条件外病例不等于已证实的伤害反例。测试上的例外触发、去掉例外后变好/变坏的计数见 `results/evaluation.json`。

我们分别追踪“药物未进入候选”“已有候选但漏选”“药物正确但联合字段错误”“既往订单复制到未来窗口”等程序问题。它们是可通过干预检验的工作流假设，还不是临床因果机制。仅减少多开不代表治疗覆盖提升；技能数量增长不代表收益；开发集通过也不保证新患者改善。

## 8. 距离强结论还差什么

要完整支持用户提出的命题，需要三类错误可靠下降、真正有临床含义的疾病条件与反例、不同病例顺序与模型上的稳定保留收益，以及适当性审查。目前不能预先宣布上述各项都已成立，更不能把有界规则搜索称为学习算法本身的递归升级。本轮结果必须与这些更强目标分开。

## 9. 费用与交付

新增API费用 **0美元**；本地成功调用{cost['local_successful_calls']}次，输入/输出token {cost['input_tokens']:,}/{cost['output_tokens']:,}。本地算力未折价。当前10美元授权累计API支出仍为此前的0.085203美元；历史已定位约89.53美元账目另计。

代码、冻结协议、患者隔离检查、状态哈希、完整结果JSON均在本目录。英文ACL论文原位更新；中英文结果同步。没有将受限病例或凭证上传GitHub。
'''
 (HERE/'RESULTS.en.md').write_text(en);(HERE/'RESULTS.zh.md').write_text(zh);figures(e)
 examples=json.loads((PRIVATE/'case_studies.json').read_text());local=['# 受限病例分析 / Restricted case studies — do not publish','这些是真实回顾性记录的匹配分析，不是给患者的用药建议。原始机器可读记录见同目录 case_studies.json。']
 for j,x in enumerate(examples,1):
  c=x['case'];a=counts(x['before'],c['gold']);z=counts(x['after'],c['gold'])
  local += [f"\n## Case {j}: {x['type']}",f"漏开/多开/完整元组错误：{a[:3]} → {z[:3]}。总错误变化 {x['error_delta']}。",'决策前已记录诊断：'+'; '.join(c['context']['diagnoses'][:8]),'执行的技能：'+('; '.join(s['operator']+' when '+s['when']+' unless '+str(s['unless']) for s in x['active_skills']) or '无技能触发。')]
  for label,orders in [('记录的GT',c['gold']),('更新前',x['before']),('更新后',x['after'])]:
   local += ['\n### '+label,'','| 药物（HICL） | 途径 | 剂量字符串 | 频次 |','|---|---|---|---|']
   for o in orders:local.append('| '+' | '.join(str(v or '未知').replace('|','/') for v in [c['drug_names'].get(o['drug_code'],o['drug_code'])+' ('+o['drug_code']+')',o['route'],o['dosage'],o['frequency']])+' |')
   if not orders:local.append('| 无新订单预测/记录 | — | — | — |')
  gg={o['drug_code'] for o in c['gold']};cc={o['drug_code'] for o in c['catalogue'].values()};pp={o['drug_code'] for o in x['after']}
  local += ['\n可验证的剩余差距：',f'- GT中目录外药物：{len(gg-cc)}个。',f'- 目录可用但仍漏选：{len((gg&cc)-pp)}个。',f'- GT外预测药物：{len(pp-gg)}个。','- GT表示这个时间窗口中实际录入的订单；不能仅据未记录就认定药物在临床上不适用。']
 (PRIVATE/'CASE_STUDIES.md').write_text('\n'.join(local)+'\n')
 for lang,body in [('en',en),('zh',zh)]:
  short=(f"## New-patient conditional-memory study\n\n256 eICU audit patients;6 rounds/192 feedback patients; drug F1 {100*b['drug_f1']:.2f}% → {100*m['drug_f1']:.2f}%, native4 F1 {100*b['joint_f1']:.2f}% → {100*m['joint_f1']:.2f}%; {len(state)} retained rules. New API spend USD 0. This does not establish recursive optimizer improvement. [Full results](../upgrade_v52/RESULTS.en.md)." if lang=='en' else f"## 新患者条件技能实验\n\n256例 eICU 审计、6轮/192例反馈；药物F1 {100*b['drug_f1']:.2f}% → {100*m['drug_f1']:.2f}%，原生四字段F1 {100*b['joint_f1']:.2f}% → {100*m['joint_f1']:.2f}%；保留{len(state)}条规则。新增API费0美元，尚不能声称学习算法本身递归升级。[完整结果](../upgrade_v52/RESULTS.zh.md)。")
  replace_block(ROOT/'paper'/f'CURRENT_RESULTS.{lang}.md',short,'V52')
 extra_analysis(e)
 runtime_notes(e)
 manuscript(e,state)
def runtime_notes(e):
 d=json.loads((HERE/'results/decoder_evaluation.json').read_text());b=d['arms']['fixed_qwen_compatible']['all'];r=d['arms']['qwen-compatible-52'];z=r['all']
 names={'fixed_qwen_compatible':'Fixed Qwen, compatible runtime','qwen-compatible-52':'RxRSIAgent, compatible runtime + gated memory','qwen-compatible-52-shuffle':'Reflection-label shuffle, true development gates','compatible_static_all_repairs':'Static all repairs, compatible runtime','fixed_llama_compatible':'Fixed Llama, compatible runtime (128)','llama_compatible_transfer':'Llama + transferred memory, compatible runtime (128)'}
 rows=['| Method | Drug F1 % | Native4 F1 % | Missed/patient | Extra/patient | Joint errors/patient |','|---|---:|---:|---:|---:|---:|']
 for n,label in names.items():
  v=d['arms'][n]['all'];rows.append(f"| {label} | {100*v['drug_f1']:.2f} | {100*v['joint_f1']:.2f} | {v['missed_drugs_per_patient']:.3f} | {v['extra_drugs_per_patient']:.3f} | {v['joint_errors_per_patient']:.3f} |")
 table='\n'.join(rows)
 en=f'''## Compatible runtime, regated learning and current decision

Complete JSON with a mixture of known and unknown IDs previously lost the entire output. The compatible runtime retains only verified IDs, logs unknown IDs, accepts complete fenced JSON, and never completes a truncated structure. It restores nonempty outputs for8 Qwen audit patients and13 Llama patients. **All development gates were rerun using this same decoder before audit metrics**, rather than attributing an output-parser change to learned improvement. No new LLM inference was needed.

{table}

The compatible learner also loses6 correct drug targets; the omission-rate difference95% interval is [{r['paired95']['missed_drugs_per_patient'][0]:.4f}, {r['paired95']['missed_drugs_per_patient'][1]:.4f}] per patient. {r['any_primary_worsened_patients']} patients worsen on at least one primary component. A lower summed error count must not conceal these trade-offs. The reflection-label-shuffle control permutes **only reflection labels**; proposal and guard references remain correct, so it does not eliminate development supervision. After decoder repair it also retains3 rules. This weakens attribution to patient-specific reflection learning.

**The strong hypothesis is not established.** We observed automatic conditional rule selection, but no accepted explicit exception, no recovery of a previously missed correct drug, and no jointly improving three-endpoint trajectory. The current catalogue reaches only54.21% of target drugs and11.30% of complete target order tuples. No bounded selector can recover a target absent from its action space. The next scientific target is order-level applicability and joint-field construction with independently verified evidence, followed by a new patient lock; this audit is now exposed and must not be reused as unseen confirmation.

The learned memory is **not promoted**. `serve.py` uses the compatible initial actor by default; `--experimental-memory` reproduces the failed memory for research. This rollback does not retrospectively change the frozen result table or count as a positive evolution result.

'''
 zh=f'''## 当前兼容接口结果与是否启用记忆

已修复“完整JSON里混入一个未知编号，就把所有有效订单丢掉”的问题：保留可核验编号、记录未知编号、接受完整代码围栏、不补猜截断结构。Qwen测试中恢复8例非空输出，Llama恢复13例。**开发集门控也在相同解码器下重新执行，并在查看测试指标前冻结**；没有把解析器修复当成进化，也没有新增模型推理。

{table}

兼容接口下的学习器仍删掉6个正确药物，漏开率差95%区间为每患者[{r['paired95']['missed_drugs_per_patient'][0]:.4f}, {r['paired95']['missed_drugs_per_patient'][1]:.4f}]；{r['any_primary_worsened_patients']}例至少一项主要错误增加。不能用总错误下降掩盖这些取舍。打乱反馈对照只打乱**反思训练标签**，提案/守门仍使用正确GT；修复解码后它也保留3条规则，所以不能把门控选择的收益全部归因于逐病例反思。

**目前没有证明完整研究命题。** 已实现条件规则的自动选择，但没有保留有效的显式例外，没有补回新的正确药物，也没有实现三项指标一起改善。候选空间只包含54.21%的目标药物、11.30%的完整目标订单；目录外目标不可能靠继续选择已有编号找回来。下一步真正需要改变的是订单级适用性、联合字段构造和可核验证据，而非只增加轮次；本次审计集已经暴露，后续必须重新冻结新患者。

**本轮记忆不启用为默认状态。** `serve.py`默认使用修复接口后的初始actor；只有`--experimental-memory`才复现退步的实验记忆。回退不会改写本轮真实结果，也不算进化成功。

'''
 for lang,note in [('en',en),('zh',zh)]:
  path=HERE/f'RESULTS.{lang}.md';text=path.read_text().replace('## 8.',note+'## 8.')
  headline=('**Outcome: the full hypothesis is not established. The compatible runtime changes drug F1 from7.38% to7.20% after learning and loses6 correct targets. The learned memory is not enabled by default.**' if lang=='en' else '**结论：尚未证明完整命题。统一兼容接口后，学习使药物F1从7.38%降到7.20%，丢失6个正确目标药物；实验记忆不作为默认状态启用。**')
  first,rest=text.split('\n',1);path.write_text(first+'\n\n'+headline+'\n'+rest)
  (ROOT/'paper'/f'RXRSI_PROOF_STATUS.{lang}.md').write_text(('# RxRSIAgent evidence status\n\n' if lang=='en' else '# RxRSIAgent 研究命题验证状态\n\n')+note)
 save(HERE/'results/release_decision.json',{'experimental_memory_promoted':False,'default_runtime_state':'compatible actor, no retained repair cards','reason':'Independent audit increases omissions by6 correct drug targets; no recovered correct drug; full three-error improvement is unsupported.','audit_now_exposed':True,'next_confirmatory_study_requires_new_patients':True})
def extra_analysis(e):
 d=json.loads((HERE/'results/mechanisms.json').read_text());v=json.loads((HERE/'results/refined_evaluation.json').read_text());t=d['transition']
 tab=['| Updater | Rules | Exception clauses | Drug F1 % | Native4 F1 % | Missed/patient | Extra/patient |','|---|---:|---:|---:|---:|---:|---:|']
 for n,r in v['variants'].items():
  z=r['final']['all'];tab.append(f"| { {'qwen-refined-52':'Both updater repairs (order A)','qwen-refined-152':'Both updater repairs (order B)','qwen-counterexample-only-52':'Componentwise counterexamples only','qwen-rejection-only-52':'Rejected-program memory only'}[n]} | {len(r['state'])} | {sum(len(s['unless']) for s in r['state'])} | {100*z['drug_f1']:.2f} | {100*z['joint_f1']:.2f} | {z['missed_drugs_per_patient']:.3f} | {z['extra_drugs_per_patient']:.3f} |")
 table='\n'.join(tab)
 texts={
 'en':f'''## Additional mechanism audit and updater repair

Final-minus-initial set transitions: recovered correct drugs **{t['recovered_correct_drugs']}**, lost correct drugs **{t['lost_correct_drugs']}**, removed extras **{t['removed_extra_drugs']}**, added extras **{t['added_extra_drugs']}**. Recovered complete target tuples: **{t['recovered_complete_joint_targets']}**; lost complete target tuples: **{t['lost_complete_joint_targets']}**. These counts distinguish genuine coverage or field correction from output shrinkage. All three primary errors strictly decrease: **{d['all_three_primary_errors_strictly_decreased']}**.

Development inspection found an objective mismatch: the initial counterexample detector marks cases harmful only when total discrepancy rises, whereas the gate rejects an increase in any component. Losing one correct drug can therefore be concealed by removing other extras. It also repeatedly submits rejected state/program pairs. Before any audit metric was calculated, we froze an explicitly exploratory amendment with componentwise counterexamples and rejected-program memory, including each change alone and two streams of both changes. Audit actor generation had already started, but its predictions and outcomes were not used by the amendment. The original primary study remains unchanged; the amendment is a researcher repair, not an automatically evolved learning algorithm.

{table}

The amended detector can identify more harmful cases without yielding a transferable exception rule. Conditions are currently patient-level, while the action changes individual drug orders; a broad patient exclusion may suppress useful edits along with harmful ones. This is a granularity hypothesis motivated by the implemented rule language, not a demonstrated clinical mechanism. Raw subgroup associations do not prove a disease-specific prescribing principle.

Source audit also finds7 cancelled rows among473 audit target source rows (distinct from unique drugs). Cancellation time is unavailable and cancellation status is not an input or a target filter. The [official medication contract](https://raw.githubusercontent.com/MIT-LCP/eicu-code/main/website/content/eicutables/medication.md) describes orders, not guaranteed administrations. This further limits interpretation of GT as clinical correctness.

''',
 'zh':f'''## 追加：收益来源及学习器修复结果

更新前后集合对照：**新找回正确药物{t['recovered_correct_drugs']}个、丢失原本正确药物{t['lost_correct_drugs']}个、删除额外药物{t['removed_extra_drugs']}个、新增额外药物{t['added_extra_drugs']}个**；新增匹配完整GT元组{t['recovered_complete_joint_targets']}个，丢失匹配元组{t['lost_complete_joint_targets']}个。三项主要错误是否全部严格下降：**{'是' if d['all_three_primary_errors_strictly_decreased'] else '否'}**。因此不能把减少输出自动解释为学会补漏或修正剂量。

开发集检查发现：旧反例检测看“总错误增加”，但守门看“三项中任一项不能增加”。删掉一个正确药同时删掉更多错误药，会被旧反例检测漏掉。另一问题是重复提交已经失败的状态/规则组合。

在计算任何测试指标之前，我冻结了明确标注的探索性修正版：按分项损失识别反例，并记忆已拒绝规则；还分别测试了只修反例、只加拒绝记忆、两项一起修，后者跑两种病例顺序。此时测试模型生成已经开始，但修正版没有读取测试预测或分数。原实验保留不变；**这是研究者修复学习器，不能算agent已经自我升级了学习算法**。

{table}

更正确的反例检测不保证能学出可迁移的例外。当前条件作用于整位患者，操作却改变某一药物；用整位患者的排除条件，可能同时挡住有益和有害的修改。这是下一步需要检验的“患者级条件与订单级动作粒度不一致”假设，还不是已发现的临床机制。

源表审计另发现：测试目标473条原始订单行中有7条最终标记取消（不等于药物去重计数）；取消时间不可用，未将取消状态作为输入或筛选目标。[官方药物表说明](https://raw.githubusercontent.com/MIT-LCP/eicu-code/main/website/content/eicutables/medication.md)也区分订单和实际给药。所以GT只能先表示记录行为，不能直接等同于临床正确答案。

'''}
 for lang,body in texts.items():
  path=HERE/f'RESULTS.{lang}.md';text=path.read_text();marker='## 8.';text=text.replace(marker,body+marker);path.write_text(text)
def manuscript(e,state):
 tex=ROOT/'paper/latex/v0.3/prismatic_v03_en.tex';text=tex.read_text();b=e['arms']['fixed_qwen']['all'];m=e['arms']['qwen-52']['all'];r=e['arms']['qwen-52'];ci=r['paired95']['drug_f1_pp']
 rows=[]
 for name in ['frozen_predictor','fixed_qwen','qwen-52','qwen-152','static_all_repairs','qwen-52-shuffle','qwen_unscoped']:
  z=e['arms'][name]['all'];rows.append(f"{LABELS[name]} & {100*z['drug_f1']:.2f} & {100*z['joint_f1']:.2f} & {z['missed_drugs_per_patient']:.3f} & {z['extra_drugs_per_patient']:.3f} & {z['joint_errors_per_patient']:.3f}\\\\")
 cr=[]
 for x in e['curves']['qwen-52']:
  z=x['metrics'];cr.append(f"{x['round']} & {x['seen']} & {x['skills']} & {x['exception_clauses']} & {100*z['drug_f1']:.2f} & {100*z['joint_f1']:.2f}\\\\")
 ll=e['arms']['llama_transfer_128']['all'];lb=e['arms']['llama_fixed_128']['all'];multi=e['arms']['qwen-52']['strata']['multi'];mb=e['arms']['fixed_qwen']['strata']['multi']
 section=r'''
\subsection{Conditional executable memory on new patients}\label{sec:conditional-memory}
We separately test whether reference feedback can induce executable conditions and exceptions over frozen repair tools. This experiment uses eICU\citep{eicu}, with 192 new feedback patients in 6 rounds,64 proposal patients,64 guard patients and256 audit patients;128 audit patients also support frozen-state Llama transfer. All patients are excluded from prior eICU training, development and test membership. Reflection, development and audit use distinct source-hospital partitions, but audit hospitals were previously used for different patients' development. This is new-patient evidence, not globally unseen-institution validation.

\paragraph{Observable context and target.} Inputs contain demographics, prior orders, revised laboratory observations and diagnoses entered by ICU hour6. Diagnosis entry offsets provide timing; resolved/ruled-out status is unavailable. Discharge activity and diagnosis priority are excluded. Targets are recorded orders entered in hours6--12, including zero-target stays. Native4 denotes HICL identity, route, dosage string and frequency string; it differs from MIMIC Core4 and omits additional clinical fields. Half of each split has at least 2 recorded disease-system categories, an operational multisystem stratum rather than confirmed chronic multimorbidity.

\paragraph{Failure-guided program induction.} The local Qwen actor uses one call with a 256-token output cap. Every arm sees the same frozen supervised draft and diagnosis-aware retrieval from 40000 old training stays. A deterministic learner induces \texttt{when}/\texttt{unless} clauses and a sequence of four fixed operators: retrieve consensus omissions, prune unsupported predictions, revise joint fields and reconcile unchanged prior orders. Operators cannot read target labels at execution. No drug-name predicate, newly fitted medication score, backbone update or generated executable tool code is allowed. This isolates bounded procedural-memory induction; it is not autonomous discovery of arbitrary tools or improvement of the optimizer itself.

A candidate requires at least 4 applicable and 2 inapplicable seen cases. An empirical exception requires at least 2 harmful training applications; scope-negative examples alone are not harmful counterexamples. Seen training, proposal and guard must each improve total discrepancy count without increasing any of missed drugs, extra drugs or complete-joint symmetric difference. At most 3 proposal-ranked candidates reach the guard and 1 is retained per round. Two case orders and shuffled training feedback are evaluated; every state freezes before audit inference, and no audit score selects a checkpoint. Repeated gate reuse can nevertheless overfit.

\begin{figure*}[t]\centering
\begin{tikzpicture}[x=1cm,y=1cm,>=Stealth,b/.style={draw,rounded corners,align=center,text width=2.55cm,minimum height=1.05cm,font=\small}]
\node[b](a) at(0,0){Hour6 context\\recorded diagnoses\\prior orders + labs};
\node[b](b) at(3.4,0){Fixed training tools\\ranked draft + retrieval\\stable joint-order IDs};
\node[b](c) at(6.8,0){Frozen local LLM\\candidate order set};
\node[b](d) at(10.2,0){Conditional programs\\when / unless / action\\compiled order set};
\draw[->](a)--(b);\draw[->](b)--(c);\draw[->](c)--(d);
\node[b](e) at(0,-2){Training feedback\\missing / extra drugs\\wrong joint tuples};
\node[b](f) at(3.4,-2){Program induction\\observable scopes\\harmful exceptions};
\node[b](g) at(6.8,-2){Proposal + guard\\three error constraints\\accept or reject};
\node[b](h) at(10.2,-2){Frozen round states\\new-patient audit\\multisystem + transfer};
\draw[->](e)--(f);\draw[->](f)--(g);\draw[->](g)--(h);\draw[->](g.north)--++(0,.4)-|(d.south);
\end{tikzpicture}
\caption{Executed conditional-memory experiment. Tools and actor weights stay fixed. Feedback learns bounded routing and composition; audit outcomes never enter selection.}\label{fig:conditional-memory}
\end{figure*}
\begin{table*}[t]\centering\small\setlength{\tabcolsep}{4pt}
\caption{Frozen new-patient eICU audit (256 patients). F1 is a percentage; the three error columns are counts per patient, lower is better. Native4 scores use complete tuples and must be read with field coverage. Controls share catalogue information; static and retained programs differ in tool execution, and the supervised predictor uses no LLM.}
\label{tab:conditional-memory}\begin{tabular}{@{}lrrrrr@{}}\toprule
Method & Drug F1 & Native4 F1 & Missed & Extra & Joint errors\\\midrule
'''+'\n'.join(rows)+r'''
\bottomrule\end{tabular}\end{table*}
\begin{table*}[t]\centering\small
\caption{All frozen round states for the first prespecified stream; unchanged states are not independent repetitions.}\label{tab:conditional-rounds}
\begin{tabular}{@{}rrrrrr@{}}\toprule Round & Feedback patients & Rules & Exception clauses & Drug F1 & Native4 F1\\\midrule
'''+'\n'.join(cr)+r'''
\bottomrule\end{tabular}\end{table*}
'''
 section+=f"\nThe first stream retains {len(state)} rules and changes {r['changed_patients']}/256 outputs; {r['pareto_improved_patients']} patients improve without worsening another primary component, while {r['any_primary_worsened_patients']} worsen on at least one component. Drug F1 changes from {100*b['drug_f1']:.2f}\\% to {100*m['drug_f1']:.2f}\\%, with paired patient-bootstrap 95\\% difference interval [{ci[0]:.2f}, {ci[1]:.2f}] points. Native4 F1 changes from {100*b['joint_f1']:.2f}\\% to {100*m['joint_f1']:.2f}\\%. Catalogue coverage is {100*e['candidate_drug_coverage']:.2f}\\% of target drugs and {100*e['candidate_complete_joint_coverage']:.2f}\\% of complete target tuples; target field coverage is {100*m['target_complete_field_coverage']:.2f}\\%. All target drug identities remain in the denominator.\n"
 section+=f"\nIn the 128-patient multisystem stratum, drug F1 changes from {100*mb['drug_f1']:.2f}\\% to {100*multi['drug_f1']:.2f}\\%; omissions change from {mb['missed_drugs_per_patient']:.3f} to {multi['missed_drugs_per_patient']:.3f} per patient and extras from {mb['extra_drugs_per_patient']:.3f} to {multi['extra_drugs_per_patient']:.3f}. Frozen transfer to Llama changes drug F1 from {100*lb['drug_f1']:.2f}\\% to {100*ll['drug_f1']:.2f}\\% and native4 F1 from {100*lb['joint_f1']:.2f}\\% to {100*ll['joint_f1']:.2f}\\%. These limited experiments do not guarantee monotonic improvement or arbitrary-backbone transfer. New paid API spend is USD 0; local compute is unpriced.\n"
 section+=r'''
\paragraph{Mechanistic scope.} A learned condition can encode a statistical context association rather than a clinical indication. Reducing copied prior orders can reduce extras without recovering missed therapy; similarly, complete-joint improvement can reflect fewer extra tuples rather than corrected dose decisions. We separately retain improvement, regression and unchanged-failure cases locally, and report removal of scopes/exceptions and shuffled-feedback controls. These are workflow interventions, not evidence of newly discovered clinical causal mechanisms. Complete original medical-agent workflows and adjudicated appropriateness are not established by this table.
'''
 section+=r'''
\paragraph{Observed regression and counterexample repair.} The original retained memory removes105 extra drug predictions but also removes6 correct targets, recovers0 new correct targets and loses1 previously matched complete order. Thus lower total discrepancy can conceal increased omissions. The paired omission-rate difference interval is [0.0078,0.0430] per patient. An exploratory amendment, frozen before audit metrics but after audit actor generation began, replaces total-loss counterexamples with componentwise counterexamples and adds rejected-program memory. Each change is also ablated. The combined repair retains1 and4 rules under the two case orders, with drug F1 of6.98\% and7.12\%; neither demonstrates a gain over the initial7.13\%. Eight exception-bearing candidates reach the first stream's guard, but none is retained. Fixing the detector therefore does not establish a transferable clinical exception.

\paragraph{Uniform runtime repair and rerun gates.} A complete JSON response may contain both valid and unknown catalogue IDs. Rejecting the whole response discards valid orders. A separate compatible compiler preserves only known IDs, logs unknown IDs, accepts a complete fenced wrapper, and never completes truncated structures. It restores8 nonempty Qwen audit outputs and13 Llama outputs. All development gates are rerun under the same compiler and freeze before audit metrics. This engineering change is separated from RSI: initial-to-learned drug F1 is7.38\% to7.20\%, and native4 F1 is1.64\% to1.60\%. The corrected-runtime learner still loses6 correct targets. Shuffling only reflection labels now also retains3 rules; proposal and guard labels remain correct. Consequently, the experiment does not isolate the contribution of patient-specific reflection from development-set selection. The learned memory is not promoted to the default research runtime. The strong claim of jointly improving omissions, extras and order correctness remains unsupported.
'''
 begin='% V52-BEGIN';end='% V52-END'
 if begin in text:text=text[:text.index(begin)]+text[text.index(end)+len(end):]
 text=text.replace('\\section{Clinical Scope and Limitations}',begin+'\n'+section+'\n'+end+'\n\\section{Clinical Scope and Limitations}')
 abstract_note=f" A separate new-patient eICU study induces {len(state)} conditional programs over fixed tools from192 feedback patients: drug F1 changes from {100*b['drug_f1']:.2f}\\% to {100*m['drug_f1']:.2f}\\% on256 audit patients. This bounded program induction does not update the learning algorithm."
 # A clearly delimited abstract addition makes generation idempotent.
 ab='% V52-ABSTRACT-BEGIN';ae='% V52-ABSTRACT-END'
 if ab in text:text=text[:text.index(ab)]+text[text.index(ae)+len(ae):]
 # Preserve the editorially consolidated abstract; update the experiment section above.
 tex.write_text(text)
if __name__=='__main__':main()
