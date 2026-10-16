"""User-facing bilingual task map, trace case studies, and honest upgrade results."""
import json
from pathlib import Path
from common45 import ROOT, HERE, RUN, digest, save, ledger_total


def read(path):
    return json.loads((ROOT / path).read_text())


def main():
    patterns = read('upgrade_v45/results/training_patterns.json')
    cases = read('upgrade_v45/results/case_studies.json')
    mimic = read('upgrade_v45/results/mimic_recount.json')
    audit = read('upgrade_v45/results/audit.json')
    selection = {v: read('upgrade_v' + v + '/results/selection.json') for v in ('45', '46', '47')}
    scoped_audit = read('upgrade_v47/results/audit.json')
    protocol = read('upgrade_v45/protocol.json')
    summaries = []
    for arm, name in [('tools', 'Product-scope tools'), ('tools_contract', 'Tools + decision obligations'), ('whole_sentence', 'Tools + whole sentences')]:
        scores = []
        for split in ['train', 'proposal_rx', 'proposal_med', 'guard_rx', 'guard_med']:
            score = audit['outcomes'].get(arm + '-' + split)
            scores.append(f"{score['correct']}/{score['n']} ({score['fixes']} / {score['regressions']})" if score else '—')
        summaries.append('| ' + name + ' | ' + ' | '.join(scores) + ' |')
    scores = []
    for split in ['train', 'proposal_rx', 'proposal_med', 'guard_rx', 'guard_med']:
        score = scoped_audit['outcomes'].get(split)
        scores.append(f"{score['correct']}/{score['n']} ({score['fixes']} / {score['regressions']}; routed {score['routed']})" if score else '—')
    summaries.append('| Scoped product/sentence repair | ' + ' | '.join(scores) + ' |')
    experiment_table = '| Candidate | Train diagnostic | RxSafe proposal | MedQA proposal | RxSafe guard | MedQA guard |\n|---|---:|---:|---:|---:|---:|\n' + '\n'.join(summaries)
    mimic_rows = []
    names = {'retrieval_conditional_tool': 'Case retrieval + order tool', 'rxrsi_selected': 'Earlier supervised artifact agent', 'word_char_ensemble': 'Word/character ensemble + order tool'}
    for method, name in names.items():
        m = mimic['methods'][method]
        mimic_rows.append('| ' + name + ' | ' + ' | '.join(f"{100*m[k]['mean']:.2f}" for k in ['drug_precision', 'drug_recall', 'drug_f1', 'core4_f1', 'order5_f1']) + ' |')
    mimic_table = '| Historical method | Drug precision % | GT drug recall % | Drug F1 % | Core-4 F1 % | Order-5 F1 % |\n|---|---:|---:|---:|---:|---:|\n' + '\n'.join(mimic_rows)
    case_rows = []
    for case in cases:
        path = RUN.parent / 'rxrsi-v46/runs/whole_sentence/train' / (digest(case['case_id']) + '.json')
        refined = json.loads(path.read_text())
        case['candidate']['whole_sentence'] = {'prediction': refined['prediction'], 'trace_sha256': __import__('hashlib').sha256(path.read_bytes()).hexdigest()}
        def name(answer):
            return '/'.join(answer) if answer else 'invalid'
        case_rows.append('| ' + case['case_id'].replace('medqa_train_', '')[:12] + ' | ' + case['gold'] + ' | ' + name(case['baseline']) + ' | ' + name(case['candidate']['tools']['prediction']) + ' | ' + name(case['candidate']['tools_contract']['prediction']) + ' | ' + name(refined['prediction']) + ' |')
    save(HERE / 'results/case_studies.json', cases)
    case_table = '| Case ID prefix | GT | Before | Product tools | + obligations | + whole sentences |\n|---|---|---|---|---|---|\n' + '\n'.join(case_rows)
    accepted = {v: x['accepted'] for v, x in selection.items()}
    cost = ledger_total() - protocol['ledger_start_usd']
    sources = '''
- [RxSafeBench, original three-option protocol](https://arxiv.org/html/2511.04328v1)
- [RxQA author repository: 300 released OpenFDA questions; BNF unavailable](https://github.com/Google-Health/rxqa)
- [MedPIC-Bench paper](https://arxiv.org/abs/2608.03028)
- [MIMIC-IV prescriptions fields](https://mimic.mit.edu/docs/iv/modules/hosp/prescriptions.html)
- [FDA: homeopathic products](https://www.fda.gov/drugs/information-drug-class/homeopathic-products)
- [BiDil combination label, including adjunct-therapy qualification](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=e1e63cd5-d1e4-4af5-bad5-1ad41ea46b00)
- [CDC diphtheria clinical guidance](https://www.cdc.gov/diphtheria/hcp/clinical-guidance/index.html)
'''
    zh = f'''# RxRSIAgent：失败病例、任务边界与 MIMIC-IV 实际进展

更新：2026-10-16。本次新跑工具修复候选，重新计分旧 MIMIC 预测；主表冻结方法保持原样。当前三个公开任务并不等于完整开处方。

## 1. 三个 bench 分别测什么？

| 数据集 | 输入与输出 | 当前样本 | 可以说明什么 | 不能代替什么 |
|---|---|---:|---|---|
| RxSafeBench | 模拟问诊中的禁忌/相互作用风险；三个药物选项中选一个 | 本地测试 988；原论文 2,443 场景 | 情境下药物选择准确率 | 一整张处方的漏开、多开、剂量与频次 |
| RxQA | 基于药品说明书的用药推理；四选一 | 全部公开 OpenFDA 300；原研究另有 BNF 300 未公开 | 说明书知识与用药推理准确率 | 多药处方覆盖率及实际订单执行 |
| MedPIC-Bench | 患者条件与用药决策，包括患者信息改变的反事实题；单选或多选 | 467；其中 108 多选；本地识别 35 对同选项反事实病例 | 完整答案集合准确率、两病例同时正确率、条件敏感性 | 无候选集的自由处方生成 |

所以先前 49.70%、65.33%、58.67% 是答题准确率，不能称为“处方覆盖率”。多选题的完整集合匹配也仍是给定选项上的判断。

## 2. 真正的处方应怎样评分？

设预测药物集合 P、记录的目标药物集合 G：GT 覆盖率/召回率 = |P∩G|/|G|；精确率 = |P∩G|/|P|。必须同时报告 precision、recall、F1、Jaccard、漏开数、多开数、平均药物数及空输出率。只提高覆盖率可能只是开了更多药。

还需报告药物＋途径＋剂量＋单位＋频次的联合完全匹配，并把缺失字段比例写清楚。分别匹配每个字段不能证明它们组成了一张正确订单。历史记录外的药物称“相对 GT 多出”，不能未经临床判断就称不当用药。

三个不同的“覆盖率”不能混淆：①模型召回了多少 GT 药物；②原始药物行有多少成功映射进标准药物空间；③GT 有多少完整剂量/频次字段。病情治疗目标覆盖、安全与合理性则需额外标注或可信规则，无法仅由药物集合计算。

## 3. MIMIC-IV 做过，而且有 prescription GT

### A. 已完成：按记录可用时间预测下一窗口订单

- MIMIC-IV 3.1，入院后 6 小时决策，预测后续 6 小时的新开/变更订单。输入仅使用决策前已记录的医嘱和化验；未来诊断和化验不进入输入。
- 训练 40,000、proposal 2,000、guard 2,000；测试 **1,082 次入院、1,024 名患者**，患者不跨集合。
- GT 来源于 prescriptions，与 POE/pharmacy 的身份和录入时间核对。128 个训练期原始规范化药名；未入词表 GT 仍计入召回分母。
- 本次从保存的预测**本地重新计分三种方法、三个种子**，与旧 drug/core-order F1 逐一一致。没有重新训练，也没有把受限病例发给 API。

{mimic_table}

表中为三个种子均值。Core-4 = 药名、途径、剂量、单位；Order-5 再加入频次，是本次新增的事后描述性计分，不用于挑模型。GT 原始订单行的五字段完整率为 **60.20%**，五字段指标只对完整的观测元组计分，不能说覆盖所有订单。不同字段定义的分数不能混合。

旧 agent 的药物召回率较高，但精确率与 F1 低于集成对照。这些旧模型主要是监督学习及订单模板，不是当前的 LLM RxRSIAgent，不能把旧成绩改个名字放入当前方法主表。

### B. 已有开发结果、最终比较未完成：ATC-L4 住院药物集合

另一条线有 7,115 个训练患者、18,429 次训练住院、271 个 ATC-L4 类；预留测试 890 患者/2,422 次住院。全住院诊断/操作码是输入，所以它是回顾性整次住院集合任务，不能冒充入院即刻可用的输入。

已实际训练并核验部分 ARMR、GAMENet、SafeDrug 与规则记忆对照；当前可引用的是开发集结果，完整最终测试主表尚未完成。NDC→ATC 映射只覆盖所选原始 prescription 行的 **27.23%**；分子共同空间另为 219 类。不能把映射子集称为完整处方 GT。

因此，论文的完整开处方主张仍缺：**将当前 RxRSIAgent 接入明确时间点的 MIMIC 订单任务，并完成同患者切分、同药物空间、同输入与预算的比较**。公开 QA 应作为机制和安全推理次级证据。

## 4. 失败 case study：先定位失真发生在哪一步

以下均来自公开**训练病例**，用来开发修复，不能当独立泛化成绩。GT 是数据集参考答案；不因此宣称其他药物临床绝对错误。

### Case 1：同名成分不等于同一种可用产品

`e7a30d739ee5b9be`：贫血相关问诊，GT=A 硫酸亚铁，原答案=C 富马酸亚铁。旧检索返回硫酸亚铁同名的顺势疗法产品，适应描述是潮热；模型据此排除 A。旧源读取器丢掉了 `spl_unclassified_section`，该字段恰好声明产品是 homeopathic。

共性规律：必须核对产品类别、成分组合、剂型、途径，不能只匹配药名或 UNII。已实现完整元数据读取、显式产品类别核验；不能仅因 OTC 标签就排除产品，也不能因出现在 openFDA 中便称 FDA 批准。修复后此题回到 A。

### Case 2：联合方案的证据不能由两个单药说明书拼出来

`3c3087307869…`：高血压合并左室功能不全心衰，题干给出 African American 患者背景。GT=C 硝酸异山梨酯＋肼屈嗪，原答案=B 氨氯地平＋缬沙坦。旧工具只有拆开的单药证据。

第一轮已检索到联合制剂，但仍错：字符窗口从句子中间开始，丢掉适用人群条件。第二轮保留完整条件句后，此题改为 C。联合制剂说明书含“标准治疗的辅助治疗”等限定；这一病例改善不证明单凭人口属性就应开药。

共性规律：验证“问题所问的方案—证据描述的方案”是否一致；检索命中后还要检查条件在截取与预算压缩中是否丢失。

### Case 3：相关病史被误当成明确禁忌条件

`20084f0b868433c8`：题干提及肾病和定期输血，GT=A Injectafer，原答案=C 硫酸亚铁。原推理把输血补成透析，继而用非透析 CKD 的适应范围排除 A；原文没有支持这个等价关系。

工具修复后答案为 A，但新增核验指令的候选仍为 C。**加入“请核验”文字不保证模型真正消除错误前提。** 新工具保留未知条件；来源引用核验也仅证明有这段文字，并不证明该文字支持全部临床推论。GT 匹配改善不能视为已验证的临床处方建议。

### Case 4：证据缺失时，时间阶段仍然推错

`c4e678277e78…`：题目问上次已经出现感染症状入院时，什么干预能预防后来的心肌损害；GT=D 靶向循环毒素的免疫球蛋白，原答案=A 类毒素疫苗。模型认出了疾病，却把急性期治疗时间点理解为事前免疫。

三个候选都仍然答 A。CDC 临床指导区分呼吸道白喉的抗毒素/抗菌治疗与后续免疫安排。该失败说明药品说明书不是所有决策的完整证据源，下一层需要指南证据和治疗时间阶段核验，不能靠重复泛泛反思解决。

### Case 5：没有检索到警告，不等于更安全

`1dfc1ce34019…`：孕 28 周的尿路感染题，GT=B 呋喃妥因，原答案=D 头孢氨苄。原推理一面承认足月禁忌不适用于 28 周，一面因另一药的片段未见妊娠禁忌就偏向它。产品工具修复后选择 B。它说明证据缺口不能成为安全优势；并不证明所有妊娠 UTI 只能用该参考药。

{case_table}

## 5. 共性出现多少次？

检查全部 400 个既有训练轨迹，原来错 {patterns['wrong']} 题。原反思器把 84 例归为最终选择、32 例归为产品选择、8 例归为输入理解、7 例归为适用性；**这是模型的根因假设分布，不是因果裁定**。

可执行结构检查发现：多个选项共享成分的病例 8 例（原错 2）；需要联合方案检索的病例 10 例（原错 2）。完整来源补查发现的顺势疗法匹配数量及病例 ID 见 `training_patterns.json`；由于仅补查本轮涉及的来源，该数是下界。这些机制解释部分失败，不能声称解释全部 131 个错误。

## 6. 从规律到代码，再到实际验证

前三个修复候选分别是：①产品范围工具；②工具＋带引文的决策条件核验；③工具＋完整句子证据。随后增加第四个**有边界的路由**：只有原产品被完整来源明确标为顺势疗法，或原计划显示选项含联合方案，才启用③；其他病例逐字复用原证据和调用。路由只读输入/来源，不读答案或预测得失。

它们共享原计划调用，每例最多 3×1,536 输出 token、18,000 字符来源预算；新的来源请求和输入 token 成本不等同于旧方法。前三个候选的数据读取/窗口/排序一起改变，因此不能把整体差异归因于某一项补丁。

{experiment_table}

括号为“修复 / 退步”，都相对于冻结旧 actor。前三个候选训练诊断基线 55/85；路由候选另在全部 400 个训练病例上检查，基线 269/400，不能直接与85例分数比较。proposal 基线 RxSafe 99/190、MedQA 103/120；guard 基线 104/197、102/120。85 例由按哈希固定抽取的 80 例与 5 个明确失败案例组成，不能当随机独立测试。

验证规则在相应候选推理前冻结：proposal 每项任务均不退步、合计严格提高且无效输出不增；再在独立划分的 guard 上逐任务检查不退步。路由是在已看到全局改动的开发结果后设计，不能声称从未观察开发反馈。它们均为历史重复使用的开发集合。当前门控结果：{json.dumps(accepted)}。`false` 表示不接受；未通过 proposal 的候选不继续跑 guard。主方法未被这些开发结果自动替换，主测试分数没有重写。

这些是**研究者从失败轨迹总结规律后的工程修复**。尚不能称 agent 自主 RSI，也没有新独立任务的逐轮进化证据。长期 RSI 应记录失败证据→可检验根因→有边界的工具/技能改动→支持例修复与反例不退步→独立确认，并允许拒绝失败更新；根因总结本身不是性能收益。

## 7. 交付和下一项实质缺口

本次已交付代码、五例完整对照、{audit['rows']} 条全局修复候选预测＋{scoped_audit['rows']} 条路由候选预测（同一病例不同条件重复计行），{audit['source_spans']} 处全局来源片段核验，以及 MIMIC 的三种方法/三个种子本地重计分。新增成功响应账本费用 USD {cost:.4f}。主表继续使用冻结旧方法，不能用训练病例修好来宣称测试集已超越对照。

来源获取共 {audit['source_requests']} 个缓存请求，状态为 {json.dumps(audit['source_status'])}；达到800请求上限后未获取的新来源明确保留未知。上限与来源缺失可能限制结果。作用域路由使用冻结的来源分类注册表，不知道分类的产品不会触发；因此它也不能保证识别所有产品错配。

完整处方方向的下一项工作应是沿用 MIMIC 的记录时间协议，补足药物身份/候选召回与可观测订单字段，再接当前 agent；同时保留历史强监督模型、检索与医学 agent 对照。不要继续把全部开处方能力压缩为选项准确率。

结果：`upgrade_v45/results/`、`upgrade_v46/results/`；原 MIMIC：`upgrade_v21/RESULTS.en.md`；ATC 开发：`upgrade_v27/results/development_methods.json`。受限病例与订单预测留在本地，公开仅汇总数据。

## 来源
{sources}
'''
    en = f'''# RxRSIAgent: failure cases, task boundaries, and actual MIMIC-IV progress

Updated 16 October 2026. New results concern researcher-authored tool repairs on development data and a local recount of frozen MIMIC predictions. The main-table actor is unchanged.

## 1. What the three public benchmarks measure

| Dataset | Task | Evaluated size | Endpoint |
|---|---|---:|---|
| RxSafeBench | Three-option medication choice after simulated contraindication/interaction consultations | Local test988; original paper2,443 scenarios | Single-choice accuracy |
| RxQA | Formulary-grounded medication reasoning, four options | All300 public OpenFDA questions; another300 BNF questions are not released | Single-choice accuracy |
| MedPIC-Bench | Patient-conditioned medication decisions and counterfactuals; single/multiple answers |467, including108 multiple-answer questions;35 strict same-option pairs locally identified | Exact answer-set accuracy and both-members-correct |

These are choice tasks. The current49.70%,65.33%,58.67% results are not complete-prescription coverage. For open medication sets P and G, report recall |P∩G|/|G| together with precision |P∩G|/|P|, F1, Jaccard, misses, extras, prescription size and empty outputs. Increasing recall alone can reward excessive prescribing. Extras relative to a recorded reference are not automatically clinically inappropriate.

Full orders require joint drug/route/dose/unit/frequency matching and missing-field denominators. Drug recall, source-row mapping coverage and complete-GT-field coverage are different quantities. Clinical treatment-goal coverage and safety require additional reliable rules or annotation.

## 2. MIMIC-IV was evaluated, but not with the current QA actor

The completed time-controlled task uses MIMIC-IV3.1 admission+6h and predicts newly entered/changed orders over the next6h. Inputs exclude future results and untimed discharge diagnoses. Prescriptions are linked to provider/pharmacy entry times. Patient-disjoint splits contain40,000 training,2,000 proposal,2,000 guard and1,082 test admissions (1,024 test patients). The initial128 normalized-name vocabulary is fixed; OOV reference drugs remain in recall denominators.

We locally recounted saved predictions for three methods and three seeds; every drug/core4 F1 agrees with its original report. No new model inference or restricted-data API call was performed.

{mimic_table}

Means are across three seeds. Core4 uses drug, route, dose and unit. Order5 additionally requires frequency; it is a new post hoc descriptive endpoint, not a selection criterion. Only60.20% of reference order rows contain all five fields, and exact-tuple scoring uses complete observed tuples. The earlier agent raises recall but loses precision/F1 to the ensemble. It is a supervised artifact-learning pipeline, not the current LLM RxRSIAgent; its scores must not be relabeled as current-method results.

A separate retrospective completed-visit ATC-L4 task has7,115 training patients/18,429 training visits and271 classes, with890 patients/2,422 visits reserved for test. It uses completed-visit diagnosis/procedure codes, not prospective admission-time observations. ARMR/GAMENet/SafeDrug and rule-memory work has audited development results, but its full final-test comparison remains unfinished. Public NDC mapping covers only27.23% of selected prescription rows; the molecular shared panel has219 classes. Neither is complete prescription GT.

The outstanding prescribing claim therefore needs the current RxRSIAgent evaluated on an explicit decision-time MIMIC order task, against shared-split, shared-space, shared-input comparators. Public QA should remain complementary mechanism evidence.

## 3. Five inspectable training cases

All examples below were used for development. A dataset answer is a reference, not an adjudication that every alternative is clinically unacceptable.

1. **Product scope (e7a30d739ee5b9be).** Reference A=ferrous sulfate; original C=ferrous fumarate. The old retriever selected a same-ingredient homeopathic product whose indication concerned hot flashes. Its reader discarded the `spl_unclassified_section` containing the homeopathic classification. Full metadata and explicit product-scope filtering restore A. OTC status alone must not exclude a product, and an openFDA record does not establish approval.
2. **Regimen and evidence-window scope (3c3087307869…).** Reference C=isosorbide dinitrate/hydralazine; original B=amlodipine/valsartan. The question describes hypertension and left-ventricular heart failure in an African American patient. Component-only retrieval omitted combination evidence. Adding the combination label still failed because character-window truncation lost its population qualifier. Preserving the full sentence changes this example to C. The label's adjunct-to-standard-therapy condition remains relevant; demographic membership alone is not a sufficient prescribing rule.
3. **Unsupported patient inference (20084f0b868433c8).** Reference A=Injectafer; original C=ferrous sulfate. The original assessment inferred dialysis from recurrent transfusions and used that invented condition to exclude A. The product-tool arm selects A, whereas the added-obligation arm still selects C. Requesting verification does not guarantee removal of the premise; exact quotation checks do not verify full clinical entailment.
4. **Unresolved treatment phase (c4e678277e78…).** The question asks about an intervention during a previous admission with active infection that could prevent subsequent myocardial injury. Reference D=antitoxin-targeting immunoglobulin; original A=toxoid vaccination. All three candidates remain A. CDC guidance distinguishes acute respiratory diphtheria treatment from immunization. Label-only retrieval and generic self-reflection do not resolve this timing error.
5. **Absence-of-warning shortcut (1dfc1ce34019…).** In a28-week pregnancy UTI question, reference B=nitrofurantoin versus original D=cephalexin. The old explanation recognized that a term-pregnancy restriction did not apply, yet preferred the other drug partly because its excerpts lacked a pregnancy contraindication. Product retrieval changes the answer to B. This is a reference-agreement observation, not proof that every such patient has one uniquely valid treatment.

{case_table}

## 4. Recurring patterns and executed repairs

Across all400 prior training traces,131 were wrong. The model's root hypotheses placed84 at final selection,32 at product selection,8 at input interpretation and7 at applicability. These are hypotheses, not causal adjudications. Structural checks find8 cases with shared ingredients across options (2 wrong), and10 with multi-component options requiring regimen retrieval (2 wrong). Full-source homeopathic matches are a lower bound because only newly requested sources can recover discarded metadata. These mechanisms explain only part of the error population.

The repair bundle reads full metadata, excludes explicitly homeopathic evidence from conventional-product matching, resolves combination ingredients, retains shared-component option roles and balances evidence across alternatives. A second candidate adds patient/source-bound decision obligations; a further repair expands source windows to whole sentences without silently dropping their qualifications. Support quotes prove provenance, not semantic entailment. No drug-to-answer lookup or learned drug-name scorer is introduced.

{experiment_table}

Parentheses denote fixes/regressions versus the frozen actor. Baselines: train55/85 for the first three arms; the scoped arm separately uses all400 training cases, baseline269/400. Proposal baselines are99/190 RxSafe and103/120 MedQA; guard104/197 and102/120. The85-case diagnostic contains80 hash-selected training cases plus5 selected failures. It is not an independent random test, and its score is not directly comparable with the400-case scope analysis.

The fourth candidate routes to the sentence-preserving tool only when original source metadata explicitly classifies a selected label as homeopathic, or the original plan identifies a joint-regimen option. Otherwise it preserves the original evidence and requests. Routing reads no reference answer or correctness outcome. It was designed after observing the global-repair development scores; this exposure is disclosed. Unknown product classifications do not activate it, so detection is incomplete.

Before new inference, the gate required no per-task proposal regression, strictly positive pooled gain, and no invalid-output increase; a selected candidate then faces separate per-task guard non-regression. Both are historically reused development cohorts. Gate outcomes: {json.dumps(accepted)}. Failed proposal candidates do not run guard. The current main actor and test scores are not replaced by these development findings.

All arms reuse the same initial planning request and allow3×1,536 output tokens and18,000 source characters. Source-query volume and actual input costs differ. These are researcher-authored failure-directed repairs, not successful autonomous RSI. A real evolution claim still requires retained executable changes and benefits on an independent task, beyond reflection-ledger growth.

## 5. Deliverables

Released: code, five paired case studies, {audit['rows']} global-repair prediction rows plus{scoped_audit['rows']} routed prediction rows (cases repeat across conditions), verification of {audit['source_spans']} global-repair source spans, and a local three-seed MIMIC recount. Incremental successful-response ledger cost: USD{cost:.4f}. Patient/source prose and restricted individual records remain local. Main-table scores retain their frozen provenance.

The full-source cache has{audit['source_requests']} requests with statuses {json.dumps(audit['source_status'])}. Requests beyond the800-query cap remain unavailable. Source failures and caps may limit outcomes. The global repair also changes source windows/ranking and metadata jointly; its aggregate effect is not an isolated causal estimate of a single patch.

The next substantive prescribing work is to connect the current agent to the recorded-time MIMIC order protocol, improve identity/candidate coverage and observable order fields, and compare with strong supervised, retrieval and medical-agent controls. QA accuracy alone cannot establish complete prescribing.

## Sources
{sources}
'''
    for language, text in [('zh', zh), ('en', en)]:
        (HERE / ('RESULTS.' + language + '.md')).write_text(text.rstrip() + '\n')
        (ROOT / 'paper' / ('TASKS_CASES_AND_MIMIC.' + language + '.md')).write_text(text.rstrip() + '\n')
    save(HERE / 'results/delivery.json', {'accepted': accepted, 'cost_increment_usd': cost,
        'current_actor_replaced': False, 'new_main_test_result': False, 'mimic_new_inference': False})
    print('Bilingual case/task/MIMIC report written')


if __name__ == '__main__':
    main()
