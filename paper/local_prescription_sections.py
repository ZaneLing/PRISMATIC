"""Data-linked local prescription and cross-backbone evaluation sections."""
def render(read,table):
    audit=read('upgrade_v50/results/audit.json');learning=read('upgrade_v50/results/learning_scope.json')
    read('upgrade_v50/protocol.json');read('upgrade_v50/results/preparation.json');read('upgrade_v21/results/independent_cohort_audit.json')
    read('upgrade_v50/test_freeze_scope.json');read('upgrade_v50/results/embedding_backend.json');read('upgrade_v50/results/flame_conversion.json')
    comp=read('upgrade_v50/results/comparison.json');transfer=read('upgrade_v50/results/transfer.json');curve=read('upgrade_v50/results/round_curve.json')
    read('upgrade_v50/results/skemex.json');read('upgrade_v50/results/skemex_learning.json');read('upgrade_v50/results/flame.json')
    published=read('upgrade_v50/published_reference_scores.json')['sources']
    assert comp['complete'] and transfer['complete'] and learning['complete'] and curve['complete']
    methods=audit['methods'];m=methods['rxrsi_selected']['metrics'];pct=lambda x:f'{100*x:.2f}'
    rows=[]
    for name,label in [('direct','Direct self-refinement'),('saferx',r'SafeRx-Agent task adaptation \citep{saferx}'),('skemex',r'SkeMex memory-core adaptation \citep{skemex}'),('rxrsi_base','RxRSIAgent, initial state'),('rxrsi_selected',r'\textbf{RxRSIAgent}, retained state')]:
        v=methods[name]['metrics'];rows.append(label+' & '+' & '.join(pct(v[k]) for k in ['drug_precision','drug_recall','drug_micro_f1','core_order_micro_f1','core5_micro_f1'])+r'\\')
    tab=table('Complete1,082-admission local order evaluation. All local rows share Qwen3-4B, a24-drug catalogue, the offline label resource and a128+128+96 output-token allowance. Actual input tokens and offline training computation differ. SafeRx is an independent limited task adaptation; SkeMex executes the author memory core with a common actor, not the full original agent. These rows do not establish superiority over the original papers.','tab:local-orders','p{5.4cm}rrrrr','Method & Drug P & Drug R & Drug F1 & Core4 F1 & Core5 F1',rows)
    flame=methods['flame_list']['metrics']
    seed=methods['candidate_top8']['metrics']
    ft=table('Separate transfer of the released, trained FLAME list policy after adapter fusion and4-bit quantization, with its local initializer shown as a control. The full classifier and collaborative-embedding pipeline is not reproduced; the backbone, prior training and supervised initializer differ. This is not an equal-information comparison or a full FLAME result.','tab:flame-component','lrrr','Component / initializer & Drug F1 & Core4 F1 & Core5 F1',[
      'Frozen supervised top8 + order tool & '+' & '.join(pct(seed[k]) for k in ['drug_micro_f1','core_order_micro_f1','core5_micro_f1'])+r'\\',
      'FLAME released list policy '+r'\citep{flame} & '+' & '.join(pct(flame[k]) for k in ['drug_micro_f1','core_order_micro_f1','core5_micro_f1'])+r'\\'])
    rows=[]
    for r,t in zip(learning['rounds'],curve['trajectory']):
        cards=r['state']['cards'];all_scope=sum(c.get('fact_scope')=='all_observed' for c in cards)
        rows.append(f"{r['round']} & {r['cases_seen']} & {len(cards)}/{all_scope} & {pct(r['proposal']['drug_micro_f1'])}/{pct(r['proposal']['core_order_micro_f1'])} & {pct(r['guard']['drug_micro_f1'])}/{pct(r['guard']['core_order_micro_f1'])} & {pct(t['metrics']['drug_micro_f1'])}/{pct(t['metrics']['core_order_micro_f1'])}"+r'\\')
    rt=table('Six-round update trajectory on144 new training admissions, disjoint from144 earlier training cases used for interface diagnostics. C/A counts procedural cards/cards activating all observed facts, not newly invented tools. Every test state is frozen before scoring; repeated identical states share predictions. Drug/Core4 F1 are percentages.','tab:local-rounds','rrrrrr','Round & New cases & C/A & Proposal & Guard & Test',rows)
    a=transfer['methods']['rxrsi_base'];b=transfer['methods']['rxrsi_selected'];n=len(learning['selected_state']['cards']);ct=methods['rxrsi_selected']['counts']
    ab=read('upgrade_v50/results/evidence_ablation.json');no=ab['without_label_excerpts'];obs=read('upgrade_v49/results/observability_audit.json')
    probe=read('upgrade_v49/results/schema_probe.json')
    text=r'''
\subsection{Local structured-prescription evaluation}\label{sec:local-orders}
We extend the workflow to the entire set of new/change orders within the audited six-hour window. The cohort is retrospectively restricted to nonempty targets, complete12-hour follow-up and no ambiguous target rows. Provider order and pharmacy entry times must both fall in hours6--12, with verification by hour12. Prior orders and labs are filtered by recorded availability clocks. Released field-version histories are incomplete; this does not establish all-admission performance. This is a local prescription-task adaptation of RxRSIAgent; the hosted QA backbone is not sent restricted EHR records. A frozen40,000-admission supervised tool proposes24 joint order templates from the original128-name vocabulary, shared by all local actors. It supplies a candidate space rather than overriding the final selection. Every out-of-vocabulary target remains in recall. Thus this is catalogue-constrained structured order prediction, not unrestricted prescribing or prediction of the entire hospitalization. Facts are bound to observed input identifiers, product-label excerpts are retrieved offline, and selected identifiers compile to joint drug/route/dose/unit/frequency fields. Missing information is preserved. Current diagnoses, allergy completeness, renal clearance, infusion purpose and duration are not established by this input contract.

\begin{figure*}[t]\centering
\begin{tikzpicture}[x=1cm,y=1cm,>=Stealth,
b/.style={draw,rounded corners=2pt,align=center,text width=2.55cm,minimum height=1.15cm,font=\small},l/.style={->,semithick}]
\node[b] (input) at (0,0) {Observed by +6h\\prior orders / labs\\demographics};
\node[b] (cat) at (3.15,0) {Fixed candidate tool\\24 joint templates\\40k training cases};
\node[b] (facts) at (6.3,0) {Call1: fact IDs\\exact input binding\\offline label tool};
\node[b] (check) at (9.45,0) {Call2: assessment\\selected facts or\\all observed facts};
\node[b] (out) at (12.6,0) {Call3: order IDs\\compile drug / route /\\dose / unit / frequency};
\draw[l](input)--(cat);\draw[l](cat)--(facts);\draw[l](facts)--(check);\draw[l](check)--(out);
\node[b] (gt) at (0,-2.25) {Training feedback\\recorded new/change\\orders, +6h to +12h};
\node[b] (trace) at (3.15,-2.25) {Full training traces\\inputs / evidence / checks\\predictions / references};
\node[b] (rule) at (6.3,-2.25) {Conditional proposal\\procedure + counterexample\\bounded verifier scope};
\node[b] (gate) at (9.45,-2.25) {Proposal48 / guard64\\retain only if the\\declared gate passes};
\node[b] (test) at (12.6,-2.25) {Freeze all states\\1,082-case evaluation\\Qwen to Llama transfer};
\draw[l](gt)--(trace);\draw[l](trace)--(rule);\draw[l](rule)--(gate);\draw[l](gate)--(test);
\draw[l](test.north)--++(0,.48)-|(check.south);
\node[fill=white,font=\scriptsize] at (10.8,-1.24) {Retained state};
\node[align=center,font=\scriptsize,text width=14.7cm] at (6.3,-3.45) {Training references provide feedback only; no target prescription is a runtime condition.\\The local adapter does not execute the hosted QA threshold verifier or establish clinical indication/safety.};
\end{tikzpicture}
\caption{Executed local prescription adapter. The local updater sees full training traces and reference discrepancies; reference membership is never a runtime predicate. The researcher defines the allowable fact-scope switch; the model proposes its conditional activation.}
\label{fig:local-workflow}\end{figure*}

''' + tab + f"Candidate support covers {pct(m['catalogue_drug_recall_ceiling'])}\\% of reference drugs; complete observed Core5 coverage is {pct(m['core5_gt_field_coverage'])}\\%. The retained state has drug/Core4 F1 {pct(m['drug_micro_f1'])}/{pct(m['core_order_micro_f1'])}\\%, with {pct(m['empty_fraction'])}\\% empty and {pct(m['invalid_fraction'])}\\% malformed final outputs. The test had historical exposure in earlier supervised studies and is exploratory. " + r'''
SafeRx's source ICD/MEDI routing and ATC safety matrices cannot be reproduced from these decision-time inputs. Our limited adaptation groups specialty and supportive proposals, criticism and adjudication into three calls. SkeMex uses the pinned author encoder, store, utility update, governance and retriever with144 training admissions; embeddings use local MiniLM over complete text chunks, the category is fixed to prescribing, and pre-screening is disabled. Its original web/ReAct loop is not executed. These boundaries are material, so partial adapters cannot justify a claim against the complete author methods.

''' + ft + r'''
\paragraph{Evolution and transfer.}
Six rounds process 24 new training cases each. The local reflector sees discrepant traces and a comparatively better trace (not necessarily correct), including available input, evidence, checker output, predictions and reference orders. It proposes a general procedure with an observable condition and counterexample, optionally selecting all-observed fact scope. Explicit empty JSON means no proposal. The frozen syntax gate filters numeric dose strings in instructions or counterexamples, copied drug actions and unavailable conditions. The researcher defines this bounded interface; executable tool code, weights, candidate model, templates and descriptive schemas remain fixed during learning. Natural-language counterexamples are recorded but not formally proved. The 48 proposal and 64 guard cases are reused: proposal mean drug/Core4 F1 must strictly increase, and neither guard endpoint may decrease. All states freeze before corrected-interface test inference. Prior literal-schema test scores were already observed, so this is exploratory development.

''' + rt + f"The final state retains {n} procedural cards. Transferred without Llama-specific selection to Llama-3.2-3B on all1,082 cases, initial drug/Core4 F1 is {pct(a['drug_micro_f1'])}/{pct(a['core_order_micro_f1'])}\\%, versus {pct(b['drug_micro_f1'])}/{pct(b['core_order_micro_f1'])}\\% with the frozen state. " + ('The states are identical; this does not demonstrate positive transfer. ' if n==0 else 'This measured transfer is limited to these two local backbones. ') + r'''
No test-best checkpoint is chosen. The original candidate tool had already been trained on40,000 admissions;144 refers to newly processed reflection cases, not total system supervision.

\paragraph{Failure evidence and intervention limits.}
A training-only controlled experiment keeps 48 patients, catalogue contents and batch layout fixed while changing format examples. With an A1 example, A1 is selected in 36 cases and A23 in 5. Moving the example to A23 changes these counts to 0 and 46. Removing valid-ID examples yields 8 and 3; drug F1 changes from 3.57 to 7.57\%. This identifies format-example anchoring in this adapter, not a universal medical-model mechanism. Descriptive schemas are applied to every common control; this researcher repair is not an accepted RSI update. ''' + f"Removing offline label excerpts on 48 proposal cases yields drug/Core4 F1 {pct(no['drug_micro_f1'])}/{pct(no['core_order_micro_f1'])}\\%, versus {pct(ab['baseline']['drug_micro_f1'])}/{pct(ab['baseline']['core_order_micro_f1'])}\\% with excerpts. This changes both information and input length and cannot establish clinical benefit from source removal. " + f"The training-only observability audit finds {obs['cases_in_different_target_groups']:,} admissions in {obs['different_target_groups']} identical-context groups with differing target drug sets. On the retained test output, {ct['selection_missing']} missed targets are inside the catalogue and {ct['catalogue_missing']} are outside it. " + r'''
These findings separate candidate coverage, decision selection, observed information and joint-field assembly. Recorded actions do not reveal every physician rationale or a unique optimal regimen. Patient-level before/after cases remain in the restricted artifact; only aggregates are published.

\paragraph{Incremental expenditure.}
All new patient inference, reflection and embeddings run locally, with zero paid model API requests against the USD10 incremental allowance. Local compute is not monetized. Output allowances are matched for local actors; total input use, learning computation and pretrained supervision are not identical. FLAME component results remain separately qualified. An engine probe changes the final selection in 2/16 development cases when prefill batch size changes from 2 to 8; that optimization is rejected. The retained engine uses prefill batch 2 and completion batch 8. Greedy quantized decoding remains batch-sensitive, and cached requests reuse their first recorded responses.
'''
    diagnostic=read('upgrade_v50/results/component_ablation.json');read('upgrade_v50/component_protocol.json')
    dr=[]
    for key,label in [('initial','Initial state'),('instruction_only','Procedure text only'),('fact_scope_only','Verifier scope only'),('retained','Retained combined state')]:
        v=diagnostic['arms'][key];mm=v['metrics']
        dr.append(label+f" & {pct(mm['drug_micro_f1'])} & {pct(mm['core_order_micro_f1'])} & {v['mean_checked_facts']:.2f}"+r'\\')
    text+=table('Predeclared component diagnostic on128 hash-selected test admissions. All arms and membership were fixed before corrected-interface test inference, after prior literal-schema scores were observed; no checkpoint is selected from this diagnostic. The intervention separates card text from executable fact-scope configuration.','tab:order-components','lrrr','Component & Drug F1 & Core4 F1 & Checked facts',dr)
    replay=diagnostic['cached_full_cohort_to_fresh_replay']['initial']
    text+=f"All four component arms use fresh generation with the same case order and chunks. A no-edit replay changes the semantic order set in {replay['changed_cases']}/128 cases relative to cached full-cohort responses; this execution variation must not be interpreted as learned improvement. "
    base=methods['rxrsi_base']['metrics'];delta=100*(m['drug_micro_f1']-base['drug_micro_f1'])
    ci=audit['paired_patient_bootstrap']['rxrsi_base_to_rxrsi']['drug_delta_ci95']
    text+=f"The full-cohort initial-to-retained drug-F1 change is {delta:+.2f} percentage points (patient-cluster95\\% interval [{100*ci[0]:+.2f}, {100*ci[1]:+.2f}]). "
    text+=('The interval includes zero; this does not establish a reliable improvement. ' if ci[0]<=0<=ci[1] else 'This interval is exploratory and unadjusted for repeated development. ')
    per=read('upgrade_v50/results/catalogue_permutation.json');read('upgrade_v50/permutation_protocol.json')
    text+=f"Permuting the same catalogue contents and reassigning order identifiers preserves the selected drug set in {per['same_drug_set_cases']}/128 cases; drug F1 changes from {pct(per['original']['drug_micro_f1'])}\\% to {pct(per['permuted']['drug_micro_f1'])}\\%. This diagnoses position sensitivity and cannot exclude pretrained drug priors. "
    text+=r'An earlier literal-schema scope update passed development but changed full-test drug F1 from7.34 to7.27\%, adding3 true-positive drugs and138 extra drugs. Development acceptance therefore did not establish generalization. '
    read('upgrade_v50/results/learning_diagnostics.json')
    text+=r'The two valid candidates trigger only when both prior orders and laboratory observations are absent. They activate on two cases in each development subset, each containing one observed fact. All-observed scope adds no checked facts, and no order changes. This is an observed condition/action mismatch, not effective tool improvement. '
    tr=read('upgrade_v50/results/training_trace_audit.json')['counts']
    text+=f"Across144 training admissions, {tr['reference_drugs_in_catalogue']}/{tr['reference_drugs']} reference drugs enter the catalogue, {tr['reference_candidate_drugs_with_cached_label']} have a cached exact-name label, and only {tr['reference_drugs_with_excerpt']} receive a selected excerpt; {tr['predicted_drugs_with_excerpt']}/{tr['predicted_drugs']} predicted drugs receive excerpts. Two global sentences per case create uneven evidence coverage. This association is not a causal treatment-selection result. The checker covers {tr['checked_unique_facts']}/{tr['observed_facts']} supplied facts; the actor still sees the full supplied input. "
    read('upgrade_v50/results/validator_replay.json')
    text+=r'Validator replay finds that all three numeric-dose rejections concern observational counterexamples, not new dose instructions. A corrected checker separates these fields and requests abstraction of training-trace references; it flags such references in the two previously schema-valid candidates as well. This correction changes feedback classification only: no frozen state, prediction or reported retention decision is altered. '
    de=methods['rxrsi_selected']['descriptive_endpoints']
    text+=f"The retained state has mean drug Jaccard {pct(de['mean_drug_jaccard'])}\\%, exact-set agreement {pct(de['drug_exact_set_accuracy'])}\\%, and {de['missed_drugs_per_admission']:.2f}/{de['extra_drugs_per_admission']:.2f} reference-relative omissions/extras per admission. The catalogue covers {pct(de['catalogue_core4_recall_ceiling'])}\\% of complete Core4 reference tuples. Joint fields are supplied by the fixed template tool, not independently generated by the LLM. "
    text+=table('Published reference results, shown only with their own protocols. None is a matched local comparison, a local MIMIC-IV order score, or evidence that our adapter exceeds the original method.','tab:published-prescribing','p{3.1cm}p{7.5cm}p{3.5cm}','Original method & Source task and setting & Reported endpoint',[
      r'SafeRx-Agent \citep{saferx} & Completed-visit MIMIC-IV, ATC-L4, Claude Sonnet4.6; source Table2 without safety filter & F1 '+pct(published[0]['without_safety_filter']['f1'])+r'\%\\',
      r'FLAME \citep{flame} & MIMIC-III medication recommendation; source Table1; different inputs, drug space and supervision & F1 '+pct(published[1]['f1'])+r'\%\\',
      r'SkeMex \citep{skemex} & Seven heterogeneous medical-reasoning endpoints, DeepSeek-V3.2; source Table1 & Mean score '+f"{published[2]['skemex_average_percent']:.2f}"+r'\%\\'])
    text+=r'Inference output allowances are matched for the common local actors. RxRSIAgent additionally uses48 proposal and64 guard labels; SkeMex updates directly on144 training admissions. Validation supervision and offline update compute are therefore not matched, although the fixed40,000-admission candidate tool is shared.'
    summary=f"A local catalogue-constrained adapter is evaluated on1,082 MIMIC-IV admissions: drug F1 changes from {pct(base['drug_micro_f1'])}\\% to {pct(m['drug_micro_f1'])}\\% after development retains {n} conditional update(s)."
    conclusion=f"On the local order task, {n} conditional update(s) are retained; the measured drug-F1 change is {delta:+.2f} points, with a95\\% interval [{100*ci[0]:+.2f}, {100*ci[1]:+.2f}]. "
    return {'LOCAL_PRESCRIPTION':text,'ABSTRACT_ORDERS':summary,'CONCLUSION_ORDERS':conclusion}
