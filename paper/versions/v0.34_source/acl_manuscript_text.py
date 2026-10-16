"""Editorial narrative for the existing standalone English ACL manuscript.

Tables are populated by render_acl.py from saved, audited experiment artifacts.
This module does not train models, call providers, or resume paused experiments.
"""

MANUSCRIPT = r'''
\documentclass[11pt]{article}
\usepackage[review]{acl}
\usepackage{times,latexsym}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{microtype,booktabs,tabularx,amsmath,amssymb,graphicx,tikz}
\usetikzlibrary{arrows.meta,positioning}
\title{RxRSIAgent: Evidence-Grounded Prescription Assistance\\with Persistent Skill Memory}
\author{Anonymous ACL submission}
\begin{document}
\maketitle
\begin{abstract}
Prescription assistance requires medication decisions, applicable evidence, complete orders, and reliable execution. We present RxRSIAgent, a prescription-agent architecture with explicit evidence tools, persistent skill memory, and structured review contracts. Its evaluated configuration uses a fixed language-model backbone and a skill state selected on 387 development questions. On 988 derived RxSafeBench questions it answers 501 correctly, compared with 499 for the same evidence tool without learned skills and 502 for an adapted GRASP author-core baseline. On 300 public RxQA questions it answers 183 correctly, showing that development improvement does not ensure transfer. Public case studies reveal both a corrected option choice and a frequency error. An audit identifies a concrete tool failure: exact option-name lookup returns evidence for only one RxQA question. A mention-aware, dosage-inclusive retriever raises coverage to 214 questions, but a subsequent 190-question development intervention scores 98 with the frozen skill versus 99 with original retrieval and is rejected before test evaluation. We organize eighteen prescribing concerns into scoped review interfaces and report their implementation boundaries. Executed MedAgents and MDAgents author-workflow adapters supply further same-question comparisons with disclosed multi-call budgets. A separate counterexample-scoped memory intervention uses three training orders, four rounds and an independently frozen 200-question MedQA task. Its gains are 0.5, 0 and 2.0 percentage points over empty memory, below both medical-agent adapters. These results expose a gap between traceable adaptation and reliable transfer; broad method superiority remains unsupported.
\end{abstract}

\section{Introduction}
Medication recommendation uses patient information to support the selection of drug regimens. A systematic survey identifies personalization, temporal patient history, and drug--drug interactions as recurring challenges in learning from electronic health records (EHRs) \citep{mrsurvey}. Recent language-model approaches extend this setting to clinical narratives, external evidence, and explicit verification \citep{lamrec,saferx}. These systems are entering bounded prescribing workflows: Utah announced the Doctronic prescription-renewal pilot in January 2026 \citep{utahrenewal}, and its Nolla Health pilot, whose term began on October 5, 2026, permits initial prescriptions and refills for a restricted set of topical acne treatments for adults \citep{utahpilots}. These are scoped regulatory pilots with clinical safeguards, not general medical licensure for AI \citep{utahfaq}. Their emergence motivates evaluating prescription quality, appropriate escalation, and the reliability of updates as experience accumulates; authorization alone does not establish clinical effectiveness or justify uncontrolled self-modification.

Existing evaluation resources cover different parts of this process. MIMIC-III and MIMIC-IV supply EHR data for medication-set recommendation, but papers construct their own cohorts, medication spaces, and prediction protocols \citep{gamenet,armr,mimiciv}. RxSafeBench evaluates medication risks in simulated consultations \citep{rxsafe}; RxQA tests formulary-grounded medication reasoning \citep{rxqa}. RxEval moves to time-specific choices among medication--dose--route triples \citep{rxeval}, while Rx-LLM separates six medication-management tasks, including order generation, interactions, and renal-dose identification \citep{rxllm}. MedAgentBench adds interactive FHIR tasks and measures successful execution \citep{medagentbench}. Together, these resources motivate evaluating knowledge, prescription decisions, and execution separately. A score on one does not establish competence on the others, and none of these endpoints alone identifies what an agent learns as cases accumulate.

Methods address complementary obstacles. GAMENet uses graph-augmented memory to combine patient history and medication relations \citep{gamenet}. SafeDrug incorporates molecular representations and an interaction objective \citep{safedrug}, while ARMR models historical reuse and changing medication needs \citep{armr}. Language-Assisted Medication Recommendation aligns language models with medication decisions to address overprescription \citep{lamrec}; SafeRx-Agent combines clinical context, knowledge retrieval, and safety verification \citep{saferx}. In the broader agent literature, Self-Refine revises individual responses, Reflexion retains linguistic feedback, and GRASP maintains skills with regression-aware acceptance \citep{selfrefine,reflexion,grasp}. These approaches provide mechanisms for prediction and adaptation, but their results do not by themselves answer which persistent update improves a prescription agent under matched experience and evaluation conditions.

Prescription errors also arise from missing patient constraints, unsupported doses, incomplete evidence, and failures to execute an intended order. Medicines reconciliation and review require an accurate medication history and patient-specific goals \citep{nice,who}; RxBench distinguishes fourteen prescription-review error categories \citep{rxbench}. Our experiments reveal that an improved development score can coexist with negative transfer, and that a retrieval tool can return almost no evidence on a differently phrased task. This motivates our central question: \textbf{How can a prescription agent convert accumulated case-level feedback into reusable improvements in medication selection and order completion, and how can we attribute those improvements to specific updates and verify their transfer beyond the cases used to select them?} We operationalize this question through three requirements: identify the updated object, compare feedback-driven learning with equal-data and matched-budget controls, and evaluate frozen versions on subsequent or held-out cases. Artifact changes and rising learning curves are insufficient evidence on their own.

We introduce \textbf{RxRSIAgent}, an evidence-grounded prescription agent with a persistent skill memory and explicit tool and output contracts. Its evaluated configuration combines a fixed language-model backbone, frozen drug-label retrieval, and the skill checkpoint selected on development cases. We retain one selected configuration in the method comparison. A scoped clinical-review layer maps prescribing concerns to required facts, tools, and unresolved checks. We distinguish its implemented structural checks from clinical rules that still require authoritative resources and outcome validation. The skill updater uses the credited GRASP author core; we do not claim a new optimizer or recursive redesign of the learning algorithm.

Our contributions are:
\begin{itemize}
\item \textbf{A prescription-specific agent architecture.} We connect evidence retrieval, decision making, persistent skills, structured review, and output verification, with explicit boundaries between measured capabilities and newly implemented interfaces.
\item \textbf{A traceable evaluation of the selected agent.} We report named method comparisons, matched component ablations, experience trajectories, and public case studies. MedAgents and MDAgents author-workflow adaptations are measured, and recorded answers are distinguished from clinical correctness. Three independently frozen learning trajectories test scoped memory on a new task.
\item \textbf{An actionable evidence-retrieval diagnosis.} On all 300 public RxQA questions, a revised mention-aware retriever increases the number receiving label excerpts from 1 to 214; 193 receive dosage-section excerpts. This is a retrieval-coverage result, not a claim of improved answer accuracy. A separate fixed-policy intervention also establishes useful order-tool learning.
\end{itemize}

\section{Related Work}
\paragraph{Medical agents.}
MedAgents assembles domain experts and uses iterative discussion for medical reasoning \citep{medagents}; MDAgents selects a collaboration structure according to task complexity \citep{mdagents}. SafeRx-Agent focuses on medication recommendation with clinical knowledge and safety verification \citep{saferx}. These are distinct methods. MedAgentBench is an interactive evaluation environment, not a competing agent \citep{medagentbench}. GRASP provides the skill-learning optimizer reused by our implemented agent \citep{grasp}; its contribution is credited explicitly.

\paragraph{Prescription tasks.}
GAMENet, SafeDrug, and ARMR address structured medication-set prediction \citep{gamenet,safedrug,armr}. Their medication-code results cannot be placed in a question-answering accuracy column. RxSafeBench, RxQA, RxEval, Rx-LLM, and RxBench expose different prescription-related decisions and risks \citep{rxsafe,rxqa,rxeval,rxllm,rxbench}. Our public experiments use their declared local task adaptations. We do not equate a benchmark answer with an independently verified treatment recommendation.

\section{RxRSIAgent}
\subsection{One selected configuration}
The measured agent consists of a fixed backbone, a frozen label corpus and retrieval profile, the selected persistent skill file, and a JSON answer contract. The backbone is DeepSeek-V4.1-Flash; each evaluation case receives one actor call with a 512-token output cap. The selected skill state is the best checkpoint in the saved validation record: 206/387 correct, compared with 190/387 before skill learning. Selection precedes this checkpoint's test evaluation. The benchmark itself had been inspected in earlier research, so the comparison remains exploratory.

We call this configuration \textbf{RxRSIAgent} throughout the main table. The new clinical-review interfaces and revised retriever are implemented additions whose end-to-end accuracy has not yet been measured. They receive no retroactive credit for the selected agent's saved scores. Model weights remain frozen in the retained configuration; unsuccessful parameter-update prototypes are excluded from the method definition.

\subsection{Architecture and decision flow}
Figure~\ref{fig:workflow} shows the complete architecture and its evidence boundaries. Given a task context $x$, an evidence tool obtains $E(x)$ and the actor uses the persistent skill state $K$:
\begin{equation}
 \widehat y = C\bigl(\pi_{\theta}(x,E(x),K)\bigr),
\end{equation}
where $C$ checks the task's output representation. In the measured question task, $C$ validates a choice letter and JSON fields. For order drafts, the review layer tracks required fields and unresolved clinical domains. It does not convert structural completeness into a safety clearance.

\begin{figure*}[t]
\centering
\begin{tikzpicture}[x=1cm,y=1cm,>=Stealth,
 box/.style={draw,rounded corners=2pt,align=center,text width=2.55cm,minimum height=1.05cm,font=\small},
 newbox/.style={box,dashed},line/.style={->,semithick}]
\node[box] (patient) at (0,0) {Patient context\\and task contract};
\node[box] (evidence) at (3.2,0) {Label evidence\\source and section};
\node[box] (actor) at (6.4,0) {RxRSIAgent\\fixed LLM + skills};
\node[box] (format) at (9.6,0) {Output compiler\\and validation};
\node[box] (answer) at (12.8,0) {Answer / draft\\with explicit scope};
\draw[line] (patient)--(evidence);\draw[line] (evidence)--(actor);
\draw[line] (actor)--(format);\draw[line] (format)--(answer);
\node[newbox] (registry) at (3.2,-2) {18 review domains\\facts + required tools};
\node[newbox] (review) at (9.6,-2) {Structured review\\unresolved checks};
\draw[line,dashed] (registry)--node[above,font=\scriptsize]{source-bound requirements}(review);
\draw[line,dashed] (actor.south)--(review.north west);
\draw[line,dashed] (review.north)--(format.south);
\node[box] (feedback) at (0,-4) {Training cases\\prediction vs. labels};
\node[box] (proposal) at (3.2,-4) {Skill proposal\\credited GRASP core};
\node[box] (gate) at (6.4,-4) {Development checks\\select checkpoint};
\node[box] (memory) at (9.6,-4) {Frozen skill memory\\scope and provenance};
\node[box] (evaluation) at (12.8,-4) {Held-out evaluation\\never update feedback};
\draw[line] (feedback)--(proposal);\draw[line] (proposal)--(gate);
\draw[line] (gate)--(memory);\draw[line] (memory)--(evaluation);
\draw[line] (memory.north)--(9.6,-2.95)--(6.4,-2.95)--(actor.south);
\node[font=\scriptsize,fill=white] at (7.9,-2.95) {reuse selected experience};
\end{tikzpicture}
\caption{RxRSIAgent architecture. Solid boxes describe the evaluated option-selection core and its learning/evaluation lifecycle. Dashed boxes are the newly implemented clinical-review interfaces; the main-table scores do not include them. Revised mention-aware retrieval is audited separately. The order-draft interface does not execute real clinical writes.}
\label{fig:workflow}
\end{figure*}

\subsection{Evidence tools and clinical review}
The evaluated retriever searches a frozen openFDA label snapshot and returns source-tagged contiguous excerpts. It assumes that each option is a drug name and omits the dosage section. This works poorly when options are full treatment statements. The revised tool instead finds exact normalized aliases from source generic/brand-name fields in both the question and options, and permits dosage-section excerpts. It preserves label identity, section, date, offset, and corpus hash. Product/formulation applicability is still unresolved: recognizing an ingredient is not sufficient to validate its route or dose.

The review layer organizes eighteen concerns spanning patient context, treatment purpose, medication reconciliation, allergy, interactions, renal/hepatic function, special populations, dose and units, formulation/route, schedule, IV preparation, adjunct purpose, duplication, monitoring, feasibility, evidence, and execution. These concerns are informed by medicines-optimization guidance and prescribing benchmarks \citep{nice,who,rxbench,rxllm}. Each interface declares required facts, a procedure, tool dependencies, source references, and an unknown-state policy.

Implemented deterministic checks detect missing fields, invalid numeric doses, repeated supplied ingredient identifiers, exact recorded ingredient-allergy matches, adjuncts without a linked purpose, and missing IV preparation/rate evidence. An empty draft requires an explicit justification rather than receiving a structural pass. These are structural checks. Clinical interaction resolution, renal-dose calculation, formulation compatibility, and patient-specific treatment selection require external validated rules and are not reported as solved. Twelve automated contract tests cover representative failure and unknown-state paths, including delivery of the hash-verified selected skill to the actor; they are software checks, not clinical accuracy measurements.

\subsection{Persistent experience and update mechanism}
We represent an agent checkpoint as $A_t=(\theta,E,C,K_t)$: backbone weights, evidence tool, output contract, and persistent language skills. In the evaluated run, only $K_t$ changes. The updater is the unmodified GRASP author core \citep{grasp}; its source commit and unchanged working tree are checked. We contribute the prescription task interface and evaluation, not this optimizer. The mechanism is:
\begin{enumerate}
\item \textbf{Observe training errors.} Run the current state on each new batch of 157/157/157/154 cases. Compare answers with training labels and group failures for diagnosis. Test labels are excluded.
\item \textbf{Propose bounded edits.} Sample four candidate skill edits, with add/modify/remove operations supported by the author core. Each candidate is evaluated in a forked skill repository, leaving the incumbent intact.
\item \textbf{Measure fixes and regressions.} Re-evaluate the incumbent and candidates on forty training probes targeting twenty earlier failures and twenty successes. Later rounds use prior training batches; the first round falls back to its own batch. This first-round overlap is not an independent validation set.
\item \textbf{Gate and retain.} For candidate fixes $F$, regressions $R$, new invalid-action regressions $I$, and replayed-incumbent values $F_b,R_b$, the implemented score is
\begin{equation}
 S=(F-F_b)-(R-R_b)-I.
\end{equation}
Invalid actions already count in $R$ and incur the additional penalty above. A candidate must satisfy $S>0$ and $R\leq R_b$; the best eligible edit is retained. The core can propose a contrastive revision of a winner that regresses, retaining it only if it improves the same gate.
\item \textbf{Select and freeze.} Evaluate the baseline and the end of the single training epoch on 387 development questions, then freeze the best checkpoint before test evaluation. There is no measured per-round development curve; the per-round test curves are post-selection descriptions.
\end{enumerate}

The final skill concerns indication matching and patient-triggered cautions. Skill revisions carry content hashes, provenance and artifact diffs. New memory-entry contracts require scope, source hashes, triggers, actions and counterexamples, and reject entries declared to originate from test data. These checks validate record structure, not source truth or clinical authority. RSI here studies persistent experience-driven improvement; the updater does not recursively redesign itself, and the measured run does not evolve model weights or tool code.

\section{Experimental Setup}
\subsection{Data and selection}
Table~\ref{tab:data} fixes the task boundaries. RxSafeBench's 2,443 source records yield 2,000 distinct local cases after exact task/dialogue/correct-drug deduplication. They are adapted to three-option selection and split into 625 training, 387 development, and 988 evaluation cases. The task differs from the original free-generation benchmark. RxQA uses all 300 released OpenFDA questions; its licensed BNF component is unavailable. No RxQA answer selects the retained skill.

\begin{table*}[t]\centering\small
\caption{Evaluation scope. Datasets and metrics are not pooled. New retrieval coverage is measured without rerunning an actor.}
\label{tab:data}
\begin{tabularx}{\textwidth}{@{}p{2.4cm}p{3.9cm}X@{}}\toprule
Resource & Task / metric & Local scope\\\midrule
RxSafeBench & Derived option selection / accuracy & 625 train, 387 development, 988 evaluation; historically observed, exploratory.\\
RxQA OpenFDA & Original option selection / accuracy & All 300 public questions; transfer of frozen skills.\\
MedQA & General medical reasoning / accuracy & 200 hash-selected questions, frozen before scoped-memory learning; exact overlap with prior public cases excluded.\\
eICU & Recorded orders / exact joint-order F1 & Separate order-tool component study; 8,005 stays from sixteen held-out hospitals.\\
Clinical review contracts & Structural detection / software checks & Synthetic contract tests only; no clinical-safety benchmark score.\\
Planned clinician study & MIMIC-IV prescription drafts / clinical rubric & Decision-time context; target100 random patients plus50 challenge cases. Enrollment and annotation pending.\\
\bottomrule\end{tabularx}\end{table*}

\subsection{Named methods and controls}
Table~\ref{tab:main} names external agents explicitly. GRASP is an executed task adaptation of its author core with the same backbone and one-call inference cap, without our label evidence. MedAgents and MDAgents use pinned author workflows with a shared network adapter, explicit medication-choice instructions and a common strict answer parser. MedAgents uses its five-stage verification workflow with up to three voting attempts and original per-stage output limits. MDAgents uses adaptive collaboration, zero demonstrations on these tasks and a 1,024-token per-call cap. Each has a ceiling of eighty calls and 24,000 output tokens per case. Development-only repairs address recruitment formatting and missing report propagation; all changes precede test inference and are recorded. These are author-workflow task adaptations, not reproductions of published scores. Their budgets differ from the retained one-call agent, so we report calls and do not claim equal-compute superiority. SafeRx-Agent remains unexecuted; its medication-set task requires a separate compatible protocol.

Component controls use the same question identities: chain-of-thought with no evidence/learned skills, GRASP skills without evidence, label evidence without learned skills, and RxRSIAgent with both. Accuracy counts invalid received answers as incorrect; failed transport requests do not become model errors. Paired scenario intervals for RxSafeBench and item intervals for RxQA use 4,000 resamples without multiplicity adjustment. They are exploratory.

\subsection{Clinical quality beyond reference overlap}
Reference-set F1 and question accuracy remain task-specific endpoints. A complete prescription also requires coverage of treatment needs, correct order details, avoidance of unnecessary drugs, monitoring and appropriate escalation. We therefore specify a separate clinician-oriented assessment, informed by medication review and the Medication Appropriateness Index \citep{nice,mai}. Table~\ref{tab:clinicalmetrics} defines the proposed endpoints. This is a research rubric, not a validated replacement for the MAI. The two available reviewers have not yet supplied ratings; no clinician-derived score is imputed from QA accuracy or structural tests.

\section{Results}
\subsection{Main agent comparison}
@@AGENT_TABLE@@
RxRSIAgent scores 501/988 on RxSafeBench and 183/300 on RxQA. GRASP answers one more RxSafeBench question and six more RxQA questions correctly. The current evidence therefore does not establish a method advantage. MedAgents scores 468/988 on RxSafeBench and 208/300 on RxQA; MDAgents scores 478/988 and 199/300. The retained agent exceeds both on RxSafeBench, while both exceed it on RxQA, by 8.33 and 5.33 percentage points, respectively, with more calls. SafeRx-Agent remains a missing comparison, not an unsuccessful baseline.

\subsection{Component ablations}
@@ABLATION_TABLE@@
Adding selected skills to fixed grounding fixes 83 RxSafeBench answers and regresses 81, a net gain of two. The paired difference is 0.20 percentage points with interval $[-2.43,2.73]$. On RxQA it fixes 19 and regresses 24, losing five answers. The combination is not reliably better than its components. ``Without skills'' and ``without evidence'' are ablations of the retained method, not separate claimed algorithms.

\subsection{Experience trajectory}
@@TRAJECTORY_TABLE@@
@@EVOLUTION_FIGURE@@
These checkpoints describe learning rounds within the same algorithm, not historical manuscript versions. Independent recounting verifies 625 unique training cases, sixteen initial proposal evaluations, one contrastive revision, and three accepted edits. Round one rejects all four proposals because their regressions exceed the replayed incumbent. At 314 cases, one skill is added: indication matching followed by patient-triggered cautions. At 471 cases, it is revised to distinguish stop language from monitoring cautions; the additional contrastive revision is rejected. At 625 cases, it is revised again to require checking cautions even when only one option matches the indication and to expand evidence instructions.

The instruction body changes from zero to 711, 645, and 774 whitespace-delimited words. These are artifact-size measurements, not capability scores. Round two fixes 70/regresses 94 RxSafeBench answers relative to the previous state; round three fixes 74/regresses 56; round four fixes 76/regresses 68. The corresponding RxQA changes are 19/32, 17/17 and 22/14. Round one reuses the unchanged zero-skill state, rather than adding an independent stochastic evaluation. The trajectory is non-monotonic and transfer regresses. Development improvement from 190/387 to 206/387 does not establish improvement on new questions. Module-level changes and their evidence are separated in Table~\ref{tab:modulegrowth}.

\subsection{Order-tool component evidence}
@@ORDER_TABLE@@
This auxiliary experiment isolates order completion on eICU \citep{eicu} and is not an end-to-end RxRSIAgent score. A structured selector supplies identical drug sets while initial versus learned tools choose observed route/dosage/frequency tuples. The three-seed joint-order F1 increase persists when incomplete predictions enter the denominator: 0.01770 to 0.02114. Completeness decreases from 53.67\% to 51.13\%, so exact matching and field coverage must be reported together. The study supports conditional order-tool learning; it does not prove clinical dose correctness or a benefit from language-agent feedback.

\section{Case Studies and Tool Diagnosis}
\subsection{Observed answers on public questions}
We choose the first lexicographic public question ID in each fixed-grounding-to-agent fix/regression group. This is a post hoc illustrative selection, not a representative sample or a source of new skills. Case identities, answer changes, source hashes, and the selection rule are retained. We report output behavior rather than inventing hidden reasoning.

\begin{table*}[t]\centering\small
\caption{Two public RxQA cases from saved predictions. Summaries are paraphrases; correctness means agreement with the dataset's answer. No treatment recommendation is issued.}
\label{tab:cases}
\begin{tabularx}{\textwidth}{@{}p{2.1cm}XX@{}}\toprule
Case & Observed behavior & Interpretation and required tool\\\midrule
104: fix & A pregnancy-related dicyclomine/IBS question. Fixed grounding chooses C (substitution); RxRSIAgent chooses B (counseling and a lower starting regimen), matching the dataset. & The answer changes correctly under the dataset label. Both original runs receive zero label excerpts; this does not establish successful evidence use or the clinical validity of the choice.\\
10: regression & A cyanocobalamin nasal-spray question. Fixed grounding chooses the weekly option C; RxRSIAgent chooses daily option A. The dataset expects C. & Frequency changes despite a correct baseline answer. The frozen label corpus still has no recognized label for this case after repair; dose/schedule reasoning remains unsupported.\\
\bottomrule\end{tabularx}\end{table*}

\subsection{Retrieval failure and implemented repair}
@@COVERAGE_TABLE@@
The original tool resolves options as exact drug names. RxQA commonly expresses complete actions or dosage statements, so this lookup returns any excerpt for only 1/300 questions. It also explicitly excludes dosage sections. The repaired retriever searches source aliases in question and option text and includes dosage material. On the same snapshot it returns excerpts for 214/300 questions, including dosage excerpts for 193. An independent source-span recount verifies all 1,666 returned excerpts against their original label paragraphs and offsets. Question 104 gains eight excerpts, while question 10 still receives none. This exposes both a fixable interface mismatch and a remaining corpus gap.

Coverage is not retrieval relevance or answer accuracy. Exact mention matching can retrieve a label for a different formulation, and many retrieved ingredients may be contextual rather than treatment candidates. We do not use the repaired retriever's coverage to replace the frozen agent's main scores. A development-only end-to-end comparison below fails its promotion gate; relevance and formulation applicability remain unresolved.

\section{Clinician-Oriented Evaluation Protocol}
@@CLINICAL_METRICS_TABLE@@
\paragraph{Completeness with a fixed denominator.}
Before examining anonymized model outputs, reviewers establish the eligible clinical requirements $\mathcal R_i$ for each case, with acceptable alternatives and explicit escalation options. We measure
\begin{equation}
 \mathrm{coverage}_i=\frac{\sum_{r\in\mathcal R_i}\mathbb{1}[r\text{ satisfied}]}{|\mathcal R_i|}.
\end{equation}
This denominator is determined by patient needs, not by the drugs the model happens to generate. Empty prescriptions cannot obtain perfect coverage by omitting required treatments. Conversely, prescribing nothing can be correct when the reference requirement is to withhold treatment or escalate. Unknown applicability, missing judgments and zero denominators are reported explicitly, never converted into success. We pair observed rates with assessment coverage and confirmed-success lower bounds.

\paragraph{Blinded review and analysis.}
The planned offline study uses MIMIC-IV decision-time contexts reconstructed from recorded information availability, targeting 100 randomly sampled eligible patients plus a separate 50-case challenge set stratified by input-defined risk domains. Patient membership must be checked against earlier experiment exposure before freezing the roster; any reused cases are labeled exploratory. This full-order assessment is separate from the public QA main table. Twenty additional calibration cases are excluded from analysis. The primary cohort and challenge cohort are reported separately; these sample sizes are planning targets, not a power claim. Two qualified reviewers independently assess the same outputs, blinded to method and checkpoint with randomized presentation. They first freeze patient needs and acceptable alternatives from permitted context and sources; output-specific errors are judged afterward. Disagreements are discussed, while unresolved items remain unknown and original ratings are retained. We report binary agreement, severity-weighted kappa, adjudicated estimates, assessment coverage, and patient-paired bootstrap intervals. The three primary endpoints are treatment-goal coverage, major-error case rate, and joint clinically correct order rate; any confirmatory testing must preregister multiplicity handling. No single weighted score hides their trade-offs.

\paragraph{Connection to evolution.}
For future complete-order experiments, the same frozen endpoint definitions apply to every learning round. Training feedback may propose skill or tool changes, but clinical assessment data used to select them must be disjoint from final evaluation. An update should be evaluated against the incumbent, frozen memory, ordinary feedback and shuffled feedback under matched experience and budgets. Module swaps hold all other components fixed. Evidence availability, artifact count and software-test coverage remain diagnostic measures; they do not substitute for clinical benefit. The implemented rating aggregator has seven synthetic tests, and its empty template contains no clinician observations.

@@MODULE_GROWTH_TABLE@@

\subsection{Development-gated retrieval intervention}
@@REPAIR_TABLE@@
We subsequently cross original versus repaired retrieval with absent versus frozen incumbent skills on the 190-question proposal partition. Before inference, we record a promotion rule: repaired retrieval with the frozen skill must improve correct count without increasing invalid answers on this partition, and then on the separate 197-question development guard. Only a passing candidate may be frozen for test evaluation. These development questions were used in earlier work, so this is an exploratory engineering check, not independent confirmation. No new skill is learned in this experiment.

Original retrieval scores 90 without skills and 99 with skills; repaired retrieval scores 92 and 98, respectively. The repaired skill condition fixes 29 incumbent errors and regresses 30. Its paired difference is $-0.53$ percentage points with an exploratory item-bootstrap interval of $[-8.42,7.37]$. It fails the first gate; neither the guard nor test stage is run. Evidence availability on these questions decreases from 190 to 181 despite the earlier RxQA coverage improvement. In the nine newly uncovered questions, both skill conditions answer six correctly, so those missing excerpts alone do not explain the net loss. Skill-condition input tokens increase from 517,261 to 809,651 without a measured accuracy gain.

An independent recount verifies all 760 outputs and their cached response hashes. There are 380 new calls and 380 exact-request historical cache hits; incremental provider cost is USD0.294. Controls are not a contemporaneous rerun, and the upstream model service may change. The original main-table checkpoint is retained. These results reject this particular repair as a complete-agent upgrade; they do not establish that all evidence retrieval is unhelpful.


\section{Scoped Memory and Independent Transfer}
\paragraph{Explicit applicability and counterexamples.}
We test a separate memory intervention while retaining the selected main-table checkpoint. Each card specifies observable positive conditions, exclusions, a procedure, training-error support cases and distinct successful counterexamples. A TF--IDF shortlist supplies at most four cards to a semantic router, which activates at most two with exact quotations from the current input. Activated cards include one support example and one contrasting example. This validates provenance and input grounding, not the clinical correctness of the procedure. The current question's answer is never supplied. Model weights, tools and optimizer code remain fixed; only procedural memory changes.

\paragraph{Learning protocol and independent task.}
Three seeds change the order of the same 625 training cases. Four rounds expose 156,312, 468 and 625 unique cases. Admission requires strictly more correct answers and no increase in invalid outputs on both the 190-question proposal set and 197-question guard. The guard is reused for selection, so its improvement is not independent evidence. A development schema repair separates erroneous support cases from successful counterexamples; all three trajectories restart under that implementation before transfer evaluation.

Two hundred MedQA questions from the pinned MedAgents release \citep{medagents} are selected by a question-text hash before learning, without answer or outcome filtering. Exact normalized overlap with prior public cases is removed; semantic overlap and pretraining exposure are not ruled out. All three complete state sequences freeze before MedQA inference. This task measures general medical reasoning rather than full prescription quality. No best test seed replaces the main-table method.

@@SCOPED_TABLE@@
@@INDEPENDENT_TABLE@@
\paragraph{Measured gains and regressions.}
The empty-memory actor answers 166/200 correctly. Final seeds 42, 137 and 2026 answer 167, 166 and 170, respectively: gains of 0.5, 0 and 2.0 percentage points, averaging 0.83 across the three training orders. Seed 42 fixes two and regresses one answer; seed 2026 fixes five and regresses one. Their paired item-bootstrap 95\% intervals are$[-1.0,2.0]$ and$[0.0,4.5]$ percentage points. The three seeds share the same 200 cases and baseline; they are not 600 independent observations. Identical states reuse cached responses. MedAgents and MDAgents answer 172 and 173 correctly, respectively. Thus no new candidate exceeds the medical-agent comparators on this task.

The final states retain one, zero and two cards. Seed 42 retains an interaction/contraindication procedure. Seed 2026 retains diagnosis-specific selection and a procedure that sometimes prefers an ingredient already named in the dialogue. The latter is a potential benchmark shortcut despite its exclusions, not validated clinical knowledge. Active memory adds a 512-token router call before the 1,024-token actor; empty memory uses one actor call. Equal-data retrieval, shuffled feedback and matched-budget refinement controls remain necessary to attribute gains to learning. The declared engineering target of ten absolute percentage points over the strongest comparator is unmet.

\section{Discussion}
The current architecture offers concrete locations for addressing prescribing failures: source lookup for evidence gaps, structured fields for dose/schedule omissions, explicit patient facts for contraindication review, and scoped memory for reusable procedures. Adding a named skill is not evidence that the associated clinical problem is solved. Our interface inventory makes unresolved checks visible instead of converting absent evidence into a pass.

The central empirical distinction is between a selected artifact, a useful component, and an improved complete agent. The selected skill changes behavior but fails to improve transfer. The order tool has a measurable component benefit. The new retriever repairs an observed RxQA coverage defect but fails the subsequent development promotion gate. These findings guide the next complete agent evaluation without claiming that every prescribing risk has been addressed.

\section{Conclusion}
RxRSIAgent combines a fixed language model, drug-label evidence, and development-selected persistent skills within explicit prescription interfaces. The retained agent and its ablations expose limited generalization of learned skills. Traceable public cases identify an evidence-interface failure, and a repaired retriever substantially improves excerpt availability. The architecture also specifies clinical-review dependencies and unknown-state behavior. Broad medical-agent superiority and end-to-end clinical utility remain to be demonstrated.

\section*{Limitations}
The main comparison is exploratory. MedAgents and MDAgents are executed author-workflow task adapters with higher inference budgets; an equal-budget study and SafeRx-Agent comparison remain missing. The independent scoped-memory intervention has three training seeds but only one shared200-question general-medical task, with small gains and possible shortcut learning. The retained configuration has one skill-learning seed and a fixed backbone. Benchmark answer agreement is not clinical correctness; public questions and reference prescriptions can be incomplete or imperfect. The proposed clinician rubric has no completed ratings or validation study. The first skill-update probe overlaps its proposal batch, and training-probe acceptance does not guarantee held-out gains. The revised retriever has a failed development-only accuracy intervention; the new clinical-review layer has no end-to-end clinical outcome estimate. Their label corpus lacks some drugs, and exact matching does not resolve product applicability. The eICU component study has limited temporal availability and native-code targets; it is not interchangeable with RxQA or ATC-based evaluation. No universal risk-coverage, autonomous optimizer redesign, prospective clinical outcome, or overall superiority claim is supported.

\section*{Ethics and Reproducibility}
All evaluations are offline. Public-case studies contain no restricted patient records. Restricted eICU records and fitted artifacts remain local; released reports contain aggregates and source bindings. The review module makes no clinical writes. Recorded labels permit automated agreement scoring, while clinical appropriateness is a separate question. Learned skills are experience artifacts and must not be treated as prescribing authority. The supplied evidence manifest binds the current manuscript, selected configuration, aggregate outcomes, and case audit to their sources.

@@REFERENCES@@
\clearpage
\appendix
\section{Retained Configuration and Reproduction}
The measured skill updater uses the GRASP author-core commit \texttt{9d7d125a3e9b46ed591692475eb07aff4ae67d34}. It sees four training batches of 157/157/157/154 questions, uses four candidate slots and balanced probes of forty training questions, and selects on 387 development questions. The actor output cap is 512 tokens and the proposer cap is 3,072. The evidence profile, label snapshot, backbone weights, and source code remain fixed during this skill experiment. The selected file and validation record are bound in the retained-profile manifest. This is best validation within the saved run, not a search for the largest observed test score across historical prototypes.

For the auxiliary eICU study, the first 8,000 training stays define a 512-code vocabulary; experience grows to 40,000 stays in five checkpoints. Three seeds use patient/hospital-disjoint proposal, guard, and test partitions. The conditional tool chooses among observed joint tuples with sufficient training support. Test contains 6,227 patients and 3,842 zero-target stays. The registered score uses complete tuples; a separate sensitivity includes all predicted tuples in the denominator. None of these component scores is assigned to the main question-answering agent.

\section{Clinical Review Scope}
The eighteen-domain registry supplies trigger context, required facts, tool dependencies, source pointers, and memory boundaries. It covers broadly documented concerns; it is not an exhaustive taxonomy of all possible prescribing errors. The available source-backed label lookup and structural checks are executable. Product-specific interaction, organ-function, population, infusion, monitoring, formulary, and treatment-appropriateness engines remain integration dependencies. In the current software, those domains explicitly return \texttt{not\_assessed}.

The software checks exercise unknown allergy status, duplicate ingredients, an exact recorded allergy, absent schedule fields, invalid numeric doses, IV evidence requirements, unsupported adjunct purposes, invalid output types, and memory provenance boundaries. Passing those checks establishes behavior on the declared synthetic fixtures only. No clinical pass rate is reported.
\end{document}

'''
