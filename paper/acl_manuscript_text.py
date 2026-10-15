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
\usepackage{microtype,booktabs,tabularx,amsmath,amssymb,graphicx}
\title{RxRSIAgent: Tracing Memory, Tool, and Parameter Updates\\in Prescription Agents}
\author{Anonymous ACL submission}
\begin{document}
\maketitle

\begin{abstract}
Prescription agents can change their memories, tools, and model parameters as cases accumulate, but these changes need not improve prescribing. We introduce RxRSIAgent, a versioned prescription harness, and evaluate which updates help under explicit data and selection protocols. A common MIMIC-IV medication-set comparison evaluates executable rule memory against conventional predictors and adapted author implementations. An external eICU study evaluates five experience checkpoints, three seeds, and thirteen methods or component configurations on 8,005 stays from sixteen held-out hospitals. Error-prioritized updates reach drug F1 of 0.11306, below matched uniform updates at 0.11825. Holding drug selections fixed, updating the order tool improves exact order F1 from 0.02334 to 0.02838; the improvement persists when incomplete outputs count in the prediction denominator. Local language-model experiments expose a different failure: parameter changes can collapse to empty selections, and removing numerical score ties does not remove candidate-position dependence. Supplementary language-skill and executed-tool studies retain both improvements and transfer regressions. Our results support separating artifact change, component utility, and generalizing improvement. They provide evidence for order-tool learning, but do not establish a distinct advantage from own-error feedback or overall method superiority.
\end{abstract}

\section{Introduction}
Prescription assistance requires several decisions: which medications to select, how to complete their orders, and, in an interactive environment, whether the intended changes were actually recorded. These decisions also provide different opportunities for learning. An agent may accumulate co-prescription rules, improve an order-completion tool, acquire reusable language instructions, or update its prediction parameters. Calling all of these changes self-improvement obscures what was learned and whether it helped.

The distinction matters when evaluating agents that encounter increasing numbers of cases. A later checkpoint can outperform an early checkpoint because it has more supervised data. A tool can improve order fields while the drug-selection policy remains weak. A validation gate can accept an update that subsequently regresses on new patients. An output repair can improve parsing without improving the underlying decision. These alternatives require different controls.

We study these questions through \textbf{RxRSIAgent}, a prescription harness with explicit runtime contracts and versioned update objects. We use recursive self-improvement (RSI) as a research hypothesis about feedback-dependent updates, rather than as an assumed property of the system. The implemented updater is fixed: the experiments do not demonstrate recursive modification of the learning algorithm itself. Recorded prescription labels supply supervised error feedback; the central question is whether using the agent's own errors adds value beyond ordinary learning with the same cases and update budget.

We ask three questions. \textbf{RQ1:} How does each instantiated method compare with strong methods on the same patients and medication space? \textbf{RQ2:} Do frozen checkpoints improve as experience grows? \textbf{RQ3:} Which changed object accounts for an improvement, and does feedback alignment matter? Improvement on RQ2 does not imply a positive answer to RQ3.

Our contributions are: (1) a task-specific prescription harness that records the lineage and acceptance of memory, tool, skill, and parameter updates; (2) a common medication-set comparison and an external-hospital order study with ordinary-learning, shuffled-feedback, and frozen-component controls; and (3) a failure analysis separating empty outputs, candidate-position dependence, and numerical readout effects. The strongest completed evidence is a positive order-tool intervention. The same experiments also expose negative results: error priorities underperform uniform updates, rule-memory gains are not unique to the language agent, and current local language-model updates remain unstable.

\section{Related Work}
\paragraph{Medication recommendation.}
GAMENet combines longitudinal records with graph-augmented memory \citep{gamenet}. SafeDrug adds molecular representations and an explicit interaction objective \citep{safedrug}; ARMR distinguishes historical medication reuse from changing medication needs \citep{armr}. SafeRx-Agent combines clinical context, external knowledge, and verification for finer-grained medication sets \citep{saferx}. We compare available author cores under one local preprocessing protocol and identify adaptations explicitly. Their original published scores are not interchangeable with our local results.

\paragraph{Agent improvement and execution.}
Self-Refine iterates feedback and revision within a generation task \citep{selfrefine}, while Reflexion retains linguistic feedback across trials \citep{reflexion}. GRASP updates a bounded skill library with regression-aware acceptance \citep{grasp}. These mechanisms motivate distinguishing inference-time revision, persistent experience, and parameter updates. MedAgentBench evaluates agents in a FHIR-based electronic-record environment \citep{medagentbench}; successful interaction is a different endpoint from matching a medication set. Our supplementary experiments adapt language-skill learning and execute actual FHIR actions, while keeping their scores separate from prescription agreement.

\section{RxRSIAgent}
\subsection{Runtime and persistent state}
At experience round $r$, the state is
\begin{equation}
 S_r=(\theta_r,M_r,T_r,K_r),
\end{equation}
where $\theta$ denotes selection parameters, $M$ executable or episodic memory, $T$ learned order-tool state, and $K$ language skills. A task adapter specifies the available input $x$, candidate construction, output contract, and scoring function. The shared inference pattern is
\begin{equation}
 \begin{aligned}
 C&=\mathcal{R}(x),\quad D=\pi_{\theta,M,K}(x,C),\\
 \widehat{Y}&=\mathcal{C}\bigl(T(x,D)\bigr),
 \end{aligned}
\end{equation}
where $\mathcal{R}$ obtains candidates, $D$ is the selected medication set, and $\mathcal{C}$ compiles the task's required representation. In the FHIR adapter, compilation is followed by execution and persisted-state readback.

The adapters are explicit instantiations, not a claim that a single trained model solves every task. The ATC adapter predicts classes and does not produce doses. The order adapter completes observed templates. The local LLM selects supplied candidate templates. The public question adapter chooses an answer option. An agent's output contract determines what its score can establish.

\begin{figure*}[t]
\centering\small
\begin{tabular}{c@{\ $\rightarrow$\ }c@{\ $\rightarrow$\ }c@{\ $\rightarrow$\ }c}
\fbox{\parbox{3.0cm}{\centering Task-available patient state}} &
\fbox{\parbox{3.0cm}{\centering Candidate retrieval\\and applicable memory}} &
\fbox{\parbox{3.0cm}{\centering Selection policy\\$\theta_r,M_r,K_r$}} &
\fbox{\parbox{3.0cm}{\centering Order tool $T_r$\\Compile; execute if required}}\\[1em]
\fbox{\parbox{3.0cm}{\centering Training prediction\\and observed-label errors}} &
\fbox{\parbox{3.0cm}{\centering Propose a typed update\\Record changed objects}} &
\fbox{\parbox{3.0cm}{\centering Declared development\\selection and checks}} &
\fbox{\parbox{3.0cm}{\centering Freeze active state\\Retain rejected versions}}
\end{tabular}
\caption{Prescription inference (top) and experience-driven updating (bottom). Each experiment declares which state components change. Test labels are used only for measurement. Fixed compiler repairs and numerical changes are recorded separately from learned updates.}
\label{fig:workflow}
\end{figure*}

\subsection{Update lineage and selection}
For a newly encountered training block $B_r$, we retain pre-update predictions and compare them with recorded labels. The updater produces a candidate state $\widetilde S_r$ from the existing state and its declared feedback. A study-specific development rule chooses an active state. We save the parent state, case membership, feedback, changed artifact hashes, selection scores, and accept/reject decision. Both raw and active checkpoints remain available.

Selection has different roles across experiments. The order study selects a threshold on proposal data, then uses a separate development guard to accept a bundle. The rule study verifies individual edits on training witnesses and uses its guard only for reporting. The local LLM study selects checkpoints on proposal data before any report-only guard evaluation. Reusing development patients across rounds is disclosed; these resources are not repeatedly described as fresh independent tests.

\subsection{Executable rule memory}
The medication-set instantiation refits a shared logistic policy on nested fractions of training patients. Three patient-disjoint cross-fitting folds generate prediction errors for rule induction. A memory rule tests an observed input feature and a near-threshold probability band, then adds or removes one medication class. It cannot inspect the current prescription label at inference.

Candidate induction considers at most 128 frequent features, requires support from at least 30 visits and 20 patients, and retains up to 24 beneficial candidates. Actions are restricted to probabilities within 0.15 of the shared threshold. The language agent receives aggregate descriptors and error changes, selects at most four edits per round, and retains at most twenty rules. Individual patient records never enter these API requests.

A fixed 20\% of seen training patients supplies witness checks: an edit must affect at least five witness patients, improve patient-average F1, and not reduce Jaccard. Controls use the same shared policy and candidate mechanism: no rules, greedy selection, random selection, shuffled numeric evidence, and the agent's matched proposals with the witness gate removed. The last control is an intervention on the same proposals, not an independently relearned trajectory. Cross-fitting prevents a target from fitting its own predictor, but witness reuse and shared fitting resources do not constitute fully isolated confirmation.

\subsection{Policy and order-tool learning}
The eICU instantiation uses logistic SGD policies and learned joint-order templates. Three arms see identical cases in the same order with the same sixty classifier epochs: uniform learning, own-error priorities, and shuffled priorities. For a newly encountered case $i$, feedback weight is
\begin{equation}
 w_i=1+3\bigl(1-F_1(\widehat D_i,D_i^{\mathrm{reachable}})\bigr).
\end{equation}
Weights are computed before using that block's targets for fitting, retained for earlier cases, and normalized to cumulative mean one. The shuffled arm preserves the new-block weight distribution while breaking its alignment with cases. Empty prediction and empty reachable target have quality one for this feedback calculation; evaluation still retains unreachable targets.

The order tool learns global tuple defaults and conditional classifiers over supported observed tuples. It changes order fields without inventing unobserved doses or interpreting ambiguous units. All three arms share the fitted tool within a seed and round; rejected bundles retain their earlier policy and tool. Component interventions freeze the initial tool under the selected policy, or freeze the initial policy under the final tool. Thus drug-selection gains, order-tool gains, and error-priority effects can be measured separately.

\section{Experimental Protocol}
\subsection{Tasks and data}
Table~\ref{tab:data} summarizes the primary experiments. MIMIC-IV and eICU require credentialed access \citep{mimiciv,eicu}. Patient records, predictions, learned weights, and cached hidden states remain local.

\begin{table*}[t]\centering\small
\caption{Task boundaries. ``Proposal'' selects development settings; ``guard'' has the study-specific role stated in the text. Counts describe the local cohorts, not the complete source databases.}
\label{tab:data}
\begin{tabularx}{\textwidth}{@{}p{2.1cm}p{4.0cm}X@{}}\toprule
Experiment & Input and target & Partition and evaluation status\\\midrule
MIMIC-IV 3.1 & Completed-visit diagnoses/procedures and history $\rightarrow$ ATC-L4 medication set & 18,429 train / 1,095 proposal / 1,231 guard visits. Main comparison here is guard development evidence; reserved test is not reported.\\
eICU & Recorded early medications/labs at ICU hour six $\rightarrow$ new orders in hours six--twelve & 40,000 train / 2,000 proposal / 2,000 guard / 8,005 test stays; hospitals and patients separated. Completed held-out-hospital test.\\
Local LLM & Retrospective admission context and twenty candidate templates $\rightarrow$ selection mask & Three 600-case feedback blocks; 100 proposal and 200 report-only guard admissions. Current diagnostics use proposal only.\\
Public supplements & Medication questions or FHIR tasks $\rightarrow$ options or executed actions & Dataset-specific splits; no pooling with medication or order F1. Details in Appendix~\ref{app:public}.\\
\bottomrule\end{tabularx}\end{table*}

\paragraph{Common medication space.}
The MIMIC cohort contains 8,905 patients and 23,177 visits, with training/proposal/guard/reserved-test patient counts of 7,115/433/467/890. We use exact unambiguous NDC mapping to five-character ATC-L4 classes. The bridge covers 27.23\% of source prescription rows. Training defines 271 medication classes; the molecular-compatible panel contains 219. Its restriction removes 52 classes lacking required molecular coverage and changes the target task. Inputs include completed-visit diagnoses and procedures, so this is a retrospective task rather than a prospective admission-time prescription claim. Historical research exposure also makes this panel exploratory. Reserved-test scores remain unreported.

\paragraph{External orders.}
The eICU test has 6,227 patients in sixteen hospitals and includes 3,842 stays with no target orders. We train within eICU and test on unseen hospitals; this is not zero-shot transfer of a MIMIC model. Inputs include age decade, gender, early medications, and finite laboratory measurements with draw and revision timestamps before the decision. Medication storage clocks and full field histories are unavailable. Stays with any target lacking a valid HICL code are excluded before fixed sampling, creating a retrospective completeness selection. The order tuple is HICL, route, dosage string, and frequency string; normalization does not infer absent units.

\subsection{Comparators, budgets, and metrics}
The common panel includes prevalence, prior-visit reuse, case retrieval, logistic regression, and adapted author cores for GAMENet, SafeDrug, and ARMR. Author methods use fifty epochs and proposal-based checkpoint/threshold selection. Thirteen of fifteen registered author runs are complete at this snapshot; molecular ARMR has one completed seed. We do not infer results for unfinished seeds. SafeDrug is evaluated in the molecular panel. Training and search budgets differ across method families and are disclosed, while the feedback comparisons match their specified cases and update budgets.

For medication sets, we report F1 and Jaccard averaged first over visits within a patient and then over patients. For orders, drug and joint-order F1 are micro scores aggregated from set counts. Let $P_i^c$ and $G_i^c$ denote complete predicted and reference tuples. The registered joint score is
\begin{equation}
 F_{\mathrm{joint}}=\frac{2\sum_i|P_i^c\cap G_i^c|}
 {\sum_i|P_i^c|+\sum_i|G_i^c|}.
\end{equation}
We also report completion coverage. A post-test sensitivity score replaces $|P_i^c|$ in the denominator with all distinct emitted tuples $|P_i|$; missing reference fields remain unscorable. This sensitivity analysis preserves the original predictions and primary results. All medication recall denominators retain out-of-vocabulary targets.

Seed standard deviations describe completed runs. Paired patient intervals, and hospital intervals for eICU, use within-study resampling protocols. They are descriptive, without multiplicity correction; they do not represent uncertainty over an unseen population of training seeds. Independent checks reconstruct saved selections, scores, and relevant update decisions. Their scope does not imply replaying every optimizer step or every model forward pass.

\section{Results}
\subsection{Common-data method comparison}
Table~\ref{tab:main} compares methods within each medication space. Rule memory yields 0.61260 F1 in the full space, compared with 0.61151 for the shared policy and 0.61267 for greedy rules. In the molecular space, own-error memory reaches 0.58198, below greedy rules and shuffled evidence. Its full-space difference from ARMR is approximately 0.00396, with paired patient interval $[-0.00075,0.00870]$. These results establish neither a reliable advantage over the strongest comparator nor a unique benefit from language-agent rule selection.

@@COMMON_TABLE@@

The rule operators and their effects are inspectable, but inspectability is not clinical validity. They encode statistical co-prescription corrections. In particular, their scores do not show that the agent acquired human-like prescribing rationale. A later isolated-witness program study also fails to outperform its calibrated ordinary control consistently (Appendix~\ref{app:memory}).

\subsection{External-hospital method comparison}
Table~\ref{tab:eicu} contains all thirteen completed method/configuration rows. Full-data uniform learning has the highest drug and joint-order F1 point estimates in this table. Among matched sequential arms, own-error priorities score 0.11306/0.02838 versus uniform updates at 0.11825/0.02993. Their mean difference is $-0.00519/-0.00155$. Shuffling the priorities does not produce a consistent disadvantage relative to using the aligned error values.

@@EICU_TABLE@@

\subsection{Experience growth and component attribution}
Table~\ref{tab:growth} evaluates the same held-out hospitals at each frozen active checkpoint. All arms improve substantially over the initial 8k-case state. This supports a learning-with-experience observation, but own-error updates remain below uniform updates. Active-state scores can regress at a later checkpoint because acceptance used development data. Raw final states also retain this ordering: uniform 0.11956/0.03087, own-error 0.11355/0.02906, and shuffled 0.11499/0.02937.

@@GROWTH_TABLE@@

The tool intervention gives a more specific positive result. Keeping the selected own-error policy and its drug sets fixed, the updated tool improves joint-order F1 from 0.02334 to 0.02838. All six per-seed patient/hospital intervals have positive lower bounds. With all emitted tuples in the denominator, the corresponding scores are 0.01770 and 0.02114. The latter analysis independently recounts all 129 frozen states. However, complete-output coverage falls from 53.67\% to 51.13\%: improved exact matches do not imply more complete outputs. This result supports learned order completion, not superiority of the entire feedback-driven agent.

\section{Diagnosing Language-Model Updates}
\subsection{Empty selections and prefix mismatch}
The local parameter experiment uses a four-bit Qwen3-4B backbone with rank-eight adapters, fixed retrieval candidates, and observed order templates. Four arms cross ordinary versus error-based sampling with ranked or permuted candidate presentations. Each update uses 400 samples and 100 steps. The registered schedule contains three seeds and three rounds; @@PARAMETER_COUNT@@ updates are complete, so this remains a partial development study.

Eight of the nine completed updates produce empty selections on all 100 proposal admissions in both presentation views and are rejected by the checkpoint-selection rule. Ranked ordinary training improves its first ranked-view checkpoint to drug/order F1 of 0.23301/0.14815, but scores only 0.10800/0.06960 after permutation; its second update collapses. Complete generated JSON therefore need not encode useful decisions. Appendix~\ref{app:parameters} retains every completed update.

A controlled one-round repair holds 400 training admissions and 100 steps fixed while crossing teacher versus all-zero answer prefixes with uniform versus class-balanced binary loss. Four fits complete. Class balancing reduces empty outputs under a fixed 0.5 threshold, but proposal calibration often selects nearly all twenty candidates. In particular, the zero-prefix balanced state selects 20.00/19.91 drugs on average across ranked/permuted views. Apparent nonempty output invariance in this regime does not demonstrate discrimination.

\subsection{Numerical precision versus decision binding}
To separate ranking from selection count, every state selects exactly eight candidates, with label-independent drug-identity tie breaking. We then compare three readouts of the same frozen hidden states: the native quantized output projection, an FP32 two-token projection reconstructed from the same stored four-bit parameters, and that FP32 output re-rounded to BF16. FP32 versus re-rounded output isolates final-logit rounding within the dense path; native versus FP32 also changes projection arithmetic.

@@PRECISION_TABLE@@

The full 1,200-case-forward comparison is independently checked against saved hidden states, directly extracted output rows, all selections, and paired metrics. Native replay exactly matches the parent probabilities. FP32 removes every selection-boundary tie, but exact top-eight set agreement after candidate permutation remains 0\% for all six neural states. Display-slot rank correlation remains larger than drug-identity-aligned correlation.

Teacher-prefix/uniform loss has the only FP32 ranked drug-F1 point estimate above retrieval: 0.28840 versus 0.28706. The paired difference is $+0.00134$ with interval $[-0.01058,0.01313]$, and joint-order F1 remains lower, 0.19534 versus 0.20181. Every permuted configuration is below retrieval in both endpoints. For zero-prefix/uniform loss, FP32 actually reduces permuted drug F1 from 0.23877 to 0.20657. Thus eliminating numerical ties does not repair the decision representation. This post-proposal diagnostic neither selects a new model nor constitutes learned RSI.

\section{Discussion}
Three distinctions explain the results. First, \emph{artifact change} is necessary for a claim about learning, but a new hash or a larger memory is not evidence of benefit. Second, \emph{component utility} can be positive while the complete system loses to a simpler method: the order-tool intervention is such a case. Third, \emph{feedback-specific improvement} requires comparison with ordinary learning and aligned-versus-shuffled feedback. Our current evidence does not support that stronger claim.

These distinctions also guide interpretation of supplementary language-skill experiments. A skill can improve in-domain task completion while harming transfer, and engineering repairs can improve an answer contract without changing what the model learned. The next architectural hypothesis suggested by the local failure analysis is explicit binding of each medication to its decision. It remains untested here. We do not attribute future improvements to a mechanism before running its matched controls.

\section{Conclusion}
RxRSIAgent makes prescription-agent updates explicit and evaluates their consequences under task-specific protocols. Completed experiments show useful order-tool learning, small non-unique rule-memory gains, and failure modes in parameter and language-skill updates. Increasing experience improves several trajectories, yet error-driven updates do not consistently outperform ordinary learning. A defensible account of prescription-agent evolution therefore requires common-data comparators, frozen-state trajectories, component interventions, and retained regressions. The current results support these evaluation practices and the order-tool contribution, while leaving overall superiority and feedback-specific RSI unproven.

\section*{Limitations}
\paragraph{Exploratory and incomplete evidence.}
The MIMIC main table is development evidence, with historical cohort exposure; its reserved test is not reported. Molecular ARMR has only one completed seed, and the parameter study is incomplete. The later program, numerical, and public-benchmark interventions were motivated by earlier observations and are explicitly exploratory. Reusing development or previously inspected benchmark cases can overfit researcher choices. The eICU hospital test supplies a stronger transport setting, but the denominator sensitivity analysis was specified after its primary results.

\paragraph{Targets and availability.}
Mapped medication labels cover a limited fraction of source prescriptions. Molecular filtering changes the target space. The MIMIC visit task uses completed-visit information; the local LLM task is an admission proxy. Even the eICU six-hour task lacks complete storage-time histories. Neither observed-order agreement nor a low known-graph interaction rate establishes safe prescribing. Recorded prescriptions are imperfect behavioral labels; alternative appropriate orders, contraindications, renal adjustment, clinical indications, and patient outcomes are not comprehensively assessed. No clinician-rated outcomes are reported.

\paragraph{Scope of improvement.}
The eICU updater is supervised and uses no language model. The rule agent chooses typed corrections; it does not autonomously rewrite its optimizer. The LLM selects existing templates rather than generating clinically validated doses. Separate adapters and medication spaces cannot be pooled into a universal agent score. Budget matching applies to specified causal contrasts, not to every baseline family. Three seeds and descriptive resampling intervals do not resolve all statistical uncertainty.

\section*{Ethics and Reproducibility}
This work evaluates research systems offline. Ground-truth agreement can be measured automatically without requiring clinicians to label each prediction; establishing clinical appropriateness is a separate question. The system has not been validated for patient care. Restricted patient data, predictions, fitted models, and hidden states remain in the licensed local environment. Public API experiments use released benchmark content or aggregate rule descriptors, not restricted patient records. Simulated FHIR actions are read back and cleaned up. No real clinical order is transmitted.

Protocols, preprocessing code, aggregate outcomes, update receipts, and audit programs are retained. Case identifiers and protected artifacts are excluded from the public release. Audits state what they reconstruct; saved-prediction recounts are not described as full training replication. Transport failures remain incomplete requests rather than incorrect model answers. The evidence inventory accompanying this manuscript binds the reported snapshot to source hashes.

@@REFERENCES@@

\clearpage
\appendix
\section{Detailed Reproduction Protocol}\label{app:protocol}
\subsection{Medication-set preprocessing and adaptation}
Eligible MIMIC patients are adults with an ICU-associated hospital visit and at least two eligible visits. Each visit must contain diagnoses, procedures, and at least one unambiguously mapped medication class. Visits are ordered chronologically; current medication labels are excluded from current inputs. Training-only vocabularies contain 10,726 diagnosis codes, 5,330 procedure codes, and 271 medication classes. Five reserved-test target occurrences fall outside the training medication vocabulary and remain in the recall denominator of the declared future evaluation.

The molecular panel retains 219 classes. Its filtering excludes 5,613 targets in the reserved partition, while retaining three resulting empty-target visits. Molecular resources contain 627 graphs, 863 BRICS substructures, and 326 fingerprints. The known DDI graph has 266 edges and covers 202 classes; an absent edge or uncovered class is not treated as proof of safety. All resources and source mappings are pinned in the cohort audit.

Author implementations retain their documented model cores with local input and label-space adapters. Each completed run has fifty epochs and 921,450 visit exposures; actual optimizer steps differ by architecture. ARMR uses 29,750 steps, while the recorded GAMENet and SafeDrug loops use 921,450. These counts are not equal FLOPs. The SafeDrug adaptation resolves the released minimum-versus-paper-maximum objective discrepancy in favor of the paper's maximum formulation and persists its molecular encoder; the choice is disclosed rather than labeled a bit-identical reproduction. Proposal search evaluates 300 epoch/threshold settings per author run. Concurrent wall time is not used to claim a speed advantage.

@@JACCARD_TABLE@@

The 890-patient reserved partition overlaps historical study memberships. A separately frozen sensitivity subset excludes recorded earlier exposure and retains 318 patients/801 visits; neither the complete reserved test nor this subset has results in the present manuscript. The exposure inventory cannot establish that every patient is globally untouched.

\subsection{External-order training}
The eICU parent cohort has 142,485 stays; 8,003 fail target-code completeness, leaving 134,482 before fixed hash sampling. Training, proposal, guard, and test use 40,000/2,000/2,000/8,005 stays from 124/13/17/16 hospitals. Their patient counts are 35,249/1,914/1,912/6,227. Both patient and hospital identities are separated across these partitions. Test targets contain 11,853 complete order tuples among 15,594 target tuples.

The initial 8,000 stays define the 512-code vocabulary and word, character, and numeric feature maps. Each subsequent block adds 8,000 stays. Policy fitting uses logistic SGD, regularization $10^{-5}$, exactly sixty epochs, and no tolerance-based early stop; each round refits from initialization. The conditional order tool considers at most eight frequent tuples per code, requiring tuple support of at least ten, at least eighty records, and at least two tuple choices. Its SGD regularization is $10^{-4}$, with at most forty iterations and tolerance $10^{-3}$.

Proposal selects from thresholds $\{.10,.15,.20,.25,.30,.40,.50\}$ by the mean of drug and complete-order micro-F1. Guard promotion requires a composite improvement with neither endpoint decreasing by more than .002. All choices freeze before test inference. Word/character ensembles additionally search five mixture weights, so their larger fitting/search budgets are reported separately. Seeds are 42, 137, and 2026. Within each seed, matched priority arms share the same cases, exposure order, and optimizer budget.

\section{Additional Memory Controls}\label{app:memory}
A subsequent experiment reserves 1,423 of 7,115 training patients as witnesses and fits the policy on the remaining 5,692. It combines class calibration with conditional program synthesis over at most two predicates and four edits. This changes witness isolation, calibration, and program expressivity together; comparison with the earlier rule study cannot isolate any one change. Within the revised study, three-seed guard F1 is 0.60803 for class calibration, 0.60801 for greedy programs, and 0.60790 for own-error synthesis in the full space. Molecular values are 0.57989, 0.58094, and 0.58021. These results again do not establish an advantage from language-agent synthesis.

Proposal-only replay of accepted edits finds both positive and negative transfer from witness evaluation. Later compatibility and whole-update confirmation experiments reuse the audited policy fits and separate edit and confirmation witness groups. Only two of six seed/panel runs are fully audited at this snapshot. They are not treated as a completed method comparison. Their unchanged protocols, partial receipts, and all rejected updates remain available in the release.

\section{Parameter and Precision Diagnostics}\label{app:parameters}
\subsection{Completed update inventory}
The four parameter arms use ranked ordinary training, permuted ordinary training, permuted own-error sampling, and permuted shuffled-error sampling. All preserve original retrieval-rank fields and remap twenty-position masks by medication identity. The fixed backbone is Qwen3-4B in four-bit form; LoRA targets the last eight layers with rank eight, scale twenty, and zero dropout. Each round has 400 complete examples, batch size four, learning rate $10^{-4}$, and 100 optimizer steps. Completion-only loss excludes padding. The resulting adapters contain 3,670,016 trainable parameters.

Feedback uses each arm's latest raw adapter on the next 600-case block before labels enter training. Earlier priorities retain their recorded errors. Ordinary arms sample uniformly; error arms use the same $1+3e$ weighting, with the shuffled control permuting error-to-case assignments. Each arm continues from its latest raw adapter even when that state is rejected for serving; optimizer state resets each round. Proposal selects by average drug/order F1 over ranked and permuted views with earliest ties. The base is eligible. The current inventory is incomplete and does not open the old 500-case test.

@@PARAMETER_TABLE@@

\subsection{Repair and precision scope}
The four binary-loss repairs share 400 admissions from the first permuted-uniform update, comprising 8,000 decisions with 1,604 positive and 6,396 negative labels. Balanced loss uses positive weight $6396/1604$. Proposal has 100 admissions/97 patients, disjoint from those fitting patients. The first failed adapter, the frozen base, direct retrieval top-eight, and selecting all twenty candidates remain controls. Calibrated thresholds are chosen on a fixed .01--.99 grid, shared across views. Several optima occur at the lower boundary; this grid is not an exhaustive calibration procedure.

The precision experiment is specified after the parent proposal and fixed-cardinality results. It runs all six frozen neural states in both views, three readouts per shared forward, and both drug-hash and lexical tie rules. It changes no weights, candidates, threshold, or promotion decision. Case-level AUROC includes 67 admissions with both positive and negative candidates; all 100 remain in F1. All selected eight-candidate outputs have complete core tuples, so incomplete predicted tuples do not explain this fixed-cardinality comparison.

Independent raw-weight unpacking and float64 projection replay check 144,000 binary logit values. Maximum dense-logit and probability residuals are $1.98\times10^{-5}$ and $3.58\times10^{-6}$, within tolerances fixed before execution. All 1,200 forwards have completion receipts and none is unresolved. The audit replays readout and metric arithmetic, not the backbone or native projection kernel. All paired intervals use 4,000 patient resamples. The guard comparison remains unexecuted.

@@PRECISION_DETAIL_TABLE@@

\section{Supplementary Public Tasks}\label{app:public}
\subsection{Language skills and medication questions}
RxSafeBench's 2,443 source records \citep{rxsafe} yield 2,000 distinct cases after exact task/dialogue/correct-drug deduplication. The local three-option adaptation has 625 training, 190 proposal, 197 guard, and 988 test questions with scenario grouping; it is not the original free-generation benchmark. Historical full-data evaluation covers all 2,000 derived cases, while later evolution comparisons use the frozen 988-case partition. Subsequent development reused this benchmark, so these results are exploratory. Transfer uses all 300 public RxQA OpenFDA questions \citep{rxqa} with their original options; the unavailable licensed BNF portion is not evaluated.

With DeepSeek-V4.1-Flash, direct selection scores 46.15\%, chain-of-thought 47.27\%, two-call self-refinement 47.57\%, and case retrieval 49.09\% on the same 988 questions. A task adapter around the pinned author GRASP core retains its failure classification, proposals, regression gate, and skill injection. It scores 502/988 versus chain-of-thought's 467, with 102 fixes and 67 regressions. This is an adaptation to option selection, not a reproduction of the paper's original benchmark score.

\begin{table}[t]\centering\small
\caption{Completed language-skill composition, one learned skill trajectory. Counts are correct answers; each method uses one inference call. RxQA is transfer.}
\label{tab:public}
\begin{tabularx}{\columnwidth}{@{}Xrr@{}}\toprule
Method & RxSafe /988 & RxQA /300\\\midrule
Chain-of-thought & 467 & 193\\
Author-core skills & 502 & 189\\
Fixed label grounding & 499 & 188\\
Grounding + evolving skills & 501 & 183\\
\bottomrule\end{tabularx}\end{table}

The evidence tool returns exact excerpts from a pinned openFDA label snapshot; its retrieval source code is fixed. The grounded learner changes one persistent indication/caution procedure. Its frozen round-zero through round-four RxSafe counts are 499, 499, 475, 493, and 501; RxQA counts are 188, 188, 175, 175, and 183. The final gain over fixed grounding is two questions, with paired scenario interval $[-2.43,2.73]$ percentage points. A changed skill therefore does not imply monotonic improvement or positive transfer.

Frozen DeepSeek-learned artifacts also transfer unchanged to Gemini-3.8-Flash under a development-selected 2,048-token cap and low reasoning. On the same 988 questions, chain-of-thought, author skills, fixed grounding, and grounded skills score 532, 527, 538, and 510. The last method has 24 invalid outputs, including 23 reaching the length cap; on the 961 jointly valid cases, it still falls from 528 to 508 correct. This conditional diagnosis does not replace the full result or support a truncation-only explanation. Provider failures are handled as interrupted execution, while received malformed answers count as errors.

\subsection{Executed FHIR tasks}
The MedAgentBench adaptation runs the pinned released application/database through an actual local FHIR service. It executes writes, reads back persisted fields, and cleans up created resources. Reference trajectory success and persisted-state checks are recorded separately. A development-discovered singleton-note shape mismatch is handled by a declared lossless reference view before final selection; original traces remain retained. Task partitions contain 96 training, 80 validation, 64 ID, and 60 held-out-type cases. They overlap in patient identity, so held-out-type results are not patient-disjoint transfer.

\begin{table}[t]\centering\small
\caption{Completed executed-tool comparison. One learning seed; at most eight model action calls per episode.}
\begin{tabularx}{\columnwidth}{@{}Xrr@{}}\toprule
Method & ID /64 & Held-out type /60\\\midrule
Direct tools & 39 & 27\\
Fixed compiled workflow & 38 & 17\\
Workflow + learned skills & 45 & 10\\
\bottomrule\end{tabularx}\end{table}

The two retained skills concern patient-name queries and a laboratory code/text fallback. Relative to the fixed workflow, ID success rises by 10.94 percentage points with paired patient interval $[0,20.55]$, while held-out-type success falls by 11.67 points with interval $[-22.95,-1.64]$. A post-test answer-contract diagnosis finds that fifteen correct first values were rejected for an extra timestamp; this does not replace the strict score, and fifteen other first values were wrong. Single-skill removals do not establish robust synergy.

A subsequent fixed $2\times2\times2$ contract/statistics/skill factorial completes 23 of 24 split-condition cells. It retains the same eight-call episode budget and counts additional HTTP evidence requests. The completed cells are below; the missing cell prevents a complete factorial transfer conclusion. These are engineering interventions with frozen skills, not newly learned tools.

@@FHIR_TABLE@@

\section{Published Results under Their Original Protocols}
Table~\ref{tab:published} gives directly cited results for context. Different cohorts, coding granularity, input fields, and evaluation conventions prevent ranking these numbers against our local main table. The original SafeRx test partition is unavailable locally, so we do not insert an RxRSIAgent result into its protocol.

\begin{table*}[t]\centering\small
\caption{Author-reported F1, not local reproductions. Each row retains its cited source protocol. Dashes indicate a dataset not reported in this selected source table.}
\label{tab:published}
\begin{tabular}{@{}lrrl@{}}\toprule
Method & MIMIC-III & MIMIC-IV & Original source\\\midrule
GAMENet & 0.6081 & -- & \citet{gamenet}, Table 3\\
SafeDrug & 0.6768 & -- & \citet{safedrug}, Table 2\\
ARMR & 0.6959 & 0.6712 & \citet{armr}, Table 3\\
SafeRx / Claude Sonnet-4.6, no safety filter & 0.2758 & 0.4325 & \citet{saferx}, Table 2\\
\bottomrule\end{tabular}\end{table*}

\section{Evidence Inventory and Snapshot}
The companion evidence manifest identifies the source files and hashes used to generate every table. Primary sources are the common-method development recount, independently audited molecular ARMR seed 42, the eICU frozen-test summary and denominator recount, the local parameter snapshot and its audit, and the precision summary with independent readout audit. Public-task sources include the grounded-skill, frozen-transfer, executed-FHIR, and repair summaries. The manuscript preserves the official pinned ACL review style. It is a research snapshot based on completed evidence, not a claim that the unfinished common test, remaining training seeds, or clinical evaluation have been completed.
\end{document}
'''
