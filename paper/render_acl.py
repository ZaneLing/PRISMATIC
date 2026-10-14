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
        d=json.loads(public.read_text());pr='\n'.join(f"{name.replace('_',' ')} & {z['accuracy']*100:.2f} & {2 if name=='self_refine' else 1} \\\\" for name,z in d['methods'].items())
        if (ROOT/'upgrade_v10/results/grasp_core_seed_42.json').exists():
            pr+=r'''
Author GRASP core + task adapter & 50.81 & 1\\
Scoped RxRSI skills & 47.27 & 1\\'''
        if (ROOT/'upgrade_v11/results/summary.json').exists():
            evidence=json.loads((ROOT/'upgrade_v11/results/summary.json').read_text())
            for key,label in [('balanced','Fixed balanced evidence'),('safety','Fixed safety evidence')]:
                pr+=f"\n{label} & {100*evidence['complete_test_methods'][key]['accuracy']:.2f} & 2 \\\\"
        if (ROOT/'upgrade_v12/results/summary.json').exists():
            gates=json.loads((ROOT/'upgrade_v12/results/summary.json').read_text())['gate_summaries']
            for key,label in [('independent_guard','Router: separate guard'),('joint_validation','Router: pooled validation')]:
                z=gates[key];pr+=f"\n{label} & {100*z['accuracy_mean']:.2f} $\\pm$ {100*z['accuracy_sample_sd']:.2f} & {z['mean_calls']:.2f} \\\\"
        public_section=r'''\begin{table}[t]\centering\small
\caption{Executed method comparison on the same 988 derived RxSafeBench questions with DeepSeek-V4.1-Flash. Router rows are three-order means $\pm$ SD; other evolving rows use seed 42. Calls are mean test-time model calls; development costs differ. This is a development comparison, not original benchmark score equivalence.}
\begin{tabular}{lrr}\toprule Method & Accuracy (\%) & Calls\\\midrule
PUBLICROWS
\bottomrule\end{tabular}\end{table}'''.replace('PUBLICROWS',pr)
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

\paragraph{Incomplete requests are unscored.}
Account-credit exhaustion interrupted 153/988 indication-review requests and all 380 Gemini development requests. A later language-evolution seed has 713 unfinished GRASP-adaptation test requests; another has an incomplete round-four selection, which is rolled back before resumption. These evaluations are marked incomplete, not zero accuracy. The client now stops on account errors, and the scorer rejects transport failures. The complete seed-42 and author-core results are unaffected. Received malformed outputs still count as errors.'''
    parameter_section=r'\paragraph{Execution status.} Local parameter-update experiments are in progress. No fine-tuning gain is claimed before generation-based evaluation is complete.'
    if parameter.exists():
        d=json.loads(parameter.read_text());rr=f"Frozen Qwen3-4B & {d['base']['drug_micro_f1']:.4f} & {d['base']['core_order_micro_f1']:.4f} \\\\\n"
        rr+='\n'.join(f"{name.replace('_',' ')} & {v['selected_test']['drug_micro_f1']:.4f} & {v['selected_test']['core_order_micro_f1']:.4f} \\\\" for name,v in d['arms'].items())
        parameter_section=r'''\begin{table}[t]\centering\small
\caption{Local parameter evolution on 500 new test admissions. Checkpoints are selected on the separate guard set.}
\begin{tabular}{lrr}\toprule Method & Drug F1 & Order F1\\\midrule
PARAMROWS
\bottomrule\end{tabular}\end{table}'''.replace('PARAMROWS',rr)
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
An improving prescription agent must demonstrate what changes between versions and whether those changes improve held-out decisions. We study RxRSIAgent as a system of separately versioned prescription policies, episodic memories, order-completion tools and language skills. Ground-truth training prescriptions provide error feedback, while disjoint proposal and regression-guard sets control updates. Our completed structured-order experiment uses 40,000 training admissions and 4,000 new test admissions from MIMIC-IV/ED, with three training seeds and five checkpoints. Accepted-state drug and joint-order scores increase with accumulated cases, but the final system does not outperform a strong same-data supervised control. Conditional order tools improve field matching, whereas episode-memory expansion is not consistently beneficial. We preserve these negative controls and continue with language-artifact and parameter-update experiments. Published results are cited under their original protocols. The work targets ACL 2027; external-benchmark superiority and a unique recursive-improvement advantage are research hypotheses, not established conclusions.
\end{abstract}

\section{Introduction}
Prescription generation combines medication selection with detailed order construction. A system that improves as cases accumulate could reduce repeated omissions and field errors, but a higher final score alone does not establish recursive self-improvement (RSI). More training data, a stronger backbone, a larger inference budget or a changed scorer can produce the same appearance.

We therefore separate three questions. H1 concerns performance against methods under a common task protocol. H2 concerns improvement across frozen checkpoints on a fixed test set. H3 concerns the causal contribution of updated artifacts relative to equal-data controls. H2 can hold even when H3 fails. Existing prescription ground truth supports automatic training and evaluation; clinician review is not a prerequisite for observed-label agreement.

Our current contributions are an executable structured-order task, a versioned update protocol, and an artifact-level evaluation that retains regressions and rejected versions. We do not present ordinary cumulative supervised fitting as proof of autonomous reasoning improvement. Two further experiments isolate LLM-authored language artifacts and actual LLM parameter updates.

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

\section{Study B: Language-Artifact RSI}
To test genuine changes to language-guided behavior, the next experiment freezes DeepSeek-V4.1-Flash and evolves reusable skills, episodic memory and the configuration of an evidence-focus tool. The tool returns exact current-dialogue excerpts selected by learned focus terms; its source code is fixed. An LLM proposes changes from its own training-error traces, and the runner saves the full before/after artifacts.

The public RxSafeBench data are verified against pinned source hashes and converted to a clearly labeled three-option task. Medication-scenario grouping yields 625 training, 190 proposal, 197 guard and 988 test cases with no cross-split scenario or exact-dialogue overlap. Four rounds expose additional training cases. Direct, CoT, Self-Refine, case RAG and explicit Reflexion/GRASP/EvoTool task adaptations form the comparison set. Evolving comparators receive four candidate-evaluation slots per round; all token costs are reported. The separate 300-question RxQA subset tests transfer without using its labels for evolution. These are public simulated/released questions; restricted patient inputs are never uploaded.

PUBLICSECTION

\section{Study C: Parameter Evolution}
A local Qwen3-4B QLoRA study compares uniform supervised updates with feedback-prioritized updates, holding the initial-8k candidate tools fixed. Three disjoint feedback blocks contain 600 new training admissions each. Both arms make pre-update predictions, train on 400 sampled examples for 100 optimizer steps per round, and use the same 200-case guard. Feedback weights target reachable candidate-selection errors rather than blaming the language model for drugs missing from its fixed catalogue. A separate 500-admission test excludes all patients in the earlier v0.6/v0.7 tests.

The Qwen chat template can emit an empty reasoning envelope before valid JSON. The parser removes only that empty envelope uniformly for all checkpoints, retains strict and normalized validity, and rebinds cached outputs to the current case. These repairs occurred on development data before test scoring; raw generations and learned weights are unchanged.

PARAMETERSECTION

\section{Limitations}
The completed structured-order experiment uses admission-proxy inputs. Triage has no verified entry timestamp and medication reconciliation lacks storetime; temporal availability is therefore not fully established. Candidate vocabularies and one-template-per-drug output limit recall. Recorded prescriptions may omit clinically acceptable alternatives, and agreement does not prove indication or safety. Current language-artifact baselines are task adaptations, not official reruns. Repeated development selection can overfit; independent tests, multiple evolution orders, transfer and matched optimization budgets are necessary before claiming general RSI benefits. External RxEval and SafeRx data access remains unresolved.

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
\end{thebibliography}
\end{document}
'''
    body=body.replace('METHODROWS',rows).replace('GROWTHROWS',growth).replace('PUBLICSECTION',public_section).replace('PARAMETERSECTION',parameter_section)
    sty=STYLE.read_text();prefix='% Official ACL style embedded for the standalone editor. See acl_template_provenance.json.\n'+r'\begin{filecontents*}[overwrite]{acl.sty}'+'\n'+sty+'\n'+r'\end{filecontents*}'+'\n% PRISMATIC MANUSCRIPT START\n'
    PAPER.write_text(prefix+body)
    provenance={'repository':'https://github.com/acl-org/acl-style-files','commit':'d5adc823ff0f80f98c80405ca0ab66c68e684409',
        'acl_sty_sha256':hashlib.sha256(STYLE.read_bytes()).hexdigest(),'target':'ACL 2027','mode':'review','path_preserved':str(PAPER.relative_to(ROOT)),
        'previous_template':'Original AAMAS template preserved in Git history through commit 9875d2fd.'}
    (PAPER.parent/'acl_template_provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')

if __name__=='__main__':run()
