"""Measured failure-directed candidates and separate historical order endpoint."""


def render(read, table):
    global_audit = read('upgrade_v45/results/audit.json')
    scoped = read('upgrade_v47/results/audit.json')
    mimic = read('upgrade_v45/results/mimic_recount.json')
    read('upgrade_v45/results/case_studies.json')
    for version in ('45', '46', '47'):
        read('upgrade_v' + version + '/protocol.json')
        read('upgrade_v' + version + '/results/selection.json')
    rows = []
    for key, label in [('tools', 'Product-scope tools'), ('tools_contract', 'Tools + decision obligations'), ('whole_sentence', 'Tools + whole sentences')]:
        parts = []
        for split in ('train', 'proposal_rx', 'proposal_med'):
            score = global_audit['outcomes'][key + '-' + split]
            parts.append(f"{score['correct']}/{score['n']}")
        rows.append(label + ' & ' + ' & '.join(parts) + r'\\')
    rows.append('Scope-routed tools & ' + ' & '.join(f"{scoped['outcomes'][s]['correct']}/{scoped['outcomes'][s]['n']}" for s in ('train', 'proposal_rx', 'proposal_med')) + r'\\')
    diagnostic_table = table('Researcher-authored failure-directed repairs, evaluated on reused development data. The first three arms use an85-case training diagnostic (baseline55); the routed arm uses all400 training cases (baseline269). Proposal baselines are99/190 and103/120. Training denominators differ. None passes the per-task non-regression gate, so no new main-test checkpoint is selected.', 'tab:failure-repairs', 'lrrr', 'Candidate & Training diagnostic & RxSafe proposal & MedQA proposal', rows)
    case_text = r'''
\paragraph{Product identity is insufficient.}
In training case\texttt{e7a30d739ee5b9be}, the reference is ferrous sulfate, but the actor chooses ferrous fumarate. Retrieval supplies a same-ingredient homeopathic product whose indication concerns hot flashes; the original reader discards the source field declaring its homeopathic status. Full metadata and product-scope filtering restore reference agreement. OTC status alone must not trigger this exclusion, and listing in openFDA does not establish approval. This repairs an evidence mismatch, not proof that every alternative iron treatment is inappropriate.

\paragraph{A correct source can lose its decisive condition.}
A heart-failure combination question has isosorbide dinitrate/hydralazine as its reference, whereas the actor chooses amlodipine/valsartan. Component-only retrieval misses regimen-level evidence. Retrieving the combination label still fails when a character window removes the population qualifier. Expanding to the complete original sentence restores reference agreement in this example. The source also specifies adjunctive treatment; its population qualifier is not a sufficient standalone prescribing rule.

\paragraph{Some premises survive explicit verification prompts.}
In\texttt{20084f0b868433c8}, the actor infers dialysis from recurring transfusions and uses it to exclude the reference treatment. Product retrieval changes the answer to the reference, but the additional decision-obligation prompt still selects the original alternative. In another training case, the actor confuses intervention during active diphtheria with pre-exposure toxoid vaccination; all tested repairs remain incorrect. Source-provenance checks do not validate semantic entailment, and label retrieval does not replace treatment-phase guidance.

\paragraph{From case repair to population validation.}
Across400 training traces, structural checks identify8 cases with a shared component across options and10 requiring joint-regimen retrieval; each group contains2 original errors. These patterns account for only part of the131 observed failures. The repaired tools preserve option roles, full product metadata and combination identities. A further candidate expands evidence to whole sentences under the same18,000-character source limit. A final router activates only for source-classified homeopathic products or joint-regimen options, preserving the original evidence and requests elsewhere. No answer label or prediction correctness is read by the router. Its design follows observed development failures and is not an unseen-test intervention.
'''
    case_text += diagnostic_table + r'''
The scoped candidate activates on16/400 training cases, fixes5 and regresses1, but loses one correct answer on each proposal task. The other candidates also fail the declared per-task gate. They are executable researcher repairs, not accepted autonomous RSI updates. The frozen main-table actor therefore remains unchanged. These positive and negative examples are training illustrations, not independent clinical validation.
'''
    rows = []
    for method, label in [('retrieval_conditional_tool', 'Case retrieval + order tool'), ('rxrsi_selected', 'Supervised artifact agent'), ('word_char_ensemble', 'Word/character ensemble + tool')]:
        metrics = mimic['methods'][method]
        rows.append(label + ' & ' + ' & '.join(f"{100*metrics[k]['mean']:.2f}" for k in ('drug_precision', 'drug_recall', 'drug_f1', 'core4_f1', 'order5_f1')) + r'\\')
    order_table = table('Separate historical MIMIC-IV order task, locally recounted from frozen predictions across three seeds. These are earlier supervised/retrieval pipelines, not current RxRSIAgent results. Core4 matches drug/route/dose/unit; Order5 adds frequency and is a post hoc descriptive endpoint. Only60.20\% of reference order rows have all five fields; tuple scores use complete observed labels.', 'tab:historical-orders', 'lrrrrr', 'Historical method & Drug P (\%) & Drug R (\%) & Drug F1 (\%) & Core4 F1 (\%) & Order5 F1 (\%)', rows)
    task_text = r'''
\subsection{Choice reasoning versus complete prescription prediction}
The three main public resources score supplied answer options: RxSafeBench is three-way choice, public RxQA is four-way choice, and MedPIC includes single- and multiple-answer items. Their accuracies are not prescription coverage. For a predicted drug set$P$ and recorded reference$G$, recall is$|P\cap G|/|G|$ and precision is$|P\cap G|/|P|$. Both must accompany F1, Jaccard, omissions, extras and prescription size. An extra relative to recorded treatment is not automatically clinically inappropriate. Joint order matching and reference-field completeness must be reported separately from drug identity.

Completed earlier local work on MIMIC-IV3.1 predicts newly entered or changed orders in the six hours after an admission-plus-six-hour decision, with patient-disjoint40,000/2,000/2,000/1,082 training/proposal/guard/test admissions. The test contains1,024 patients. Prescriptions are linked to provider/pharmacy entry times; inputs exclude future results and untimed discharge diagnoses. The initial128 normalized-name vocabulary is fixed, with out-of-vocabulary targets retained in recall. A local recount of three seeds reproduces every original drug/core4 F1 and additionally computes frequency-inclusive order agreement. No restricted records are sent to an external provider.
'''
    task_text += order_table + r'''
A separate retrospective completed-visit study has271 ATC-L4 classes,18,429 training visits and2,422 reserved test visits. Its NDC mapping covers only27.23\% of selected prescription rows; molecular comparisons use a different219-class panel. Author-method implementations have audited development results, but the full final comparison remains unfinished. Completed-visit codes are not decision-time observations. Neither this mapped subset nor the earlier supervised order pipeline establishes the current LLM agent's complete prescribing ability. Evaluating current RxRSIAgent on shared decision-time inputs and full order endpoints remains a substantive requirement.
'''
    return case_text, task_text
