"""Build bilingual living results and the current executable profile from audits."""
import json,hashlib,collections,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent;HERE=ROOT/'upgrade_v44'
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 a=read('upgrade_v44/results/audit.json');assert a['status']=='complete';learn=read('upgrade_v44/results/learning.json');ind=read('upgrade_v44/results/independent.json');sc=read('upgrade_v44/results/shortcuts.json');old=read('upgrade_v35/results/audit.json')['methods'];native=read('upgrade_v34/results/audit.json')['author_methods'];x=a['methods']['test_rx']['final'];y=a['methods']['test_qa']['final'];z=ind['trajectory'][-1];states=learn['rounds'];cards=states[-1]['state']['cards'];fmt=lambda r:f"{r['correct']}/{r['n']} ({100*r['correct']/r['n']:.2f}%)"
 rows=['| Method / 方法 | RxSafe988 | RxQA300 | Output cap / 输出上限 |','|---|---:|---:|---:|']
 for k,n in [('grasp','GRASP'),('medagents','MedAgents'),('mdagents','MDAgents')]:rows.append(f"| {n} | {fmt(old[k]['test'])} | {fmt(old[k]['rxqa'])} | 4608 |")
 rows.extend([f"| Supervised source-agent control / 普通监督校准对照 | {fmt(old['calibrated']['test'])} | {fmt(old['calibrated']['rxqa'])} | 4608 |",f"| **RxRSIAgent** | **{fmt(x)}** | **{fmt(y)}** | 4608 |",f"| MedAgents, higher allowance / 高额度 | {fmt(native['medagents']['test'])} | {fmt(native['medagents']['rxqa'])} | 24000 |",f"| MDAgents, higher allowance / 高额度 | {fmt(native['mdagents']['test'])} | {fmt(native['mdagents']['rxqa'])} | 24000 |"]);main_table='\n'.join(rows)
 curve=['| Round / 轮次 | Cases / 累计病例 | Cards / 技能 | Retrieval edits / 检索项 | Terms / 条件词 | Proposal S/M | Guard S/M | MedPIC |','|---:|---:|---:|---:|---:|---:|---:|---:|']
 for s,i in zip(states,ind['trajectory']):
  cs=s['state']['cards'];g=s['gates'];curve.append(f"| {s['round']} | {s['cases_seen']} | {len(cs)} | {sum(len(c.get('retrieval_patch',{})) for c in cs)} | {sum(len(v) for c in cs for v in c.get('trigger_terms',{}).values())} | {g['proposal_rx']['correct']}/190; {g['proposal_med']['correct']}/120 | {g['guard_rx']['correct']}/197; {g['guard_med']['correct']}/120 | {i['metrics']['correct']}/467 |")
 curve='\n'.join(curve);up=['| Experiment / 实验 | Attempts / 尝试 | Schema / 角色或格式 | No edit / 无证据更新 | Probe rejected / 探针拒绝 | Proposal / 候选集拒绝 | Guard / 守门拒绝 | Accepted / 保留 |','|---|---:|---:|---:|---:|---:|---:|---:|'];ntrial=0
 for v in range(37,45):
  l=read(f'upgrade_v{v}/results/learning.json');ts=[t for s in l['rounds'] for t in s.get('trials',[])];ct=collections.Counter(t.get('rejection','accepted') for t in ts);ntrial+=len(ts);up.append(f"| v{v} | {len(ts)} | {ct['schema']} | {ct['no_supported_edit']} | {ct['training_intervention']} | {ct['proposal']} | {ct['guard']} | {sum(t['accepted'] for t in ts)} |")
 up='\n'.join(up);ss=sc['result']['final'];short_table='| Condition / 条件 | Exact-set / 完全正确 | Both pair members / 成对全对 |\n|---|---:|---:|\n'+f"| Original / 原始 | {ss['original_correct']}/70 | {ss['original']['paired']['both_correct']}/35 |\n| Permutation / 选项置换 | {ss['permuted']['metrics']['correct']}/70 | {ss['permuted']['detail']['paired']['both_correct']}/35 |\n| No vignette / 去掉患者背景 | {ss['no_patient']['metrics']['correct']}/70 | {ss['no_patient']['detail']['paired']['both_correct']}/35 |";families=z['detail']['families'];root=a['root_hypotheses'];trials=[t for s in states for t in s.get('trials',[])];totalaccepted=sum(t['accepted'] for t in trials)
 conclusion_zh=('**没有证实逐轮能力增长：最终技能、检索配置和条件词表均未保留变化，独立曲线是相同状态的缓存复用。不能称为已实现成功 RSI。**' if not cards else f'最终保留{len(cards)}个技能；是否有迁移收益，以独立任务前后差异为准，不能由技能数量推出。')
 conclusion_en=('**No positive evolution is established: no procedural, retrieval or vocabulary update is retained. Identical states reuse predictions; the flat trajectory is not five independent replications.**' if not cards else f'The final state retains{len(cards)} cards; transfer must be judged from independent outcomes, not memory size.')
 goals_zh='**两个 bench 同时超过最强对照的目标尚未完成。**' if x['correct']<=556 or y['correct']<=208 else '**当前实测超过已完成的命名 agent 对照，但重复测试集研究与不同训练计算量限制了结论；不能声称全领域 SOTA。**'
 goals_en='**The target of beating the strongest completed named-agent controls on both benchmarks is unmet.**' if x['correct']<=556 or y['correct']<=208 else '**Observed counts exceed the completed named-agent controls, with repeated-benchmark and unequal-training-compute limitations; this is not a global SOTA claim.**'
 links='[RxSafeBench paper](https://arxiv.org/html/2511.04328v1), [MedPIC paper](https://arxiv.org/abs/2608.03028), [MedPIC author data](https://huggingface.co/datasets/TIM0927/MedPIC-Bench), [openFDA fields](https://open.fda.gov/apis/drug/label/searchable-fields/).'
 en=f'''# RxRSIAgent: trace-root reflection, scoped interventions, and independent evaluation

Updated16 October2026. This living report supersedes the previous current summary; prior evidence is archived. The paper method is **RxRSIAgent**, not a list of version names.

## 1. Actual results and outstanding targets

- Current frozen actor: **{fmt(x)} RxSafe; {fmt(y)} RxQA**.
- Independent MedPIC exact-set score: **{fmt(z['metrics'])}**. Guideline-following:{families['guideline_following']['correct']}/284; counterfactual:{families['counterfactual']['correct']}/183; both members correct:{z['detail']['paired']['both_correct']}/35 strict pairs.
- {goals_en}
- {conclusion_en}

## 2. What supervised calibration actually means

The previous556/988 result includes ordinary logistic regression trained on625 labeled cases. It learns weights for drug identities, drug/UNII–question-word interactions, and an LLM draft indicator. When all options are short names seen in training and the score gap is at least0.2, it may override the LLM. It was applied on527 RxSafe cases and applied on zero RxQA items. This is a statistical option scorer, not reflection, root-cause tracing or tool evolution. A name-only diagnostic scored564/988, exposing a shortcut concern.

GT feedback can legitimately supervise an agent-update experiment. The distinction is **what is updated and what is validated**: ordinary option-weight fitting is kept separate from persistent process/tool-configuration changes. Even the latter does not become successful RSI merely because code exists or memory grows. We require an actual accepted change and independent improvement. The current actor has no fitted option ranker or raw training-answer retrieval; pretrained drug knowledge still exists.

## 3. Named-method main table

{main_table}

Same served DeepSeek identifier and identical question sets. Author workflows are pinned local adaptations, not their papers' copied scores. RxRSIAgent uses3×1536 output tokens. Shared output allowance does **not** equal input cost, call count or training supervision. The source-agent calibration control uses its earlier fixed source workflow; it is a separate method/control, not a clean one-factor ablation of the new actor. Higher-allowance MedAgents remains208/300. No SafeRx-Agent score is invented; medication-set methods cannot populate QA accuracy columns.

## 4. Why earlier skill updates all failed

The earlier eight updates never passed the proposal set; no guard rejection occurred. Two produced no schema-valid cards. The other proposals caused more regressions than fixes (for example9 corrections versus16 regressions). The code audit identified missing retrieved spans/intermediate checks in reflection, unconditional skill injection, nearest-success examples without scope validation, and missing replay of rejected interventions.

Further real experiments found: long-context ID/role confusion; a broad age-or-pregnancy trigger activating on115/120 MedQA questions and reducing103 correct to97; a missed gestational-timing phrase in the context detector; old root IDs being invalidated solely because they came from an earlier round; and treating a legitimate null/no-edit response as a schema error, forcing an unsupported repair. These defects have explicit fixes and retained negative experiments. They are not all failures of clinical knowledge or merely an overly strict gate.

## 5. Current inference and learning mechanism

1. Extract quoted facts, medication roles and explicit routes.
2. Resolve product variants and retrieve indication/dose/safety windows with balanced per-product allocation. Record exact source offsets and unresolved metadata.
3. Assess every option. Verify quotations, bounded arithmetic and explicitly sourced age/eGFR/CrCl comparisons. Unit consistency, all rule qualifiers and overall clinical applicability remain unverified.
4. Decide with the original input and check results; no numeric answer override.
5. On training feedback, record GT/prediction discrepancy, earliest suspected failure stage, source-grounded root hypothesis, minimal repair and counterexample requirement. A model's hypothesis is not clinical adjudication.
6. Accumulate past eligible roots, recent rejected edits and the two highest positive-net failed probes. Use compact typed role pools and short IDs. Do not forget an earlier root when new cases arrive.
7. Propose one scoped procedure or one retrieval-parameter change; data-bound context-vocabulary patches can repair detector misses. The patch must match a failure and a success; this does not prove every term's meaning. Explicit no-edit decisions are preserved.
8. Training probe: at least2 net corrections and no extra invalid answers. Proposal RxSafe190/MedQA120: neither loses and pooled count improves. Guard RxSafe197/MedQA120: neither loses. Freeze all states before evaluation.

Only procedures, retrieval configuration and condition vocabulary can change. Backbone weights and executable tools remain fixed during learning. Tool repairs between experiments are **researcher changes**, not autonomous agent gains. The final proposal model is **anthropic/claude-opus-4.8**; actor and initial reflector remainDeepSeek. This is externally assisted agent-state learning with additional offline compute, not autonomous same-model recursion. Earlier controls used a strict positive guard gain; the non-regression guard was declared before tests.

## 6. Completed updater experiments

{up}

These are{ntrial} proposal attempts across eight four-round development experiments, all reusing the same400-case training cohort. They are not3,200 unique cases or independent random-seed runs. All rejected/declined candidates remain in the records. v37 adds full traces; v38 explicit role repair; v39 narrow interventions; v40 condition vocabulary; v41 compact context; v42 external proposer; v43 legitimate abstention; v44 cumulative root and promising-failure replay.

## 7. Round-by-round independent validation

{curve}

{conclusion_en} New training comprises200 existing RxSafe train cases and200 non-overlapping MedQA train cases, mixed50/50 per round. Repeated development exposure is disclosed. Main RxSafe/RxQA sets have historical exposure and are exploratory. MedPIC uses the pinned author release467, including108 multiple-answer questions. All stages freeze before independent inference; no best-test checkpoint selection occurs. One publicly viewed schema example remains in the predeclared denominator.

## 8. Drug-prior and patient-condition diagnostics

{short_table}

The35 pairs share identical option strings and all35 change the correct answer set when patient information changes. Option-remapping prediction agreement is{ss['permuted']['same_prediction_after_remap']}/70. No-vignette inputs retain the question/options, which can still contain clinical clues. Removing the vignette leaves24/70 exact answers unchanged, and option permutation changes22/70 mapped predictions. Thus shortcut robustness is not demonstrated. These controls assess context and position sensitivity; they cannot exclude all parametric drug priors or establish clinical quality.

## 9. Audits, costs and limitations

- Recounted{a['unique_evaluated_rows_audited']} distinct evaluation rows and{a['source_spans_checked']} exact source spans; receipts and numeric checks were revalidated. A declared post-freeze parser repair normalized list-valued search focus for two incomplete cases; the other986 saved predictions were hash-verified unchanged. Ten synthetic verifier/routing tests pass; these are software checks, not clinical validation.
- Root ledger:{root['n']} records,{root['quote_valid']} with verified supporting quotes. Reference-status judgments:{json.dumps(root['reference_status'])}. These model-generated categories do not prove GT errors.
- Enhanced source-request outcomes:{json.dumps(a['source_statuses'])}. An intended600-request cap overshot during initial concurrent fetching; cached responses and actual counts are retained, not hidden. Missing labels and query-limit fallbacks remain limitations.
- Shared new successful-response ledger increment: **USD{a['ledger_increment_usd_shared_37_38']:.6f}**, including all updater variants and final evaluation. Logical cached inference cost differs from newly billed responses; this is not an invoice.
- Source-span validity and narrow threshold checks do not establish correct complete prescriptions, full DDI handling, renal dosing, dose units, formulation strength or monitoring. Clinical annotations and real EHR execution remain unfinished.

## 10. Protocol correction and artifacts

**Correction:** original RxSafeBench already uses three-option MCQ (paper SectionII-C). Earlier local prose calling it free generation was wrong. Our local deduplication, ordering, grouped split and evaluation subset still differ, so published scores cannot be copied into the same-protocol main table. Historical hash-bound files remain archived with this correction.

- Current code/profile: `rxrsiagent/selected_agent.py`, `rxrsiagent/selected_profile.json`.
- Actor/checks: `upgrade_v40/agent40.py`; evidence tool: `upgrade_v37/evidence37.py`.
- Final learner and compact context: `upgrade_v44/learn.py`, `proposal_context.py`.
- Final states/gates: `upgrade_v44/results/learning.json`; independent trajectory and shortcut results alongside it.
- Freeze and audit: `upgrade_v44/test_freeze.json`, `upgrade_v44/results/audit.json`.
- Public per-case answer letters: `upgrade_v44/results/public_predictions.jsonl` (1,895 rows, no patient/source prose); its manifest independently recounts the totals.
- Current English ACL source: `paper/latex/v0.3/prismatic_v03_en.tex`; numbers are generated from audited artifacts. The paper does not rename earlier variants as different proposed methods.
- Raw benchmark data, downloaded label bodies, provider receipts, restricted records and credentials remain outside Git.

Sources: {links}
'''
 zh=f'''# RxRSIAgent：根因追踪、技能干预与独立验证结果

更新：2026年10月16日。本文为长期更新的当前结果，旧结果保留档案；论文方法统一叫 **RxRSIAgent**。

## 1. 这次实际做到了什么

- 当前冻结方法：**RxSafe {fmt(x)}；RxQA {fmt(y)}**。
- 独立 MedPIC：**{fmt(z['metrics'])}**；指南类{families['guideline_following']['correct']}/284，反事实类{families['counterfactual']['correct']}/183；同选项、改患者条件的35对题，成对全对{z['detail']['paired']['both_correct']}/35。
- {goals_zh}
- {conclusion_zh}

## 2. 监督校准是什么，为什么不算我们要的 RSI

之前556/988的结果包含一个普通逻辑回归：用625个带GT的病例训练，根据药名、药物/UNII与问题词的组合、LLM草稿选项，给候选答案打分。所有选项均为见过的短药名、且分数差≥0.2时，它可能覆盖LLM答案。它在527例RxSafe上生效，在RxQA上0例生效。

直观说，这是“从有答案的题里拟合一个选项打分器”，不是“发现自己在哪一步犯错→总结可复用程序→验证工具或技能更新”。药名单独作为特征就达到564/988，说明此前提升有明显先验捷径疑虑，不能解释成学会医生的处方思路。

**使用GT反馈本身不排斥agent进化；关键是更新了什么、有没有独立收益。** 新方法不再用这个打分器覆盖答案，也不检索训练题答案。可更新对象是流程技能、检索配置和条件识别词表。但代码有这些能力、存了反思记录，并不等于进化成功；仍需真实保留更新和独立任务前后提升。预训练模型原有的药物知识和偏好无法靠删除一个校准器全部消除。

## 3. 跨方法主表

{main_table}

统一推理骨干、相同问题。命名agent为固定作者代码后的本地任务适配实测，不是抄原论文分数。RxRSIAgent为3×1536输出token；**等输出额度不等于等输入成本、等调用数、等训练监督**。普通监督校准行使用此前的固定来源流程，作为单独对照，不能当作新actor的一项严格单因素消融。高额度MedAgents的208/300继续保留。SafeRx-Agent未测，不编造分数；药物集合方法不能填进QA准确率列。

## 4. 为什么之前的技能更新全部失败

旧八轮没有一轮通过第一组候选集，根本没有发生guard拒绝。两轮没有产生格式与角色都有效的技能；其余更新修复少于退步，例如修复9例却退步16例。根因不是简单“门槛太高”：

1. 反思看不到真实检索片段、中间评估和执行检查，只能泛泛总结。
2. 技能无条件注入所有题；相似正确题并不天然是该技能的反例。
3. 被拒更新的诊断没有有效回放。
4. 后续实测发现长上下文和长ID导致角色混淆；模型说换了ID，JSON却没换。
5. 年龄/妊娠的宽触发覆盖115/120个MedQA开发题，使103个正确降到97。
6. 条件检测器漏识别gestation等表述，妊娠技能连自己的支持例都不能触发。
7. 根因虽然保存，下一轮却只允许引用本轮根因；上一轮的有效线索被丢掉。
8. 合理的“证据不足，暂不更新”被误当格式错误，修复提示反而逼出缺乏支持的技能。

以上问题都对应真实轨迹或代码路径。已逐项修复，并保留修复后仍失败的结果。反思模型认为GT有歧义，**不等于已经证明GT错误**。

## 5. 现在的完整流程与进化设计

**推理：** 输入患者信息和选项→提取有原文出处的事实与药物角色→解析品牌/成分/途径与产品变体→均衡检索适应证、剂量、安全证据→逐项评估→执行引用、算式和明确年龄/eGFR/CrCl阈值检查→最终作答。缺失信息保留未知，没有数值校准器再改答案。

**学习：** 每100个新训练病例，比较GT和预测；保存最早可见偏差、证据、根因假设、最小修复与反例要求。累计使用过去根因、最近失败，以及两项“净修复为正但未达标”的候选。更新器每次只处理一个根因类别，用少量具备明确角色的病例和短ID。

可进化的三个对象：

- **技能记忆**：有可执行触发与排除条件的处理步骤。
- **检索配置**：窗口、产品变体数、证据预算或段落权重；每次最多改一项。
- **工具条件词表**：例如用训练原文中的一般条件表达修复检测遗漏；补丁需在失败例和成功例中有文本支持，但这并不独立验证每个词的临床含义。

骨干权重、工具可执行代码在一条学习轨迹内固定。人工修代码是研究者改进，不能记成agent自己进化。最终提案器为 **anthropic/claude-opus-4.8**，推理和最初根因反思仍为DeepSeek；因此属于外部模型辅助的agent状态学习，增加了离线训练计算，不能声称同模型完全自主递归。

保留规则：训练探针最多32例，净修复≥2且无效输出不增；RxSafe190/MedQA120候选集分别不下降、合计严格提高；RxSafe197/MedQA120守门集分别不下降。全部状态先冻结，再跑独立测试，不能用测试分数挑最好轮次。较早实验要求guard合计也严格提高；当前非退步门槛是在测试前声明的协议变化。明确的“不更新”会被保留，不再强迫改写。

## 6. 完成的迭代实验，而不只是计划

{up}

共{ntrial}次提案尝试，8组×4轮开发实验，**重复使用同一批400个训练病例，不是3200个独立病例，也不是8个独立随机种子**。v37补完整轨迹；v38修角色；v39收窄干预；v40加入条件词表；v41缩小上下文；v42用外部提案模型；v43保留合理拒绝；v44累计根因并回放有希望但未达标的干预。版本用于档案，论文只保留当前RxRSIAgent和机制对照。

## 7. 病例增加后，具体哪里增长、指标是否提高

{curve}

{conclusion_zh} 训练为200例既有RxSafe训练题＋200例排除重复后的MedQA训练题，每轮各50例。开发阶段重复使用这些训练数据。主bench在历史研究中已被观察，结果属于探索性。MedPIC采用固定作者revision的全部467题，其中108题为多选，按完整答案集合评分；一个事先看过的公开格式示例仍保留在预声明分母中。

## 8. 排除药名先验捷径的证据与边界

{short_table}

35对题的选项文本完全一致，患者条件变化后，35对的正确答案集合均发生改变。置换后映射回原选项，预测一致{ss['permuted']['same_prediction_after_remap']}/70。去患者背景仍保留题目和选项，其中可能残留临床线索。

当前没有训练药名频率打分器或训练题答案记忆；去掉背景后仍为24/70，置换选项使22/70个映射后预测变化，说明当前尚未通过捷径稳健性验证。这些诊断检验患者信息依赖与选项位置敏感性，**不能证明所有预训练先验或捷径都被排除**，也不能推出处方临床安全。

## 9. 审计、费用与尚未完成的能力

- 独立重算{a['unique_evaluated_rows_audited']}条不同的评测轨迹，核对{a['source_spans_checked']}处原始来源片段，复核响应、解析和可执行检查。两例因检索焦点为列表而中断，在冻结后做了确定性的类型转换；此前986例文件哈希逐一保持不变，未换预测。10项合成软件测试通过，不等于临床验证。
- 根因库共{root['n']}条，{root['quote_valid']}条支持引用可核对；参考答案判断分类为{json.dumps(root['reference_status'],ensure_ascii=False)}。它们是模型诊断，不能当作医生裁定。
- 增强说明书请求结果：{json.dumps(a['source_statuses'])}。初始并发请求使预期600次上限发生超出，实际数量和缓存均保留；来源缺失与请求上限仍限制检索。
- 本轮全部变体与最终评测，共新增成功响应账本费用 **USD{a['ledger_increment_usd_shared_37_38']:.6f}**。这是本地响应账本，不是供应商发票；逻辑推理成本包含缓存复用，另行统计。
- 数值比较只能验证明示条件，不覆盖单位、完整规则前提、全部DDI、完整肾功能给药、剂型强度、监测或完整处方。医生盲评和真实EHR状态操作尚未完成；不能用QA准确率代替。

## 10. 协议纠错、交付与后续判断

**纠正此前说明：RxSafeBench原论文已经是三选一MCQ，不是自由生成。** 原文II-C节可核实。本地去重、顺序、分组切分和评测子集仍不同，所以跨论文原始分数不能直接填入同协议主表。旧版哈希绑定文件保留档案，由本次纠错覆盖其错误描述。

当前英文论文：`paper/latex/v0.3/prismatic_v03_en.tex`，继续在原编辑器路径更新。核心代码：`upgrade_v40/agent40.py`、`upgrade_v37/evidence37.py`、`upgrade_v44/learn.py`及`proposal_context.py`；当前入口与冻结配置：`rxrsiagent/selected_agent.py`、`selected_profile.json`。另提供`upgrade_v44/results/public_predictions.jsonl`的1,895条公开题逐例答案字母与GT，便于重算；不含病例或说明书正文。最终逐轮状态、主表、独立任务、捷径实验及审计均在`upgrade_v44/results/`，测试前冻结在`test_freeze.json`。中英文完整结果同步本目录及`paper/CURRENT_RESULTS.*.md`。

{goals_zh} {conclusion_zh} 当前证据支持的是可追踪的实现改进和真实的失败归因。后续需要针对可靠、可重复的根因构造支持与反例，补足说明书之外的适用性证据，并使用新的独立最终测试验证；不能通过挑测试结果、药名统计或把人工修复算作RSI来达到目标。

来源：{links}
'''
 for lang,text in [('en',en),('zh',zh)]:
  pieces=re.split(r'(`[^`]*`)',text)
  for ii in range(0,len(pieces),2):pieces[ii]=re.sub(r'(?<![A-Za-z0-9_/])([A-Za-z]{2,})(?=[0-9])',r'\1 ',pieces[ii])
  text=''.join(pieces)
  (HERE/f'RESULTS.{lang}.md').write_text(text);(ROOT/'paper'/f'CURRENT_RESULTS.{lang}.md').write_text(text);(ROOT/'paper/versions'/f'v0.44-2026-10-16.{lang}.md').write_text(text)
 profile={'name':'RxRSIAgent','status':'Final development-gated state frozen before main and independent inference','model':'deepseek/deepseek-v4.1-flash','offline_proposer':'anthropic/claude-opus-4.8','state':states[-1]['state'],'actor_calls':3,'output_cap_per_call':1536,'calibration':None,'measured':{'rxsafe':{'n':988,'correct':x['correct']},'rxqa':{'n':300,'correct':y['correct']},'medpic':{'n':467,'correct':z['metrics']['correct']}},'selection':'upgrade_v44/results/learning.json','freeze':'upgrade_v44/test_freeze.json','audit':'upgrade_v44/results/audit.json','scope':'Offline single- or multi-option selection; no clinical clearance; no positive RSI claim from unretained proposals.','code_sha256':{p:sha(ROOT/p) for p in ['upgrade_v44/runtime.py','upgrade_v44/actor44.py','upgrade_v40/agent40.py','upgrade_v37/evidence37.py','upgrade_v37/common37.py','upgrade_v35/workflow.py','upgrade_v35/evidence.py']}}
 (ROOT/'rxrsiagent/selected_agent.py').write_text((HERE/'release_entrypoint.py').read_text());(ROOT/'rxrsiagent/selected_profile.json').write_text(json.dumps(profile,indent=2)+'\n');print(json.dumps({'main':profile['measured'],'accepted':totalaccepted,'attempts':ntrial}))
if __name__=='__main__':main()
