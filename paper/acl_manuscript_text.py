"""Current English ACL narrative; results are inserted from frozen audited runs."""
MANUSCRIPT = r'''
\documentclass[11pt]{article}
\usepackage[review]{acl}
\usepackage{times,latexsym}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{microtype,booktabs,tabularx,amsmath,amssymb,graphicx,tikz}
\usetikzlibrary{arrows.meta,positioning}
\title{RxRSIAgent: Tracing Errors and Testing Scoped Updates\\for Prescription Assistance}
\author{Anonymous ACL submission}
\begin{document}
\maketitle
\begin{abstract}
Prescription agents need patient-applicable evidence and experience updates that transfer beyond the cases used to construct them. We introduce RxRSIAgent, a three-call workflow with product-aware label retrieval, source-bound checks, and a persistent trace--reflection--intervention loop. Its update state contains scoped procedures, retrieval settings and observable-condition vocabulary; no drug-frequency ranker overrides the answer. Training errors are traced through intermediate evidence and decisions, candidate changes are tested against successes as well as failures, and a development gate controls retention. We distinguish this process from ordinary supervised option calibration. @@ABSTRACT_RESULTS@@ We evaluate the frozen learning trajectory on467 independently sourced MedPIC-Bench questions and perform same-option patient-context and option-permutation diagnostics. Rejected proposals, unchanged states and remaining errors are reported rather than equated with successful self-improvement. These experiments measure reference-answer agreement and update reliability, not clinical prescribing effectiveness.
\end{abstract}

\section{Introduction}
Medication recommendation uses patient information to support drug selection and management. A systematic survey identifies temporal history, personalization and drug--drug interactions as recurring challenges \citep{mrsurvey}. Language-model approaches extend this task to clinical narratives, external evidence and verification \citep{lamrec,saferx}. Deployment is entering bounded prescribing workflows: Utah announced the Doctronic prescription-renewal pilot in January2026 \citep{utahrenewal}; its Nolla Health pilot covers initial prescriptions and refills for a restricted set of topical acne treatments for adults \citep{utahpilots}. These are scoped regulatory pilots with safeguards \citep{utahfaq}. They motivate careful evaluation of decisions and updates; authorization alone does not establish effectiveness.

Existing benchmarks cover different portions of prescribing. MIMIC-based medication-set studies use cohort-specific drug spaces \citep{gamenet,armr,mimiciv}. RxSafeBench uses three-option medication-safety questions derived from simulated consultations \citep{rxsafe}. RxQA tests medication reasoning grounded in formulary information \citep{rxqa}; RxEval evaluates medication--dose--route choices, while Rx-LLM separates management tasks including orders, interactions and renal dosing \citep{rxeval,rxllm}. RxBench studies prescription review, and MedAgentBench tests tool execution in an interactive EHR \citep{rxbench,medagentbench}. MedPIC-Bench changes patient information to probe medication-safety reasoning \citep{medpic}. These resources do not share a single endpoint or directly comparable published score.

Methods address complementary problems. GAMENet uses medication graphs and patient history; SafeDrug uses molecular representations and interaction objectives; ARMR models changing treatment needs \citep{gamenet,safedrug,armr}. Language-assisted recommendation addresses alignment and overprescription, while SafeRx-Agent combines retrieval and safety verification \citep{lamrec,saferx}. MedAgents and MDAgents use expert collaboration \citep{medagents,mdagents}. Self-Refine revises outputs, Reflexion stores linguistic feedback, and GRASP proposes persistent skills with regression-aware acceptance \citep{selfrefine,reflexion,grasp}. These mechanisms motivate experience-based prescription agents, but a stored reflection or a larger memory does not itself demonstrate transferable improvement.

Our error analysis identifies three obstacles. Retrieved text may describe the wrong product or a condition absent in the patient; broadly routed skills can break previously correct decisions; and numerical gains can arise from medication-identity statistics. \textbf{The central problem is to convert a traceable discrepancy from the reference prescription into a narrowly applicable process improvement that survives counterexamples and improves an independent patient-conditioned task.} A successful update must do more than restate the answer or match a medication prior. Medicines optimization requires patient-specific review \citep{nice,who}, and benchmark agreement cannot substitute for that assessment.

We propose \textbf{RxRSIAgent}. It records the observed discrepancy, the earliest suspected failure stage, source and patient evidence, the proposed repair, and the repair's actual corrections and regressions. Its tools distinguish provenance from applicability; its learner can modify procedural memory, bounded retrieval settings and a context detector's vocabulary. Backbone weights and executable tool code remain fixed within a trajectory. Our contributions are:
\begin{itemize}
\item \textbf{An inspectable prescribing-assistance workflow} connecting product variants, evidence spans and narrow executable checks to explicit unresolved conditions.
\item \textbf{A trace-based update mechanism} with observable routing, successful counterexamples, persistent rejected-intervention feedback, and separately measured state changes.
\item \textbf{A falsifiable evaluation} against executed medical-agent workflows, ordinary supervised calibration, and an independent patient-condition benchmark, with frozen trajectories and shortcut diagnostics.
\end{itemize}

\section{RxRSIAgent}
\subsection{Evidence and decision workflow}
Figure~\ref{fig:workflow} shows the complete process. The served backbone is \texttt{deepseek/deepseek-v4.1-flash}. Each case permits three calls, each with a1,536-token output cap. The evaluated outputs are benchmark option selections; the system does not submit a clinical order.

\paragraph{Extract observable context.}
Call1 identifies question intent, quoted patient facts and medication entities. Patient facts require exact input spans. Routes are retained only when the quoted span explicitly supports a recognized route. Missing information remains unknown. Medication mentions in both the question and options are considered, with current treatment distinguished from proposed alternatives.

\paragraph{Retrieve product-specific evidence.}
The tool resolves brands, ingredients and salt names against frozen labels and cached openFDA requests \citep{openfda}. A single ingredient cannot silently inherit an unrelated combination-product label. It exposes available routes and product metadata, rejecting excerpts with an explicit route conflict. Up to two distinct route/release-form signatures are retrieved by default. Form metadata may be missing and is not a complete strength/form compatibility verifier.

TF--IDF ranks source windows using the question and extracted focus. Indication, dose and safety slots are reserved per product. Round-robin allocation distributes an18,000-character default budget across products; each excerpt retains label ID, date, section, paragraph and offset. Default windows contain1,600 characters. Scoped updates can change bounded retrieval parameters. Requests are cached, including HTTP failures, and subject to a declared query cap. Missing evidence remains unknown; source coverage does not establish relevance or safety.

\paragraph{Assess applicability and execute narrow checks.}
Call2 evaluates every option, distinguishes contraindications from precautions, and proposes exact citations and supported arithmetic. The verifier checks source substrings and bounded numeric expressions. An added comparison tool binds an observed age, eGFR or creatinine-clearance value to an exact patient quote and an explicitly quoted source threshold. Unsupported parameters, operators or values remain unverified. Even a successful comparison does not verify units, all rule qualifiers or overall clinical appropriateness. Call3 uses the original input, assessment and check outcomes to produce the final answer and uncertainty. Multi-answer questions require the complete answer set; a pre-test task adapter removes inherited single-answer JSON examples. Two incomplete RxSafe cases later required a declared deterministic list-to-text focus repair. The other986 saved predictions were preserved byte-for-byte; this post-freeze engineering amendment is not an RSI gain.

\begin{figure*}[t]\centering
\begin{tikzpicture}[x=1cm,y=1cm,>=Stealth,
 b/.style={draw,rounded corners=2pt,align=center,text width=2.12cm,minimum height=1.05cm,font=\small},l/.style={->,semithick}]
\node[b] (q) at (0,0) {Question + options\\patient context};
\node[b] (p) at (2.6,0) {Call1\\facts + query intent};
\node[b] (e) at (5.2,0) {Label retrieval\\product / route / spans};
\node[b] (a) at (7.8,0) {Call2\\option assessments};
\node[b] (v) at (10.4,0) {Executable checks\\quotes / arithmetic\\explicit thresholds};
\node[b] (f) at (13,0) {Call3\\answer + uncertainty};
\draw[l](q)--(p);\draw[l](p)--(e);\draw[l](e)--(a);\draw[l](a)--(v);\draw[l](v)--(f);
\node[b] (gt) at (0,-2.2) {Training feedback\\GT versus prediction};
\node[b] (root) at (2.6,-2.2) {Trace reflection\\earliest mismatch\\root hypothesis};
\node[b] (edit) at (5.2,-2.2) {One scoped edit\\procedure / retrieval\\context vocabulary};
\node[b] (probe) at (7.8,-2.2) {Paired intervention\\failures + successes};
\node[b] (gate) at (10.4,-2.2) {Proposal + guard\\retain or reject};
\node[b] (state) at (13,-2.2) {Frozen state\\independent test};
\draw[l](gt)--(root);\draw[l](root)--(edit);\draw[l](edit)--(probe);\draw[l](probe)--(gate);\draw[l](gate)--(state);
\draw[l](gate.south)--++(0,-.65)-|(root.south);
\node[font=\scriptsize,fill=white] at (6.5,-2.85) {Rejected edits and observed regressions remain in the ledger};
\draw[l](state.north)--++(0,.55)-|(e.south);
\draw[l](state.north)--++(0,.55)-|(a.south);
\node[font=\scriptsize,fill=white] at (8.7,-1.12) {Retained state only};
\draw[l](state.north)--(f.south);
\node[align=center,font=\scriptsize,text width=13.7cm] at (6.5,-3.6) {Only training/development feedback enters updates. All retained round states freeze before independent evaluation.\\Human tool repairs, supervised calibration and accepted agent updates are accounted for separately.};
\end{tikzpicture}
\caption{RxRSIAgent's inference and update lifecycle. State changes route procedures and configure tools; backbone weights and executable code are fixed during each trajectory. A root hypothesis becomes supported intervention evidence only through measured outcomes.}
\label{fig:workflow}\end{figure*}

\subsection{Trace reflection and scoped updates}
Let $A_t=(\theta,T,P,K_t,R_t,V_t)$ contain fixed backbone weights, executable tools and prompts, together with procedural cards, retrieval settings and condition vocabulary. These three latter components are the only candidate learned state. No option-frequency model, raw case--answer retrieval or learned drug-name score is used in the actor.

\paragraph{Trace the gap before proposing a fix.}
Four rounds reveal100 training cases each. For every newly observed error, the reflector receives the full input, reference, prediction, retrieved excerpts, intermediate assessment and check results. It reports an observed discrepancy, earliest suspected stage, causal hypothesis, exact supporting quotes, a minimal process change and a counterexample requirement. References may be ambiguous; this is a model-generated diagnosis, not clinical adjudication. Only quote-valid roots marked supported can sponsor a procedural proposal. Detector gaps compare proposed context features with the actually detected features.

\paragraph{Change one scoped behavior.}
Each candidate has one narrow observable trigger, optional exclusions, a procedure, supporting failures and successful counterexamples. At most one retrieval parameter may change. New context terms must be general normalized phrases without drug names or numeric patient values. A patch must match at least one supporting failure and one successful counterexample; this does not validate every term independently. The fixed matcher applies these terms before routing. This makes vocabulary a measurable tool-configuration update, not newly generated executable code. Applicable cards enter calls2 and3; inactive cards do not modify the prompts. Exact role and scope validation precedes inference. Schema repairs receive invalid IDs and legal pools. The final updater uses compact root-feature clusters, stable short IDs and typed failure/success pools. An external proposer, \texttt{anthropic/claude-opus-4.8}, receives at most three full training traces per proposal; the actor and initial root reflector retain the fixed DeepSeek backbone. This is externally assisted agent-state learning with additional training compute, not same-model autonomous recursion. All past quote-validated roots remain eligible through the current round, with originating state hashes preserved. Recent rejected edits and the two highest positive-net failed probes are replayed to later proposals. The incumbent is re-evaluated before each new probe. An explicit no-edit response is retained with its reason and is never forced into an unsupported procedure.

\paragraph{Gate the intervention.}
At most four candidates are tested per round. Each first runs on up to32 accumulated training failures and successes, including its designated support and counterexamples. It must produce at least two net corrections with no extra invalid outputs. The proposal stage then requires no accuracy loss on either RxSafe190 or MedQA120 and a strictly positive pooled gain. The separate guard requires no loss on either RxSafe197 or MedQA120, with no increase in invalid answers. Rejection restores the incumbent. The final retained state is selected by this development rule, never by main-benchmark or independent-test scores. Earlier updater controls required a strictly positive pooled guard gain; the current non-regression guard was declared before independent evaluation and is disclosed as a protocol change.

\subsection{Why supervised calibration is a separate baseline}
The numerical comparator trains an ordinary logistic regression on625 labeled RxSafe cases. Each candidate option is represented by normalized drug identity, drug/UNII--focus-word interactions and an LLM draft indicator. Development selects regularization $C=10$ and a probability-gap threshold of0.2. The model may override the LLM only when all options are short, previously observed medication names. This learns statistical weights from GT; it does not trace a failure, invent a procedure or recursively improve a tool. Its previously recorded local result is retained as a \emph{supervised control}, not credited to RxRSIAgent's procedural evolution. A name-only diagnostic performs strongly, motivating independent patient-condition tests.

\section{Experimental Setup}
@@DATA_TABLE@@
RxSafeBench's2,443 released records produce2,000 local cases after task/dialogue/correct-drug deduplication. The original paper already specifies three-option multiple choice; an earlier local description as free generation was incorrect. Local deduplication, option ordering, grouping and split construction differ from the source protocol, so published paper scores are not copied into our comparison table. We use the existing190/197/988 proposal/guard/evaluation split and sample200 training cases from its625 training cases.

Another200 medication/treatment-related MedQA training questions exclude normalized exact overlap with previous local cohorts and the independent benchmark; image-dependent questions are removed from this new training subset. Each round mixes50 RxSafe and50 MedQA cases. Development reuses the separately designated120 proposal and120 guard MedQA cases. The training cohort was reused during updater debugging; this is a sequential development experiment, not a pristine prospective learning stream. Main RxSafe/RxQA questions also have historical research exposure. We make no stronger unseen-test claim for them.

\paragraph{Independent task and shortcut diagnostics.}
We pin the author-released MedPIC-Bench revision and evaluate all467 questions:284 guideline-following and183 counterfactual. There are108 multiple-answer items; exact-set agreement is required. One schema example was viewed before freezing, and remains in the predeclared full-set denominator. A strict ID/option rule identifies35 counterfactual pairs with identical option strings. Other counterfactual items still count in full accuracy, but not the strict pair metric. On all70 paired items, we also permute options with deterministic answer remapping and remove the patient vignette while retaining the question and options. These diagnose context and position sensitivity; they cannot exclude all drug priors in pretrained weights. All learning states freeze before inference; identical states share cached predictions and are not independent replications.

\paragraph{Methods, budgets and reporting.}
We execute pinned author-workflow adaptations of MedAgents and MDAgents, and a GRASP author-core adaptation. These are local same-question runs, not their published scores. The main table fixes the maximum generated output at4,608 tokens/case; actual calls, input tokens, costs and training supervision differ. Higher-allowance completed comparisons remain visible. Transport failures are retried and not scored as answers; received invalid answers and exhausted workflows count as wrong. SafeRx-Agent has no fabricated row because a compatible official task/split is unavailable. Medication-set methods cannot populate QA accuracy columns. Paired bootstrap intervals use4,000 draws, source-scenario clusters for RxSafe and items otherwise; they are exploratory and unadjusted for repeated development.

\section{Results}
\subsection{Named-agent comparison}
@@AGENT_TABLE@@
@@NATIVE_TABLE@@
@@MAIN_RESULTS@@
The supervised control remains556/988 on RxSafe and199/300 on RxQA. Its calibration is applied in527 RxSafe cases and no RxQA cases, fixing118 and regressing34 relative to its underlying source agent. A post hoc name-only diagnostic reaches564/988; this does not replace a preselected method and does not establish patient-specific reasoning. We therefore keep its gain separate from the procedural learner.

\subsection{Do more cases produce useful state changes?}
@@TRAJECTORY_TABLE@@
@@EVOLUTION_RESULTS@@
The earlier eight language-memory updates all failed the proposal stage; no guard rejection occurred. Two had no schema-valid cards. The remaining proposals produced more regressions than fixes. Code inspection found missing intermediate evidence in reflection, unconditional skill injection, similarity-selected rather than scope-checked counterexamples, and no persistent rejected-intervention ledger. The repaired control exposed a further failure: a pregnancy/age card activated on115/120 MedQA proposal cases, reducing103 correct to97 despite a positive training probe. Narrow routing and condition-vocabulary updates address these concrete implementation failures; their efficacy must still be measured.

@@UPDATER_TABLE@@
@@INDEPENDENT_RESULTS@@
@@SHORTCUT_TABLE@@

On the strict paired subset, removing the vignette leaves exact accuracy unchanged at24/70, although complete-pair correctness falls from3/35 to0/35. Option permutation changes22/70 mapped predictions. These diagnostics do not support shortcut robustness; they expose a remaining patient-condition and position-sensitivity problem.

\subsection{Case studies: failures as inspectable interventions}
@@FAILURE_CASES@@

@@MIMIC_STATUS@@

\section{Clinical Scope and Limitations}
QA agreement does not measure complete treatment coverage, omissions, unnecessary medication, dose/route/schedule correctness, full interactions, organ-function adjustment or monitoring. A separately specified clinician rubric follows medicines review and the Medication Appropriateness Index \citep{nice,mai}; two available reviewers have not returned blinded ratings. No clinical outcome is inferred from these QA results. Evaluation of the current LLM actor on complete decision-time prescriptions and real MedAgentBench tool/state execution remains unfinished; earlier local order experiments are reported separately.

Repeated main-benchmark exposure, reused development cohorts, a single served backbone and provider nondeterminism limit inference. A model's root explanation is a hypothesis, even when quotations are valid. Sparse or inconsistent benchmark feedback can yield unsupported procedures. Context terms may overgeneralize, and proposed exclusion conditions are not clinically certified. Label coverage, exact provenance and numeric comparisons do not establish complete applicability; missing formulations, strengths, units and temporal treatment context remain limitations. The query cap and source failures constrain retrieval. Equal output allowance does not equal compute or data. This work studies stateful, externally supervised agent updates; it does not establish autonomous recursive improvement of model weights or tool code.

\section{Conclusion}
RxRSIAgent connects accumulated errors to observable trace hypotheses, scoped interventions and explicit retention decisions. Ordinary supervised option calibration is kept separate. @@CONCLUSION_RESULTS@@ Independent patient-conditioned evaluation and transparent failure accounting are necessary before claiming progressively better prescribing.

\section*{Ethics and Reproducibility}
Only public benchmark material is sent to the external provider in these experiments. Restricted clinical records, credentials, raw responses and downloaded label bodies remain local. Public artifacts include source pins, code, aggregate results, state hashes and rejected gates. Source and response receipts support independent recounts. These research outputs are not autonomous clinical prescriptions.

@@REFERENCES@@
\appendix
\section{Compute and Audit Details}
@@COMPUTE_TABLE@@
@@AUDIT_DETAILS@@
\section{Clinical Endpoints Awaiting Annotation}
@@CLINICAL_METRICS_TABLE@@
\end{document}
'''
