"""Update the active English source in place; leave embedded AAMAS class intact."""
from pathlib import Path
import re,statistics as st
from render_results import render

def run():
    rows,b,g,l,m,t,o,coverage=render()
    path=Path(__file__).resolve().parents[1]/'paper/latex/v0.3/prismatic_v03_en.tex'
    source=path.read_text();prefix,body=source.split('% PRISMATIC MANUSCRIPT START',1)
    body=body.replace('A Time-Frozen, Method-Level Evaluation Protocol for Evolving Prescription Support',
                      'A Method-Level Evaluation of Evolving Prescription Support')
    body=body.replace('Research draft v0.4-dev --- 14 October 2026','Research draft v0.4, execution r1 --- 14 October 2026')
    abstract=fr'''Medication-set agreement does not establish clinical prescribing quality. We evaluate PRISMATIC using patient-disjoint MIMIC-IV/ED admission snapshots, a common ATC-L4 medication space and explicit unknown-label handling. All 201,750 eligible ED-to-hospital admissions are retained. A dictionary plus fallbacks learned only from the sampled 40,000 training admissions maps {coverage:.3f}\% of 1,788,195 six-hour orders. On the same 4,000 development admissions, prevalence and retrieval micro-F1@5 are 0.2839 and 0.3281; three-seed mean scores are 0.3864 for TF-IDF/SGD and 0.3436 for an independently adapted, single-visit GAMENet. The adaptation changes the original inputs and training schedule and is not a faithful reproduction. On a nested 50-case local-LLM comparison, direct, ordinary repeat, retrieval and bounded PRISMATIC review achieve observed micro-F1 of 0.2445, 0.2445, 0.2871 and 0.2082. Review improves output validity but abstains on half the cases, reducing recall. A ten-case complete-order probe exposes coding and fluid-information failures. Input timestamps and medication mapping remain incomplete: 2,127 pre-admission lab rows were stored after the decision, and saline-name proxy orders are entirely absent from the ATC mapping. These developmental findings motivate explicit abstention, coverage reporting and independent clinical review; they do not establish clinical superiority or safety.'''
    body=re.sub(r'\\begin\{abstract\}.*?\\end\{abstract\}',lambda _:r'\begin{abstract}'+'\n'+abstract+'\n'+r'\end{abstract}',body,count=1,flags=re.S)
    body=body.replace('preregistered but unmeasured rows','planned but unmeasured rows')
    body=body.replace('supportive-care and verification roles','specialty routing and safety verification')
    body=body.replace('The three completed predictors actually use only','The completed predictors use only')
    mapping=fr'''The public ATC-L4 dictionary is the official SafeDrug \texttt{{RXCUI2atc4.csv}} pinned to commit \texttt{{88ce5c3}}. Raw and dictionary NDCs are normalized to unambiguous 11-digit codes. GSN and exact-name fallbacks require at least 10 mapped observations and 98\% purity, using only the same 40,000 training admissions as the predictors. This corrects the v0.3 use of the larger training-patient pool. The new map covers 814,254 orders ({coverage:.3f}\%); 973,941 remain unmapped. IV coverage is only 19.518\%, compared with 81.874\% for PO/NG. All 240,310 saline-name proxy rows remain unmapped. These name matches are neither clinical indications nor fluid-purpose labels. Unmapped names and order fields remain local with unknown ingredient identifiers; no ATC or RxNorm code is invented. Smaller case-growth checkpoints must rebuild training-derived maps or use a fixed external dictionary.

'''
    body=re.sub(r'(?:The ATC-L4 map is|The public ATC-L4 dictionary is).*?(?=\\subsection\{Input timestamp)',lambda _:mapping,body,count=1,flags=re.S)
    body=body.replace('Laboratory records provide both charttime and storetime but are not used by the current predictors; both must be checked before expanding the input. A prespecified sensitivity analysis excluding fields with unverified availability remains required.',
      'A follow-up audit extracts selected same-admission blood laboratories charted within 24 hours before admission. Of 171,455 event-time-eligible rows, 2,127 were stored after admission and excluded. The remaining numeric, dual-timestamp-eligible records cover 33,393 admissions, with zero post-filter violations. Records lacking admission linkage are excluded. These laboratories are not added post hoc to the frozen method comparison. Input sensitivities use home medications alone and no patient text; neither establishes that the primary proxy is free of leakage.')
    methods=r'''\subsection{Methods, budgets and outcomes}
The executed protocol uses 40,000 training, 4,000 validation and 4,000 test admissions, with patient-disjoint membership and a fixed top-80 training ATC-L4 vocabulary. Baselines predict five classes. Recall retains all observed mapped target classes. All-case observed overlap is the primary engineering measure; absent or unmapped labels are not clinical negatives. A separate mapped-label-only sensitivity conditions on future label observability and is not an unbiased population endpoint. Three SGD seeds are retained without selecting the best test result.

The independent GAMENet adaptation loads the author's pinned GCN, GRU and readout modules. Complaint/acuity and home-medication tokens replace diagnosis/procedure codes, and the single-visit setting omits historical dynamic-memory reads. A real author-linked TWOSIDES source supplies class-level graph edges: 67 of 80 classes have source compound coverage, producing 1,959 undirected edges. Missing edges do not establish safety. Unlike the original side-effect subset, this graph aggregates all source pairs. Three seeds use Adam, BCE plus a fixed DDI penalty and five epochs, with validation-only checkpoint selection. Batched evaluation agrees with the original single-visit forward computation within $10^{-5}$. Validation was still improving at the budget boundary; this is a short adaptation experiment, not a converged reproduction.

The nested 50-case comparison holds local Qwen3-4B-Instruct-2507-4bit weights fixed (revision \texttt{50d4277}). Direct and ordinary repeat share the first response; three-case retrieval and bounded PRISMATIC share a retrieved first response. The harness preserves snapshot, retrieval, proposal, structural check, one revision and final-parse states, with explicit uncertainty and abstention. Repeat and harness each use two calls with 192 output tokens per call. Retrieval increases input tokens, so exact token-cost equality is not claimed. Invalid output is an empty prediction in the full denominator. No restricted text is sent to an external API.

\subsection{Complete-order contract}
Each order records drug name, ingredient ID, formulation, concentration, ATC class, dose/unit, route, frequency, duration, indication, patient evidence and uncertainty. Fluid orders add purpose, volume, rate and reassessment. Unknowns remain null; retrieved cases are not patient-specific evidence. Structural review checks missing fields, invalid numerics, duplicate ingredients, reference existence and missing fluid information, while clinical entailment remains unreviewed. Status is abstained, needs information or needs clinical review; no status authorizes administration. The class-level research graph is not an ingredient-level clinical DDI or renal rule base.

'''
    body=re.sub(r'\\subsection\{Methods, budgets and outcomes\}.*?(?=\\section\{Results\})',lambda _:methods,body,count=1,flags=re.S)
    table=r'''\begin{table*}[t]
\centering\small
\caption{\textbf{Method comparison on MIMIC-ED6-ATC4.} Within each panel, all rows use identical cases, observed labels and the same 80-class space. Panel A uses five outputs and reports three-seed means where marked; Panel B allows up to five outputs. F1 measures observed historical overlap, not clinical quality. GAMENet is an explicit text/single-visit adaptation, not faithful reproduction.}
\label{tab:main}
\begin{tabular}{@{}p{6.5cm}rrrrr@{}}
\toprule
Method & $N$ & Precision & Recall & F1 & Mean classes \\
\midrule
\multicolumn{6}{l}{\textbf{A. Full development sample}} \\
'''
    for name,metric,sd in rows:
        name=name.replace('(3 seeds)','(3-seed mean)')
        table+=f"{name} & 4,000 & {metric['precision_at_5']:.4f} & {metric['micro_recall_at_5']:.4f} & {metric['micro_f1_at_5']:.4f} & 5.00 \\\\\n"
    table+=r'\midrule'+'\n'+r'\multicolumn{6}{l}{\textbf{B. Nested same-case local-LLM pilot}} \\'+'\n'
    for key,name in [('prevalence','Training prevalence'),('case_retrieval','30-neighbor voting'),('direct_sgd','TF-IDF/SGD (seed 42)')]:
        r=b['same_50_case_baselines'][key]
        table+=f"{name} & 50 & {r['precision_at_5']:.4f} & {r['micro_recall_at_5']:.4f} & {r['micro_f1_at_5']:.4f} & 5.00 \\\\\n"
    r=g['same_50_case_seed42']
    table+=f"GAMENet text adaptation (seed 42) & 50 & {r['precision_at_5']:.4f} & {r['micro_recall_at_5']:.4f} & {r['micro_f1_at_5']:.4f} & 5.00 \\\\\n"
    for key,name in [('direct','Local LLM direct'),('ordinary_repeat','Local LLM ordinary repeat'),('case_retrieval','Local LLM with case retrieval'),('bounded_harness','PRISMATIC bounded harness')]:
        r=l['metrics'][key]
        table+=f"{name} & 50 & {r['observed_precision']:.4f} & {r['observed_recall']:.4f} & {r['observed_micro_f1']:.4f} & {r['mean_predicted_classes']:.2f} \\\\\n"
    table+=r'''\midrule
SafeDrug, compatible ATC-L4 reproduction & -- & -- & -- & -- & -- \\
SafeRx-Agent, compatible reproduction & -- & -- & -- & -- & -- \\
Clinically complete PRISMATIC harness & -- & -- & -- & -- & -- \\
\bottomrule
\end{tabular}
\end{table*}

Table~\ref{tab:main} reports methods rather than different foundation models. SGD's three-seed mean F1 is 0.3864 (sample SD 0.0007); GAMENet adaptation reaches 0.3436 (SD 0.0022). The seed-42 SGD minus retrieval difference is 0.05888 (patient-bootstrap 95\% interval [0.05325, 0.06460], 3,115 patients, 2,000 draws). Different representations and incomplete mapping prevent a clinical interpretation. The mapped-label-only subset produces higher overlap scores but changes the estimand.

In the local-LLM panel, bounded review lowers F1 relative to retrieval by 0.07886 (95\% patient-bootstrap interval [$-0.13372,-0.02355$]) and relative to ordinary repeat by 0.03634 (interval [$-0.11168,0.03931$]). Output validity is 94\%, 94\%, 90\% and 100\% for direct, repeat, retrieval and harness, respectively. The harness returns an empty set on 50\% of cases. Its higher precision (0.3511) and lower recall (0.1480) show a strong abstention trade-off, not demonstrated safety improvement. Repeat and harness consume 199,348 and 234,313 input tokens and approximately 286.44 and 324.24 accumulated arm seconds. Shared first-call usage is included in each arm.

\subsection{Input sensitivity and order generation}
Removing complaint/acuity reduces retrieval F1 from 0.3281 to 0.3139 and three-seed mean SGD F1 from 0.3864 to 0.3695. With no patient text, retrieval reaches 0.2653 and SGD mean 0.2772. The latter control retains seed variation; a seed with poorer optimization is not discarded. This quantifies input dependence without verifying the availability of untimestamped fields.

On ten fixed development cases, one complete-order draft and one retrieval-informed revision each yield only 4/10 raw schema-valid responses. Wrong ATC granularity is the main failure; one response per arm is truncated. A separate normalization revision retains unresolved code strings in uncertainty and converts the ATC field to null, yielding 9/10 structurally parseable bundles in both arms. This is not a rise in correct model generation from 40\% to 90\%. Each arm contains 13 proposed orders in valid normalized bundles; the revised arm has 11 fluid-information findings and one missing patient-evidence reference. Clinical correctness is unreviewed. Seven contract tests cover unknown preservation, wrong code granularity, invalid doses, duplicate ingredients, invented evidence and abstention semantics.

'''
    body=re.sub(r'(\\section\{Results\}\n).*?(?=\\subsection\{Public secondary)',lambda match:match.group(1)+table,body,count=1,flags=re.S)
    body=body.replace('200 held-out test admissions','200 development-test admissions')
    nexttext=r'''\section{Remaining experiments and limitations}
The data and order protocol is now executable, with unknown availability and mapping explicitly retained. It does not manufacture missing timestamps or clinical truth. SafeDrug's bundled molecular keys are ATC-L3; a validated ATC-L4 molecule/substructure map in the common vocabulary is still missing. SafeRx-Agent additionally requires a compatible current-diagnosis/procedure adapter, specialty routing and versioned indication/contraindication knowledge. Neither is assigned a borrowed score. The available TWOSIDES class graph does not close the ingredient-level clinical knowledge gap.

The bounded harness has executed retrieval and revision but remains incomplete clinically. Next steps are validation-set repair of order encoding/truncation and over-abstention; compatible SafeDrug/SafeRx implementations; complete-order blinded review by the two available reviewers; and controlled reviewed-case growth without test feedback. The repeatedly inspected development test must not be relabeled as unseen confirmation. A new confirmatory patient set, clinical power analysis, renal/fluid evidence extraction, full public secondary arms and live MedAgentBench FHIR evaluation remain required. Negative results and original raw outputs are retained across versions.

Restricted patient inputs, predictions, training weights and review packets remain local. Only code, protocols and aggregate audits enter the repository. No restricted MIMIC text was sent to OpenRouter. Historical orders are observational behavior, not expert truth; no current result warrants clinical deployment.

'''
    body=re.sub(r'\\section\{(?:Next experimental gates and limitations|Remaining experiments and limitations)\}.*?(?=\\begin\{thebibliography\})',lambda _:nexttext,body,count=1,flags=re.S)
    path.write_text(prefix+'% PRISMATIC MANUSCRIPT START'+body)
    print(str(path))

if __name__=='__main__':run()
