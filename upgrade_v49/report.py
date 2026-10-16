"""Generate bilingual reports only from completed local experimental artifacts."""
import json
from common import *
LABELS={'rxrsi_base':'RxRSIAgent, initial state','rxrsi_selected':'RxRSIAgent, retained state','direct':'Direct self-refinement',
 'saferx':'SafeRx-Agent task adaptation','skemex':'SkeMex author memory core + common actor','flame_list':'FLAME released list-policy transfer'}
def main():
    audit=json.loads((HERE/'results/audit.json').read_text());learning=json.loads((HERE/'results/learning_scope.json').read_text())
    comparison=json.loads((HERE/'results/comparison.json').read_text());transfer=json.loads((HERE/'results/transfer.json').read_text())
    assert comparison['complete'] and learning['complete'] and transfer['complete']
    methods=audit['methods'];rounds=learning['rounds'];fmt=lambda x:f'{100*x:.2f}'
    lines=['| Method | Drug P | Drug R | Drug F1 | Core4 F1 | Core5 F1 | Empty |', '|---|---:|---:|---:|---:|---:|---:|---:|']
    for name in ['direct','saferx','skemex','rxrsi_base','rxrsi_selected','flame_list']:
        if name in methods:
            m=methods[name]['metrics'];lines.append('| '+LABELS[name]+' | '+' | '.join(fmt(m[k]) for k in ['drug_precision','drug_recall','drug_micro_f1','core_order_micro_f1','core5_micro_f1','empty_fraction'])+' |')
    table='\n'.join(lines)
    curve=json.loads((HERE/'results/round_curve.json').read_text())['trajectory']
    trajectory=['| Round | New cases processed | Retained rules | Proposal drug / Core4 F1 | Guard drug / Core4 F1 | Test drug / Core4 F1 | Accepted |','|---:|---:|---:|---:|---:|---:|---|']
    for r,t in zip(rounds,curve):trajectory.append(f"| {r['round']} | {r['cases_seen']} | {len(r['state']['cards'])} | {fmt(r['proposal']['drug_micro_f1'])} / {fmt(r['proposal']['core_order_micro_f1'])} | {fmt(r['guard']['drug_micro_f1'])} / {fmt(r['guard']['core_order_micro_f1'])} | {fmt(t['metrics']['drug_micro_f1'])} / {fmt(t['metrics']['core_order_micro_f1'])} | {r['accepted']} |")
    tr='\n'.join(trajectory);a=transfer['methods']['rxrsi_base'];b=transfer['methods']['rxrsi_selected'];main=methods['rxrsi_selected']['metrics'];counts=methods['rxrsi_selected']['counts']
    en=f'''# MIMIC-IV prescription experiment: executed results

## 1. Main result and task

**RxRSIAgent: drug F1 {fmt(main['drug_micro_f1'])}%; Core4 F1 {fmt(main['core_order_micro_f1'])}% on all 1,082 test admissions.**

This is a local Qwen3-4B prescription-task adaptation, not the frozen hosted DeepSeek QA agent. Predict the full set of new/change orders in hours 6–12 after admission, using observations available at hour 6. Output comprises joint drug/route/dose/unit/frequency templates selected from a common 24-drug catalogue; it is not unrestricted prescribing or the entire hospital-stay regimen. The 128-name vocabulary and 40,000-admission supervised candidate tool are frozen. Out-of-vocabulary GT remains scored.

## 2. Measured comparison

All numbers below are percentages. The first five local rows use the same cases, candidate catalogue, offline label resource, Qwen backbone and maximum 128+128+96 output tokens. Actual token use and offline learning compute differ. **SafeRx and SkeMex are explicitly limited task/subsystem adaptations. FLAME uses a released trained list-policy checkpoint with a different backbone and initializer; its row is a separate transfer experiment, not a full-method, equal-information comparison. These measurements do not establish superiority over the original papers.**

{table}

Candidate coverage ceiling: **{fmt(main['catalogue_drug_recall_ceiling'])}% of GT drugs**. Complete Core5 reference coverage: **{fmt(main['core5_gt_field_coverage'])}%**. Missing frequency does not become a match. No saline-presence metric is used.

## 3. Sequential experience updates

{tr}

The first three rounds process 72 training admissions and retain no rules. The table describes a further three rounds on 72 different training admissions (144 total). Full-trace profiles expose counts of observed/selected facts and missed reference medications, while withholding drug identities from the proposer. The researcher supplies a bounded verifier-scope option; the model chooses conditional procedures and selected/all-observed scope. This menu design is not autonomous tool invention. The proposal/guard subsets contain 48/64 reused admissions. Model weights and executable tools stay fixed within this trajectory. Each rule has a trigger and counterexample. Retention requires a strictly higher proposal composite and no guard drug/Core4 decrease. Test labels never select a rule. Rejected rules remain reported. A flat retained trajectory is not evidence of successful RSI.

## 4. Frozen-memory transfer

On Llama-3.2-3B, all 1,082 cases: initial drug/Core4 F1 **{fmt(a['drug_micro_f1'])}/{fmt(a['core_order_micro_f1'])}%**; retained memory **{fmt(b['drug_micro_f1'])}/{fmt(b['core_order_micro_f1'])}%**. Drug-F1 change **{100*(b['drug_micro_f1']-a['drug_micro_f1']):+.2f} percentage points**. No Llama-specific rule selection or retraining. Two local backbones do not establish model-independent benefit.

## 5. Failure findings and cases

- Initial protocol diagnostic, 48 proposal cases: drug/Core4 F1 9.59/4.26%; 25 parseable plans, zero parseable assessments and zero verified-fact cases. Fact-ID binding and concise intermediate JSON repair this contract. This is a researcher repair, not autonomous RSI; syntax improvement alone did not establish accuracy improvement.
- Training observability audit: 1,722/40,000 admissions belong to 144 groups with identical visible context and differing reference drug sets. This supports an information/variation limitation, not a claim that every error is unavoidable.
- Selected test predictions miss {counts['selection_missing']} targets already inside the catalogue; {counts['catalogue_missing']} targets are outside it. These distinguish selection and candidate-generation bottlenecks.
- Case-level GT/prediction differences and before/after interventions are saved locally as `failure_case_studies.json` in the restricted experiment directory. No patient-level content is published.
- Recorded actions are not unique clinical optima. No clinical-safety, DDI, allergy or renal-dose success is inferred from F1 or source quotation.

## 6. Cost, provenance and limitations

**New paid API cost: USD 0; authorization cap: USD 10.** All patient inference and reflection are local. Public checkpoint downloads do not call paid inference APIs. Local compute is not monetized. Earlier located response expenditure remains approximately USD 89.53 and is not charged to this new cap.

The test has historical exposure from earlier supervised studies; the result is exploratory. Source pins, exact predictor hashes, costs, denominators and patient-bootstrap contrasts are in `results/audit.json`, `results/*`, and `test_freeze.json`. See the README for comparator fidelity and runnable commands. Publication-quality claims still require complete author-workflow controls and a new untouched clinical evaluation.
'''
    zh=f'''# MIMIC-IV 完整窗口处方实验：真实结果

## 一、这次实际测了什么

**RxRSIAgent 在全量 1,082 例上的药物 F1：{fmt(main['drug_micro_f1'])}%；四字段订单 F1：{fmt(main['core_order_micro_f1'])}%。**

这是本地 Qwen3-4B 的处方任务适配，不是把原来 DeepSeek 选择题分数改名。使用入院第 6 小时已可用的信息，预测随后 6 小时内全部新增/变更订单；不是预测整个住院期的所有药物。模型从共享的 24 药物候选订单库选择多项，编译出药物、途径、剂量、单位和频次。128 药物词表与 4 万例训练得到的候选工具保持冻结；库外 GT 仍计入漏开。

## 二、对比主表

数值单位均为百分比。共同本地对照使用相同病例、候选库、说明书资源、Qwen 底座和最多 128+128+96 输出 token；实际输入量、训练与记忆计算量不同。**SafeRx 是独立任务适配，SkeMex 使用作者记忆子系统与共同处方执行器。FLAME 是已发布训练检查点的列表策略迁移，底座及初始化信息不同。这些都不能冒充完整原方法复现，也不能据此声称超过原论文。**

{table}

候选库最多覆盖 **{fmt(main['catalogue_drug_recall_ceiling'])}%** 的 GT 药物；五字段均已知的参考订单覆盖率为 **{fmt(main['core5_gt_field_coverage'])}%**。缺失频次不算匹配，不计算盐水出现 F1。

## 三、逐轮进化

{tr}

最初三轮处理 72 例，没有保留规则。表中是随后三轮的 72 例新训练病例，两阶段共 144 例。更新器读取完整追踪计算出的错误特征，药名和原样目标处方不进入提案输入。研究者提供“仅所选事实/全部已观察事实”的有限工具配置接口，模型选择带适用条件和反例的程序及配置；接口设计本身不是自主发明工具。48/64 例候选集/守门集被复用并明确披露。底座、候选排名器、药物词表及工具代码在该轨迹内固定。候选集综合指标须严格提高，守门集药物及订单 F1 均不下降，才保留更新。测试分数只在所有状态冻结后计算，不选测试最优轮次。**如果保留状态不变，不能把它称作成功进化。**

## 四、跨模型迁移

将冻结的规则直接交给 Llama-3.2-3B，不在该模型上再挑规则。全量 1,082 例：初始药物/四字段 F1 **{fmt(a['drug_micro_f1'])}/{fmt(a['core_order_micro_f1'])}%**；迁移后 **{fmt(b['drug_micro_f1'])}/{fmt(b['core_order_micro_f1'])}%**。药物 F1 变化 **{100*(b['drug_micro_f1']-a['drug_micro_f1']):+.2f} pp**。两个小型本地模型的结果不足以证明任意模型都能获益。

## 五、从失败中得到什么

1. 初始 48 例开发实验药物/订单 F1 为 9.59/4.26%，只有 25 例计划可解析，评估可解析与事实核验均为零。事实编号绑定和简短输出修复了工程协议；这不是自主 RSI，也不代表准确率随之提高。
2. 训练集中有 1,722/40,000 例属于 144 组“可见上下文相同、GT 药物集合不同”的记录。低分也受信息缺失、治疗差异或记录过程影响，不能直接推断模型不理解医生。
3. 最终测试中，已有候选却漏选的 GT 共 {counts['selection_missing']} 个；候选库外 GT 共 {counts['catalogue_missing']} 个。前者针对决策，后者针对候选检索，不能混成一种错误。
4. 真实训练失败病例、GT、前后预测及字段差异保存在受限目录的 `failure_case_studies.json`，不向 GitHub 发布病例内容。
5. GT 是记录到的医生行为，不能直接当作唯一临床最优方案；F1 和引用有效不等于 DDI、过敏、肾剂量或处方适宜性已经验证。

## 六、费用与可复现性

**本次新增付费 API 支出 0 美元，用户授权上限 10 美元。** 病例推理和反思均在本地；公开模型下载不产生模型推理 API 费用。本地计算成本没有折算。历史已找到的响应费用仍约 89.53 美元，不重复计入此次预算。

当前测试集有历史监督实验暴露，结果属于探索性评估。聚合结果、患者级 bootstrap、预测哈希、模型/代码版本与冻结状态见 `results/` 和 `test_freeze.json`。完整原方法对照和新的未触碰临床评估仍是论文定稿条件。
'''
    (HERE/'RESULTS.en.md').write_text(en);(HERE/'RESULTS.zh.md').write_text(zh)
    for lang,text in [('en',en),('zh',zh)]:
        (ROOT/f'paper/versions/v0.49-2026-10-16.{lang}.md').write_text(text)
    print('Wrote bilingual executed-result reports')
if __name__=='__main__':main()
