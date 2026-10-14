"""Update the existing editor file using the pinned official ACL style and results."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
PAPER=ROOT/'paper/latex/v0.3/prismatic_v03_en.tex'
STYLE=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/resources/acl-style-files/acl.sty'

def run():
    summary=json.loads((ROOT/'upgrade_v7/results/summary.json').read_text());m=summary['methods']
    labels={'retrieval_global':'Case retrieval + global templates','retrieval_conditional_tool':'Case retrieval + conditional tool',
       'multinomial_nb':'Naive Bayes + order tool','word_policy_global':'Word policy + global templates',
       'word_policy_conditional_tool':'Word policy + conditional tool','word':'Tuned word policy + tool',
       'char':'Character policy + tool','word_char_ensemble':'Word/character ensemble + tool',
       'rxrsi_selected':'RxRSI accepted version','without_parameters_evolution':'Freeze initial policy parameters',
       'without_tool_evolution':'Freeze initial order tool','without_memory_evolution':'Freeze initial episode memory'}
    rows='\n'.join(f"{label} & {m[k]['drug_f1_mean']:.4f} $\\pm$ {m[k]['drug_f1_sd']:.4f} & {m[k]['order_f1_mean']:.4f} $\\pm$ {m[k]['order_f1_sd']:.4f} \\\\" for k,label in labels.items())
    seeds=[json.loads((ROOT/f'upgrade_v7/results/round_results_seed_{s}.json').read_text()) for s in [42,137,2026]]
    growth='\n'.join(f"{r} & {8000*(r+1):,} & "+' & '.join(f"{sum(d['rounds'][r]['metrics'][k] for d in seeds)/3:.4f}" for k in ['drug_micro_f1','core_order_micro_f1'])+r' \\' for r in range(5))
    public=ROOT/'upgrade_v8/results/public_results_seed_42.json';parameter=ROOT/'upgrade_v9/results/parameter_results.json'
    public_section=r'\paragraph{Execution status.} The public language-artifact experiment is running; incomplete evaluations are not presented as final results.'
    if public.exists():
        d=json.loads((ROOT/'upgrade_v8/results/summary.json').read_text())
        pr='\n'.join(f"{name.replace('_',' ')} & {z['accuracy_mean']*100:.2f} $\\pm$ {z['accuracy_sample_sd']*100:.2f} & {2 if name=='self_refine' else 1} \\\\" for name,z in d['methods'].items())
        if (ROOT/'upgrade_v10/results/grasp_core_seed_42.json').exists():
            pr+=r'''
Author GRASP core + task adapter & 50.81 & 1\\
Scoped RxRSI skills & 47.27 & 1\\'''
        if (ROOT/'upgrade_v11/results/summary.json').exists():
            evidence=json.loads((ROOT/'upgrade_v11/results/summary.json').read_text())
            for key,label in [('balanced','Fixed balanced evidence'),('safety','Fixed safety evidence'),('indication','Fixed indication evidence')]:
                if key not in evidence['complete_test_methods']:continue
                pr+=f"\n{label} & {100*evidence['complete_test_methods'][key]['accuracy']:.2f} & 2 \\\\"
        if (ROOT/'upgrade_v12/results/summary.json').exists():
            gates=json.loads((ROOT/'upgrade_v12/results/summary.json').read_text())['gate_summaries']
            for key,label in [('independent_guard','Router: separate guard'),('joint_validation','Router: pooled validation')]:
                z=gates[key];pr+=f"\n{label} & {100*z['accuracy_mean']:.2f} $\\pm$ {100*z['accuracy_sample_sd']:.2f} & {z['mean_calls']:.2f} \\\\"
        if (ROOT/'upgrade_v13/results/summary.json').exists():
            verifier=json.loads((ROOT/'upgrade_v13/results/summary.json').read_text())
            pr+=f"\nFull-data outcome verifier & {100*verifier['static_verifier_correct']/verifier['test_n']:.2f} & 2 \\\\"
            for key,label in [('uniform','Incremental verifier: uniform'),('error_prioritized','Incremental verifier: priority')]:
                z=verifier['arms'][key];pr+=f"\n{label} & {100*z['accuracy_mean']:.2f} $\\pm$ {100*z['accuracy_sample_sd']:.2f} & 2 \\\\"
        if (ROOT/'upgrade_v17/results/summary.json').exists():
            grounded=json.loads((ROOT/'upgrade_v17/results/summary.json').read_text())['datasets']['rxsafebench']['methods']
            for key,label in [('fixed_grounded','One-call fixed grounding'),('evolving_grounded','Grounded skill evolution')]:
                pr+=f"\n{label} & {100*grounded[key]['accuracy']:.2f} & 1 \\\\"
        public_section=r'''\begin{table}[t]\centering\small
\caption{Executed method comparison on the same 988 derived RxSafeBench questions with DeepSeek-V4.1-Flash. Rows with $\pm$ report three evolution orders; fixed outputs are reused across orders. Author-core and scoped-skill rows use seed 42. Calls are mean test-time model calls; development costs differ. This is a development comparison, not original benchmark score equivalence.}
\begin{tabularx}{\columnwidth}{@{}Xrr@{}}\toprule Method & Accuracy (\%) & Calls\\\midrule
PUBLICROWS
\bottomrule\end{tabularx}\end{table}'''.replace('PUBLICROWS',pr)
    core_path=ROOT/'upgrade_v10/results/grasp_core_seed_42.json'
    scoped_path=ROOT/'upgrade_v10/results/scoped_rsi_seed_42.json'
    if core_path.exists() and scoped_path.exists():
        public_section+=r'''\paragraph{Stronger implementation control.}
The unmodified author GRASP core, pinned to commit \texttt{9d7d125a}, is also executed through our new option-selection task adapter. It retains the released failure classification, skill proposals, balanced probes, regression gate and skill injection. This is not an original MedAgentBench rerun. It scores 502/988 (50.81\%) versus CoT's 467/988 (47.27\%), repairing 102 cases and regressing 67. The descriptive paired scenario-cluster 95\% interval for the gain is [0.91, 6.07] percentage points. Its RxQA result is 189/300 versus CoT's 193/300. Our additional scope-conditioned skill variant accepts no update and remains at 467/988: candidate rules activate on only 0--3 proposal cases. The author core and scoped variant use different development-selection mechanisms; their proposal cap is 3,072 tokens and inference cap is 512. No unrestricted method superiority is inferred.'''
    if (ROOT/'upgrade_v12/results/summary.json').exists():
        public_section+=r'''\subsection{Grounded Tools and Evolving Routing}
The next increment retrieves exact contiguous excerpts from company-submitted openFDA drug labels, retaining label IDs, sections and missingness. These records are not uniformly FDA-verified. A frozen snapshot matches 623/699 candidate names and covers 92.98\% of test options. Each evidence review receives the same initial CoT answer and at most two excerpts per option. The fixed balanced review, selected on proposal validation, scores 484/988; the fixed safety review scores 487/988. These require two model calls, versus one for CoT.

We learn action-benefit routing from complete counterfactual training outputs. A fixed 65,536-dimensional word/bigram hashing transform encodes the question, options and initial response. Ridge coefficients predict each review's correctness change relative to CoT. Four rounds expose 156/312/468/625 training cases. Three regularizers and three thresholds are selected on development labels. The original four-action experiment rejects all updates. A subsequent matched ablation uses the same three complete actions under two gates: 190-case proposal selection followed by 197-case regression checking, or pooled selection on all 387 development cases. Pooled selection has no independent regression check.

Across three orders, separate-guard routing reaches 48.68$\pm$0.61\%; pooled routing reaches 48.79$\pm$0.54\%, against the selected fixed tool's 48.99\%. Mean runtime calls are 1.710 and 1.490, respectively. Coefficients, intercepts and thresholds change; LLM weights, retrieval code and labels stay fixed. Full version hashes and per-round repairs/regressions are released. An accepted pooled update for seed 2026 reduces test correctness from 480 to 476. Thus accepted updates need not generalize, and parameter changes alone do not establish recursive improvement. This offline trace replay makes no new requests, but generating counterfactual development traces has an explicit model-call cost. It is a development extension on an already observed test, not untouched confirmation.

\paragraph{Transport recovery and output validity.}
Credit exhaustion interrupted indication review, Gemini development requests and two language-evolution orders. After account restoration, these runs resumed under their existing protocols; the invalid round-four selection was rolled back before resumption. All three language-evolution seeds are now complete, and indication review scores 478/988 (48.38\%). The client stops on account errors and the scorer rejects transport failures. Received malformed outputs still count as errors. Original invalidated summaries remain archived; they are not model scores.

The completed Gemini-3.8-Flash development pilot illustrates a separate token-budget failure. With its default reasoning setting and 512-token completion cap, CoT scores 72/190 with 69 invalid outputs; safety evidence scores 62/190 with 85 invalid outputs. Most invalid generations reach the output cap. A declared development-only repair selects low reasoning and a 1,024-token cap from two settings on the first 30 proposal cases. On all 190 proposal cases, CoT reaches 100/190 with 16 invalid outputs and evidence reaches 94/190 with 13. The 30-case selection subset contains only contraindication questions, a limitation of this pilot. A separately declared 2,048-token follow-up further reaches 105/190 with two invalid CoT outputs and 100/190 with one invalid evidence output. The setting is selected on development only. These are budget-sensitive development measurements, not a cross-backbone test claim.'''
    if (ROOT/'upgrade_v13/results/summary.json').exists():
        public_section+=r'''\subsection{Outcome-Aware Verification}
The pre-tool router cannot assess a revision it has not observed. A subsequent verifier consumes both the initial answer and the completed balanced evidence review, then chooses between them. Its features encode option mentions, nearby negative/positive terms and optionally separate fixed hashes of the question and both responses. Training targets the revision's correctness change. Uniform and error-prioritized updates use identical accumulated cases and 18 proposal candidates per round. Feedback weights are computed before updating and emphasize reachable selection errors; neither answer being correct provides no reachable repair. The same proposal/guard split controls promotion, and a full-data ordinary supervised verifier is included.

Three-order final accuracy is 49.12$\pm$0.23\% for uniform updates and 49.02$\pm$0.06\% for error priorities, compared with 48.99\% for fixed review and 47.87\% for the full-data verifier. Only one update is accepted in each of two runs; four runs remain unchanged. Both responses are charged even when the initial answer is returned. These small exploratory changes do not surpass the author-core GRASP control or establish a feedback-prioritization advantage. Parameter, weight and transition journals are released; actual language-model weight updates are tested separately below.'''
    if (ROOT/'upgrade_v17/results/summary.json').exists():
        public_section+=r'''\subsection{Grounded Skill Composition}
We combine the fixed balanced label tool with the unchanged GRASP optimizer, holding the actor prompt, backbone and one-call 512-token inference budget constant. The four-cell comparison is CoT (467/988), skills without labels (502), labels without skills (499), and learned skills with labels (501). The combined state repairs 83 cases and regresses 81 relative to fixed grounding: +0.20 percentage points, with a descriptive paired scenario interval [-2.43, 2.73]. The factorial interaction is -3.34 points, interval [-7.18, 0.30]. Thus separate component gains do not add reliably.

On 300 RxQA transfer items, the same four states score 193, 189, 188 and 183. The first feedback batch accepts no skill; the following three add and then twice modify one indication/caution procedure. Actual text and hashes are released. The author core selects its final checkpoint on end-of-epoch validation, which rises from 49.1\% to 53.2\%; it does not apply our independent-guard mechanism at every batch. LLM weights and retrieval code remain fixed. On the fixed 988-case test, round 0--4 correctness is 499, 499, 475, 493 and 501; on RxQA it is 188, 188, 175, 175 and 183. The first accepted skill therefore regresses before later edits recover part of the loss. These are frozen-state trajectories, distinct from batch accuracies on different cases; they do not show monotonic self-improvement.'''
    if (ROOT/'upgrade_v18/results/summary.json').exists():
        transfer=json.loads((ROOT/'upgrade_v18/results/summary.json').read_text())
        names={'cot':'CoT','frozen_author_grasp':'Frozen author-core skills','fixed_grounded':'Fixed grounded harness','frozen_grounded_grasp':'Frozen grounded skills'}
        rr='\n'.join(f"{label} & {transfer['methods'][key]['correct']} & {transfer['methods'][key]['invalid']} \\\\" for key,label in names.items())
        public_section+=r'''\subsection{Frozen Skill Transfer to a Second Backbone}
The two DeepSeek-learned skill states transfer unchanged to Gemini-3.8-Flash. All four methods use the same 988 questions, one call, low reasoning and a 2,048-token completion cap selected on development before testing. Skills, tool code and backbone weights remain fixed during evaluation. These are method comparisons within the second backbone; different completion caps prevent interpreting the two backbones as an equal-compute ranking.
\begin{table}[t]\centering\small
\caption{Frozen-artifact transfer: correct answers out of 988 and received invalid outputs.}
\begin{tabular}{lrr}\toprule Method & Correct & Invalid\\\midrule
TRANSFERROWS
\bottomrule\end{tabular}\end{table}
All case-level decisions are independently recounted. Transport failures are resumed from cache and never scored as model errors. Paired source-scenario intervals, fixes, regressions and actual logical token costs are released. One source skill-learning path does not establish seed robustness.'''.replace('TRANSFERROWS',rr)
    temporal_section=''
    if (ROOT/'upgrade_v21/results/independent_cohort_audit.json').exists():
        temporal_section=r'''\subsection{Recorded-Availability-Controlled New Orders}
The earlier start-time task does not establish prospective availability. We therefore re-read the complete source tables and set the decision to actual hospital admission plus six hours, predicting new/changed orders in the next six hours. Both provider ordertime and pharmacy entertime must lie in that future window, linked patient/admission/POE identities must agree, and pharmacy verification must occur by its end. An admission is excluded if any potentially in-window order fails these criteria, and follow-up must cover the whole window. This defines a selected coherent-time, nonempty-target cohort, not the general inpatient population.

Inputs contain gender, decade-binned age, at most 24 prior joint-order tuples and 32 blood measurements. Every prior order has all three recorded timestamps before the decision; laboratory charttime and storetime must both be available. Untimed triage and discharge diagnoses are excluded. Of 201,750 source admissions, 54,959 satisfy eligibility. After fixed sampling and excluding all previous v0.6/v0.7/v0.9 test patients, the split is 40,000/2,000/2,000/1,082 train/proposal/guard/test, with 1,024 test patients and no cross-split patient overlap. Independent reconstruction checks 198,850 target rows, 589,393 prior-order rows and 506,710 lab rows with zero violations of the declared identity/time/finiteness checks.

The initial-8k vocabulary, feature mapping, output cap, method family and three seeds are frozen before training. We repeat policy, memory and conditional-tool evolution alongside full-data word/character models, retrieval, naive Bayes, prevalence and prior-order reuse. Test scoring follows within-seed selection freeze. This is a separate temporal task; its raw-name scores cannot be pooled with the older start-time table or published ATC results. Released tables lack full field-version histories, so recorded timestamps do not prove what clinicians actually viewed.
'''
        if (ROOT/'upgrade_v21/results/summary.json').exists():
            tm=json.loads((ROOT/'upgrade_v21/results/summary.json').read_text())['methods']
            keys={'prevalence':'Training prevalence','reuse_prior_orders':'Reuse prior orders','retrieval_conditional_tool':'Case retrieval + tool','word_policy_conditional_tool':'Word policy + tool','word_char_ensemble':'Word/character + tool','rxrsi_selected':'RxRSI selected state','without_tool_evolution':'Freeze initial tool','without_memory_evolution':'Freeze initial memory'}
            tr='\n'.join(f"{label} & {tm[k]['drug_f1_mean']:.4f} $\\pm$ {tm[k]['drug_f1_sd']:.4f} & {tm[k]['order_f1_mean']:.4f} $\\pm$ {tm[k]['order_f1_sd']:.4f} \\\\" for k,label in keys.items())
            temporal_section+=r'''\begin{table*}[t]\centering\small
\caption{Recorded-availability task: matched 1,082 test admissions, mean $\pm$ sample SD across three seeds. Fixed prevalence/reuse controls are reused across seeds.}
\begin{tabular}{lrr}\toprule Method & Drug micro-F1 & Core-order micro-F1\\\midrule
TEMPORALROWS
\bottomrule\end{tabular}\end{table*}
Independent saved-prediction counting reproduces all method and checkpoint scores. Accepted-state trajectories, per-case improvements/regressions, artifact hashes and descriptive patient-cluster intervals accompany the release. A gain over the initial 8k checkpoint alone is insufficient evidence of an advantage over equal-data learning.'''.replace('TEMPORALROWS',tr)
            temporal_section+=r'''Mean drug/order F1 rises from 0.1660/0.0942 to 0.1914/0.1153, yet the full-data ensemble reaches 0.2010/0.1207. Drug-F1 differences versus the ensemble have negative paired intervals in all three seeds. Freezing initial memory improves the final mean to 0.1956/0.1183. The final empty-output rate is 2.74\% on this new protocol; it is not a matched before/after comparison to earlier pilots. These results again separate case-growth gains from a unique RSI advantage.'''
        else:temporal_section+=r'\paragraph{Execution status.} The cohort and its independent audit are complete; the registered three-seed method experiment is running. No incomplete method table is treated as final.'
        if (ROOT/'upgrade_v22/results/summary.json').exists():
            temporal_section+=r'''\paragraph{Development-only representation intervention.}
The text policy treats numerical measurements as tokens. A subsequent registered pilot fits typed prior-order/lab features and numerical scales on the initial 8k training contexts, then compares typed and combined word/typed selectors on proposal validation. The single selected candidate retains the original conditional order tool and improves 2,000-case guard drug/order F1 from 0.2194/0.1346 to 0.2246/0.1366. Paired patient intervals for the differences are [-0.0006, 0.0108] and [-0.0024, 0.0065]. Both include zero. No test prediction is generated in this one-seed pilot; it motivates further study rather than establishing an RSI or held-out superiority result.'''
    parameter_section=r'\paragraph{Execution status.} Local parameter-update experiments are in progress. No fine-tuning gain is claimed before generation-based evaluation is complete.'
    if parameter.exists() and (ROOT/'upgrade_v9/results/summary.json').exists():
        d=json.loads((ROOT/'upgrade_v9/results/summary.json').read_text())
        names={'base':'Frozen Qwen3-4B','uniform_sft':'Uniform updates','error_prioritized_sft':'Error-prioritized updates','all_20_candidate_tools':'All 20 candidate tools','guard_selected_top_k_tools':'Guard-selected top-8 tool'}
        rr='\n'.join(f"{label} & {d['methods'][key]['drug_f1']:.4f} & {d['methods'][key]['core_order_f1']:.4f} \\\\" for key,label in names.items())
        parameter_section=r'''\begin{table}[t]\centering\small
\caption{Local parameter evolution on 500 new test admissions. Checkpoints are selected on the separate guard set.}
\begin{tabular}{lrr}\toprule Method & Drug F1 & Order F1\\\midrule
PARAMROWS
\bottomrule\end{tabular}\end{table}'''.replace('PARAMROWS',rr)
        parameter_section+=r'''Both training arms improve over the frozen language model, but neither beats direct use of the same guard-selected top-8 tool. The paired patient-cluster 95\% drug-F1 intervals versus that tool are [-0.0367, -0.0132] for uniform updates and [-0.0400, -0.0149] for error priorities. Uniform updating is slightly stronger on drug F1; the priority-minus-uniform interval [-0.0067, 0.0013] does not establish a prioritization benefit.

The test contains 6.784 gold drugs per admission and 3.802 reachable drugs in the fixed catalogue. Selected uniform and priority models emit 17.416 and 18.976 drugs on average, exposing severe over-selection. The uniform active state improves in round one, slightly regresses after the accepted round-two update, and retains round two thereafter. Priority retains round one; its last raw checkpoint degenerates on the guard, with 53\% empty outputs, and is rejected. This is a genuine learned-checkpoint failure after valid parsing. A subsequent exact 20-position inclusion-mask intervention was declared before these test results and is now training with the same patients and step budgets.'''
    body=r'''
\documentclass[11pt]{article}
\usepackage[review]{acl}
\usepackage{times,latexsym}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{microtype,booktabs,tabularx,amsmath,graphicx}
\title{RxRSIAgent: Auditing Iterative Improvement in Prescription Decisions}
\author{Anonymous ACL submission}
\begin{document}
\maketitle
\begin{abstract}
An improving prescription agent must demonstrate what changes between versions and whether those changes improve held-out decisions. We study RxRSIAgent as a system of separately versioned prescription policies, episodic memories, order-completion tools and language skills. Ground-truth training prescriptions provide error feedback, with explicit development-selection protocols. Three-seed experiments use 40,000 training admissions, a legacy 4,000-admission test and a rebuilt recorded-availability task with 1,082 new test admissions. Five-checkpoint scores increase with cases, but strong same-data supervised controls remain better. On 988 public prescription-choice questions, combining grounded evidence with learned skills scores 50.71\%, against 50.81\% for the author skill-learning core, and transfer declines. Local QLoRA updates improve over a frozen model on 500 new admissions but trail direct top-8 tool use. Real FHIR probes additionally show that accepted writes can discard fields. These results distinguish artifact changes, reliable execution and generalizing gains. Published comparisons retain their original protocols; universal superiority and a unique RSI advantage remain unproven.
\end{abstract}

\section{Introduction}
Prescription generation combines medication selection with detailed order construction. A system that improves as cases accumulate could reduce repeated omissions and field errors, but a higher final score alone does not establish recursive self-improvement (RSI). More training data, a stronger backbone, a larger inference budget or a changed scorer can produce the same appearance.

We therefore separate three questions. H1 concerns performance against methods under a common task protocol. H2 concerns improvement across frozen checkpoints on a fixed test set. H3 concerns the causal contribution of updated artifacts relative to equal-data controls. H2 can hold even when H3 fails. Existing prescription ground truth supports automatic training and evaluation; clinician review is not a prerequisite for observed-label agreement.

Our current contributions are an executable structured-order task, a versioned update protocol, and an artifact-level evaluation that retains regressions and rejected versions. We do not present ordinary cumulative supervised fitting as proof of autonomous reasoning improvement. Two further experiments isolate LLM-authored language artifacts and actual LLM parameter updates.

\begin{figure*}[t]\centering\small
\begin{tabular}{c@{\ $\rightarrow$\ }c@{\ $\rightarrow$\ }c@{\ $\rightarrow$\ }c}
\fbox{\parbox{2.9cm}{\centering Available patient or task state}} &
\fbox{\parbox{2.9cm}{\centering Candidate orders, labels or FHIR records}} &
\fbox{\parbox{2.9cm}{\centering Decision policy with versioned skills}} &
\fbox{\parbox{2.9cm}{\centering Compile orders; execute and read back}}\\[1.2em]
\fbox{\parbox{2.9cm}{\centering Training-only GT and error traces}} &
\fbox{\parbox{2.9cm}{\centering Propose artifact or parameter updates}} &
\fbox{\parbox{2.9cm}{\centering Declared development selection}} &
\fbox{\parbox{2.9cm}{\centering Freeze accepted state; retain regressions}}
\end{tabular}
\caption{Shared prescription-harness design. Each study instantiates the stated components: option selection does not execute orders, and local template selection does not generate new doses. Only training feedback drives updates; test GT is reserved for measurement. The FHIR compiler is an engineering repair, not an autonomously evolved tool.}
\label{fig:harness}
\end{figure*}

\section{Related Work and Comparison Protocols}
GAMENet and SafeDrug predict medication sets from structured histories \citep{gamenet,safedrug}. SafeRx-Agent evaluates finer ATC-L4 sets using expert generation and verification \citep{saferx}. RxEval evaluates medication--dose--route options at prescribing timepoints \citep{rxeval}. Their reported results can be cited directly without reproducing every baseline, but our own comparison row must follow the corresponding data, input and scoring protocol.

GRASP learns persistent skills with regression-aware selection \citep{grasp}. EvoTool mutates modular tool-use policies while freezing the backbone \citep{evotool}. Process-oriented work such as EvoPathBench motivates evaluating capability retention and adaptation along artifact trajectories \citep{evopath}. These mechanisms inform our controls; our task adaptations are explicitly distinguished from official benchmark reruns.

\begin{table*}[t]\centering\small
\caption{Published task registry. These datasets and protocols differ from the local order task.}
\label{tab:registry}
\begin{tabularx}{\textwidth}{@{}p{2.2cm}p{4.0cm}X@{}}\toprule
Work & Data & Experiments / outputs\\\midrule
GAMENet & MIMIC-III; 6,350 patients, 15,016 visits & 145 medication classes; prediction, DDI and memory ablations\\
SafeDrug & MIMIC-III; 6,350 patients, 14,995 visits & 131 classes; DDI, molecular representations, efficiency\\
SafeRx-Agent & MIMIC-IV 1,586 test; MIMIC-III 901 patients & ATC-L4, expert routing and verification\\
RxEval & MIMIC-IV; 1,547 questions, 584 patients & Medication/dose/route options; macro F1 and exact match\\
RxSafeBench & 2,443 source consultation scenarios & Medication risks; our derived option-selection split is separate\\
RxQA & Public OpenFDA subset: 300 questions & Pharmacist-reviewed medication reasoning; transfer evaluation\\
GRASP / EvoTool & FHIR and general tool-task benchmarks & Skill or modular prompt evolution; regression/transfer ablations\\
\bottomrule\end{tabularx}\end{table*}

\begin{table*}[t]\centering\small
\caption{Directly cited author-reported prescription results (R). Panels must not be ranked across protocols. Our matching official RxEval and SafeRx test data are unavailable locally; no unsupported comparison row is inserted.}
\label{tab:reported}
\begin{tabular}{@{}p{8.4cm}rr@{}}\toprule Method / source protocol & Primary score & Secondary score\\\midrule
\multicolumn{3}{l}{Original GAMENet, Table 3 \citep{gamenet}}\\
GAMENet (R) & F1 0.6081 & Jaccard 0.4509\\
\multicolumn{3}{l}{SafeDrug MIMIC-III, Table 2 \citep{safedrug}}\\
GAMENet, as reported by SafeDrug (R) & F1 0.6626 & DDI 0.0864\\
SafeDrug (R) & F1 0.6768 & DDI 0.0589\\
\multicolumn{3}{l}{SafeRx ATC-L4, Table 2: MIMIC-IV / III F1 \citep{saferx}}\\
GAMENet, as reported by SafeRx (R) & 0.3356 & 0.2153\\
SafeDrug, as reported by SafeRx (R) & 0.3519 & 0.2361\\
SafeRx / GPT-5.2, no filter (R) & 0.4138 & 0.2812\\
SafeRx / Claude Sonnet-4.6, no filter (R) & 0.4325 & 0.2758\\
\multicolumn{3}{l}{RxEval option selection, Table 2 \citep{rxeval}}\\
Gemini-3.1-Pro (R) & F1 77.10\% & Exact match 46.10\%\\
Qwen3.6-27B (R) & F1 71.70\% & Exact match 40.00\%\\
\bottomrule\end{tabular}\end{table*}

\section{Agent State and Update Mechanism}
At round $r$, let the persistent state be $S_r=(W_r,M_r,T_r,K_r)$: prescription-selection parameters, episodic memory, order-tool state, and language skills. Runtime inference takes a patient snapshot, retrieves candidates and applicable experience, plans selections, and compiles structured orders. The current order compiler returns drug, route, dose string, dose unit and observed frequency; unobserved clinical attributes remain unknown.

\begin{figure}[t]\centering\small
\fbox{\parbox{.91\columnwidth}{\centering Patient state\\$\downarrow$\\Candidate policy + order tools + applicable memory\\$\downarrow$\\Prescription planner and structured compiler\\$\downarrow$\\Research prescription\\[3pt]\hrule\vspace{3pt}Training prediction $\rightarrow$ observed GT errors\\$\rightarrow$ candidate artifact edits\\$\rightarrow$ proposal validation + regression guard\\$\rightarrow$ accepted state or retained prior version}}
\caption{Inference and training feedback. Test labels enter scoring only. Different experiments isolate different evolving objects.}
\end{figure}

For an incoming training block in the language and parameter studies, predictions precede ground-truth feedback. Error records identify omissions, extra drugs and observed-field mismatches. The updater proposes artifact changes. The candidate is selected on proposal validation; a patient-disjoint guard set then checks whether it improves the composite objective without excessive regression in either primary endpoint. Old states are retained. The guard is reused across rounds and is therefore a development resource, not an untouched test.

Each version records the parent, edited objects, data membership hashes, artifact hashes, validation scores, acceptance, improvements and regressions. A changing memory size or hash demonstrates that an artifact changed; leave-one-object-out evaluation is required to demonstrate that it helped. LLM weights, tool configuration and executable tool code are distinct objects and are never conflated.

\section{Study A: Structured-Order Artifact Learning}
\subsection{Data and metrics}
The task uses six-hour all-route prescription targets after an ED-to-hospital admission in MIMIC-IV/ED. Training contains 40,000 admissions. Proposal validation and the regression guard contain 2,000 admissions each; test contains 4,000 admissions from 3,440 patients. Development/test patients used in the previous v0.6 increment are excluded. All current splits are patient-disjoint.

Actual model inputs are chief complaint, acuity and home-medication text. The 128 raw-name vocabulary and word representation are fixed from the first 8,000 training admissions. Drug micro-F1 compares name sets, including out-of-vocabulary targets in recall. Joint-order micro-F1 compares complete normalized (drug, route, dose-string, unit) tuples. The test contains 30,769 complete reference tuples. Frequency agreement is secondary and excludes missing GT values. These endpoints measure recorded-order agreement, not clinical safety.

\subsection{Methods and rounds}
We compare retrieval, Naive Bayes, word and character policies, a validation-tuned ensemble, global templates, and a learned context-conditioned joint-order tool. The tool predicts an observed field combination rather than independently mixing fields. Thresholds and word/character weights are selected using proposal validation, with the same 20-order maximum.

The evolving system receives 8k, 16k, 24k, 32k and 40k accumulated cases. Candidate updates change parameters, memory, the order tool, or their combination. The guard accepts a candidate only when the mean drug/order F1 improves and neither endpoint falls by more than 0.002. Seeds 42, 137 and 2026 repeat the experiment. Test evaluation begins after all choices are frozen.

\begin{table*}[t]\centering\small
\caption{Executed same-4,000-case comparison: mean $\pm$ sample SD across three seeds. The final three rows freeze one object of the selected state without retuning the others.}
\label{tab:local}
\begin{tabular}{@{}p{7.7cm}rr@{}}\toprule Method & Drug micro-F1 & Joint-order micro-F1\\\midrule
METHODROWS
\bottomrule\end{tabular}\end{table*}

\begin{table}[t]\centering\small
\caption{Accepted-state trajectory on the fixed test; mean over three seeds.}
\label{tab:rounds}
\begin{tabular}{rrrr}\toprule Round & Cases & Drug F1 & Order F1\\\midrule
GROWTHROWS
\bottomrule\end{tabular}\end{table}

The accepted-state curves are non-decreasing on this test for all three seeds, including a flat final step when seed 137 rejects its proposal. Individual cases still regress. Conditional order-tool learning improves joint-field matching. Memory expansion is not consistently helpful; freezing initial memory can improve the final state. The full evolving system does not beat the strong same-data ensemble/tool control. Thus case-growth gains support H2 in this setting but do not establish H3. Independent set counting reproduces all scores; paired patient-cluster bootstrap intervals and per-round regressions are released with the aggregate results.

TEMPORALSECTION

\section{Study B: Language-Artifact RSI}
To test genuine changes to language-guided behavior, the next experiment freezes DeepSeek-V4.1-Flash and evolves reusable skills, episodic memory and the configuration of an evidence-focus tool. The tool returns exact current-dialogue excerpts selected by learned focus terms; its source code is fixed. An LLM proposes changes from its own training-error traces, and the runner saves the full before/after artifacts.

The public RxSafeBench data are verified against pinned source hashes and converted to a clearly labeled three-option task. Medication-scenario grouping yields 625 training, 190 proposal, 197 guard and 988 test cases with no cross-split scenario or exact-dialogue overlap. Four rounds expose additional training cases. Direct, CoT, Self-Refine, case RAG and explicit Reflexion/GRASP/EvoTool task adaptations form the comparison set. Evolving comparators receive four candidate-evaluation slots per round; all token costs are reported. The separate 300-question RxQA subset tests transfer without using its labels for evolution. These are public simulated/released questions; restricted patient inputs are never uploaded.

PUBLICSECTION

\section{Study C: Parameter Evolution}
A local Qwen3-4B QLoRA study compares uniform supervised updates with feedback-prioritized updates, holding the initial-8k candidate tools fixed. Three disjoint feedback blocks contain 600 new training admissions each. Both arms make pre-update predictions, train on 400 sampled examples for 100 optimizer steps per round, and use the same 200-case guard. Feedback weights target reachable candidate-selection errors rather than blaming the language model for drugs missing from its fixed catalogue. A separate 500-admission test excludes all patients in the earlier v0.6/v0.7 tests.

The Qwen chat template can emit an empty reasoning envelope before valid JSON. The parser removes only that empty envelope uniformly for all checkpoints, retains strict and normalized validity, and rebinds cached outputs to the current case. These repairs occurred on development data before test scoring; raw generations and learned weights are unchanged.

PARAMETERSECTION

\section{Study D: Executed FHIR Tools}
We extract the unchanged application and public database from the digest-pinned official MedAgentBench image and run its HAPI FHIR 7.6.0 service on a native Java runtime. Five executed probes cover creation, readback, versioned updates, atomic rejection and cleanup. Original counts are restored: 695 patients, 21,991 medication requests and 563,426 observations. Runtime equivalence beyond these checks is not assumed.

The released benchmark wrapper records accepted POST actions without performing the HTTP write; its reference grader checks trajectories. Our development adapter performs actual writes for both methods, reports the reference trajectory criterion separately from persisted-state checks, and removes only resources it creates. A 16-case pilot uses the first two cases from each of eight development task types, DeepSeek-V4.1-Flash and at most eight 512-token action calls. Direct tool use succeeds on 10/16; a fixed workflow/preflight/readback harness succeeds on 8/16. All 11 created resources pass readback checks and are cleaned up. Invalid-action counts are one and three, respectively. These small development results expose protocol and retrieval failures; they are neither full benchmark scores nor evidence of self-improvement. No restricted MIMIC records enter this service.

A further synthetic medication-order probe finds that the server accepts a literal route string with HTTP 201 but fails to preserve the dosage fields. A lossless conversion to FHIR R4 CodeableConcept text preserves the route on readback \citep{fhirr4}. Duration-like units in legacy rate fields are retained and flagged, without claiming clinically valid rate semantics. This motivates checking stored fields in addition to API status. Full ID and held-out-task-type evaluation is in progress. Released task splits overlap in patients (22 explicit development/ID-test patients and 33 development/held-out-type patients); this study does not claim patient-disjoint transfer.

\section{Limitations}
The completed structured-order experiment uses admission-proxy inputs. Triage has no verified entry timestamp and medication reconciliation lacks storetime; temporal availability is therefore not fully established. A full target-row audit links 1,788,195 records to provider and pharmacy clocks: 42,005 matching provider orders precede admission, 1,425,392 fall within the intended next-six-hour horizon, and 276,269 occur later. There are 438 provider-link admission conflicts, which remain untrusted. Pharmacy entry falls within the horizon for 1,777,546 rows. The two source linkage paths agree on all 1,757,038 rows where both IDs exist and reproduce identical temporal counts. These clocks still differ; the retrospective start-window results are not prospective new-order evidence. A new availability-controlled cohort must be reconstructed from complete source tables rather than filtering old targets. Candidate vocabularies and one-template-per-drug output limit recall. Recorded prescriptions may omit clinically acceptable alternatives, and agreement does not prove indication or safety. Current language-artifact baselines are task adaptations, not official reruns. Repeated development selection can overfit; independent tests, multiple evolution orders, transfer and matched optimization budgets are necessary before claiming general RSI benefits. External RxEval and SafeRx data access remains unresolved.

\section{Conclusion}
An auditable improving agent must show both changing artifacts and beneficial effects. Our completed rounds show data-growth gains and a useful conditional order tool, alongside weak memory gains and a stronger static control. We continue beyond that negative result by isolating language-artifact and parameter evolution. No claim that RxRSIAgent is the best existing method is made without corresponding benchmark evidence.

\section*{Ethics and Data Access}
All restricted MIMIC records, predictions and checkpoints remain on the authorized local machine. Public releases contain code, configurations and aggregate measurements. Existing GT supports automated evaluation without mandatory new clinical annotation. The system is evaluated for research and is not deployed to prescribe for patients.

\begin{thebibliography}{9}
\bibitem[Shang et al.(2019)]{gamenet} Shang et al. 2019. GAMENet. \url{https://arxiv.org/abs/1809.01852}.
\bibitem[Yang et al.(2021)]{safedrug} Yang et al. 2021. SafeDrug. \url{https://arxiv.org/abs/2105.02711}.
\bibitem[Wang et al.(2026)]{saferx} Wang et al. 2026. SafeRx-Agent. \url{https://arxiv.org/abs/2605.29146}.
\bibitem[Chen et al.(2026)]{rxeval} Chen et al. 2026. RxEval. \url{https://arxiv.org/abs/2605.14543}.
\bibitem[Moll et al.(2026)]{grasp} Moll et al. 2026. GRASP: Gated Regression-Aware Skill Proposer for Self-Improving LLM Agents. \url{https://arxiv.org/abs/2605.29668}.
\bibitem[Yang et al.(2026)]{evotool} Yang et al. 2026. EvoTool: Self-Evolving Tool-Use Policy Optimization in LLM Agents via Blame-Aware Mutation and Diversity-Aware Selection. ACL. \url{https://syang2000.github.io/ACL_2026_EvoTool/}.
\bibitem[Lin et al.(2026)]{evopath} Lin et al. 2026. Beyond Endpoint Performance: Process-Level Evaluation of Self-Evolving Agents. \url{https://arxiv.org/abs/2609.24663}.
\bibitem[HL7 International(2019)]{fhirr4} HL7 International. 2019. FHIR R4: Dosage Detailed Descriptions. \url{https://hl7.org/fhir/R4/dosage-definitions.html}.
\end{thebibliography}
\end{document}
'''
    body=body.replace('METHODROWS',rows).replace('GROWTHROWS',growth).replace('PUBLICSECTION',public_section).replace('PARAMETERSECTION',parameter_section).replace('TEMPORALSECTION',temporal_section)
    sty=STYLE.read_text();prefix='% Official ACL style embedded for the standalone editor. See acl_template_provenance.json.\n'+r'\begin{filecontents*}[overwrite]{acl.sty}'+'\n'+sty+'\n'+r'\end{filecontents*}'+'\n% PRISMATIC MANUSCRIPT START\n'
    PAPER.write_text(prefix+body)
    provenance={'repository':'https://github.com/acl-org/acl-style-files','commit':'d5adc823ff0f80f98c80405ca0ab66c68e684409',
        'acl_sty_sha256':hashlib.sha256(STYLE.read_bytes()).hexdigest(),'target':'ACL 2027','mode':'review','path_preserved':str(PAPER.relative_to(ROOT)),
        'previous_template':'Original AAMAS template preserved in Git history through commit 9875d2fd.'}
    (PAPER.parent/'acl_template_provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')

if __name__=='__main__':run()
