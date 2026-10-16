"""Bilingual report from frozen aggregate evidence; no inference or selection."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent;HERE=ROOT/'upgrade_v35'
def main():
 a=json.loads((HERE/'results/audit.json').read_text());v=json.loads((ROOT/'upgrade_v36/results/audit.json').read_text());m=a['methods'];diag=json.loads((HERE/'results/calibration_diagnostics.json').read_text());curve=json.loads((HERE/'results/calibration_curve.json').read_text())['curve'];rows=[]
 for key,name in [('grasp','GRASP'),('medagents','MedAgents'),('mdagents','MDAgents'),('calibrated','**RxRSIAgent**')]:
  s=m[key]['test'];q=m[key]['rxqa'];rows.append(f"| {name} | {s['correct']}/988 ({100*s['accuracy']:.2f}%) | {q['correct']}/300 ({100*q['accuracy']:.2f}%) | {s['mean_calls']:.2f} / {q['mean_calls']:.2f} | {s['invalid']} / {q['invalid']} |")
 table='\n'.join(rows);arows='\n'.join(f"| {name} | {m[k]['test']['correct']}/988 | {m[k]['rxqa']['correct']}/300 |" for k,name in [('no_evidence','No evidence / 无证据'),('old_evidence','Old lookup / 原名称检索'),('verified_evidence','Verified source / 来源核验'),('calibrated','Selected full agent / 选定完整方法')]);crows='\n'.join(f"| {x['cases']} | {x['features']:,} | {x['proposal']['correct']}/190 | {x['guard']['correct']}/197 | 0 / 0 |" for x in curve);drows='\n'.join(f"| {k} | {x['splits']['proposal']['correct']}/190 | {x['splits']['guard']['correct']}/197 | {x['splits']['test']['correct']}/988 |" for k,x in diag['arms'].items());billed= json.loads((HERE/'results/billing_close.json').read_text())['ledger_total_usd']-json.loads((HERE/'protocol.json').read_text())['ledger_start_usd'];total=billed+v['ledger_increment_usd']
 en=f'''# RxRSIAgent: completed evidence, calibration and matched-output experiments

Updated 16 October 2026. Versioned evidence: v35 main experiment and v36 independent follow-up. Method name remains **RxRSIAgent**. [English ACL source](../paper/latex/v0.3/prismatic_v03_en.tex).

## 1. Findings

- Selected RxRSIAgent: **556/988 (56.28%) RxSafeBench;199/300 (66.33%) RxQA**.
- Relative to the prior retained agent501/988 and183/300: **+5.57 and+5.33 percentage points**. These are historical descriptive changes, not a causal matched-budget ablation.
- RxSafe exceeds matched-output GRASP495/988 by6.17pp, paired scenario-bootstrap95% interval[2.84,9.63]. It exceeds earlier GRASP502/988 descriptively by5.47pp.
- RxQA remains below matched-output MedAgents200/300 by0.33pp and higher-allowance MedAgents208/300 by3.00pp. The latter paired interval is[-8.33,+2.33]pp. **The two-benchmark superiority target is not achieved.**
- Gains come from ordinary supervised calibration, not proven autonomous skill evolution. Strong identity-only controls expose a shortcut risk.

## 2. Main table: other methods on the same questions

Same served model `deepseek/deepseek-v4.1-flash`. Each row permits4608 generated output tokens/case. Author adapters preserve their workflow within an80-call ceiling; RxRSIAgent uses3×1536 and GRASP one call. **Equal output allowance does not equal input cost, training supervision or number of calls.** MedAgents/MDAgents are task-adapted author workflows; GRASP uses the pinned author core and previously selected skill. These are executed local results, not imported paper scores.

| Method | RxSafeBench derived test | RxQA OpenFDA | Mean calls S/Q | Invalid S/Q |
|---|---:|---:|---:|---:|
{table}

Higher-allowance results remain visible:

| Method | Total output allowance | RxSafe988 | RxQA300 |
|---|---:|---:|---:|
| MedAgents |24000|468 (47.37%)|208 (69.33%)|
| MDAgents |24000|478 (48.38%)|199 (66.33%)|
| GRASP earlier run |512|502 (50.81%)|189 (63.00%)|

MedAgents' matched-output failures:78/14 budget exhaustion and3/2 invalid finals (RxSafe/RxQA). MDAgents:8/7 exhaustion and10/2 invalid finals. Invalids are retained in denominators. SafeRx-Agent is unexecuted; GAMENet/SafeDrug medication-set scores do not belong in QA accuracy columns. No global SOTA claim is supported.

## 3. Datasets and selection

RxSafeBench:2443 source rows become2000 deduplicated local option tasks;625 train,190 proposal,197 guard,988 evaluation. This is a derived three-option task, not the original free-generation metric. RxQA:all300 public OpenFDA questions; no licensed BNF subset. Main benchmarks have historical exposure and remain exploratory.

New independent development uses the public MedQA training mirror (revision `153e61cdd129eb79d3c27f82cdf3bc5e018c11b0`, source train10178). An input-only medication/treatment keyword plus one option longer than6 words gives784 eligible cases; hash order selects120 proposal and120 guard. Exact overlap with earlier local benchmark texts is excluded. These are general medical exam questions, including some references to unavailable images, not a curated dose dataset. The mirror and parquet hash are pinned in `upgrade_v36/protocol.json`; raw data is not uploaded.

## 4. What changed in the agent

1. Call1 extracts patient facts with input quotations, drug entities, explicit route and question intent.
2. Label tool rejects unrelated fixed-combination products, handles generic/salt/brand identity, exposes UNII and available routes, and excludes explicit route conflicts. It returns balanced indication/dose/safety windows with source IDs and offsets.
3. Call2 assesses each option, proposes citations and source-bound arithmetic.
4. Deterministic tools check exact quotations and bounded arithmetic. They do not validate clinical applicability, units, renal dosing or complete DDIs.
5. Call3 chooses a final option with remaining uncertainty.
6. A frozen supervised logistic calibrator may override short, previously observed medication names when its probability gap is≥0.2. After an override, the old explanation is explicitly separated and is not presented as justification for the new choice.

Current entry: `rxrsiagent/selected_agent.py`; profile: `rxrsiagent/selected_profile.json`. Historical `core.py` and `evaluated_profile.json` preserve their old audits and are not the current main-table entry.

## 5. Controlled components and attribution

| Configuration | RxSafe988 correct | RxQA300 correct |
|---|---:|---:|
{arows}

Verified retrieval alone **regresses** on RxSafe test, despite improving proposal94→103 and guard98→102 against the no-evidence control. RxQA source availability rises from1/300 under old name lookup to267/300. Availability is not relevance or correctness. The selected calibrator fixes118 source-agent test errors and regresses34, adding8.50pp [6.08,10.93]. It applies527 times on RxSafe and0 on RxQA.

The numerical module uses draft, normalized medication-name indicators and medication/UNII×focus words. It uses ordinary logistic regression; C grid0.1/1/10 and margin grid0/.05/.1/.2/.3. Proposal selects C10,margin0.2:110/190; guard116/197 versus102. Model hash freezes before test. There are no answer-position or case-ID features.

### Post-selection diagnostic controls

Fixed C10 and margin0.2; none replaces the selected main model using test performance.

| Features | Proposal | Guard | RxSafe test |
|---|---:|---:|---:|
{drows}

Identity-only scoring reaches564/988 and context interactions without a draft574/988, above the selected full model556. This weakens a claim that the full architecture is necessary or that all gain reflects clinical reasoning. New medication combinations and independently constructed tasks are required for confirmation.

## 6. What evolves as cases increase

Two four-round language-memory attempts require applicability, exclusion conditions, supporting failures and successful counterexamples. Every proposed update is rejected. No text card is retained. The numeric state is learned by ordinary supervised optimization; tools, prompts and backbone weights do not evolve during learning.

| Cumulative cases | Numeric features/weights | Proposal | Guard | Retained text cards run1/run2 |
|---:|---:|---:|---:|---:|
{crows}

These are **post hoc fixed-hyperparameter prefix diagnostics**: C and margin were selected using all625 training cases and development feedback. They are not a prospective onlineRSI study. Proposal accuracy is nonmonotonic. Guard growth alone does not prove independent transfer.

## 7. Continued independent experiments, including failures

| Candidate | Proposal120 | Fixes/regressions vs static | Decision |
|---|---:|---:|---|
| Static source agent |99|reference|control|
| Expanded dose/population sections |99|4/4|rejected|
| Independent draft + contradiction review |99|7/7|rejected|
| Retrieval of3 training examples from9936 cases |99|5/5|rejected|

All three candidates retain3×1536 call allowance. The last uses extra external training data, so is not equal-data. None strictly improves proposal; **guard and RxQA are not run for these candidates**. The240-case cohort was prepared, but only its120 proposal cases were needed. Earlier active second retrieval also fails103→100/190. Failure gates prevent test-driven cherry-picking; they do not guarantee that the retained configuration generalizes.

## 8. Cases and clinical boundary

Deterministically choose the first lexical calibration fix and regression (post hoc public examples):

- `0445a1cf61c5e4ac`:risperidone→sertraline, matching the reference. The old rationale supports risperidone and cannot justify the overridden answer. This is a reference correction, not established clinical improvement.
- `0d0cc811ec14bfd3`:griseofulvin→ketoconazole, creating an error. The source rationale also overgeneralizes from one shampoo product label. Both calibration and applicability remain imperfect.

Eight synthetic software tests pass;24735 original and1556 follow-up source spans are checked. No clinician ratings are fabricated. Fourteen clinician-oriented endpoints, including treatment-goal coverage, major-error cases, joint clinically correct orders and unnecessary medication, remain awaiting the two reviewers. QA accuracy is not prescription execution or clinical safety.

## 9. Audit, cost and reproduction

- Main audit: `upgrade_v35/results/audit.json`; test freeze: `upgrade_v35/test_freeze.json`.
- Follow-up: `upgrade_v36/results/audit.json`; calibration diagnostics: `upgrade_v35/results/calibration_diagnostics.json`.
- Main successful-response ledger increment:USD{billed:.6f}; follow-up:USD{v['ledger_increment_usd']:.6f}; total:USD{total:.6f}. This is the local response ledger, not a provider invoice. Logical full-inference costs include cached responses and are reported separately.
- 1655 receipt references differ from the latest exact-request cache because concurrent identical calls can yield different raw responses; per-case raw receipts are authoritative. This count includes repeated references. No claim of identical planner samples in v35; v36 adds cross-process request locks.
- Source requests are cached with statuses, including missing sources and HTTP errors. No missing evidence is converted to “safe.”
- Raw benchmark traces, downloaded labels, credentials and trained pickle remain local. Code, aggregates and hashes are tracked.

Reproduction uses Python3.9 with numpy/scipy/scikit-learn/pandas/pyarrow and the existing public client. After restoring the local input/cache manifests, run the stage CLIs in the README; audits run without new API calls. Do not rerun `prepare.py` over an existing experiment directory because it starts a new ledger/split record.

## 10. Remaining research target

The two-benchmark win and convincing autonomous RSI are **not complete**. Priority:build independent label-grounded dosing/applicability tasks, fix product-strength/release-form matching, validate clinical rules, and compare calibration against ordinary supervised baselines on unseen medication combinations. Choose subsequent configurations on new development data; reserve a new final test before further optimization. Real order execution and blinded clinical endpoints are separate required evidence.

Primary sources: [openFDA](https://open.fda.gov/apis/drug/label/), [MedQA author repository](https://github.com/jind11/MedQA), [RxQA official release](https://github.com/Google-Health/rxqa). Historical runs and rejected candidates remain versioned; only the selected configuration appears as RxRSIAgent in the main paper.
'''
 zh=f'''# RxRSIAgent：证据工具、经验校准与等输出预算实验结果

更新：2026年10月16日。版本档案为v35主实验和v36独立开发续实验，论文方法统一叫 **RxRSIAgent**。[英文ACL论文](../paper/latex/v0.3/prismatic_v03_en.tex)。

## 1. 本轮实际成果

- **RxSafeBench：556/988，56.28%；RxQA：199/300，66.33%。**
- 相比上一保留方法501/988和183/300，分别提高 **5.57pp、5.33pp**。这是跨轮次描述性变化，不能当作相同预算的单因素因果结论。
- RxSafe超过等输出预算GRASP的495/988，增益6.17pp，配对场景bootstrap95%区间[2.84,9.63]；相对之前GRASP502/988，描述性提高5.47pp。
- **RxQA没有超过最强已运行医学agent**：等输出预算MedAgents是200/300；高预算MedAgents是208/300（69.33%）。我们与后者差-3.00pp，配对区间[-8.33,+2.33]。
- 增益主要来自普通监督数值校准。药名先验也很强，因此还不能说agent学会了医生思路，更不能宣称已实现自主递归进化。

## 2. 主表：论文方法之间的同题对照

统一模型`deepseek/deepseek-v4.1-flash`；每例允许最多4608个生成输出token。RxRSIAgent为3次×1536，GRASP为1次，MedAgents/MDAgents保留作者流程并设80次调用上限。**相同输出额度不等于相同输入token、成本、训练监督或调用次数。** 这里是固定作者代码后的本地任务适配实测，不是跨论文抄分。

| 方法 | RxSafeBench派生测试 | RxQA OpenFDA | 平均调用 S/Q | 无效输出 S/Q |
|---|---:|---:|---:|---:|
{table}

同时保留更高额度的比较，避免只在压缩别人预算后宣称获胜：

| 方法 | 总输出额度 | RxSafe988 | RxQA300 |
|---|---:|---:|---:|
| MedAgents |24000|468（47.37%）|208（69.33%）|
| MDAgents |24000|478（48.38%）|199（66.33%）|
| GRASP之前单次调用 |512|502（50.81%）|189（63.00%）|

等额度MedAgents的失败由预算耗尽78/14例、最终格式无效3/2例组成；MDAgents分别为8/7和10/2（RxSafe/RxQA）。这些都留在分母内。SafeRx-Agent尚未执行；GAMENet、SafeDrug的药物集合指标不填入问答准确率列。当前不能宣称全方法最优。

## 3. 数据集与选择过程

RxSafeBench原始2443条，经本地去重后2000例，构造三选一任务：625训练、190候选选择、197守门验证、988评测。它不是原论文的自由生成任务。RxQA覆盖全部300道公开OpenFDA题；BNF部分没有授权数据。主bench在历史研究中已多次观察，因此结果属于探索性实验。

续实验另取MedQA公开训练镜像10178条，固定revision与parquet哈希。只按题干用药/治疗关键词以及至少一个选项超过6词筛选，共784题；哈希排序取120候选选择、120守门验证，排除与既有本地题目的标准化完全重复。它是一般医学考试题，有些题引用未提供图片，并非专门的剂量评测集。全部来源和规则见`upgrade_v36/protocol.json`。本轮候选都在第一组失败，因此第二组尚未运行。

## 4. 完整流程改了什么

1. 第一次调用：提取任务意图、患者事实、药名和明确给药途径；事实保留原文证据。
2. 说明书工具：筛除单药错误对应复方的情况；核对品牌/通用名/盐型，展示UNII、可用途径；排除明确途径冲突；为适应证、剂量、安全段落预留检索位置，记录来源、日期、段落和偏移。
3. 第二次调用：逐一评估候选药，提出引用与有输入出处的算式。
4. 可执行工具：检查引用是否真实存在、算式是否安全且数值有来源。**尚不等于临床适用性、量纲、肾功能剂量或完整DDI正确。**
5. 第三次调用：结合核验结果作答，保留未知项。
6. 数值经验校准：仅当全部选项是训练中见过的短药名且概率差≥0.2才可能覆盖；否则保留原答案。覆盖之后，原模型解释单独保留，不能冒充新答案的解释。

当前代码入口：`rxrsiagent/selected_agent.py`；配置：`rxrsiagent/selected_profile.json`。原`core.py`和`evaluated_profile.json`用于保留历史审计，不代表新主表配置。

## 5. 消融：提升究竟来自哪里

| 配置 | RxSafe988答对数 | RxQA300答对数 |
|---|---:|---:|
{arows}

来源核验检索单独在RxSafe上**退步**，尽管开发阶段相对无证据对照从94→103/190、98→102/197。RxQA有证据的题数从旧检索1/300升到267/300，但覆盖率不等于相关性和临床正确性。校准在RxSafe上修复118例、退步34例，净增84例（8.50pp，区间[6.08,10.93]）。它在527道RxSafe题上生效，在RxQA上0例生效。

数值模块是普通逻辑回归，特征为草稿答案、标准化药名、药物/UNII与问题焦点词交互。开发网格选择C=10、阈值0.2；候选集110/190，守门集116/197（来源agent为102）。训练模型在测试前冻结，无caseID或答案位置特征。

### 补充的事后归因消融

固定C10、阈值0.2；不能根据下面测试成绩换成新主方法。

| 特征 | 候选集 | 守门集 | RxSafe测试 |
|---|---:|---:|---:|
{drows}

只用药名先验就有564/988；去掉草稿与纯药名项、只保留药物×上下文交互有574/988，都高于完整校准556。这说明复杂模块并非已被证明必要，benchmark可能有药名频率捷径。后续需要未见药物组合与独立临床任务验证，不能把参考答案匹配率都解释成临床推理进步。

## 6. RSI到底进化了什么

两次四轮文本技能实验都要求适用条件、排除条件、支持失败例和成功反例；八次候选更新全部被门槛拒绝，保留技能数始终0。真正改变的是普通监督训练的数值校准状态；骨干模型权重、工具代码和推理流程在学习轨迹中固定。

| 累计病例 | 数值特征/权重数 | 候选集 | 守门集 | 两次实验保留文本技能 |
|---:|---:|---:|---:|---:|
{crows}

这是**事后固定超参数的训练量曲线**：超参数已经使用完整625训练病例及开发反馈选好，不能叫前瞻性在线RSI实验。候选集并非单调增长，守门集增长也没有证明独立任务迁移。

## 7. 没有停在主实验：三项独立续实验

| 候选改进 | 独立候选集120题 | 对静态流程修复/退步 | 决策 |
|---|---:|---:|---|
| 静态来源agent |99|对照|保留|
| 扩展剂量和特殊人群说明书段落 |99|4/4|拒绝|
| 独立草稿＋逐项矛盾检查 |99|7/7|拒绝|
| 从9936个训练案例检索3个示例 |99|5/5|拒绝|

均保持3×1536调用预算；最后一项使用额外训练数据，不是等训练量比较。三种方法都没有严格提高，因此**没有运行它们的guard与RxQA，不用测试结果挑方法**。此前的主动二次检索也从103降到100/190，未晋级。保留失败记录，而不是把所有改动都称作提升。

## 8. Case study与临床边界

从校准覆盖中按ID字典顺序各取第一个修复和退步，属于事后示例：

- `0445a1cf61c5e4ac`：利培酮→舍曲林，符合参考答案；原解释支持的是利培酮，不能直接支持覆盖后的选择。这只是参考标签修复，临床改善未经确认。
- `0d0cc811ec14bfd3`：灰黄霉素→酮康唑，反而错；来源agent本身还把一个洗剂产品的范围过度推广到成分。这同时暴露校准覆盖与药品适用性的局限。

8项合成软件测试通过；原实验24735段、续实验1556段来源片段完成核对。两位评审者尚未回传盲评。临床14项指标（治疗目标覆盖、严重错误、联合医嘱正确率、不必要用药等）保留为独立待验证任务，不能从QA结果推算。

## 9. 交付、审计与成本

- `upgrade_v35/results/audit.json`：完整方法、消融、配对区间、引用审计。
- `upgrade_v35/test_freeze.json`：测试前冻结，`results/calibration_diagnostics.json`：事后简单对照。
- `upgrade_v36/results/audit.json`：独立开发三项失败结果与门槛。
- 原实验成功响应账本增量USD{billed:.6f}；续实验USD{v['ledger_increment_usd']:.6f}；合计USD{total:.6f}。这是本地响应账本，不是供应商发票；复用缓存的逻辑推理成本另列。
- 1655个响应引用与最新同请求缓存不同，源于并发相同请求可能返回不同采样；包含重复引用。保留逐例原始响应为准，不能说所有对照共享相同草稿。续实验已加入跨进程请求锁。
- 所有源请求含缺失/HTTP错误状态。下载数据、说明书正文、原始响应、模型pickle和密钥不上传。公开代码、聚合结果与哈希。
- 英文论文使用当前编辑器原路径；主表、结构图、机制、消融、曲线、case study和局限已统一到新配置。旧版本留在档案，不作为论文方法堆叠。

## 10. 下一步真正卡在哪里

**两个bench同时超过最强方法、可信的自主RSI，均尚未完成。** 下一步应建立独立的说明书剂量/条件适用性任务，完善剂型强度与缓释形式匹配，验证临床规则，并在未见药物组合上与普通监督校准比较。为后续优化保留新的最终测试集。真实完整医嘱执行与双人盲评是另外两项必要证据。

来源：[openFDA官方文档](https://open.fda.gov/apis/drug/label/)、[MedQA作者仓库](https://github.com/jind11/MedQA)、[RxQA官方发布](https://github.com/Google-Health/rxqa)。
'''
 for lang,s in [('en',en),('zh',zh)]:
  (HERE/f'RESULTS.{lang}.md').write_text(s)
  # Paper root links have one fewer path segment to the English source.
  (ROOT/'paper'/f'CURRENT_RESULTS.{lang}.md').write_text(s.replace('../paper/latex/','latex/'))
 print(json.dumps({'reports':['en','zh'],'successful_response_ledger_increment_usd':total}))
if __name__=='__main__':main()
