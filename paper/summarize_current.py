"""Maintain the bilingual entry point from completed aggregate result files."""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
def read(path):return json.loads((ROOT/path).read_text())

def main():
    public=read('upgrade_v8/results/summary.json')['methods']
    evidence=read('upgrade_v11/results/summary.json')['complete_test_methods']
    verifier=read('upgrade_v13/results/summary.json')['arms']
    local=read('upgrade_v7/results/summary.json')['methods']
    labels={'direct':'Direct LLM','cot':'CoT','self_refine':'Self-Refine','case_rag':'Case RAG','reflexion_adapt':'Reflexion task adaptation',
        'grasp_adapt':'GRASP task adaptation','evotool_adapt':'EvoTool task adaptation','rxrsi':'RxRSI language artifacts'}
    table='| Method | Accuracy (%) | Calls/case | Evidence |\n|---|---:|---:|---|\n'
    for k,label in labels.items():
        m=public[k];table+=f"| {label} | {100*m['accuracy_mean']:.2f} ± {100*m['accuracy_sample_sd']:.2f} | {2 if k=='self_refine' else 1} | [v0.8](../upgrade_v8/RESULTS.en.md) |\n"
    table+='| Author GRASP core + task adapter | **50.81** | 1 | [v0.10](../upgrade_v10/RESULTS.en.md) |\n'
    for k in ['balanced','safety','indication']:table+=f"| Fixed {k} evidence review | {100*evidence[k]['accuracy']:.2f} | 2 | [v0.11](../upgrade_v11/RESULTS.en.md) |\n"
    for k in ['uniform','error_prioritized']:
        m=verifier[k];table+=f"| Outcome verifier: {k} | {100*m['accuracy_mean']:.2f} ± {100*m['accuracy_sample_sd']:.2f} | 2 | [v0.13](../upgrade_v13/RESULTS.en.md) |\n"
    if (ROOT/'upgrade_v17/results/summary.json').exists():
        ground=read('upgrade_v17/results/summary.json')['datasets']['rxsafebench']['methods']
        for k,label in [('fixed_grounded','One-call fixed grounding'),('evolving_grounded','Grounded skill evolution')]:
            table+=f"| {label} | {100*ground[k]['accuracy']:.2f} | 1 | [v0.17](../upgrade_v17/RESULTS.en.md) |\n"
    struct='| Method | Drug micro-F1 | Core-order micro-F1 |\n|---|---:|---:|\n'
    for k,label in [('word_char_ensemble','Word/character ensemble + tools'),('rxrsi_selected','RxRSI selected state'),('without_memory_evolution','Freeze initial memory'),('without_tool_evolution','Freeze initial order tool')]:
        m=local[k];struct+=f"| {label} | {m['drug_f1_mean']:.5f} ± {m['drug_f1_sd']:.5f} | {m['order_f1_mean']:.5f} ± {m['order_f1_sd']:.5f} |\n"
    for lang in ['en','zh']:
        if lang=='zh':
            text='''# RxRSIAgent：当前主表、进化证据与执行状态

更新：2026-10-15。此文是长期更新的阅读入口；各版本保留协议、失败和结果。本轮用户充值后，之前的 API 缺失均已补齐。**目前仍未证明我们的方法优于最强对照。**

## 1. 方法对比主表在哪、测什么？

### 主表 A：处方药物和订单匹配

同一 MIMIC-IV/ED 预处理、40,000 训练住院、4,000 测试住院（3,440 位患者），三种子；药物为冻结的 128 个原始药名空间。订单为药物、途径、剂量字符串、单位的联合匹配。它不等同于原论文 ATC-L4/RxNorm 协议。这里没有盐水出现 F1。

'''+struct+'''
[完整 12 方法/消融表、逐轮结果](../upgrade_v7/RESULTS.zh.md)。临床历史 GT 可直接自动评分；额外医生标注不是计算这些指标的前提。

### 主表 B：公开处方选择题上的方法比较

RxSafeBench 去重后 2,000 题，按场景组切分为 625/190/197/988 训练/候选选择/退化检查/测试题；这是明确标注的三选项衍生任务。所有行固定 DeepSeek-V4.1-Flash，比较的是方法。± 为三个进化顺序的标准差；固定答案跨顺序复用。作者核心只跑 seed 42。模型调用数不同，开发成本另记，不能声称所有行等预算。

'''+table+'''
作者 GRASP 核心在当前完整对照中最好。`task adaptation` 是我们的任务适配，不冒充原论文实现；作者核心保持源码不变，但任务适配器由我们编写。跨论文原分数仅在英文论文的独立文献表中引用，不放入本表。

## 2. RSI 到底改变了什么？

| 实验 | 实际改变对象 | 逐轮证据与结论 |
|---|---|---|
| v0.7 | 监督策略参数、病例记忆、联合订单模板 | 三种子五检查点随病例增长改善，但输给同数据静态集成；不能归因为独有 RSI |
| v0.8 | LLM 提议技能文本、记忆、证据关注词 | 三种子四轮全部拒绝完整 RxRSI 的候选；最终未进化，不宣称成功 |
| v0.10 | 作者 GRASP 技能文件 | 在同一衍生任务上提高至 50.81%，RxQA 迁移反而 193→189/300 |
| v0.12–13 | 工具路由/结果核验器系数与阈值 | 权重真实变化，部分更新被接受，但有测试退化；错误优先没有稳定优于普通更新 |
| v0.9 | 本地 Qwen LoRA 参数 | 500 例全检查点测试完成；两臂均低于直接 top-8 工具 |
| v0.15 | 二元纳入/排除监督下的 LoRA 参数 | 训练与开发选择完成；两臂均冻结第2轮，全部检查点测试中 |
| v0.17 | 固定说明书工具上的 GRASP 技能文件 | 完整结果 501/988；固定证据 499、作者核心 502；迁移下降 |

每种对象都有版本哈希，接受/拒绝及修复/退化记录。图：

![处方病例增长轨迹](../upgrade_v7/round_curves.png)

![公开语言进化轨迹](../upgrade_v8/round_curves.png)

## 3. 本次恢复后新增实测

- **适应证证据复核：478/988，48.38%。** HTTP 缺失已全部补齐，原选择协议不变。
- **Gemini 开发预算修复：**同 190 题 CoT 72→105 正确，已收到但无效回答 69→2；证据方法 62→100 正确、无效 85→1。推理强度和完成预算同时变化，不分别归因，也不当作测试集或 RSI 成绩。[完整报告](../upgrade_v16/RESULTS.zh.md)。
- **真实 FHIR：**五项读写/回读/版本/原子失败/清理检查通过。16 题开发试验直接工具 10/16、固定核验 harness 8/16；所有 11 个写入资源回读成功并清理，独立重评分一致。[报告](../upgrade_v14/RESULTS.zh.md)。

## 4. 继续执行的顺序与交付标准

1. v0.9 全检查点测试、独立重算和患者聚类区间已完成，见新增本地参数主表。
2. v0.15 训练与选择已完成，两臂均冻结第2轮，正在测试全部检查点；患者和步数预算与v0.9匹配。
3. v0.17 四组件及全部逐轮/RxQA评价已完成。v0.18 Gemini四方法比较已全部完成并独立重算；传输缺失已补齐，固定证据538/988，冻结证据技能510/988。
4. FHIR协议修复后，完整技能学习与同分布/未见任务类型评价已启动；开发16题不能替代正式测试。
5. 最终保留没有参与迭代的确认测试、多种子、消融、费用和退化记录。若仍未超过强对照，论文结论如实保留，不能通过挑选方法或修改测试标签获得“第一”。

[英文论文](latex/v0.3/prismatic_v03_en.tex) · [持续执行计划](COMPLETION_PLAN.md) · [版本记录](CHANGELOG.md)。受限患者记录、权重、原始轨迹和密钥始终不进入 GitHub。
'''
        else:
            text='''# RxRSIAgent: current method tables, evolution evidence and execution status

Updated 15 October 2026. This maintained entry point links versioned protocols, failures and results. Funding recovery resolved all previously missing API requests. **Our method has not yet surpassed the strongest completed control.**

## 1. Main method comparisons

### A. Medication and structured-order agreement

Same MIMIC-IV/ED preprocessing, 40,000 training and 4,000 test admissions (3,440 patients), three seeds. The frozen vocabulary contains 128 raw drug names; joint orders match drug, route, dose string and unit. This is not the original ATC-L4/RxNorm protocol. Saline-presence F1 is absent.

'''+struct+'''
[Full 12-row comparison and trajectories](../upgrade_v7/RESULTS.en.md). Existing GT enables automatic scoring without mandatory new clinician annotation.

### B. Public prescription-option method comparison

2,000 deduplicated RxSafeBench questions, scenario-group split 625/190/197/988 train/proposal/guard/test. This is a labeled three-option derived task. Every row uses DeepSeek-V4.1-Flash; rows compare methods. ± denotes SD over three evolution orders; fixed outputs are reused. Author-core results use seed 42. Inference calls differ and development costs are separately recorded, so not every row has an equal budget.

'''+table+'''
The author GRASP core is the strongest completed control. Named task adaptations are not original implementations. The author-core source is unchanged, with our task adapter. Cross-paper original numbers appear only in the manuscript's separate literature panels.

## 2. What actually evolves?

| Study | Changing object | Evidence and interpretation |
|---|---|---|
| v0.7 | Supervised policy parameters, episodes, joint-order templates | Three seeds/five checkpoints improve with data; the static same-data ensemble is stronger |
| v0.8 | Proposed LLM skills, memories, evidence-focus terms | Full RxRSI rejects every candidate in all three orders; no successful final-state evolution |
| v0.10 | Author-core GRASP skill files | 50.81% on the derived task; RxQA transfer declines from 193 to 189/300 |
| v0.12–13 | Router/verifier coefficients and thresholds | Actual updates, some acceptances and test regressions; no stable error-priority advantage |
| v0.9 | Local Qwen LoRA parameters | All 500-case checkpoint tests completed; both arms trail direct top-8 tools |
| v0.15 | LoRA under explicit binary inclusion supervision | Training/selection complete; both arms freeze round2 before all-checkpoint testing |
| v0.17 | GRASP skills over frozen label evidence | Complete: 501/988 versus fixed grounding 499 and author core 502; transfer declines |

Hashes, promotions/rejections and case repairs/regressions accompany the artifacts.

![Structured case-growth trajectories](../upgrade_v7/round_curves.png)

![Public language-artifact trajectories](../upgrade_v8/round_curves.png)

## 3. New executed evidence after funding recovery

- Indication review: **478/988, 48.38%**; all missing requests recovered with the original selection protocol.
- Gemini development repair: on the same 190 questions, CoT improves 72→105 correct and 69→2 invalid; evidence improves 62→100 correct and 85→1 invalid. Reasoning effort and completion cap change jointly. These are development/budget measurements, not test or RSI gains. [Report](../upgrade_v16/RESULTS.en.md).
- Real FHIR: five integration checks pass. Direct tools score 10/16 and a fixed verified harness 8/16 on development tasks. All 11 created resources pass readback and cleanup; independent grading agrees. [Report](../upgrade_v14/RESULTS.en.md).

## 4. Execution order and completion criteria

1. v0.9 all-checkpoint tests, independent recount and patient-cluster intervals are complete; see the new parameter table below.
2. v0.15 training and selection are complete; both arms freeze round2 before all-checkpoint testing, with patients and step budgets matching v0.9.
3. v0.17 four-component, all-round and RxQA evaluations are complete. v0.18 is complete and independently recounted: fixed grounding538/988 versus frozen grounded skills510/988. Transport interruptions were resumed from cache without scoring missing responses as model errors.
4. After FHIR protocol repairs, full skill learning and ID/held-out-task-type evaluation have started. The 16-case pilot cannot substitute for those tests.
5. Retain an unobserved confirmation test, multiple orders, ablations, costs and regressions. Negative superiority outcomes remain visible rather than selecting favorable controls or changing test labels.

[English paper](latex/v0.3/prismatic_v03_en.tex) · [Maintained plan](COMPLETION_PLAN.en.md) · [History](CHANGELOG.md). Restricted records, checkpoints, raw patient traces and credentials remain outside GitHub.
'''
        if (ROOT/'upgrade_v9/results/summary.json').exists():
            parameter=read('upgrade_v9/results/summary.json')['methods']
            pt='| Method | Drug F1 | Core-order F1 | Mean drugs |\n|---|---:|---:|---:|\n'
            for name,m in parameter.items():pt+=f"| {name} | {m['drug_f1']:.5f} | {m['core_order_f1']:.5f} | {m['mean_predicted_drugs']:.2f} |\n"
            extra=('\n## 新增已完成主表：500 例本地参数进化\n\n与上方 4,000 例主表分开：这里是事先保留的 500 次住院、494 位患者，共用初始 8k 候选工具。GT 平均 6.784 个药物，固定目录可覆盖 3.802 个。选择在测试前冻结。\n\n' if lang=='zh' else '\n## Newly completed table: local parameter evolution on 500 admissions\n\nSeparate from the 4,000-admission table: 500 reserved admissions, 494 patients, same initial-8k candidate tools. Mean gold/reachable drugs are 6.784/3.802. All selection was frozen before test scoring.\n\n')+pt+'\n[Full local results / 完整本地结果](../upgrade_v9/RESULTS.'+lang+'.md)\n'
            text+=extra
        if (ROOT/'upgrade_v20/results/order_entry_audit.json').exists():
            text+=('\n## 时间协议新增审计\n\n全体 1,788,195 条旧目标中，42,005 条 provider 医嘱在入院前已开立，276,269 条开立于原六小时窗口之后。可信时间关联排除 438 条住院编号冲突。源关联路径已确认一致，但药房与 provider 时钟仍不同，不能挑一个时钟就宣称前瞻有效。[详细结果](../upgrade_v20/RESULTS.zh.md)。\n' if lang=='zh' else '\n## New temporal-protocol audit\n\nAmong 1,788,195 historical target rows, 42,005 matching provider orders precede admission and 276,269 occur after the original six-hour horizon. Timestamp counts exclude 438 admission-link conflicts. Source linkage paths agree, but the differing pharmacy/provider clocks still require an explicit prospective availability protocol. [Full results](../upgrade_v20/RESULTS.en.md).\n')
        if (ROOT/'upgrade_v21/results/independent_cohort_audit.json').exists():
            panel=('\n## 最新订单任务：控制记录可用时间\n\n决策是实际入院后第6小时，预测随后6小时的新增/修改订单。仅用此前已记录的订单、血液检验和人口学信息；医生/药房时间和身份必须一致。40,000训练 / 2,000候选验证 / 2,000退化检查 / **1,082测试住院（1,024位患者）**，患者互不交叉，排除旧版本测试患者。独立复核约19.9万目标、58.9万先前订单和50.7万检验记录，12项检查全部通过。这是时间一致且有未来订单的筛选队列，不代表所有住院。\n\n' if lang=='zh' else '\n## Latest order task: controlled recorded availability\n\nDecision: actual admission plus6h; predict new/changed orders in the following6h using previously recorded orders, blood labs and demographics. Provider/pharmacy clocks and identities must agree. Split:40,000 training /2,000 proposal /2,000 guard / **1,082 test admissions (1,024 patients)**; patient-disjoint and excluding previous test patients. Independent reconstruction checks198,850 targets,589,393 prior orders and506,710 lab rows; all12 checks pass. This selected coherent-time, nonempty-target cohort does not represent all admissions.\n\n')
            path=ROOT/'upgrade_v21/results/summary.json'
            if path.exists():
                d=json.loads(path.read_text());panel+='| Method | Drug F1 mean ± SD | Core-order F1 mean ± SD |\n|---|---:|---:|\n'
                display={'reuse_prior_orders':('复用先前订单','Reuse prior orders'),'retrieval_conditional_tool':('病例检索＋订单工具','Case retrieval + order tool'),'word_char_ensemble':('词/字符集成＋订单工具','Word/character ensemble + tool'),'rxrsi_selected':('RxRSI逐轮选择状态','RxRSI selected state'),'without_tool_evolution':('冻结初始订单工具','Freeze initial order tool'),'without_memory_evolution':('冻结初始病例记忆','Freeze initial memory')}
                for k,labels in display.items():
                    z=d['methods'][k];label=labels[0 if lang=='zh' else 1];panel+=f"| {label} | {z['drug_f1_mean']:.5f} ± {z['drug_f1_sd']:.5f} | {z['order_f1_mean']:.5f} ± {z['order_f1_sd']:.5f} |\n"
                panel+=('\n三种子完整方法/消融和逐轮预测已独立重算。本表与旧starttime任务分开。\n' if lang=='zh' else '\nAll three-seed method/ablation and round predictions are independently recounted. Separate from the earlier start-time task.\n')
                panel+=('逐轮均值药物F1从0.1660升至0.1914，但强对照是0.2010；冻结初始记忆反而更好。不能据此宣称RSI已经胜出。\n' if lang=='zh' else 'Round-mean drug F1 rises from0.1660 to0.1914, but the strong control scores0.2010 and frozen initial memory is better. A unique RSI advantage is not established.\n')
            else:panel+=('三种子方法对比正在运行；以下旧主表保留其原始协议。\n' if lang=='zh' else 'The registered three-seed comparison is running; the older tables below retain their original protocols.\n')
            panel+='\n[Full protocol/results / 完整协议结果](../upgrade_v21/RESULTS.'+lang+'.md)\n'
            text=text.replace('\n## 1.',panel+'\n## 1.',1)
        if (ROOT/'upgrade_v18/results/summary.json').exists():
            d=read('upgrade_v18/results/summary.json');text+=('\n## Gemini 上的冻结技能方法比较\n\n同988题，一次调用，2,048-token/low，测试时不学习。\n\n' if lang=='zh' else '\n## Frozen-method comparison on Gemini\n\nSame988 questions, one2,048-token/low-reasoning call, no test-time learning.\n\n')
            text+='| Method | Correct /988 | Accuracy (%) | Invalid |\n|---|---:|---:|---:|\n'
            for k,z in d['methods'].items():text+=f"| {k} | {z['correct']} | {100*z['accuracy']:.2f} | {z['invalid']} |\n"
            text+='\n[Transfer, paired intervals and costs / 迁移、区间与费用](../upgrade_v18/RESULTS.'+lang+'.md)\n'
        if (ROOT/'upgrade_v22/results/summary.json').exists():
            text+=('\n## 继续改进：数值状态开发试验已完成\n\n把已有检验值和用药剂量表示为数值，并保留缺失标记；没有增加未来信息。候选验证选定的词＋数值策略，在2,000例检查集上达到药物/订单F1 **0.22456/0.13656**，同集强对照为 **0.21942/0.13458**。通过预设继续条件，但两项患者配对区间都包含零。这里只是单种子开发结果，没有计算测试分数，也不算RSI胜出。\n' if lang=='zh' else '\n## Continued improvement: numerical-state development pilot complete\n\nRepresent existing lab/dose values numerically with observed flags; no future context is added. The proposal-selected word+typed policy reaches guard drug/order F1 **0.22456/0.13656**, versus the same-guard control at **0.21942/0.13458**. The continuation rule passes, but both patient-paired intervals include zero. This is one-seed development evidence, with no test scoring or RSI superiority claim.\n')
            text+='\n[Development protocol/results / 开发协议与结果](../upgrade_v22/RESULTS.'+lang+'.md)\n'
        if (ROOT/'upgrade_v23/protocol.json').exists():
            panel=('\n## 最新机制实验：错误反馈是否有独立收益？\n\n三种子、五轮，冻结词＋数值表示；普通更新、自身错误加权、同分布打乱权重三组共享病例和精确60轮训练预算。订单工具只用当轮已见病例。全部状态冻结后统一评价。\n\n' if lang=='zh' else '\n## Latest mechanism study: does error feedback add value?\n\nThree seeds/five rounds with fixed word+numeric features. Uniform, own-error-weighted and shuffled-weight arms share cases and exactly60 training epochs. Order tools use only cases seen by that round. Evaluation follows joint selection freeze.\n\n')
            path=ROOT/'upgrade_v23/results/summary.json'
            if path.exists():
                z=json.loads(path.read_text());panel+='| Method | Drug F1 mean ± SD | Core-order F1 mean ± SD |\n|---|---:|---:|\n'
                names={'initial_state':('初始状态','Initial state'),'uniform':('普通更新','Uniform updates'),'error_prioritized':('自身错误加权','Own-error priorities'),'permuted_priority':('打乱错误权重','Shuffled priorities'),'full_data_uniform':('全量普通监督','Full-data uniform')}
                for k,labels in names.items():
                    m=z['methods'][k];panel+=f"| {labels[0 if lang=='zh' else 1]} | {m['drug_f1_mean']:.5f} ± {m['drug_f1_sd']:.5f} | {m['order_f1_mean']:.5f} ± {m['order_f1_sd']:.5f} |\n"
                panel+=('\n1,082次住院、1,024位患者；这是已观察过的v0.21测试集上的探索性复用。权重分配、训练预算、工具成员和全部预测均已独立核对。\n' if lang=='zh' else '\n1,082 admissions/1,024 patients; exploratory reuse of the previously observed v0.21 test. Weight assignment, training budgets, tool members and every prediction are independently checked.\n')
                panel+='\n[Full results / 完整结果](../upgrade_v23/RESULTS.'+lang+'.md)\n'
            else:panel+=('三种子均已真实启动，尚未形成完整测试主表。当前不能把检查集结果当成测试结果。\n' if lang=='zh' else 'All three seed runs have started; the complete test table is pending. Guard scores are not test results.\n')+'\n[Registered protocol / 已登记协议](../upgrade_v23/README.'+lang+'.md)\n'
            text=text.replace('\n## 1.',panel+'\n## 1.',1)
        if (ROOT/'upgrade_v24/results/source_audit.json').exists():
            text+=('\n## 外部数据准备：eICU 医院隔离审计完成\n\n保留142,485次住院；测试8,188次住院来自16家医院，患者/医院跨集合重叠均为0。测试窗口缺药名的6,283条订单中，6,064条仍有HICL编码，因此不能按非空药名直接删除。排除238,680条决策后才修订的检验。这是数据审计，尚无模型测试分数；时间与订单字段和MIMIC不同。\n' if lang=='zh' else '\n## External-data preparation: eICU hospital audit complete\n\nRetain 142,485 stays, including 8,188 test stays from 16 hospitals, with zero patient/hospital overlap across splits. Of 6,283 test-window orders without names, 6,064 retain HICL codes; name-only filtering is inappropriate. Exclude 238,680 lab values revised after the decision. This is a data audit without model scores, under a different time/order-field protocol from MIMIC.\n')
            text+='\n[External audit / 外部数据审计](../upgrade_v24/RESULTS.'+lang+'.md)\n'
        (HERE/f'CURRENT_RESULTS.{lang}.md').write_text(text)

if __name__=='__main__':main()
