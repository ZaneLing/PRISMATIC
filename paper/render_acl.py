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
All case-level decisions are independently recounted. Transport failures are resumed from cache and never scored as model errors. Paired source-scenario intervals, fixes, regressions and successful-response usage are released; retry charges without returned usage are not reconciled. Frozen grounded skills score 510/988 versus 538 for fixed grounding, a difference of -2.83 percentage points with descriptive interval [-4.85, -0.81]. Of 24 invalid skill outputs, 23 reach the length cap. Yet on the 961 cases with valid outputs in both arms, correctness still falls from 528 to 508. This post-hoc conditional diagnosis does not replace the full table or establish a truncation-only explanation. One source skill-learning path does not establish seed robustness.'''.replace('TRANSFERROWS',rr)
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
    if (ROOT/'upgrade_v23/results/summary.json').exists():
        feedback=json.loads((ROOT/'upgrade_v23/results/summary.json').read_text())
        names={'initial_state':'Initial 8k state','uniform':'Uniform updates','error_prioritized':'Own-error priorities','permuted_priority':'Shuffled priorities','full_data_uniform':'Full-data uniform','error_priority_freeze_initial_tool':'Priorities, initial tool frozen'}
        fr='\n'.join(f"{label} & {feedback['methods'][k]['drug_f1_mean']:.4f} $\\pm$ {feedback['methods'][k]['drug_f1_sd']:.4f} & {feedback['methods'][k]['order_f1_mean']:.4f} $\\pm$ {feedback['methods'][k]['order_f1_sd']:.4f} \\\\" for k,label in names.items())
        temporal_section+=r'''\subsection{Matched Feedback-Assignment Controls}
Following the representation pilot, three seeds compare uniform training, own-error priorities and randomly permuted priorities with fixed word/typed features. The accepted parent predicts each new block before its labels update the model. Its weight is $1+3(1-F1)$ in the reachable vocabulary; the randomized control permutes exactly those weights within the block. Previously assigned weights persist, and cumulative weights are normalized to mean one. All three arms use the same cases and exactly 60 epochs for each of 128 logistic classifiers, reinitialized at each of five checkpoints. Initial models are shared, and conditional order tools use only cases observed by the current round. A rejected state retains both its policy and tool.

Seven thresholds compete on proposal validation; a separate guard promotes only an improved composite with neither endpoint dropping by more than 0.002. All seeds and arms finish selection before testing. Seeds change case order and optimization jointly; these retrospective blocks do not represent calendar-time deployment. The previously observed 1,082-admission test is explicitly reused for exploratory analysis, not fresh confirmation.
\begin{table*}[t]\centering\small
\caption{Matched feedback interventions on the recorded-availability task. Mean $\pm$ sample SD over three seeds; exploratory reuse of the earlier test.}
\begin{tabular}{lrr}\toprule Method & Drug micro-F1 & Core-order micro-F1\\\midrule
FEEDBACKROWS
\bottomrule\end{tabular}\end{table*}
An independent audit re-infers parent feedback, recounts error weights and test predictions, checks weight distributions, exact epochs and seen-only tool memberships, and reports patient-cluster intervals and per-case regressions. Improvements over the initial state alone do not establish an effect of error assignment; uniform and shuffled controls are the relevant comparisons. This study updates supervised parameters, persistent feedback weights and order tools, while LLM weights, executable code and representation remain fixed. Uniform updates reach 0.20446/0.12403 drug/order F1, own-error priorities 0.20143/0.12219 and shuffled priorities 0.20204/0.12197. Own-error-minus-uniform intervals contain zero for both endpoints in every seed; there is no consistent advantage over shuffled weights. Own-error mean trajectories improve from 0.16840/0.10130, but individual seed/endpoint trajectories can regress. The updated-tool mean order-F1 gain over freezing the initial tool is 0.00311, with an interval excluding zero in only one seed. These results separate observed case-growth gains from an unestablished feedback-assignment effect.'''.replace('FEEDBACKROWS',fr)
    if (ROOT/'upgrade_v24/results/source_audit.json').exists():
        temporal_section+=r'''\paragraph{External hospital evaluation preparation.}
A separate eICU feasibility audit \citep{eicu} scans 200,859 stays and 7.30 million medication records. A fixed hospital hash and cross-partition patient removal retain 142,485 adult stays, including 8,188 stays from 16 test hospitals, with zero patient or hospital overlap. Zero-target stays remain included. Of 6,283 test-window records missing drug names, 6,064 retain HICL identifiers. Native code coverage and a missing-identity policy must therefore precede modeling. Dual laboratory offsets exclude 238,680 measurements revised after the decision. This is an executed data audit without model scores; its ICU order-time protocol and dosage/frequency fields differ from the MIMIC task, and medication storage timestamps remain unavailable.'''
    if (ROOT/'upgrade_v25/results/cohort_audit.json').exists():
        temporal_section+=r'''\paragraph{Registered native-code hospital comparison.}
The subsequent cohort excludes entire stays containing any target with absent/nonpositive/noninteger HICL, removing 8,003 parent-cohort stays. Fixed sampling yields 40,000/2,000/2,000 training/proposal/guard stays and all 8,005 eligible test stays, involving 6,227 test patients and 16 test hospitals. The test includes 3,842 zero-target stays; correct abstention and false extra orders must therefore be reported separately. Test labels contain 13,994 distinct stay--code targets and 15,594 joint tuples, of which 11,853 have all four observed fields: native code, route, dosage string and frequency string. Native HICL is not asserted equivalent to RxNorm or ATC.

Independent reconstruction checks source membership, timing, finite labs, prior-order selection and complete target identities. An initial-8k vocabulary of 512 codes and feature maps are frozen. Three seeds compare uniform, own-error and shuffled-priority learning with exactly 60 epochs per classifier, alongside prevalence, prior-order reuse, retrieval, word, word/character and full-data supervised controls. All selections must freeze before test inference. Training is running; no external model score is claimed yet. This is training within eICU with hospitals held out, not zero-shot MIMIC transfer. Label-completeness selection and missing medication storage clocks limit prospective interpretation.'''
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

The test contains 6.784 gold drugs per admission and 3.802 reachable drugs in the fixed catalogue. Selected uniform and priority models emit 17.416 and 18.976 drugs on average, exposing severe over-selection. The uniform active state improves in round one, slightly regresses after the accepted round-two update, and retains round two thereafter. Priority retains round one; its last raw checkpoint degenerates on the guard, with 53\% empty outputs, and is rejected. This is a genuine learned-checkpoint failure after valid parsing. A subsequent exact 20-position inclusion-mask intervention was declared before these test results with the same patients and step budgets.'''
    if (ROOT/'upgrade_v15/results/summary.json').exists():
        binary=json.loads((ROOT/'upgrade_v15/results/summary.json').read_text())
        names={'base':'Frozen model, binary prompt','uniform_sft':'Uniform binary updates','error_prioritized_sft':'Priority binary updates','guard_selected_top_k_tools':'Direct top-8 tool'}
        br='\n'.join(f"{label} & {binary['methods'][key]['drug_f1']:.4f} & {binary['methods'][key]['core_order_f1']:.4f} \\\\" for key,label in names.items())
        parameter_section+=r'''\subsection{Explicit Inclusion and Exclusion}
The binary intervention restarts both arms from the original model and supervises every candidate decision, using the same patients, 400 sampled examples and 100 optimizer steps per round. Target-token counts differ from positive-ID output. Both arms select round two before testing.
\begin{table}[t]\centering\small
\caption{Binary supervision on the same 500 admissions. One learning seed; descriptive paired comparisons.}
\begin{tabular}{lrr}\toprule Method & Drug F1 & Order F1\\\midrule
BINARYROWS
\bottomrule\end{tabular}\end{table}
Priority-minus-uniform drug/order differences are 0.05098/0.04257, with patient-cluster 95\% intervals [0.03495, 0.06641]/[0.02972, 0.05428]. Priority still trails the top-8 tool by 0.01977/0.01410, with both intervals negative. This single-seed benefit over ordinary updates does not establish general superiority.

Raw-checkpoint diagnostics reveal failure beneath the accepted curve. The first priority checkpoint emits only all-zero or all-one masks; the second has 16 distinct masks, with 99\% selecting a prefix of the ranked catalogue, versus 34\% of GT masks. The third emits all zeros on guard and test and is rejected. Valid parsed zeros are learned outputs, not API failures. Thus checkpoint protection should not be confused with monotonic model improvement or learned clinical reasoning.

Actual adapter hashes, six 100-step logs, serialized targets, sampling from recorded weights and all test predictions are independently checked. Ten of 3,600 pre-update feedback values cannot be exactly recovered from the shared input cache because duplicate-input generations could overwrite earlier responses. Recorded weights and sampled memberships remain available; missing individual generations are not reconstructed or invented. This training-trace limitation does not change saved-prediction scores, but motivates immutable case-bound feedback receipts in subsequent runs.'''.replace('BINARYROWS',br)
    if (ROOT/'upgrade_v26/results/data_audit.json').exists():
        parameter_section+=r'''\paragraph{Registered position-sensitivity diagnostic.}
A subsequent development-only experiment freezes the base model and both selected round-two adapters on the existing 200-case guard (197 patients). Four conditions compare original prompts, explicit original retrieval ranks, deterministic permutations retaining those ranks, and reversed display order retaining ranks. Candidate fields and patient context remain identical; local IDs and masks are remapped consistently. The added-rank prompt effect is separated from reordering, so ranking information is not silently removed. Fresh deduplicated inference saves immutable case-bound receipts. This post-test-motivated diagnostic is running, with no checkpoint/prompt promotion or held-out improvement claim.'''
        if (ROOT/'upgrade_v26/results/summary.json').exists():
            position=json.loads((ROOT/'upgrade_v26/results/summary.json').read_text())
            parameter_section=parameter_section.replace('This post-test-motivated diagnostic is running, with no checkpoint/prompt promotion or held-out improvement claim.','This post-test-motivated diagnostic is complete, with no checkpoint/prompt promotion or held-out improvement claim.')
            rr='\n'.join(f"{model.replace('_',' ')} & {condition.replace('_',' ')} & {z['drug_order_f1'][0]:.4f} & {z['drug_order_f1'][1]:.4f} \\\\" for model,conditions in position['methods'].items() for condition,z in conditions.items())
            parameter_section+=r'''\begin{table*}[t]\centering\small
\caption{Frozen-model candidate-position diagnostic on the existing 200-case guard. Explicit-rank conditions preserve the same candidate content and original retrieval rank. These are development scores, not a new test comparison.}
\begin{tabular}{llrr}\toprule Frozen state & Display condition & Drug F1 & Order F1\\\midrule
POSITIONROWS
\bottomrule\end{tabular}\end{table*}
All saved outputs, remapped candidates and immutable case receipts pass independent recounting. Explicit-rank permutation reduces priority drug F1 from 0.27471 to 0.17441, a difference of $-0.10030$ with patient-cluster interval $[-0.13508,-0.06646]$. Both adapters select display prefixes in 100\% of nontrivial permuted masks, versus 1.5\% for the base model; all 2,400 outputs parse successfully. Reordering sensitivity with rank information retained is evidence of a representation weakness; it does not alone establish the cause of training collapse or clinical reasoning. No prompt winner is promoted from these results.'''.replace('POSITIONROWS',rr)
    if (ROOT/'upgrade_v31/results/data_audit.json').exists():
        parameter_section+=r'''\paragraph{Registered position-randomized parameter intervention.}
A subsequent local study compares ranked uniform, permuted uniform, permuted own-error and permuted shuffled-error QLoRA updates across three seeds and three case-growth rounds. Original retrieval ranks, candidate identities and order fields remain visible. Each round scores a fresh 600-admission feedback block before sampling 400 accumulated admissions for 100 steps (batch four); earlier priorities retain their original pre-update errors. All arms share a completion-only loss correction excluding a trailing padded target, verified before generation and fitting. This correction does not establish the cause of earlier collapse. Candidate tools and order templates remain fixed.

The 100-case proposal score averages ranked and permuted views and may retain the base model. Training continues from each latest raw adapter. All per-seed selections freeze before evaluating every raw state on the reused 200-case guard under ranked, permuted and reversed views. The 500 previous test admissions are excluded. An executed data audit checks 33,300 transformed views, zero patient-role overlap and no target truncation (maximum 1,005 of 1,536 tokens). This is exploratory development work on the legacy admission-proxy task, with incomplete entry-time provenance; it does not generate novel doses.'''
        p=ROOT/'upgrade_v31/results/audit-seed42.json'
        if p.exists():
            q=json.loads(p.read_text())['base_proposal']
            parameter_section+=f"\nThe independently recounted frozen-base drug/order F1 on proposal is {q['ranked']['drug_micro_f1']:.5f}/{q['ranked']['core_order_micro_f1']:.5f} for ranked views and {q['permuted']['drug_micro_f1']:.5f}/{q['permuted']['core_order_micro_f1']:.5f} for permuted views. These are selection-set reference scores, not evidence of an intervention gain."
        p=ROOT/'upgrade_v31/results/progress.json'
        if p.exists():
            q=json.loads(p.read_text())
            parameter_section+=f" At this snapshot, {q['optimizer_runs_with_complete_receipts']}/36 optimizer runs have completion receipts and {len(q['seeds_fully_audited'])}/3 seeds have complete independent audits. Running jobs do not establish superiority."
    compatibility_section=''
    if (ROOT/'upgrade_v27/results/cohort_audit.json').exists():
        compatibility_section=r'''\paragraph{Standard-method compatibility panel.}
A separate retrospective MIMIC-IV 3.1 panel now contains 8,905 repeated-visit adult ICU patients and 23,177 hospital visits. Patient-disjoint training/proposal/guard/test partitions contain 7,115/433/467/890 patients and 18,429/1,095/1,231/2,422 visits. Every selected diagnosis, procedure and mapped medication set is independently reconstructed from sources. Training-only vocabularies include 271 true five-character ATC-L4 classes, with five test target occurrences outside that vocabulary. The public NDC map covers only 27.23\% of selected source prescription rows; this is explicitly mapped-class prediction, not complete prescription recovery. Completed-visit diagnosis/procedure inputs also distinguish it from the six-hour task. Earlier observed test patients overlap, so this panel is exploratory.

Public molecular lookup resolves 746 CIDs and validates structures spanning 399 ATC-L4 classes. Coverage is 219/271 classes in this cohort. Actual pinned ARMR, GAMENet and SafeDrug cores pass synthetic forward/backward execution probes. SafeDrug still requires complete cohort-specific molecular/substructure compatibility; the probe's synthetic mask is never used as an experimental resource. No trained method score is claimed at this preparation stage.'''
        if (ROOT/'upgrade_v27/results/training_runtime_probe.json').exists():
            compatibility_section=compatibility_section.replace("SafeDrug still requires complete cohort-specific molecular/substructure compatibility; the probe's synthetic mask is never used as an experimental resource. No trained method score is claimed at this preparation stage.",r'''Full resources now contain 627 molecular graphs and 863 BRICS fragments; no synthetic mask is used for training. Dense/sparse forward and registered-gradient probes agree, and the released fixed molecular embedding is persisted in checkpoints. A separate 219-class molecular panel retains all visits, including three empty-target test visits, and explicitly excludes 5,613 test target occurrences. ARMR/GAMENet run in both spaces and SafeDrug in the molecular space, for three seeds and 50 full epochs each. Proposal Jaccard selects checkpoints/thresholds, guard reports development performance, and testing waits for all baseline and future RxRSI states to freeze. Equal case exposure is not equal FLOPs. The released SafeDrug training script's negative-cap coefficient conflicts with Eq.~19; the adapted run uses the paper's nonnegative cap \citep{safedrug}.''')
        if (ROOT/'upgrade_v27/results/control_audit.json').exists():
            audit=json.loads((ROOT/'upgrade_v27/results/control_audit.json').read_text());assert audit['status']=='passed'
            rr='\n'.join(f"{panel} & {name.replace('_',' ')} & {z['patient_f1']:.4f} & {z['patient_jaccard']:.4f} \\\\" for panel,p in audit['panels'].items() for name,z in p['methods'].items())
            compatibility_section+=r'''\begin{table*}[t]\centering\small
\caption{Completed conventional methods on 1,231 guard visits from 467 patients. Choices freeze on separate proposal data; independent raw-source reconstruction reproduces saved predictions exactly. These development results are not the pending neural/RxRSI test comparison.}
\begin{tabular}{llrr}\toprule Label panel & Method & Patient-average F1 & Patient-average Jaccard\\\midrule
CONTROLROWS
\bottomrule\end{tabular}\end{table*}'''.replace('CONTROLROWS',rr)
        if (ROOT/'upgrade_v27/rsi_addendum.json').exists():
            compatibility_section+=r'''
\paragraph{Executable rule-memory evolution.}
Five nested patient-hash rounds expose 20/40/60/80/100\% of training patients. A common logistic class policy is refit with the same development selection as the conventional control. Three patient-disjoint fitting folds produce training-error probabilities. Candidate edits add or remove typed feature--drug inclusion/exclusion rules within a fixed 0.15 threshold band; they cannot inspect the current prescription target at inference. A fixed candidate generator proposes at most 24 supported edits. A language agent receives only aggregate descriptors, support counts and measured error changes and selects up to four IDs per round. A training-witness gate accepts edits only when patient F1 improves without lowering Jaccard, with at least five affected witness patients. At most 20 rules persist.

The evolving artifact is this executable rule memory. Coefficients change through ordinary supervised refitting, and the language model is an offline policy-maintenance component rather than a patient-level prescription generator. Greedy, random, shuffled-evidence and no-witness controls retain identical data exposure and edit limits. The latter reuses the own-error agent's proposals; it is not an independently learned counterfactual trajectory. Full dosage generation is outside this class-set task.

Witness patients are excluded from candidate induction, but their labels participate in other folds' policy fits, and the shared regularization choice uses proposal performance of full seen-patient fits. Direct own-label fitting is prevented, but the pipeline is not wholly isolated nested validation. Repeated witness reuse is training validation, not independent confirmation. Original cross-fit probabilities were saved; fold weights were not. Fresh, explicitly labeled reconstructions reproduce the saved probabilities and threshold decisions. Candidate effects, prompt fields, rule transitions and selected guard predictions receive separate audits.

\begin{figure*}[t]\centering\small
\begin{tabular}{c@{\ $\rightarrow$\ }c@{\ $\rightarrow$\ }c@{\ $\rightarrow$\ }c}
\fbox{\parbox{2.9cm}{\centering More training patients; shared policy fits}} &
\fbox{\parbox{2.9cm}{\centering Cross-fitted errors; typed edit candidates}} &
\fbox{\parbox{2.9cm}{\centering LLM selects edits from aggregate evidence}} &
\fbox{\parbox{2.9cm}{\centering Witness verification; retained rule memory}}\\[1em]
\fbox{\parbox{2.9cm}{\centering Observed current codes and prior history}} &
\fbox{\parbox{2.9cm}{\centering Frozen class-probability policy}} &
\fbox{\parbox{2.9cm}{\centering Apply frozen feature--drug rules}} &
\fbox{\parbox{2.9cm}{\centering Medication class set; automatic GT scoring}}
\end{tabular}
\caption{Implemented rule-agent maintenance (top) and inference (bottom). No test labels enter maintenance. The two rows specify a class-set experiment rather than unrestricted clinical prescribing.}
\end{figure*}
'''
        if (ROOT/'upgrade_v27/results/rsi_development_summary.json').exists():
            z=json.loads((ROOT/'upgrade_v27/results/rsi_development_summary.json').read_text())
            rr=[];growth_rows=[]
            for panel,p in z['panels'].items():
                for arm,m in p['methods'].items():
                    def fmt(key):
                        q=m[key];return f"{q['mean']:.5f}"+(f" $\\pm$ {q['seed_sd']:.5f}" if q['seed_sd'] is not None else '')
                    rr.append(f"{panel} & {arm.replace('_',' ')} & {len(p['seeds'])} & {fmt('patient_f1')} & {fmt('patient_jaccard')} \\\\")
                for own,base in zip(p['proposal_curves']['own_error_rule_agent'],p['proposal_curves']['uniform_policy']):
                    avg=lambda v:sum(v)/len(v)
                    growth_rows.append(f"{panel} & {own['round']} & {own['training_patients'][0]} & {avg(base['proposal_patient_f1']):.5f} & {avg(own['proposal_patient_f1']):.5f} & "+'/'.join(map(str,own['memory_size']))+r' \\')
            compatibility_section+=r'''\begin{table*}[t]\centering\small
\caption{Audited rule-agent comparison on the 1,231-visit, 467-patient guard set. Included seeds have completed cross-fit and candidate/output audits. Values are mean $\pm$ sample seed deviation when multiple seeds are available. These development results do not replace the pending common test main table.}
\begin{tabular}{llrrr}\toprule Panel & Method & Seeds & Patient F1 & Patient Jaccard\\\midrule
RULEDEVROWS
\bottomrule\end{tabular}\end{table*}
\begin{table*}[t]\centering\small
\caption{Actual experience-growth curves on proposal data, which also select models and rounds. Memory counts follow the included seed order 42/137/2026. Policy-only and policy-plus-memory gains are separated.}
\begin{tabular}{lrrrrl}\toprule Panel & Round & Train patients & Shared policy F1 & Own-agent F1 & Retained rules\\\midrule
RULEGROWTHROWS
\bottomrule\end{tabular}\end{table*}
These curves demonstrate changing artifacts and improvement with more cases, but the language-agent increment is small and must outperform greedy and shuffled controls to support a distinct mechanism claim. Proposal curves are selected-development evidence; final fixed-test curves remain gated.'''.replace('RULEDEVROWS','\n'.join(rr)).replace('RULEGROWTHROWS','\n'.join(growth_rows))
        compatibility_section=compatibility_section.replace('all baseline and future RxRSI states','all baseline and registered RxRSI states')
    if (ROOT/'upgrade_v29/protocol.json').exists():
        compatibility_section+=r'''
\paragraph{Isolated witnesses and conditional program synthesis.}
An ensuing registered development study assigns 5,692 training patients to policy fits and permanently reserves 1,423 witnesses, using seed-specific label-independent hashing. The five fresh witness batches contain 285/285/285/284/284 patients, disjoint across rounds and from every coefficient fit and candidate statistic. Fixed earlier vocabularies precede this role assignment. Each batch can be adaptively queried for at most four sequential edits within its one round; it is still training validation. All original fold models are now retained, and independent refits check their provenance numerically.

The frozen per-round state is $(\theta_r,\tau_r,M_r)$: ordinary supervised logistic coefficients, ordinary class-specific threshold calibration, and executable rule memory. Two coordinate passes learn threshold offsets from cross-fitted fit-patient predictions. A language agent then synthesizes up to four typed edits with one or two present/absent feature predicates and a drug inclusion/exclusion action near the calibrated threshold. Induction support and fresh-witness F1/Jaccard changes verify each edit. No arbitrary code or dose is executed. Greedy enumeration includes positive--negative conjunctions; raw/calibrated policies, random programs, shuffled numeric evidence and the same proposals without witness verification remain explicit controls. Error-based focus-drug and feature selection are not shuffled.

This design changes witness isolation, calibration and program expressivity together; comparisons with the prior study do not isolate any one change. The new seven-arm study isolates the language contribution within the same revised data/budget protocol. Proposal data select rounds, guard is report-only, and no new test inference is authorized by its current protocol.'''
        if (ROOT/'upgrade_v29/results/summary.json').exists():
            isolated=json.loads((ROOT/'upgrade_v29/results/summary.json').read_text());names={'raw_policy':'Raw logistic','calibrated_policy':'Class calibration','greedy_conditional_memory':'Greedy programs','random_conditional_memory':'Random programs','own_error_program_agent':'Own-error synthesis','shuffled_evidence_program_agent':'Shuffled-evidence synthesis','matched_proposals_no_witness':'Same proposals, no witness'}
            rr=[]
            for panel,p in isolated['panels'].items():
                for name,z in p['methods'].items():
                    def fmt(k):
                        q=z[k];return f"{q['mean']:.5f}"+(f" $\\pm$ {q['seed_sd']:.5f}" if q['seed_sd'] is not None else '')
                    rr.append(f"{panel} & {names[name]} & {len(p['seeds'])} & {fmt('patient_f1')} & {fmt('patient_jaccard')} \\\\")
            if rr:
                compatibility_section+=r'''\begin{table*}[t]\centering\small
\caption{Isolated-witness development study on the same 1,231 guard visits/467 patients. Only independently audited seeds appear; these models fit 5,692 patients and reserve 1,423 witnesses, unlike the earlier all-training-patient policy fits. Sample seed deviation is shown only when multiple seeds complete.}
\begin{tabular}{llrrr}\toprule Panel & Method & Audited seeds & Patient F1 & Patient Jaccard\\\midrule
ISOLATEDROWS
\bottomrule\end{tabular}\end{table*}
Calibration gains are ordinary supervised gains. A score above raw logistic alone is insufficient evidence for language-agent self-improvement; the calibrated, greedy and shuffled controls are necessary.'''.replace('ISOLATEDROWS','\n'.join(rr))
        if (ROOT/'upgrade_v29/results/memory_diagnostic.json').exists():
            d=json.loads((ROOT/'upgrade_v29/results/memory_diagnostic.json').read_text());rr=[]
            for name,z in d['runs'].items():rr.append(f"{name.replace('-',' ')} & {z['accepted_positive_transfer']} & {z['accepted_negative_transfer']} & {z['accepted_zero_transfer']} \\\\")
            if rr:
                compatibility_section+=r'''\paragraph{Executed development attribution.}
A separately registered proposal-only replay compares no memory, prior-round memory and current memory under the identical current policy/calibration, and replays every actual edit without changing its original accept/reject decision. Positive witness effects can transfer negatively, and old-memory effects can change when the shared predictor changes. These descriptive decompositions motivate compatibility revalidation; they are not a newly trained counterfactual agent.
\begin{table}[t]\centering\small
\caption{Proposal transfer of actually accepted edits in audited runs. Registration followed early development observations; no test labels or new API calls are used.}
\begin{tabular}{lrrr}\toprule Run & Positive & Negative & Zero\\\midrule
TRANSFERROWS
\bottomrule\end{tabular}\end{table}'''.replace('TRANSFERROWS','\n'.join(rr))
        compatibility_section+=r'''
\paragraph{Historical metadata correction.}
Rolling exports reused a mutable nested best-selection dictionary, causing some old nested entries to show later choices. Immutable per-round receipts and each arm's stored best-round field independently preserve the actual history; corrected historical choices are released separately. Proposal scores, rule states and final selections are verified unchanged. Frozen source/result hashes are retained.'''
    if (ROOT/'upgrade_v30/protocol.json').exists():
        compatibility_section+=r'''
\paragraph{Compatibility revalidation and disjoint promotion.}
A further registered factorial tests two fixed memory-maintenance policies without refitting the audited base models. Each fresh witness batch is divided by patient into editing group A and confirmation group B. Compatibility factor C checks old memory against the empty-memory policy on cross-fitted fitting patients and A before generating new edits; failed checks reset the corrections. Confirmation factor P checks the entire edited memory once on B. All checks require at least three affected patients, positive F1 change and nonnegative Jaccard change. Failed promotion returns the calibrated policy with no correction memory, not an empty prescription.

Greedy, own-error synthesis and shuffled-evidence synthesis each run all four C/P combinations, alongside raw and calibrated policy controls: fourteen arms per seed and medication space. Every combination edits on A and computes the same shadow checks. C0P0 is consequently different from the preceding full-witness-batch study; only within-factorial contrasts isolate these gates. Identical prompts share exact responses across conditions, whereas diverging memories receive new prompts. The policies C/P are fixed engineering choices; executable rule memory remains the agent-generated object. B affects later rounds through retained memory, so this remains adaptive training validation on reused development patients.

All raw states and verification decisions are retained. Proposal Jaccard selects a checkpoint with earliest ties; both that checkpoint and raw round five receive report-only guard evaluation after all five rounds. Independent scalar replays reconstruct source probabilities, induction effects, compatibility checks, every edit, whole-state promotion and final outputs. No test inference is performed in this intervention.'''
        if (ROOT/'upgrade_v30/results/summary.json').exists():
            repair=json.loads((ROOT/'upgrade_v30/results/summary.json').read_text());rr=[]
            for panel,p in repair['panels'].items():
                for arm,z in p['endpoints']['selected']['methods'].items():
                    q=z['patient_f1'];f=f"{q['mean']:.5f}"+(f" $\\pm$ {q['seed_sd']:.5f}" if q['seed_sd'] is not None else '')
                    final=p['endpoints']['final']['methods'][arm]['patient_f1']['mean']
                    rr.append(f"{panel} & {arm.replace('_',' ')} & {len(p['seeds'])} & {f} & {final:.5f} \\\\")
            if rr:
                compatibility_section+=r'''\begin{table*}[t]\centering\small
\caption{Audited compatibility/confirmation factorial on the same 467-patient guard set. C/P enable old-memory and whole-update checks respectively. Selected states use proposal Jaccard; the separate final column reports raw round five. Only audited seeds appear, with sample deviation when multiple seeds complete. This is exploratory development evidence.}
\begin{tabular}{llrrr}\toprule Panel & Arm & Seeds & Selected patient F1 & Final-round F1\\\midrule
MEMORYGATEROWS
\bottomrule\end{tabular}\end{table*}'''.replace('MEMORYGATEROWS','\n'.join(rr))
    if (ROOT/'upgrade_v30/common_test_addendum.json').exists():
        compatibility_section+=r'''\paragraph{Frozen common-test extension.}
Before common-test inference, a separate addendum registers all seven conditional-program and fourteen compatibility/confirmation methods on the exact 2,422-visit, 890-patient test cohort and both medication spaces. All five raw rounds and proposal-selected states are retained. The implemented evaluator waits for every author-method selection and all program audits; an independent audit reexecutes 315 program states per panel from original models and raw-source features. Comparisons include every conventional, author and earlier rule method, with descriptive paired patient intervals and seed variation. The permanently reserved witness patients change policy-fitting exposure, and computation budgets differ; these limits accompany the shared test protocol. This extension is still gated and does not supply test scores at this snapshot.'''
        test_path=ROOT/'upgrade_v30/results/common_test_summary.json';audit_path=ROOT/'upgrade_v30/results/common_test_audit.json'
        if test_path.exists() and audit_path.exists():
            checked=json.loads(audit_path.read_text());test=json.loads(test_path.read_text())
            assert checked['status']=='passed' and checked['source_report_sha256']==hashlib.sha256(test_path.read_bytes()).hexdigest()
            compatibility_section=compatibility_section.replace('This extension is still gated and does not supply test scores at this snapshot.','The frozen extension and independent prediction reexecution are complete. These exploratory scores retain the known legacy test-patient overlap; they are not untouched confirmation.')
            for panel,z in test['panels'].items():
                selected=z['endpoints']['selected'];methods={f'v27 / {k}':v['metrics'] for k,v in selected['v27_methods'].items()};methods.update(selected['methods']);rows_test=[]
                for name,m in methods.items():
                    vals=[]
                    for key in ['patient_f1','patient_jaccard','micro_f1']:
                        v=m[key];vals.append(f"{v['mean']:.5f}"+(f" $\\pm$ {v['seed_sd']:.5f}" if v['seed_sd'] is not None else ''))
                    rows_test.append(name.replace('_',' ')+' & '+' & '.join(vals)+r' \\')
                compatibility_section+=r'''\begin{table*}[t]\centering\scriptsize
\caption{Frozen common test: PANEL medication space, 2,422 visits from 890 patients. All checkpoint choices use proposal data. Means and sample deviations cover three seeds where applicable; deterministic controls have one result. All methods and within-panel label spaces are shared, while training and computation budgets differ. Raw round-five endpoints, all growth curves, regressions and paired contrasts accompany the released result report.}
\begin{tabular}{p{.48\textwidth}rrr}\toprule Method & Patient F1 & Patient Jaccard & Micro F1\\\midrule
COMMONROWS
\bottomrule\end{tabular}\end{table*}'''.replace('PANEL',panel).replace('COMMONROWS','\n'.join(rows_test))
    fhir_results=''
    if (ROOT/'upgrade_v19/results/summary.json').exists():
        fhir=json.loads((ROOT/'upgrade_v19/results/summary.json').read_text())
        rr='\n'.join(f"{method.replace('_',' ')} & {split.replace('_',' ')} & {z['state_correct']}/{z['n']} & {z['trace_correct']}/{z['n']} & {z['model_calls']} \\\\" for method,splits in fhir['methods'].items() for split,z in splits.items())
        fhir_results=r'''\subsection{Completed Real-Tool Skill Comparison}
The revised study completes 96 training tasks, 80 validation tasks, 64 ID-test tasks and 60 held-out-task-type tasks. The unchanged GRASP core proposes persistent language-skill edits, while the backbone, compiler and evaluator remain fixed. Two retained skills concern patient-name URL encoding and a lab-code/text fallback query. Their text is model-authored, not an independently validated clinical rule. End-of-epoch validation selects the frozen skill state before testing; validation rises from 56.25\% to 66.25\%.
\begin{table*}[t]\centering\small
\caption{Executed FHIR task comparison, one learning seed. State success uses the declared reference-shape projection plus persisted-field verification. Original trace success remains separate. Counts are logical model calls; exact cached episodes retain their original physical receipts.}
\begin{tabular}{llrrr}\toprule Method & Split & State success & Raw trace success & Calls\\\midrule
FHIRROWS
\bottomrule\end{tabular}\end{table*}
Independent regrading recounts each creation, readback, rollback and cleanup; resource counts return to their original values. Skills-minus-fixed ID success improves by 10.94 percentage points, but the paired patient-cluster interval $[0,20.55]$ includes zero. Held-out-type success falls by 11.67 points against fixed ($[-22.95,-1.64]$) and 28.33 against direct tools ($[-40.68,-16.67]$). On held-out task7, learned skills score 0/30, versus 5/30 fixed and 14/30 direct. No held-out-type arm writes a resource; the fixed system also adds workflow instructions, preventing attribution of this decline to serialization alone. This is not evidence of overall successful evolution. Intervals use 4,000 descriptive patient-cluster resamples; one learning seed and patient overlap limit claims.

A subsequent read-only claim audit finds that the name skill's alleged space-encoding failure is contradicted by the existing HTTP adapter: raw/encoded inputs produce identical URLs and results. The generated example observations are not execution receipts. Global code/text lab-query counts differ for A1C but do not validate patient-specific utility; route serialization does not imply observation-code structure. Exact skill bytes and hashes are released as unvalidated experimental artifacts. Registered frozen single-skill removals test contribution and interaction without rewriting the evaluated skills.'''.replace('FHIRROWS',rr)
        if (ROOT/'upgrade_v19/results/answer_contract_audit.json').exists():
            fhir_results+=r'''
\paragraph{Answer-contract diagnosis.}
All 30 learned-skill task7 answers contain a number and timestamp, whereas the original reference requires a single numeric element. Complete-record read-only rechecking finds 15 correct first values rejected solely for the extra timestamp and 15 wrong first values. Name-only answers are prose strings in all 30 cases. Thus zero strict successes does not imply 30 wrong glucose values. Field projection is a post-test diagnostic, not a replacement score or executed repaired-agent result; syntax-only JSON validation is insufficient.'''
        if (ROOT/'upgrade_v19/results/skill_ablation.json').exists():
            ablation=json.loads((ROOT/'upgrade_v19/results/skill_ablation.json').read_text())
            if ablation['status']=='complete':
                rr='\n'.join(f"{name.replace('_',' ')} & {p['id_test']['state_correct']}/64 & {p['test']['state_correct']}/60 \\\\" for name,p in ablation['methods'].items())
                fhir_results+=r'''\begin{table}[t]\centering\small
\caption{Frozen-skill attribution with identical execution budgets. Registered after direct/fixed outcomes, before ablation execution; exploratory.}
\begin{tabular}{lrr}\toprule Skills & ID & Held-out type\\\midrule
ABLATIONROWS
\bottomrule\end{tabular}\end{table}
The factorial interaction is 0.00 ID points ($[-10.35,10.77]$) and $+3.33$ transfer points ($[-8.62,15.25]$). Individual removal intervals also include zero; robust skill synergy is not established.'''.replace('ABLATIONROWS',rr)
    if (ROOT/'upgrade_v28/results/summary.json').exists():
        repair=json.loads((ROOT/'upgrade_v28/results/summary.json').read_text());rr=[]
        for c in [0,1]:
            for s in [0,1]:
                for k in [0,1]:
                    cells=repair['conditions'].get(f'C{c}S{s}K{k}',{}).get('splits',{})
                    values=[str(cells[split]['state_correct']) if split in cells else '--' for split in ['val','id_test','test']]
                    rr.append(f'{c} & {s} & {k} & '+' & '.join(values)+r' \\')
        fhir_results+=r'''
\paragraph{Executed answer and evidence-tool repair.}
A registered $2\times2\times2$ fixed factorial separates an instruction-derived answer contract (C), source-bound Observation statistics (S), and the frozen two-skill state (K). Invalid answer shapes trigger another model decision inside the same eight-call budget; no favorable field is extracted after grading. The statistics tool follows actual FHIR pages, groups by exact code and unit, and reports latest/24-hour values with source IDs, completeness and omission flags. Additional HTTP calls and token costs are counted. The compiler and original reference logic remain fixed.
\begin{table}[t]\centering\small
\caption{Independently audited repair cells. C/S/K denote contract/statistics/frozen skills. Dashes mean pending, not zero. One fixed run per condition; these are reused exploratory splits.}
\begin{tabular}{rrrrrr}\toprule C & S & K & Val./80 & ID/64 & Type/60\\\midrule
REPAIRROWS
\bottomrule\end{tabular}\end{table}
These manually implemented execution repairs are not autonomous tool-code evolution. All eight conditions stay fixed; observed validation or repeated-test outcomes do not select a winner. Raw-page arithmetic, persisted fields and reference scores are independently reconstructed. Earlier skill failures remain in the original table. New independent confirmation and subsequent evidence-validated learning are still required.'''.replace('REPAIRROWS','\n'.join(rr))
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
An improving prescription agent must demonstrate what changes between versions and whether those changes improve held-out decisions. We study RxRSIAgent as a system of separately versioned prescription policies, episodic memories, order-completion tools and language skills. Ground-truth training prescriptions provide error feedback, with explicit development-selection protocols. Three-seed experiments use 40,000 training admissions, a legacy 4,000-admission test and a rebuilt recorded-availability task with 1,082 new test admissions. Mean five-checkpoint scores increase with cases, but strong same-data supervised controls remain better. On 988 public prescription-choice questions, combining grounded evidence with learned skills scores 50.71\%, against 50.81\% for the author skill-learning core, and transfer declines. Local QLoRA updates improve over a frozen model on 500 new admissions but trail direct top-8 tool use. Real FHIR skill learning improves ID success from 38/64 to 45/64 but reduces held-out-type success from 17/60 to 10/60; answer-contract errors explain part of the decline. These results distinguish artifact changes, reliable execution and generalizing gains. Published comparisons retain their original protocols; universal superiority and a unique RSI advantage remain unproven.
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

Recent structured comparators include ARMR's piecewise history and existing/new-drug modeling \citep{armr2025}, and HADRec's hierarchy/molecular fusion \citep{hadrec}. Code identity matters: the checked HADRec release truncates medication codes to four characters while calling its output level four. We retain the authors' scores as reported and flag this discrepancy against standard five-character ATC-L4 \citep{atcstructure}. LT3 generates prescription text from supplied medication attributes; its downstream entity-recognition F1 is not medication-set F1 \citep{lt3}.

GRASP learns persistent skills with regression-aware selection \citep{grasp}. EvoTool mutates modular tool-use policies while freezing the backbone \citep{evotool}. Process-oriented work such as EvoPathBench motivates evaluating capability retention and adaptation along artifact trajectories \citep{evopath}. These mechanisms inform our controls; our task adaptations are explicitly distinguished from official benchmark reruns.

\begin{table*}[t]\centering\small
\caption{Published task registry. These datasets and protocols differ from the local order task.}
\label{tab:registry}
\begin{tabularx}{\textwidth}{@{}p{2.2cm}p{4.0cm}X@{}}\toprule
Work & Data & Experiments / outputs\\\midrule
GAMENet & MIMIC-III; 6,350 patients, 15,016 visits & 145 medication classes; prediction, DDI and memory ablations\\
SafeDrug & MIMIC-III; 6,350 patients, 14,995 visits & 131 classes; DDI, molecular representations, efficiency\\
ARMR (2025) & MIMIC-III / IV; 6,350 / 9,036 patients & 131 ATC-L3 classes; history and new-drug ablations\\
HADRec (2026) & MIMIC-III / IV & Hierarchy, molecules, transfer; released coding needs clarification\\
LT3 (2025) & n2c2-2018 / MIMIC-III & Label-to-text generation and downstream entity recognition\\
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
\multicolumn{3}{l}{ARMR 2025, Table 3: MIMIC-III / IV patient-average F1 \citep{armr2025}}\\
GAMENet, as reported by ARMR (R) & 0.6674 & 0.6441\\
COGNet, as reported by ARMR (R) & 0.6869 & 0.6582\\
ARMR (R) & 0.6959 & 0.6712\\
\multicolumn{3}{l}{HADRec, Tables 4 and 8: MIMIC-III / IV F1 \citep{hadrec}}\\
HADRec (R; coding caveat in text) & 0.7010 & 0.6408\\
\multicolumn{3}{l}{SafeRx ATC-L4, Table 2: MIMIC-IV / III F1 \citep{saferx}}\\
GAMENet, as reported by SafeRx (R) & 0.3356 & 0.2153\\
SafeDrug, as reported by SafeRx (R) & 0.3519 & 0.2361\\
SafeRx / GPT-5.2, no filter (R) & 0.4138 & 0.2812\\
SafeRx / Claude Sonnet-4.6, no filter (R) & 0.4325 & 0.2758\\
\multicolumn{3}{l}{RxEval option selection, Table 2 \citep{rxeval}}\\
Gemini-3.1-Pro (R) & F1 77.10\% & Exact match 46.10\%\\
Qwen3.6-27B (R) & F1 71.70\% & Exact match 40.00\%\\
\bottomrule\end{tabular}\end{table*}

COMPATIBILITYSECTION

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

\paragraph{Development-discovered grading revision.}
Thirteen development episodes preserve their final active writes but fail the legacy reference because a valid singleton ServiceRequest note array is treated as an object \citep{fhirnote}. We stop and archive the affected learning run before final selection or any ID/OOD test. A declared lossless reference view maps singleton note arrays to legacy objects and text-only route objects to legacy strings for grading only. All text and other values remain unchanged; multi-note arrays and coded route objects are not collapsed. Every arm uses the same view and canonical-intent readback comparison, so harmless server normalization is not scored as a direct-tool error. Original raw reference scores remain separate: this is an adapted execution endpoint, not an unmodified official benchmark score.

Regrading all thirteen existing receipts accepts correct final writes while rejecting wrong-note and active-field-loss controls; eight execution/compatibility contracts pass. Prior failed readbacks were rolled back, and those changed interaction trajectories are not reused. Language-skill learning restarts with empty skills; only identical physical episodes with unchanged submissions/feedback and successful readback/cleanup are eligible for reuse. Compiler and evaluator repairs are fixed engineering changes, not agent evolution gains.

FHIRRESULTS

\section{Limitations}
The legacy structured-order experiment uses admission-proxy inputs. Triage has no verified entry timestamp and medication reconciliation lacks storetime; temporal availability is therefore not fully established. A full target-row audit links 1,788,195 records to provider and pharmacy clocks: 42,005 matching provider orders precede admission, 1,425,392 fall within the intended next-six-hour horizon, and 276,269 occur later. There are 438 provider-link admission conflicts, which remain untrusted. Pharmacy entry falls within the horizon for 1,777,546 rows. The two source linkage paths agree on all 1,757,038 rows where both IDs exist and reproduce identical temporal counts. These clocks still differ; the retrospective start-window results are not prospective new-order evidence. The rebuilt recorded-availability cohort addresses these clocks but conditions on coherent, nonempty future orders and lacks complete field-version histories. Candidate vocabularies and one-template-per-drug output limit recall. Recorded prescriptions may omit clinically acceptable alternatives, and agreement does not prove indication or safety. Current language-artifact baselines are task adaptations, not official reruns. Repeated development selection can overfit; independent tests, multiple evolution orders, transfer and matched optimization budgets are necessary before claiming general RSI benefits. External RxEval and SafeRx data access remains unresolved.

\section{Conclusion}
An auditable improving agent must show both changing artifacts and beneficial effects. Our completed rounds show data-growth gains and a useful conditional order tool, alongside weak memory gains and a stronger static control. We continue beyond that negative result by isolating language-artifact and parameter evolution. No claim that RxRSIAgent is the best existing method is made without corresponding benchmark evidence.

\section*{Ethics and Data Access}
All restricted MIMIC records, predictions and checkpoints remain on the authorized local machine. Public releases contain code, configurations and aggregate measurements. Existing GT supports automated evaluation without mandatory new clinical annotation. The system is evaluated for research and is not deployed to prescribe for patients.

\begin{thebibliography}{9}
\bibitem[Shang et al.(2019)]{gamenet} Shang et al. 2019. GAMENet. \url{https://arxiv.org/abs/1809.01852}.
\bibitem[Yang et al.(2021)]{safedrug} Yang et al. 2021. SafeDrug. \url{https://arxiv.org/abs/2105.02711}.
\bibitem[Wu et al.(2025)]{armr2025} Feiyue Wu, Tianxing Wu, and Shenqi Jing. 2025. ARMR: Adaptively Responsive Network for Medication Recommendation. IJCAI. \url{https://www.ijcai.org/proceedings/2025/871}.
\bibitem[Wang et al.(2026)]{hadrec} Junke Wang et al. 2026. HADRec: A Hierarchy-Aware Drug Recommendation Framework by Fusing Molecular Knowledge and Electronic Health Record. Preprint. \url{https://arxiv.org/abs/2610.00984}.
\bibitem[Belkadi et al.(2025)]{lt3} Samuel Belkadi et al. 2025. LT3: Generating Medication Prescriptions with Conditional Transformer. CL4Health. \url{https://aclanthology.org/2025.cl4health-1.17/}.
\bibitem[WHO Collaborating Centre(2022)]{atcstructure} WHO Collaborating Centre for Drug Statistics Methodology. 2022. ATC Structure and Principles. \url{https://atcddd.fhi.no/atc/structure_and_principles/}.
\bibitem[Wang et al.(2026)]{saferx} Wang et al. 2026. SafeRx-Agent. \url{https://arxiv.org/abs/2605.29146}.
\bibitem[Chen et al.(2026)]{rxeval} Chen et al. 2026. RxEval. \url{https://arxiv.org/abs/2605.14543}.
\bibitem[Moll et al.(2026)]{grasp} Moll et al. 2026. GRASP: Gated Regression-Aware Skill Proposer for Self-Improving LLM Agents. \url{https://arxiv.org/abs/2605.29668}.
\bibitem[Yang et al.(2026)]{evotool} Yang et al. 2026. EvoTool: Self-Evolving Tool-Use Policy Optimization in LLM Agents via Blame-Aware Mutation and Diversity-Aware Selection. ACL. \url{https://syang2000.github.io/ACL_2026_EvoTool/}.
\bibitem[Lin et al.(2026)]{evopath} Lin et al. 2026. Beyond Endpoint Performance: Process-Level Evaluation of Self-Evolving Agents. \url{https://arxiv.org/abs/2609.24663}.
\bibitem[HL7 International(2019)]{fhirr4} HL7 International. 2019. FHIR R4: Dosage Detailed Descriptions. \url{https://hl7.org/fhir/R4/dosage-definitions.html}.
\bibitem[HL7 International(2019)]{fhirnote} HL7 International. 2019. FHIR R4: ServiceRequest Detailed Descriptions. \url{https://hl7.org/fhir/R4/servicerequest-definitions.html}.
\bibitem[Pollard et al.(2018)]{eicu} Pollard et al. 2018. The eICU Collaborative Research Database, a freely available multi-center database for critical care research. Scientific Data. \url{https://doi.org/10.1038/sdata.2018.178}.
\end{thebibliography}
\end{document}
'''
    body=body.replace('METHODROWS',rows).replace('GROWTHROWS',growth).replace('PUBLICSECTION',public_section).replace('PARAMETERSECTION',parameter_section).replace('TEMPORALSECTION',temporal_section).replace('COMPATIBILITYSECTION',compatibility_section).replace('FHIRRESULTS',fhir_results)
    if fhir_results:
        body=body.replace('Full ID and held-out-task-type evaluation is in progress.','The completed ID and held-out-task-type comparison is reported below.')
    sty=STYLE.read_text();prefix='% Official ACL style embedded for the standalone editor. See acl_template_provenance.json.\n'+r'\begin{filecontents*}[overwrite]{acl.sty}'+'\n'+sty+'\n'+r'\end{filecontents*}'+'\n% PRISMATIC MANUSCRIPT START\n'
    PAPER.write_text(prefix+body)
    provenance={'repository':'https://github.com/acl-org/acl-style-files','commit':'d5adc823ff0f80f98c80405ca0ab66c68e684409',
        'acl_sty_sha256':hashlib.sha256(STYLE.read_bytes()).hexdigest(),'target':'ACL 2027','mode':'review','path_preserved':str(PAPER.relative_to(ROOT)),
        'previous_template':'Original AAMAS template preserved in Git history through commit 9875d2fd.'}
    (PAPER.parent/'acl_template_provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')

if __name__=='__main__':run()
