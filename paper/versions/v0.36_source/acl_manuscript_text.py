"""Current English ACL narrative; numbers and tables come from audited artifacts."""
MANUSCRIPT = r'''
\documentclass[11pt]{article}
\usepackage[review]{acl}
\usepackage{times,latexsym}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{microtype,booktabs,tabularx,amsmath,amssymb,graphicx,tikz}
\usetikzlibrary{arrows.meta,positioning}
\title{RxRSIAgent: Auditing Evidence and Experience Updates\\for Prescription Assistance}
\author{Anonymous ACL submission}
\begin{document}
\maketitle
\begin{abstract}
Prescription agents must find applicable evidence and improve from experience without converting unsupported assumptions into confident decisions. We present RxRSIAgent, a three-call agent combining observable-fact extraction, product-aware drug-label retrieval, executable source and arithmetic checks, and a development-gated experience calibrator. On a derived 988-question RxSafeBench task, the frozen selected agent answers 556 correctly (56.28\%), compared with 495 for a GRASP adaptation under the same 4,608-token generated-output allowance. On all 300 public OpenFDA RxQA questions, it answers @@RXQA_CORRECT@@ correctly (@@RXQA_ACC@@\%). @@ABSTRACT_TRANSFER@@ Component analysis limits the interpretation: verified retrieval alone answers 472 RxSafeBench questions, and ordinary supervised calibration supplies the improvement. A drug-name-only diagnostic also performs strongly, indicating possible benchmark shortcuts. Two four-round language-memory experiments reject every proposed update. We report actual module changes, unsuccessful interventions, source audits, compute accounting, and positive and negative case studies. Our findings support auditable adaptation, while leaving clinical prescription quality and general autonomous self-improvement unestablished.
\end{abstract}

\section{Introduction}
Medication recommendation uses patient information to support drug selection and management. A systematic survey identifies temporal history, personalization and drug--drug interactions as recurring challenges \citep{mrsurvey}. Language-model approaches extend this task to clinical narratives, external evidence and verification \citep{lamrec,saferx}. Deployment is moving into bounded prescribing workflows: Utah announced the Doctronic prescription-renewal pilot in January 2026 \citep{utahrenewal}; its Nolla Health pilot permits initial prescriptions and refills for a restricted set of topical acne treatments for adults \citep{utahpilots}. These are scoped regulatory pilots with safeguards \citep{utahfaq}. They motivate checking prescription decisions and update reliability; authorization itself does not establish clinical effectiveness.

Benchmarks cover different portions of the workflow. EHR studies construct medication-set tasks using MIMIC cohorts and their own drug spaces \citep{gamenet,armr,mimiciv}. RxSafeBench examines medication risks in simulated consultations \citep{rxsafe}; RxQA tests medication reasoning grounded in formulary information \citep{rxqa}. RxEval evaluates medication--dose--route choices, while Rx-LLM separates medication-management tasks including orders, interactions and renal dosing \citep{rxeval,rxllm}. RxBench evaluates prescription review \citep{rxbench}; MedAgentBench tests execution in an interactive EHR environment \citep{medagentbench}. These resources do not share a single outcome or directly comparable published score.

Methods address complementary problems. GAMENet combines historical information with medication graphs, SafeDrug uses molecular representations and interaction objectives, and ARMR models changing treatment needs \citep{gamenet,safedrug,armr}. Language-assisted recommendation addresses alignment and overprescription \citep{lamrec}; SafeRx-Agent combines knowledge retrieval and safety verification \citep{saferx}. MedAgents and MDAgents use expert collaboration \citep{medagents,mdagents}. Self-Refine revises responses, Reflexion stores linguistic feedback, and GRASP proposes persistent skills with regression-aware acceptance \citep{selfrefine,reflexion,grasp}. They offer useful mechanisms, but do not establish which experience update improves a prescription workflow on a subsequent task.

Our investigation exposes three connected failures: a drug-name lookup can miss treatment-statement questions; a correct source quotation can describe the wrong product or patient condition; and a memory update can improve development performance without transferring. \textbf{The central problem is to turn accumulated prescribing feedback into reusable, patient-applicable improvements, while distinguishing genuine transfer from extra inference, medication-frequency shortcuts, and test-specific adaptation.} Medicines optimization requires reconciliation and patient-specific review \citep{nice,who}; a benchmark reference answer cannot replace these requirements.

We introduce \textbf{RxRSIAgent}, which separates evidence acquisition, decision assessment and executable checks, then applies a frozen experience calibrator only within its declared eligibility conditions. An update must improve a proposal set and a separate guard set before test inference. We examine language-memory proposals and an ordinary supervised numeric module separately. The latter is not a new learning optimizer, and the former provides no positive update in the current experiment. Our contributions are:
\begin{itemize}
\item \textbf{An auditable prescription-agent workflow.} Product identity, route, source offsets and arithmetic checks are connected to explicit uncertainty, with measured implementation boundaries.
\item \textbf{Named-agent comparisons with budget accounting.} We execute GRASP, MedAgents and MDAgents task adaptations under a shared output allowance, retain higher-budget comparisons, and disclose invalid outputs, input cost and repeated benchmark use.
\item \textbf{Module-level adaptation evidence.} We measure experience-size curves, accepted and rejected updates, component ablations and independent development. Strong simple calibration controls and failed memory proposals constrain claims of self-improvement.
\end{itemize}

\section{RxRSIAgent}
\subsection{Decision workflow}
Figure~\ref{fig:workflow} depicts the measured agent. The served backbone identifier is \texttt{deepseek/deepseek-v4.1-flash}; weights are not updated. Each case has three calls, each capped at 1,536 output tokens. A forced-choice question is the evaluated task; the workflow does not write an actual clinical order.

\paragraph{Extract observable context.}
The first call identifies the requested decision, patient facts and medication entities. Facts require exact input quotations. A proposed route is retained only when its supporting input span contains a recognized route expression. Missing facts remain unknown. Both the question and options can supply medication names.

\paragraph{Retrieve applicable source candidates.}
The tool combines a previous frozen label snapshot with cached name/route lookups from openFDA \citep{openfda}. A single ingredient cannot silently inherit an unrelated combination-product label. Exact brands and ingredient/salt names are resolved; available routes and UNII identifiers are exposed. An explicit route conflict excludes that product's excerpts. If route is unspecified, it remains unknown rather than becoming a negative clinical judgment. Products are ranked by overlap between the extracted focus and indication text. Within a selected product, TF--IDF ranks 1,000-character windows with a 750-character step; reserved indication, dose and safety slots prevent one section from occupying every slot. At most 24 excerpts enter the static workflow. Each retains label ID, date, section, paragraph and offset. Strength and release-form compatibility are not fully verified.

\paragraph{Assess and execute narrow checks.}
The second call compares all options, cites exact supplied spans and proposes arithmetic expressions with source-bound inputs. A deterministic verifier checks quotations and evaluates only bounded arithmetic syntax. Numeric inputs must occur in their cited source. These checks establish provenance and arithmetic, not clinical dose appropriateness or dimensional consistency. The third call resolves the original question using the assessment and check results. Missing evidence is explicitly unknown. A valid quote cannot establish that a warning applies to this patient. @@CONTRAST_METHOD@@

\begin{figure*}[t]\centering
\begin{tikzpicture}[x=1cm,y=1cm,>=Stealth,
 b/.style={draw,rounded corners=2pt,align=center,text width=2.5cm,minimum height=1.05cm,font=\small},
 l/.style={->,semithick}]
\node[b] (x) at (0,0) {Question + options\\observable context};
\node[b] (p) at (3.2,0) {Call 1: facts\\entities + query intent};
\node[b] (e) at (6.4,0) {Label resolver\\identity / route / spans};
\node[b] (a) at (9.6,0) {Call 2: option review\\citations + calculations};
\node[b] (v) at (12.8,0) {Executable checks\\quotation + arithmetic};
\draw[l] (x)--(p);\draw[l] (p)--(e);\draw[l] (e)--(a);\draw[l] (a)--(v);
\node[b] (f) at (12.8,-2) {Call 3: final decision\\with unresolved issues};
\node[b] (c) at (9.6,-2) {Eligible calibration\\else keep LLM choice};
\node[b] (o) at (6.4,-2) {Answer + provenance\\draft kept separately};
\draw[l] (v)--(f);\draw[l] (f)--(c);\draw[l] (c)--(o);
\node[b] (tr) at (0,-4) {Training feedback\\625 labeled cases};
\node[b] (up) at (3.2,-4) {Scoped text proposals\\or supervised weights};
\node[b] (gate) at (6.4,-4) {Proposal then guard\\reject regressions};
\node[b] (state) at (9.6,-4) {Freeze selected state\\before evaluation};
\node[b] (te) at (12.8,-4) {Held-out evaluation\\no update feedback};
\draw[l] (tr)--(up);\draw[l] (up)--(gate);\draw[l] (gate)--(state);\draw[l] (state)--(te);\draw[l] (state)--(c);
\node[align=center,font=\scriptsize,text width=5.4cm] at (1.6,-2) {Current text-memory proposals: all rejected.\\Numeric calibration: ordinary supervised learning.\\Backbone and tool code: fixed during learning.};
\end{tikzpicture}
\caption{The measured RxRSIAgent workflow and its update lifecycle. Product/source checks have narrower scope than clinical verification. A calibrated choice does not inherit the superseded draft's explanation. Tool and prompt repairs are researcher interventions, distinct from learned state updates.}
\label{fig:workflow}\end{figure*}

\subsection{Experience state and update gates}
Let $A_t=(\theta,T,P,K_t,w_t)$ denote backbone weights, tools, prompts, text memory and numeric calibration. Within a learning trajectory, $\theta,T,P$ are fixed. We disclose which of $K_t$ and $w_t$ changes, rather than equating more stored words with greater clinical ability.

\paragraph{Scoped language memory.}
Training cases are encountered in four cumulative batches of 156, 312, 468 and 625. Proposed cards contain an applicability condition, exclusion condition, procedure, supporting failures and counterexamples drawn from earlier successes. One implementation validates these roles after proposal; a second constrains IDs to explicit allowed pools and permits one schema repair. Each candidate must strictly improve the 190-case proposal set and then the 197-case guard set without increasing invalid answers. Rejected states roll back. Both runs retain empty memory at every round. These are regression-aware experiments inspired by prior skill-learning work \citep{grasp}, not a reproduction of its optimizer or evidence that the agent invented new tools.

\paragraph{Supervised numeric calibration.}
A binary logistic model scores each option using its normalized medication identity, medication/UNII--focus-word interactions and a second-call draft indicator. There are no case-ID or answer-position features. It is trained on 625 labeled cases with standard library optimization. Development selects $C=10$ from $\{0.1,1,10\}$ and a probability-gap threshold $\tau=0.2$ from $\{0,.05,.1,.2,.3\}$; ties favor fewer overrides and stronger regularization. All option strings must have at most six words and have appeared in training. Otherwise the LLM decision is retained:
\begin{equation}
\widehat y=\begin{cases}
\arg\max_j p_{w}(j\mid x),&\text{eligible and gap}\geq\tau,\\
\widehat y_{\mathrm{LLM}},&\text{otherwise}.
\end{cases}
\end{equation}
Selection gives 110/190 on proposal and 116/197 on guard, exceeding the source agent's 103 and 102. The model hash is frozen before test inference. This is ordinary supervised calibration with a persistent state, not autonomous recursive algorithm invention. After an override, the original explanation is retained only as the original draft's explanation; the calibrated answer reports its separate provenance.

\section{Experimental Setup}
\subsection{Data and comparison scope}
@@DATA_TABLE@@
RxSafeBench's 2,443 source records yield 2,000 local cases after exact task/dialogue/correct-drug deduplication. The derived task uses three answer options and 625 training, 190 proposal, 197 guard and 988 evaluation cases. It differs from the source free-generation task. RxQA uses every released OpenFDA question (300); the licensed BNF part is unavailable. The main benchmarks have been observed in earlier research: new changes freeze before their new evaluation, but results remain exploratory rather than a pristine final test.

For a subsequent retrieval experiment, we obtain MedQA's public training split through a version-pinned mirror \citep{medqa}. An input-only medication/treatment keyword rule and an option longer than six words identify 784 eligible questions; hash order selects 120 proposal and 120 guard questions. Exact normalized overlap with all prior local public cases is excluded. The mirror revision and downloaded file hash are recorded. These are general medical exam questions, sometimes referencing unavailable images; they are an independent development source, not a dedicated prescription-dose benchmark.

\subsection{Named methods and budgets}
We execute pinned author-workflow task adaptations of MedAgents and MDAgents, and a GRASP author-core adaptation with its previously selected skill. These are local same-question comparisons, not the papers' published scores. SafeRx-Agent remains unexecuted because a compatible official task/split is unavailable; it receives no invented row. GAMENet and SafeDrug predict medication sets and cannot populate these QA accuracy columns.

All methods in Table~\ref{tab:main} receive the same maximum of 4,608 generated output tokens per case. RxRSIAgent uses three calls; author workflows may use up to 80 calls with their stage constraints. GRASP receives one call. Equal output allowance does not equal input tokens, actual cost or model calls. Training supervision also differs: MedAgents and MDAgents use no newly fitted task-specific parameters, GRASP reuses its previously learned skill, and RxRSIAgent fits a calibrator on625 labeled cases. Table~\ref{tab:native} also retains completed higher-allowance medical-agent runs, avoiding a comparison based solely on budget exhaustion. Invalid received answers and exhausted workflows count as wrong; unsuccessful transport requests are retried and are not scored as model errors. All runs use the same served model identifier; provider nondeterminism remains possible even at temperature zero.

We report 4,000-resample paired intervals, clustered by source scenario for RxSafeBench and by item for RxQA. These exploratory intervals are not adjusted for repeated research or multiple comparisons. Text memory, source-only, no-evidence and ordinary supervised controls separate components. Experience-size curves fix hyperparameters selected with the full training/development data and therefore are post hoc prefix analyses, not prospective online learning curves.

\section{Results}
\subsection{Main comparison and budget sensitivity}
@@AGENT_TABLE@@
@@NATIVE_TABLE@@
The frozen selected RxRSIAgent answers 556/988 on RxSafeBench, versus 495 for matched-output GRASP: a difference of 6.17 percentage points with paired 95\% interval $[2.84,9.63]$. Against the earlier lower-cap GRASP result of 502, the descriptive difference is 5.47 points. This exceeds the earlier small numerical gain but does not establish universal superiority. @@MAIN_TRANSFER@@

Under the shared output allowance, MedAgents has 81 invalid/exhausted RxSafe outputs and 16 RxQA outputs; MDAgents has 18 and 9. Of these, budget exhaustion accounts for 78/14 and 8/7, respectively. These failures are visible rather than excluded. MedAgents' higher-allowance RxQA score remains an essential comparator. The main agent has zero invalid final outputs. Input tokens and costs differ substantially (Appendix~\ref{app:compute}).

\subsection{What produces the gain?}
@@ABLATION_TABLE@@
Static verified retrieval alone falls to 472/988, below both no evidence (487) and original name lookup (488), despite passing development gates. Calibration fixes 118 source-agent errors and regresses 34, producing 556 correct; its 8.50-point increment has paired interval $[6.08,10.93]$. It applies on 527 RxSafe questions and no RxQA questions. Thus the RxSafe gain cannot be credited to retrieval repair alone, and the numeric module has no demonstrated cross-task benefit on RxQA.

@@CALIBRATION_DIAGNOSTICS@@
Post-selection diagnostic ablations reveal a strong shortcut concern: a name-only calibrator reaches 564/988 and a medication--context interaction calibrator without the draft reaches 574/988. Neither replaces the pre-test selected main model based on these test results. The full agent's 556 is lower than these simple diagnostics; the claim that all modules are necessary is unsupported. Future confirmatory evaluation requires unseen medication combinations or independently constructed clinical cases, not repeated optimization on this split.

\subsection{Experience and rejected changes}
@@TRAJECTORY_TABLE@@
The numeric feature count grows from 4,848 at 156 cases to 17,672 at 625. Guard accuracy rises from 101/197 to 116/197; proposal counts are 102, 108, 113 and 110, so performance is not uniformly monotonic. The selection procedure has seen all 625 training cases and proposal feedback before these curves are computed. Both four-round language-memory attempts retain zero cards; their proposed card counts do not establish acquired skills. No backbone or tool-code learning occurs.

The active second-retrieval candidate scores 100/190 versus 103 for static retrieval and is rejected before guard/test. Full-section context on independent MedQA development scores 99/120, tying static retrieval with higher input cost, and is also rejected. @@INDEPENDENT_RESULTS@@ We preserve every failed candidate and gate; an unsuccessful update is not silently merged into the selected method.

\subsection{Case studies and explanation boundaries}
We choose the first lexicographically ordered correction and regression among calibration overrides, using public case IDs; this is post hoc illustration, not an error prevalence estimate.
\paragraph{Reference correction without established clinical improvement.}
Case \texttt{0445a1cf61c5e4ac} describes mood symptoms with bupropion in the history. The source agent selects risperidone; calibration changes it to sertraline, matching the benchmark reference. The saved draft explanation argues for the original choice. It cannot justify the new output, and reference agreement alone does not validate patient-specific appropriateness.
\paragraph{Regression and product overinterpretation.}
Case \texttt{0d0cc811ec14bfd3} concerns a suspected skin fungal infection. Calibration changes griseofulvin (the reference) to ketoconazole, creating an error. The source agent's original rationale also overinterprets a retrieved shampoo label as limiting the ingredient's broader applicability. The two failures coexist: a prior can override a correct reference choice, and a traceable quote can be applied too broadly. These cases motivate applicability checks and independent clinical review, rather than a blanket safety claim.

\section{Clinical Evaluation Beyond Accuracy}
Question accuracy measures agreement with benchmark answers. A full prescription requires indicated treatment coverage, omission and overprescribing assessment, correct dose/route/schedule, interactions, organ-function adjustment and monitoring. We specify a clinician-oriented rubric informed by medicines review and the Medication Appropriateness Index \citep{nice,mai}. Table~\ref{tab:clinicalmetrics} defines the endpoints; two available reviewers have not yet supplied blinded ratings. No clinical outcome is imputed from QA accuracy, source checks or field completeness.

A separate previously completed eICU order-tool experiment holds medication predictions fixed and improves joint-order F1 from 0.02334 to 0.02838 across three seeds on 8,005 stays. This is supervised component evidence, not a new full-agent comparison or clinical outcome. Decision-time MIMIC prescription evaluation and real MedAgentBench state/tool execution remain distinct unfinished evaluations.

\section{Limitations}
The strongest evidence concerns exploratory reference-answer accuracy, not deployable prescribing. RxSafeBench is adapted and may permit drug-frequency shortcuts. The numeric calibrator is ordinary supervised learning; text memory has no accepted gain. Independent development differs from RxQA and is not a prospective clinical validation. Repeated benchmark exposure and single served-model runs limit significance. Source coverage is not evidence relevance; identity/route logic omits many formulation and strength constraints. Source and arithmetic validation do not verify renal/hepatic dosing, complete interactions, units or clinical necessity. Training feedback can reflect imperfect reference labels. Calibration can separate the final choice from its original explanation. Equal output allowance leaves unequal input cost and workflow failure rates. Higher-budget baselines and simple post hoc diagnostics prevent an unqualified best-method claim.

\section{Conclusion}
RxRSIAgent makes evidence handling and persistent updates inspectable. A development-selected supervised calibration module materially improves the derived RxSafeBench result, while strong simple controls and rejected text-memory updates constrain its interpretation. @@CONCLUSION_TRANSFER@@ The next evidentiary requirement is robust transfer of patient-applicable updates to new prescription tasks with independently verified clinical endpoints.

\section*{Ethics and Reproducibility}
Only public benchmark material is sent to the external model provider in these experiments. Restricted clinical records, credentials, raw API responses and model binaries are excluded from the public repository. Code, source pins, aggregate results, state hashes, rejected gates and audit summaries are released. Raw local receipts are retained for audit. Product labels are time-varying; saved request manifests bind the source snapshots. Research outputs must not be interpreted as autonomous clinical prescriptions.

@@REFERENCES@@
\appendix
\section{Compute and Audit Details}\label{app:compute}
@@COMPUTE_TABLE@@
The initial evidence experiment records 24,735 independently checked source spans. Some concurrent identical requests received distinct service responses: 1,655 receipt references differ from the most recent request cache, including repeated references. Per-case raw receipts are authoritative; we do not claim paired runs share identical sampled planning outputs. The later independent-development experiment adds cross-process request locks for identical requests. Eight synthetic software tests cover identity, route, quotation and arithmetic failure paths; these are not clinical validation. @@AUDIT_DETAILS@@
\section{Proposed Clinical Endpoints}
@@CLINICAL_METRICS_TABLE@@
\end{document}
'''
