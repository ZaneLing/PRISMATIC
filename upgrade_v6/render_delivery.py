"""Write bilingual reports and update the existing English manuscript in place."""
import json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent
def read(name):return json.loads((HERE/'results'/name).read_text())
def table(headers,rows):return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+''.join('| '+' | '.join(map(str,row))+' |\n' for row in rows)

def run():
    e=read('order_evolution_results.json');r=read('error_replay_results.json');a=read('local_agent_results.json')
    verification=read('verification.json')['paired_patient_bootstrap']
    published=json.loads((HERE/'reported_baselines.json').read_text())['papers']
    references=[]
    for p in published:
        for row in p['reported']:
            values='; '.join(f'{k}={v}' for k,v in row.items() if k!='method')
            references.append([f"[{p['title']}]({p['url']})",p['protocol_id'],row['method'],values,p['location']])
    pubtable=table(['Source','Protocol','Reported method','Reported metrics','Source location'],references)
    registry_rows=[
      ['GAMENet','MIMIC-III: 6,350 patients; 15,016 visits; 145 medications','Medication sets, DDI, memory ablations'],
      ['SafeDrug','MIMIC-III: 6,350 patients; 14,995 visits; 131 medications','Medication sets, DDI, molecular ablations, efficiency'],
      ['SafeRx-Agent','MIMIC-IV: 100 dev / 1,586 test; MIMIC-III: 901 patients','ATC-L4, expert routing, safety filtering'],
      ['RxEval','MIMIC-IV: 1,547 questions; 584 patients','Medication-dose-route options, exact match, macro F1'],
      ['MedAgentSim','NEJM 15 / extended 120; MedQA 106 / extended 214; MIMIC-IV 288','Diagnosis, measurement/memory/reasoning/ensemble ablations'],
      ['MedAgentBench','300 FHIR tasks; 100 patients','Tool-task success by task type'],
      ['GRASP','MedAgentBench and v2: dev/val/test/OOD = 96/80/64/60','Skill edits, regressions, OOD, cross-model transfer']]
    urls={p['title']:p['url'] for p in published}
    registry=table(['Paper','Data / task','Experiments'],[[f'[{name}]({urls[name]})',data,task] for name,data,task in registry_rows])
    registry_zh=table(['论文','数据与规模','所做实验'],[
      [f'[GAMENet]({urls["GAMENet"]})','MIMIC-III：6,350 患者、15,016 就诊、145 药物类','药物集合预测、药物相互作用、记忆消融'],
      [f'[SafeDrug]({urls["SafeDrug"]})','MIMIC-III：6,350 患者、14,995 就诊、131 药物类','药物预测、相互作用、分子编码消融、效率'],
      [f'[SafeRx-Agent]({urls["SafeRx-Agent"]})','MIMIC-IV：100 开发、1,586 测试；MIMIC-III：901 患者','ATC-L4 预测、专家路由、安全过滤'],
      [f'[RxEval]({urls["RxEval"]})','MIMIC-IV：1,547 题、584 患者','药物—剂量—途径多选、整题匹配、宏平均 F1'],
      [f'[MedAgentSim]({urls["MedAgentSim"]})','NEJM 15/扩展120；MedQA 106/扩展214；MIMIC-IV 288','诊断准确率、检查/记忆/推理/集成消融'],
      [f'[MedAgentBench]({urls["MedAgentBench"]})','300 个 FHIR 任务、100 患者','工具任务成功率、按任务类型分析'],
      [f'[GRASP]({urls["GRASP"]})','MedAgentBench 及 v2：开发/验证/测试/分布外 96/80/64/60','技能更新、退化检查、分布外、跨模型迁移']])
    rows=[]
    for name,m in e['metrics'].items():
        rows.append([name,f"{m['drug_micro_f1']:.5f}",f"{m['core_order_micro_f1']:.5f}",f"{m['saline_presence_f1']:.5f}",f"{m['mean_predicted_drugs']:.2f}"])
    m=r['test'];rows.append(['RxRSIAgent r2 selected',f"{m['drug_micro_f1']:.5f}",f"{m['core_order_micro_f1']:.5f}",f"{m['saline_presence_f1']:.5f}",f"{m['mean_predicted_drugs']:.2f}"])
    localtable=table(['Method, 4,000 cases','Drug F1','Core-order F1','Saline occurrence F1','Mean drugs'],rows)
    growth=table(['Training cases','Drug F1','Core-order F1','Promoted'],[[v['training_cases'],f"{v['test']['drug_micro_f1']:.5f}",f"{v['test']['core_order_micro_f1']:.5f}",v['promoted']] for v in e['growth']])
    pilot=table(['20-case local agent','Drug F1','Core-order F1','Mean drugs'],[[name,f"{m['drug_micro_f1']:.5f}",f"{m['core_order_micro_f1']:.5f}",f"{m['mean_predicted_drugs']:.2f}"] for name,m in a['test']['metrics'].items()])
    labels_zh={'retrieval_40k':'病例检索（40k）','static_8k':'初始处方策略（8k）',
       'full_data_global_templates':'普通训练＋全局订单模板（40k）','rxrsi_promoted':'累计训练＋相似病例模板（40k）',
       'RxRSIAgent r2 selected':'RxRSIAgent 验证选定版（40k）'}
    local_zh=table(['方法：同 4,000 测试例','药物 F1','核心订单 F1','盐水出现 F1','平均开药数'],[[labels_zh[x[0]]]+x[1:] for x in rows])
    growth_zh=table(['累计训练例数','药物 F1','核心订单 F1','验证是否接纳'],[[v['training_cases'],f"{v['test']['drug_micro_f1']:.5f}",f"{v['test']['core_order_micro_f1']:.5f}",'是' if v['promoted'] else '否'] for v in e['growth']])
    arm_zh={'catalogue_planner':'无病例经验的 LLM 规划','experience_planner':'加入病例经验的 LLM 规划','learned_policy':'直接学习的处方策略','rxrsi_selected':'验证选定输出（与上行相同）'}
    pilot_zh=table(['方法：同 20 测试例','药物 F1','核心订单 F1','平均开药数'],[[arm_zh[n],f"{m['drug_micro_f1']:.5f}",f"{m['core_order_micro_f1']:.5f}",f"{m['mean_predicted_drugs']:.2f}"] for n,m in a['test']['metrics'].items()])
    for lang in ['zh','en']:
        if lang=='zh':
            head='''# RxRSIAgent v0.6：处方生成、GT 自动反馈与进化实验

2026-10-14。完整设计见 [中文设计与执行计划](DESIGN.zh.md)。

![已执行的处方流程和训练反馈闭环](architecture.png)

## 本轮修正

1. 超过现有方法是**论文目标**，不作为 Agent 的患者推理指令。
2. 输出从五个 ATC 类别扩展到药名、途径、剂量、单位、频次；原始盐水订单直接保留。
3. 有 GT 的字段自动评分，医生评审不再是训练与实验的前置条件。
4. 已有论文分数直接纳入 reported baseline 表，不要求逐个复现；不同协议分组标明。

## 已执行的结果

数据：同一 MIMIC-IV/ED 队列，40,000 训练、4,000 验证、4,000 开发测试例。药物空间变为初始 8,000 训练例选出的 128 个原始药名，测试订单覆盖率约 85.34%。**该任务与此前 ATC-L4 任务不同，分数不跨版本直接比较。**

GT 包含药名、途径、剂量字符串、单位和部分频次。Core-order F1 严格比较前四者的联合元组，只在有完整参考字段的订单上计分；测试含 33,377 个完整参考核心订单。缺失的频次不计入字段准确率分母。盐水指标只衡量是否出现，不等于用途合理性。

### A. 相同 4,000 例，已执行方法表

'''
            interpretation=f'''
### B. 病例增长：r1 的相似病例订单模板策略

{growth_zh}

训练病例增加后药物 F1 从 0.35841 提升到 0.40668。联合订单分数在 r1 并非严格单调。r2 用验证集选择全局联合模板，联合订单 F1 达到 0.28003；相同 40k 训练数据的普通策略＋全局模板也达到这一分数，**目前不能把收益归因于独有的错误回放机制**。

病例级结果已独立重算。以 3,115 个测试患者为聚类单位做 2,000 次配对 bootstrap，r2 相比初始 8k 的药物 F1 差值为 +0.04827（95% 区间 0.04447–0.05234），核心订单 F1 差值为 +0.03698（0.03321–0.04082）。这些是开发集上的数据增长结果，不证明独有进化机制有效。

### C. 实际 LLM Agent 试验

{pilot_zh}

验证集选择**直接学习的处方策略**。小样本包含 20 验证例和 20 测试例；LLM 先列问题，再选择订单工具，由编译器展开字段。它选择已有模板，并未自由创造新剂量。两种 LLM 调用均为固定本地 Qwen3-4B-Instruct-2507 4bit；没有受限患者文本发往外部 API。

### D. 真实进化与消融

- 记录了 32,000 个新增训练病例的预更新错误反馈，包括漏药、多药和字段错误。
- 更新了策略模型、病例记忆、联合订单模板；固定最初 8k 的词表与输入表示，测试患者不反馈。
- r2 在验证集比较回放权重 0 / 0.25 / 1，选中 **{r['winner']['error_weight']}**；订单模式选中 **{r['winner']['order_mode']}**，阈值 **{r['winner']['threshold']}**。错误加权未产生额外收益，保留失败候选与原 r1 结果。
- 大模型参数未微调；自然语言技能自动编辑与 SFT/DPO 属于下一阶段，未伪装为已完成。

## 别人在哪些数据集、做了哪些实验

{registry_zh}

## 直接引用的 reported baseline 数据

下表来自原论文，不是本地复现；来源、表号与协议分组均保留。GAMENet 在原文、SafeDrug 和 SafeRx 的不同分数对应不同协议。RxRSIAgent 在这些正式协议上的结果尚待测量，因此不能用本地 raw-name 分数宣称超过。

{pubtable}

## 下一步与验收

优先接入 RxEval 全量 1,547 道处方多选题，再对齐 SafeRx-ATC4 的 MIMIC 协议；无需重训 published baselines。运行我们的正式 benchmark 行后再判断胜负。机制方面，以同训练病例量比较普通回放、错误加权、技能记忆、SFT 与组合，并加入独立测试患者和多种子。详细逐项计划见 [DESIGN.zh.md](DESIGN.zh.md)。

医生评审仅用于 GT 未覆盖的临床问题，可作为补充实验。当前 GT 自动评价、训练与版本迭代已经正常执行，均不等待医生标注。
'''
        else:
            head='''# RxRSIAgent v0.6: prescription generation and GT-supervised evolution

14 October 2026. See the [design and execution plan](DESIGN.en.md).

![Implemented prescription and training loop](architecture.png)

## Revised scope

Outperforming prior methods is the paper's hypothesis, not an inference instruction. Outputs now include drug names, route, dose, unit and frequency, including saline records absent from the old ATC map. Existing ground truth drives automatic evaluation; human review is optional for claims absent from those labels. Published baseline scores are imported with sources and protocol-specific grouping, without requiring baseline reimplementation.

The experiment uses the same patient-disjoint MIMIC-IV/ED 40k/4k/4k admissions. The 128-name vocabulary is fixed from the first 8k training cases and covers about 85.34% of test orders. This new raw-name task is not numerically interchangeable with prior ATC-L4 results. Core orders require exact drug/route/dose-string/unit agreement; 33,377 complete reference tuples are available. Unobserved frequency is excluded from field-accuracy denominators. Saline presence is an occurrence endpoint, not an indication endpoint.

### A. Executed same-4,000-case method comparison

'''
            interpretation=f'''
### B. r1 growth with similar-case order templates

{growth}

Drug F1 rises from 0.35841 to 0.40668. Core-order F1 is not strictly monotonic in r1. The r2 validation-selected global template policy reaches 0.28003 core-order F1; the same-40k ordinary policy/global-template control matches it. The current evidence therefore supports additional supervised data, but does not establish a unique error-replay advantage.

Independent set counts reproduce the scores. A 2,000-replicate paired bootstrap over 3,115 test patients gives r2-minus-8k drug F1 +0.04827 (95% interval 0.04447–0.05234) and core-order F1 +0.03698 (0.03321–0.04082). These developmental intervals describe data growth, not a unique evolution-mechanism benefit.

### C. Actual local LLM agent pilot

{pilot}

Validation selects `{a['validation_gate']['chosen']}`. There are 20 validation and 20 development-test cases. The local frozen Qwen3-4B planner identifies problems and selects learned order tools; a compiler expands their structured fields. This is template-based generation, not free dose invention. Restricted patient text never leaves the local machine.

### D. Executed updates and negative ablations

The pre-update error ledger contains 32,000 later training cases. Policy weights, case memory and joint order templates are updated; the initial vocabulary and input representation remain frozen. r2 selects replay weight {r['winner']['error_weight']}, mode {r['winner']['order_mode']} and threshold {r['winner']['threshold']} using validation only. The error-weighted alternatives do not win. Original r1 outputs and failed configurations remain available. LLM fine-tuning and natural-language skill editing are not completed capabilities.

## Literature dataset and experiment registry

{registry}

## Imported author-reported baselines

All rows below are directly cited, not locally reproduced. Protocol groups retain their source table and metric units. Our raw-name development experiment is not ranked against these different datasets or metrics. RxRSIAgent's matched-protocol rows remain to be measured.

{pubtable}

## Next acceptance gates

Prioritize the 1,547-question RxEval protocol, followed by SafeRx ATC-L4 MIMIC evaluation. Reuse reported baseline scores without retraining those methods. Compare our own matched-protocol row only after its inputs/splits/metric are aligned. Then run equal-data replay/skill/SFT ablations, multi-seed robustness and independent patient confirmation. Clinical review is an optional secondary evaluation of unobserved attributes, never a prerequisite for these GT-based experiments.
'''
        (HERE/f'RESULTS.{lang}.md').write_text(head+(local_zh if lang=='zh' else localtable)+interpretation)
    update_paper(e,r,a)

def update_paper(e,r,a):
    path=HERE.parent/'paper/latex/v0.3/prismatic_v03_en.tex'
    prefix=path.read_text().split('% PRISMATIC MANUSCRIPT START',1)[0]
    m=r['test']
    rows='\n'.join(f"{label} & {z['drug_micro_f1']:.4f} & {z['core_order_micro_f1']:.4f} & {z['saline_presence_f1']:.4f} & {z['mean_predicted_drugs']:.2f} \\\\" for label,z in [
        ('Case retrieval (40k)',e['metrics']['retrieval_40k']),('Initial policy (8k)',e['metrics']['static_8k']),
        ('Accumulated policy + similar-case templates (40k)',e['metrics']['rxrsi_promoted']),
        ('Ordinary policy + global templates (40k)',e['metrics']['full_data_global_templates']),('RxRSIAgent r2 selected policy (40k)',m)])
    growth='\n'.join(f"{z['training_cases']:,} & {z['test']['drug_micro_f1']:.4f} & {z['test']['core_order_micro_f1']:.4f} \\\\" for z in e['growth'])
    pilot='\n'.join(f"{label.replace('_',' ')} & {z['drug_micro_f1']:.4f} & {z['core_order_micro_f1']:.4f} \\\\" for label,z in a['test']['metrics'].items())
    body=r'''
\documentclass[sigconf,nonacm]{aamas}
\usepackage{tabularx,array,multirow}
\usepackage{balance}
\settopmatter{printacmref=false}
\setcopyright{none}
\title[RxRSIAgent]{RxRSIAgent: Ground-Truth-Guided Evolution for Structured Prescription Generation}
\subtitle{PRISMATIC research programme, draft v0.6 --- 14 October 2026}
\author{Ziyang Ling}
\email{zaneling@mail.ustc.edu.cn}
\affiliation{\institution{University of Science and Technology of China}\country{China}}
\author{Shuyu Lu}
\email{Shuyu.Lu@uth.tmc.edu}
\affiliation{\institution{The University of Texas Health Science Center at Houston}\country{United States}}
\begin{abstract}
We develop RxRSIAgent to improve structured prescription generation as ground-truth training cases accumulate. The agent combines a learned prescription policy, joint order templates, episodic retrieval, local language-model planning and structured compilation. An offline loop predicts new training cases before reading their targets, identifies omissions, extra drugs and field mismatches, updates the policy and memory, and selects versions using validation. On patient-disjoint MIMIC-IV/ED development data with 40,000/4,000/4,000 admissions, increasing training cases from 8,000 to 40,000 improves raw-drug micro-F1 from 0.3584 to 0.4067. Validation-selected order compilation achieves core-order F1 of 0.2800 compared with 0.2430 initially. The fixed 128-name vocabulary retains saline records omitted by the earlier ATC map. However, ordinary full-data training matches the selected policy, error-prioritized replay does not improve validation, and the current evidence does not establish a unique self-improvement advantage. Published baselines are cited directly under their original protocols; matched-protocol superiority remains the research objective. Existing prescription ground truth supports automatic evaluation without a human-review prerequisite. Unobserved indication and fluid-purpose attributes are outside the measured endpoints.
\end{abstract}
\keywords{Prescription generation, experience learning, medication recommendation, ground-truth feedback, agents}
\begin{document}
\pagestyle{fancy}\fancyhead{}\maketitle

\section{Introduction}
The objective of the PRISMATIC research programme is to build a prescription agent that outperforms existing methods on comparable benchmarks and improves as additional cases become available. RxRSIAgent makes the operational task explicit: produce a structured prescription from patient information, then use training-case ground truth to improve subsequent predictions. Superiority is a paper hypothesis tested by experiments; it is not embedded as a runtime instruction.

Three hypotheses organize the study. H1 asks whether the agent exceeds published methods under their benchmark protocols. H2 asks whether fixed-test prescription performance improves with accumulated feedback. H3 asks whether the update mechanism adds value over ordinary training and retrieval with the same data, backbone and inference budget. The completed development experiments support a data-growth effect for H2, but do not yet establish H1 or H3. This distinction prevents improvements from additional training data being misattributed to a novel agent mechanism.

\section{Related work and reported comparison protocols}
GAMENet and SafeDrug evaluate structured medication recommendation, while SafeRx-Agent uses fine-grained ATC-L4 candidate generation and verification \cite{gamenet,safedrug,saferx}. Their original results may be cited directly; reimplementing every baseline is not a prerequisite. Protocol identity remains necessary for a head-to-head claim. For example, GAMENet's original 145-medication setting differs from the 131-medication SafeDrug setting, and both differ from our raw-order prediction task.

RxEval evaluates timepoint-specific medication--dose--route options \cite{rxeval}. It is a closer external target for prescription detail, although option selection differs from unconstrained generation. MedAgentSim studies diagnostic experience replay \cite{medagentsim}; MedAgentBench evaluates FHIR task completion \cite{medagent}; GRASP studies proposed skill edits and regression-aware selection \cite{grasp}. Diagnostic accuracy and tool success are retained under their own endpoint labels.

\begin{table*}[t]
\centering\small
\caption{Source-reported benchmark registry. Counts refer to the cited protocol, not to our local development cohort.}
\label{tab:registry}
\begin{tabularx}{\linewidth}{@{}p{2.2cm}p{3.7cm}X@{}}
\toprule Work & Data and scale & Task / experiment family \\
\midrule
GAMENet & MIMIC-III: 6,350 patients, 15,016 visits & First-24-hour ATC-L3 medication sets; prediction, DDI and memory ablations \\
SafeDrug & MIMIC-III: 6,350 patients, 14,995 visits & 131 medications; prediction, DDI, molecular ablation and efficiency \\
SafeRx-Agent & MIMIC-IV: 100 development, 1,586 test cases; MIMIC-III: 901 patients & ATC-L4; shared-backbone agent comparison, filtering and safety analysis \\
RxEval & MIMIC-IV: 1,547 questions, 584 patients & Medication--dose--route multi-answer selection; exact match and set metrics \\
MedAgentSim & NEJM / MedQA variants; 288 MIMIC-IV cases & Diagnosis; measurement, memory, reasoning and ensemble ablations \\
MedAgentBench & 300 tasks, 100 patients & FHIR tool-task success and task-type analysis \\
GRASP & MAB dev/val/test/OOD: 96/80/64/60 & Skill evolution, regression tests, OOD and cross-model transfer \\
\bottomrule\end{tabularx}\end{table*}

\begin{table*}[t]
\centering\small
\caption{Directly cited published results (\textsuperscript{R}), without local baseline reimplementation. Each panel is a different protocol. F1 units and averaging follow the source. RxRSIAgent has not yet been measured on these exact protocols; its local raw-order scores in Table~\ref{tab:local} must not be inserted as comparable rows here.}
\label{tab:reported}
\begin{tabular}{@{}p{8.8cm}rr@{}}
\toprule Method and source protocol & Primary reported score & Secondary score \\
\midrule
\multicolumn{3}{l}{GAMENet original MIMIC-III, Table 3 \cite{gamenet}} \\
GAMENet\textsuperscript{R} & F1 0.6081 & Jaccard 0.4509 \\
\multicolumn{3}{l}{SafeDrug MIMIC-III, Table 2 \cite{safedrug}} \\
GAMENet, as reported by SafeDrug\textsuperscript{R} & F1 0.6626 & DDI 0.0864 \\
SafeDrug\textsuperscript{R} & F1 0.6768 & DDI 0.0589 \\
\multicolumn{3}{l}{SafeRx ATC-L4, Table 2: MIMIC-IV / MIMIC-III F1 \cite{saferx}} \\
GAMENet, as reported by SafeRx\textsuperscript{R} & 0.3356 & 0.2153 \\
SafeDrug, as reported by SafeRx\textsuperscript{R} & 0.3519 & 0.2361 \\
SafeRx / GPT-5.2, without filter\textsuperscript{R} & 0.4138 & 0.2812 \\
SafeRx / GPT-5.2, with filter\textsuperscript{R} & 0.3934 & 0.2641 \\
SafeRx / Claude Sonnet-4.6, without filter\textsuperscript{R} & 0.4325 & 0.2758 \\
SafeRx / Claude Sonnet-4.6, with filter\textsuperscript{R} & 0.4229 & 0.2667 \\
\multicolumn{3}{l}{RxEval prescription-option selection, Table 2 \cite{rxeval}} \\
Gemini-3.1-Pro\textsuperscript{R} & F1 77.10\% & Exact match 46.10\% \\
Qwen3.6-27B\textsuperscript{R} & F1 71.70\% & Exact match 40.00\% \\
\bottomrule\end{tabular}\end{table*}

\section{RxRSIAgent}
\subsection{Prescription workflow}
The agent receives a decision-time patient snapshot, identifies treatment problems and missing information, retrieves a learned order catalogue and training episodes, plans a prescription, and compiles selected order tools into structured fields. The current implementation uses chief complaint, acuity and home-medication text. A local frozen Qwen3-4B-Instruct-2507 model emits brief problem labels and order IDs. Each ID expands to a joint drug, route, dose-string, unit and frequency template. Invalid references are dropped individually rather than erasing all valid selections.

\begin{figure}[t]
\centering\small
\fbox{\parbox{.91\columnwidth}{\centering Patient state and treatment problems\\$\downarrow$\\Prescription policy + order-template tools\\$\downarrow$\\Case experience retrieval and local LLM planning\\$\downarrow$\\Structured prescription compilation\\$\downarrow$\\Research prescription + missing information\\[4pt]\hrule\vspace{4pt}Training only: prediction $\rightarrow$ GT comparison\\$\rightarrow$ typed error ledger $\rightarrow$ policy/memory update\\$\rightarrow$ validation replay $\rightarrow$ version selection}}
\caption{The prescription workflow and feedback loop. The agent plans and selects orders; its harness manages context, tools, compilation, scoring and versions. Test labels never enter the update loop.}
\label{fig:agent}\end{figure}

Validation chooses whether to deploy direct policy output or LLM-based selection. In the completed pilot it selects direct policy output; the LLM pathway is an evaluated candidate, not a demonstrated improvement. The policy can select up to 20 raw-name orders; the small LLM experiment receives the top 12 candidate tools. This removes the earlier fixed-five-ATC restriction but is still a bounded vocabulary. It is template-based order generation, not free synthesis of novel doses. Indication, fluid purpose and infusion rate remain unknown when the dataset does not supply them.

\subsection{Automatic ground-truth feedback and evolution}
For an incoming training block, the prior policy first predicts prescriptions. Only then are recorded targets used to identify omitted drugs, extra drugs and known-field mismatches. These are machine-readable error types, not invented clinical rationales. The system updates (i) the prescription policy parameters, (ii) the case memory, and (iii) joint order-template counts. Templates preserve route/dose/unit/frequency combinations instead of mixing independently selected fields.

The growth experiment refits the prescription policy using accumulated 8k, 16k, 32k and 40k training admissions. Text representation and the 128-name vocabulary are fixed from the initial 8k. A 32k-case pre-update error ledger additionally supports a replay experiment with weights
\begin{equation}
w_i=1+\alpha\min\!\left(2,\frac{n_i^{\rm missed}+n_i^{\rm extra}+n_i^{\rm fields}}{\max(1,|Y_i|)}\right),
\end{equation}
where $\alpha\in\{0,.25,1\}$ and $Y_i$ contains the observed training orders. Validation selects the replay strength, global versus similar-case templates, and a score threshold from $\{.1,.15,.2,.25,.3,.4,.5\}$. Version promotion maximizes the mean of drug-set and core-order micro-F1. Failed configurations and previous versions are retained. LLM weights do not change in this increment; natural-language skill edits and SFT/DPO remain separate proposed experiments.

\subsection{Ground truth and optional clinical review}
Recorded prescriptions provide direct supervision for drug selection and observed fields. These targets support training, automatic error feedback and benchmark evaluation without requiring clinician review. Unknown fields are excluded from their relevant accuracy denominators, not turned into fabricated answers. Human assessment is optional for additional claims such as unrecorded indication appropriateness or acceptable therapeutic alternatives. Its absence does not block the primary experiments.

\section{Experimental protocol}
The development cohort retains the earlier patient-disjoint MIMIC-IV/ED admission protocol: 40,000 training, 4,000 validation and 4,000 test admissions, with six-hour all-route prescription targets. No target fields enter the patient input. Triage entry time is assumed and medication reconciliation lacks storetime; the proxy-input limitation persists. Unlike the previous ATC map, raw-name targets retain unmapped medication and saline records. The fixed 128-name vocabulary covers 85.34\% of test order rows, so out-of-vocabulary targets remain in recall denominators.

Drug micro-F1 compares name sets. Core-order micro-F1 compares exact normalized tuples (name, route, dose string, dose unit); complete reference and predicted tuple counts are reported. There are 33,377 complete reference core orders in the 4,000-case test. Field agreement additionally includes frequency when observed, conditional on a correctly predicted drug name. Saline presence F1 measures recorded occurrence only. These endpoints do not score fluid purpose or infusion-rate correctness. The tests are developmental and previously inspected; independent confirmation is required for final paper claims.

The r1 experiment evaluates fixed-case retrieval, the initial 8k policy, accumulated-data policies and joint-template alternatives. The r2 development revision, made after inspecting r1, evaluates error-weighted replay and selects all hyperparameters on validation. A separate 20-validation/20-test local-model experiment compares catalogue planning, experience-augmented planning and direct learned-policy output. Its selected arm is frozen from validation before test scoring. Restricted patient inputs, weights, traces and targets remain local.

\section{Executed results}
\begin{table*}[t]\centering\small
\caption{Executed same-4,000-case raw-order comparison. This is a different task and metric space from the published ATC and MCQ panels. No clinician annotation was required.}
\label{tab:local}
\begin{tabular}{@{}p{7.0cm}rrrr@{}}\toprule
Method & Drug F1 & Core-order F1 & Saline F1 & Mean drugs \\
\midrule
LOCALROWS
\bottomrule\end{tabular}\end{table*}

\begin{table}[t]\centering\small
\caption{r1 growth with similar-case templates; test set fixed.}\label{tab:growth}
\begin{tabular}{@{}rrr@{}}\toprule Training cases & Drug F1 & Core-order F1 \\
\midrule GROWTHROWS
\bottomrule\end{tabular}\end{table}

Drug F1 improves with case accumulation, but the r1 core-order curve is not strictly monotonic. Validation selects the 40k policy. In r2, validation selects zero additional error weighting and global joint templates, reaching drug F1 0.40668 and core-order F1 0.28003 on the test. Ordinary full-data training with global templates matches these scores. Thus the present gain cannot be uniquely attributed to error prioritization or an autonomous self-improvement mechanism. This equal-data negative control is necessary for interpreting the growth result. Independent set counting reproduces the reported scores. A paired patient-cluster bootstrap (2,000 replicates, 3,115 patients) gives r2-minus-8k differences of +0.04827 drug F1 (95\% interval 0.04447--0.05234) and +0.03698 core-order F1 (0.03321--0.04082). These developmental intervals quantify data-growth effects, not a unique mechanism advantage.

\begin{table}[t]\centering\small
\caption{Executed local planning pilot on the same 20 development-test cases. Candidate catalogue and backbone are shared.}\label{tab:llm}
\begin{tabular}{@{}p{3.8cm}rr@{}}\toprule Arm & Drug F1 & Core F1 \\
\midrule PILOTROWS
\bottomrule\end{tabular}\end{table}
The validation-selected pilot arm is \texttt{SELECTEDARM}. These 20-case results are not extrapolated to the 4,000-case policy panel. The language model selects learned templates; the compiler supplies their fields. Schema success and clinical appropriateness are not interchangeable endpoints.

\section{Next experiments and paper acceptance criteria}
H1 will be tested by running RxRSIAgent on the published RxEval and SafeRx protocols and importing their baseline scores directly. RxEval's 1,547 questions provide a concrete prescription-detail target; its candidate-option construction must be retained. SafeRx requires compatible diagnosis/procedure histories and the same test membership and label normalization. If exact membership is unavailable, the study must report a protocol adaptation rather than a strict numerical win. Baseline retraining is not required by this plan.

H3 requires equal-data ablations of static training, raw episode retrieval, typed error memory, natural-language skill updates and parameter learning. Skill proposals should be tested on disjoint previously-passing and previously-failing development cases to measure fixes and regressions, following the motivation of GRASP \cite{grasp}. Updates must never use test feedback. Complete timepoint trajectories, ingredient identifiers and broader catalogues will improve coverage; clinician review remains optional for clinical attributes outside the recorded ground truth.

\section{Limitations and conclusion}
RxRSIAgent now has an executable prescription workflow and a supervised update loop rather than only a code-list reviewer. The current study demonstrates that more training data improves raw-drug prediction and that field-level evaluation is feasible without waiting for new human labels. It does not yet demonstrate superiority under the cited external protocols or unique gains from error-weighted replay. The original 2025 and v0.2--v0.5 artefacts remain in version history and bilingual reports; failures are not removed to create an artificial improvement narrative.

\appendix
\section{Prior engineering evidence}
The v0.5 50-case audit found 25 valid empty arrays in the old bounded reviewer, including 20 erased nonempty retrieval proposals. Free-output repair increased observed ATC F1 from 0.20820 to 0.31130. Parser-only repair of the original RAG responses reached 0.31081 without another model call, so extra review had little demonstrated benefit. The old 4,000-case ATC task reached 0.39176 mean F1 for a static word/character ensemble. These values use a different output space from the new raw-order experiment and are retained as historical engineering evidence.

\begin{thebibliography}{9}
\bibitem{gamenet} Shang et al. GAMENet. 2019. \url{https://arxiv.org/abs/1809.01852}.
\bibitem{safedrug} Yang et al. SafeDrug. 2021. \url{https://arxiv.org/abs/2105.02711}.
\bibitem{saferx} SafeRx-Agent. 2026. \url{https://arxiv.org/abs/2605.29146}.
\bibitem{rxeval} RxEval: A Prescription-Level Benchmark for Evaluating LLM Medication Recommendation. 2026. \url{https://arxiv.org/abs/2605.14543}.
\bibitem{medagentsim} Almansoori et al. Self-Evolving Multi-Agent Simulations for Realistic Clinical Interactions. 2025. \url{https://arxiv.org/abs/2503.22678}.
\bibitem{medagent} Jiang et al. MedAgentBench. 2025. \url{https://arxiv.org/abs/2501.14654}.
\bibitem{grasp} GRASP: Gated Regression-Aware Skill Proposer for Self-Improving LLM Agents. 2026. \url{https://arxiv.org/abs/2605.29668}.
\bibitem{mimic} MIMIC-IV v3.1 and MIMIC-IV-ED v2.2. \url{https://physionet.org/content/mimiciv/3.1/}; \url{https://physionet.org/content/mimic-iv-ed/2.2/}.
\end{thebibliography}
\end{document}
'''
    body=body.replace('LOCALROWS',rows).replace('GROWTHROWS',growth).replace('PILOTROWS',pilot).replace('SELECTEDARM',a['validation_gate']['chosen'].replace('_',r'\_'))
    path.write_text(prefix+'% PRISMATIC MANUSCRIPT START'+body)

if __name__=='__main__':run()
