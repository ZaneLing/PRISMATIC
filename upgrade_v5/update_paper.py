"""Update the user's existing English source in place; retain embedded ZIP class."""
import json,re
from pathlib import Path
from render_results import HERE,read

PAPER=HERE.parent/'paper/latex/v0.3/prismatic_v03_en.tex'

def run():
    rank=read('ranker_memory_results.json');fusion=read('memory_fusion_results.json')
    llm=read('llm_repair_results.json');seeds=read('seed_robustness.json')
    parser=read('parser_ablation.json')['metrics']
    gate=llm['gate'];m=llm['test']['metrics'];r=m['repaired_review'];g=m['gated_harness']
    source=PAPER.read_text();prefix,body=source.split('% PRISMATIC MANUSCRIPT START',1)
    body=re.sub(r'\\subtitle\{[^\n]+\}',lambda _:r'\subtitle{Research draft v0.5, repair and memory experiments --- 14 October 2026}',body)
    abstract=r'''Medication-set agreement does not establish clinical prescribing quality. We evaluate PRISMATIC on patient-disjoint MIMIC-IV/ED admission snapshots in a common ATC-L4 space. A training-only mapper covers 45.535\% of six-hour orders; saline-name proxy orders remain unmapped. On 4,000 development admissions, three-seed mean micro-F1@5 is 0.3864 for TF-IDF/SGD, 0.3436 for a text/single-visit GAMENet adaptation, and STATIC for a validation-selected word/character ensemble. The earlier 50-case local-LLM harness returned valid empty arrays on half the cases because its reviewer conflated missing clinical evidence with historical prediction. Separating those states and repairing parsing raises free-output review F1 from 0.2082 to REPAIR and reduces empty responses to EMPTY\%. A separate validation-gated ranking/LLM pipeline achieves FINAL on the same 50 cases. A frozen-base experience experiment improves F1 from 0.3473 to 0.3528 as 32,000 training episodes are added, but gains are non-monotonic and memory fusion underperforms the stronger static ranker. The current contribution is a reproducible failure diagnosis and bounded repair, not a clinically validated prescribing agent. Full-order indication, fluid and renal outcomes, faithful contemporary-method comparisons and independent confirmation remain unmeasured.'''
    abstract=abstract.replace('STATIC',f"{seeds['f1_mean']:.4f}").replace('REPAIR',f"{r['observed_micro_f1']:.4f}").replace('EMPTY',f"{100*r['empty_output_fraction']:.0f}").replace('FINAL',f"{g['observed_micro_f1']:.4f}")
    body=re.sub(r'\\begin\{abstract\}.*?\\end\{abstract\}',lambda _: '\\begin{abstract}\n'+abstract+'\n\\end{abstract}',body,flags=re.S)
    # Idempotent replacement of v5-generated blocks only.
    body=re.sub(r'% BEGIN V5 [^\n]+\n.*?% END V5 [^\n]+\n','',body,flags=re.S)
    method=r'''% BEGIN V5 METHODS
\subsection{Failure-aware revision and train-only experience memory}
The v4 reviewer uniformly requested removal of unsupported medications when allergy, weight and renal evidence were missing. This mixed two different tasks: predicting historical records and authorizing clinical administration. The v5 parser preserves valid code members, distinguishes genuine empty arrays from invalid JSON, and recovers the prior proposal after an invalid revision. Missing clinical evidence creates a \emph{needs-information} state without automatically erasing historical candidates. No candidate receives clinical clearance. Coarse TWOSIDES class flags are queried and presented for inspection, but are not ingredient-level contraindications.

\begin{figure}[t]
\centering\small
\fbox{\parbox{0.91\columnwidth}{\centering Admission snapshot and availability audit\\$\downarrow$\\Static word/character ranker + train-only residual memory\\$\downarrow$\\Validation-selected fusion: historical candidates\\$\downarrow$\\Training-case retrieval + coarse risk flags\\$\downarrow$\\Local Qwen revision; parse, salvage or recover\\$\downarrow$\\Validation gate: accept edits or retain candidates\\$\downarrow$\\Historical predictions $\mid$ clinical needs-information state}}
\caption{Executed v5 pipeline. A separate training-episode loop updates residual memory, replays validation cases, and promotes or retains a version. Test cases never enter that loop. The LLM pipeline is evaluated on 50 test cases; the 4,000-case panel evaluates rankers only. Clinical execution and live FHIR actions are not implemented in this experiment.}
\label{fig:v5}
\end{figure}

The static ranker searches word and character TF-IDF models over three fixed regularization values using validation F1. The selected word/character blend has weights 0.25/0.75. We then repeat this fixed configuration for seeds 17, 42 and 73. This is an explicitly stronger statistical baseline, not evidence of LLM reasoning improvement.

For experience growth, a base ranker is trained on 8,000 admissions and frozen. The remaining 32,000 admissions belong to disjoint training patients. Episode $i$ stores an observed-label residual $e_i=y_i-p_0(x_i)$. For the 30 most similar memory cases, the correction is
\begin{equation}
 p_m(x)=p_0(x)+\beta\frac{\sum_{i\in N_{30}(x)}s(x,x_i)e_i}{\max(\epsilon,\sum_{i\in N_{30}(x)}s(x,x_i))}.
\end{equation}
Scores are ranking quantities, not calibrated clinical probabilities. We replay nested memory sizes 250, 1,000, 4,000, 16,000 and 32,000; choose $\beta\in\{0,.1,.25,.5,1\}$ on 4,000 validation admissions; and promote only a strictly better validation version. The append-only ledger rejects non-training feedback and records content hashes and promotion decisions. Vocabulary and mapping stay fixed from the common 40,000-case cohort; thus this is conditional memory growth, not an end-to-end low-data or prospective chronological study. Historical feedback is not clinician-rated correctness, and LLM weights never change.

A second validation search blends the selected residual-memory scorer with the stronger static ranker using memory weights $\{0,.1,.25,.5,1\}$. A separate 50-case validation set determines whether to accept local-LLM candidate revisions. That decision is frozen before the 50 test inferences. Rejected revisions remain in shadow mode, with their actual inference costs charged. The revised RAG arm reuses the immutable v4 test proposals and independently tests the missing-evidence instruction repair. v4 and v5 generation caps are 192 and 384 tokens; this is not an exactly token-matched comparison.

This design borrows the separation of evidence flags and case-specific verification from SafeRx-Agent \cite{saferx} and the idea of experience replay from MedAgentSim \cite{medagentsim}. It does not reproduce their full architectures. MedAgentBench \cite{medagent} requires real FHIR state evaluation; local transition traces alone are not a benchmark result.
% END V5 METHODS
'''
    body=body.replace('\\section{Results}',method+'\n\\section{Results}')
    # Some previous drafts label the section differently; keep insertion explicit.
    if '% BEGIN V5 METHODS' not in body:
        marker='\\begin{table*}[t]\n\\centering\\small\n\\caption{'
        pos=body.index('\\label{tab:main}')
        start=body.rfind('\\begin{table*}',0,pos)
        body=body[:start]+method+'\n'+body[start:]
    full_rows='% BEGIN V5 MAINROWS\n'
    mean=lambda key:sum(v[key] for v in seeds['metrics'].values())/3
    full_rows+=f"Static word/character ensemble (3-seed mean) & 4,000 & {mean('precision_at_5'):.4f} & {mean('micro_recall_at_5'):.4f} & {seeds['f1_mean']:.4f} & 5.00 \\\\\n"
    fm=fusion['test']
    full_rows+=f"PRISMATIC candidate ranker + memory (seed 42; no LLM) & 4,000 & {fm['precision_at_5']:.4f} & {fm['micro_recall_at_5']:.4f} & {fm['micro_f1_at_5']:.4f} & 5.00 \\\\\n% END V5 MAINROWS\n"
    needle='GAMENet text/single-visit adaptation (3-seed mean) & 4,000 & 0.2944 & 0.4125 & 0.3436 & 5.00 \\\\\n'
    assert needle in body
    body=body.replace(needle,needle+full_rows)
    pilot='% BEGIN V5 PILOTROWS\n'
    v=parser['v4_retrieval_salvage']
    pilot+=f"v4 RAG + parser repair only (no new call) & 50 & {v['observed_precision']:.4f} & {v['observed_recall']:.4f} & {v['observed_micro_f1']:.4f} & {v['mean_predicted_classes']:.2f} \\\\\n"
    for title,key in [('v5 repaired RAG review','repaired_review'),('v5 candidate ranker + memory only','anchor_only'),('v5 unrestricted anchor LLM revision','anchor_llm_revision'),('v5 validation-gated PRISMATIC','gated_harness')]:
        v=m[key];pilot+=f"{title} & 50 & {v['observed_precision']:.4f} & {v['observed_recall']:.4f} & {v['observed_micro_f1']:.4f} & {v['mean_predicted_classes']:.2f} \\\\\n"
    pilot+='% END V5 PILOTROWS\n'
    needle='PRISMATIC bounded harness & 50 & 0.3511 & 0.1480 & 0.2082 & 1.88 \\\\\n'
    assert needle in body;body=body.replace(needle,needle+pilot)
    delta=llm['paired_repaired_minus_v4'];lo,hi=delta['patient_bootstrap_95pct']
    results=r'''% BEGIN V5 RESULTS
\subsection{Diagnosing and repairing the empty-output failure}
All 25 empty v4 outputs are valid arrays. Twenty erase nonempty retrieval proposals; 19 correspond to nonempty observed mapped targets. The empty-output cases lose 20 previously matched target codes. This directly implicates the blanket review instruction rather than JSON syntax failure. The all-or-nothing parser is a separate defect addressed by partial salvage and prior-proposal recovery.

The repaired free-output review reaches F1 REPAIR and empty-output rate EMPTY\%, versus 0.2082 and 50\% previously. Its paired F1 change is DELTA (patient-bootstrap 95\% interval [LOW,HIGH]). A genuine empty response is still allowed; no top-five fill rule is applied to this repair arm. The separate candidate-ranker/LLM gate compares validation F1 ANCHORVAL with REVISIONVAL and ACCEPT. On the 50 test cases, the gated policy reaches FINAL. When the ranker is retained, its zero-empty rate follows from its fixed five-candidate budget and is not evidence that every patient needs medication.

A parser-only replay of the old RAG generations already reaches F1 0.31081 with no empty outputs and no additional model call, almost matching the repaired review's 0.31130. Under the old strict parser, the new review instead scores 0.30022 with 8\% empty outputs. The original bounded review stays at 0.20820 and 50\% under both parsers. Thus this increment primarily repairs damage; it does not demonstrate a reasoning gain from the extra review. All new calls generate at most 32 tokens, below either cap. The selected gated policy also remains below the old SGD's same-50-case F1 of 0.42706. Although unrestricted LLM edits perform better than the gated arm on this test, the frozen validation decision is not changed post hoc.

\subsection{What improves as experience grows?}
The static word/character ensemble achieves three-seed F1 STATIC with sample SD SD. For seed 42, its paired advantage over the old SGD is 0.00484 (95\% interval [0.00160,0.00803]). This gain belongs to the statistical ranking change; it is not attributed to the LLM review.

\begin{table}[t]
\centering\small
\caption{Residual-memory growth with a frozen 8,000-admission base ranker. The representation and medication map are fixed; memory updates use training cases only. Validation chooses each weight. Test scores are developmental.}
\label{tab:growth}
\begin{tabular}{@{}rrrr@{}}
\toprule
Episodes & $\beta$ & Validation F1 & Test F1 \\
\midrule
GROWTHROWS
\bottomrule
\end{tabular}
\end{table}

The final memory version improves on its frozen base by 0.00554 (95\% interval [0.00282,0.00833]). However, the test curve peaks at 16,000 episodes and declines at 32,000, although validation prefers the latter. Fusing 10\% of this memory scorer into the stronger static ranker, as selected on validation, yields 0.39022 compared with the static ranker's 0.39185: a paired change of $-0.00163$ (95\% interval [$-0.00324,0.00000$]). We retain this selected policy and negative result rather than switch configurations after inspecting test scores. Experience accumulation helps the weaker frozen base, but this does not establish a general benefit over a stronger supervised model or learning of supportive-drug indications.
% END V5 RESULTS
'''
    replacements={'REPAIR':f"{r['observed_micro_f1']:.4f}",'EMPTY':f"{100*r['empty_output_fraction']:.0f}",'DELTA':f"{delta['delta']:+.5f}",'LOW':f'{lo:+.5f}','HIGH':f'{hi:+.5f}',
       'ANCHORVAL':f"{gate['validation_anchor_f1']:.4f}",'REVISIONVAL':f"{gate['validation_llm_revision_f1']:.4f}",
       'ACCEPT':'accepts LLM edits' if gate['use_llm_prediction_revision'] else 'rejects LLM edits, retaining the candidate ranker',
       'FINAL':f"{g['observed_micro_f1']:.4f}",'STATIC':f"{seeds['f1_mean']:.5f}",'SD':f"{seeds['f1_sample_sd']:.5f}",
       'GROWTHROWS':'\n'.join(f"{x['memory_size']:,} & {x.get('beta',0):.2f} & {x['validation_f1']:.5f} & {x['test']['micro_f1_at_5']:.5f} \\\\" for x in rank['growth'])}
    for key,value in replacements.items():results=results.replace(key,value)
    body=body.replace('\\subsection{Input sensitivity and order generation}',results+'\n\\subsection{Input sensitivity and order generation}')
    body=body.replace('The bounded harness has executed retrieval and revision but remains incomplete clinically. Next steps are validation-set repair of order encoding/truncation and over-abstention; compatible SafeDrug/SafeRx implementations; complete-order blinded review by the two available reviewers; and controlled reviewed-case growth without test feedback.',
       'The v5 increment executes over-abstention repair, stronger statistical ranking and training-only residual-memory growth, while preserving the v4 failures. It remains incomplete clinically. Next steps are complete-order encoding/truncation repair; compatible SafeDrug/SafeRx implementations; blinded review by the two available reviewers; and clinician-rated experience growth without test feedback. The present observational memory cannot establish saline indication, volume, rate, or renal-dose competence.')
    if '\\bibitem{medagentsim}' not in body:
        body=body.replace('\\bibitem{mimic}',r'\bibitem{medagentsim} Almansoori et al. Self-Evolving Multi-Agent Simulations for Realistic Clinical Interactions, 2025. \url{https://arxiv.org/abs/2503.22678}.'+'\n\\bibitem{mimic}')
    PAPER.write_text(prefix+'% PRISMATIC MANUSCRIPT START'+body)

if __name__=='__main__':run()
