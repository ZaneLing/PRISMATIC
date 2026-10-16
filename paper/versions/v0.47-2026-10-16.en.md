# RxRSIAgent: failure cases, task boundaries, and actual MIMIC-IV progress

Updated 16 October 2026. New results concern researcher-authored tool repairs on development data and a local recount of frozen MIMIC predictions. The main-table actor is unchanged.

## 1. What the three public benchmarks measure

| Dataset | Task | Evaluated size | Endpoint |
|---|---|---:|---|
| RxSafeBench | Three-option medication choice after simulated contraindication/interaction consultations | Local test988; original paper2,443 scenarios | Single-choice accuracy |
| RxQA | Formulary-grounded medication reasoning, four options | All300 public OpenFDA questions; another300 BNF questions are not released | Single-choice accuracy |
| MedPIC-Bench | Patient-conditioned medication decisions and counterfactuals; single/multiple answers |467, including108 multiple-answer questions;35 strict same-option pairs locally identified | Exact answer-set accuracy and both-members-correct |

These are choice tasks. The current49.70%,65.33%,58.67% results are not complete-prescription coverage. For open medication sets P and G, report recall |P∩G|/|G| together with precision |P∩G|/|P|, F1, Jaccard, misses, extras, prescription size and empty outputs. Increasing recall alone can reward excessive prescribing. Extras relative to a recorded reference are not automatically clinically inappropriate.

Full orders require joint drug/route/dose/unit/frequency matching and missing-field denominators. Drug recall, source-row mapping coverage and complete-GT-field coverage are different quantities. Clinical treatment-goal coverage and safety require additional reliable rules or annotation.

## 2. MIMIC-IV was evaluated, but not with the current QA actor

The completed time-controlled task uses MIMIC-IV3.1 admission+6h and predicts newly entered/changed orders over the next6h. Inputs exclude future results and untimed discharge diagnoses. Prescriptions are linked to provider/pharmacy entry times. Patient-disjoint splits contain40,000 training,2,000 proposal,2,000 guard and1,082 test admissions (1,024 test patients). The initial128 normalized-name vocabulary is fixed; OOV reference drugs remain in recall denominators.

We locally recounted saved predictions for three methods and three seeds; every drug/core4 F1 agrees with its original report. No new model inference or restricted-data API call was performed.

| Historical method | Drug precision % | GT drug recall % | Drug F1 % | Core-4 F1 % | Order-5 F1 % |
|---|---:|---:|---:|---:|---:|
| Case retrieval + order tool | 16.14 | 15.08 | 15.59 | 9.52 | 6.41 |
| Earlier supervised artifact agent | 15.85 | 24.16 | 19.14 | 11.53 | 8.27 |
| Word/character ensemble + order tool | 17.56 | 23.53 | 20.10 | 12.07 | 8.51 |

Means are across three seeds. Core4 uses drug, route, dose and unit. Order5 additionally requires frequency; it is a new post hoc descriptive endpoint, not a selection criterion. Only60.20% of reference order rows contain all five fields, and exact-tuple scoring uses complete observed tuples. The earlier agent raises recall but loses precision/F1 to the ensemble. It is a supervised artifact-learning pipeline, not the current LLM RxRSIAgent; its scores must not be relabeled as current-method results.

A separate retrospective completed-visit ATC-L4 task has7,115 training patients/18,429 training visits and271 classes, with890 patients/2,422 visits reserved for test. It uses completed-visit diagnosis/procedure codes, not prospective admission-time observations. ARMR/GAMENet/SafeDrug and rule-memory work has audited development results, but its full final-test comparison remains unfinished. Public NDC mapping covers only27.23% of selected prescription rows; the molecular shared panel has219 classes. Neither is complete prescription GT.

The outstanding prescribing claim therefore needs the current RxRSIAgent evaluated on an explicit decision-time MIMIC order task, against shared-split, shared-space, shared-input comparators. Public QA should remain complementary mechanism evidence.

## 3. Five inspectable training cases

All examples below were used for development. A dataset answer is a reference, not an adjudication that every alternative is clinically unacceptable.

1. **Product scope (e7a30d739ee5b9be).** Reference A=ferrous sulfate; original C=ferrous fumarate. The old retriever selected a same-ingredient homeopathic product whose indication concerned hot flashes. Its reader discarded the `spl_unclassified_section` containing the homeopathic classification. Full metadata and explicit product-scope filtering restore A. OTC status alone must not exclude a product, and an openFDA record does not establish approval.
2. **Regimen and evidence-window scope (3c3087307869…).** Reference C=isosorbide dinitrate/hydralazine; original B=amlodipine/valsartan. The question describes hypertension and left-ventricular heart failure in an African American patient. Component-only retrieval omitted combination evidence. Adding the combination label still failed because character-window truncation lost its population qualifier. Preserving the full sentence changes this example to C. The label's adjunct-to-standard-therapy condition remains relevant; demographic membership alone is not a sufficient prescribing rule.
3. **Unsupported patient inference (20084f0b868433c8).** Reference A=Injectafer; original C=ferrous sulfate. The original assessment inferred dialysis from recurrent transfusions and used that invented condition to exclude A. The product-tool arm selects A, whereas the added-obligation arm still selects C. Requesting verification does not guarantee removal of the premise; exact quotation checks do not verify full clinical entailment.
4. **Unresolved treatment phase (c4e678277e78…).** The question asks about an intervention during a previous admission with active infection that could prevent subsequent myocardial injury. Reference D=antitoxin-targeting immunoglobulin; original A=toxoid vaccination. All three candidates remain A. CDC guidance distinguishes acute respiratory diphtheria treatment from immunization. Label-only retrieval and generic self-reflection do not resolve this timing error.
5. **Absence-of-warning shortcut (1dfc1ce34019…).** In a28-week pregnancy UTI question, reference B=nitrofurantoin versus original D=cephalexin. The old explanation recognized that a term-pregnancy restriction did not apply, yet preferred the other drug partly because its excerpts lacked a pregnancy contraindication. Product retrieval changes the answer to B. This is a reference-agreement observation, not proof that every such patient has one uniquely valid treatment.

| Case ID prefix | GT | Before | Product tools | + obligations | + whole sentences |
|---|---|---|---|---|---|
| e7a30d739ee5 | A | C | A | A | A |
| 20084f0b8684 | A | C | A | C | A |
| c4e678277e78 | D | A | A | A | A |
| 1dfc1ce34019 | B | D | B | B | B |
| 3c3087307869 | C | B | B | B | C |

## 4. Recurring patterns and executed repairs

Across all400 prior training traces,131 were wrong. The model's root hypotheses placed84 at final selection,32 at product selection,8 at input interpretation and7 at applicability. These are hypotheses, not causal adjudications. Structural checks find8 cases with shared ingredients across options (2 wrong), and10 with multi-component options requiring regimen retrieval (2 wrong). Full-source homeopathic matches are a lower bound because only newly requested sources can recover discarded metadata. These mechanisms explain only part of the error population.

The repair bundle reads full metadata, excludes explicitly homeopathic evidence from conventional-product matching, resolves combination ingredients, retains shared-component option roles and balances evidence across alternatives. A second candidate adds patient/source-bound decision obligations; a further repair expands source windows to whole sentences without silently dropping their qualifications. Support quotes prove provenance, not semantic entailment. No drug-to-answer lookup or learned drug-name scorer is introduced.

| Candidate | Train diagnostic | RxSafe proposal | MedQA proposal | RxSafe guard | MedQA guard |
|---|---:|---:|---:|---:|---:|
| Product-scope tools | 62/85 (7 / 0) | 98/190 (13 / 14) | 100/120 (2 / 5) | — | — |
| Tools + decision obligations | 57/85 (6 / 4) | 97/190 (14 / 16) | 100/120 (2 / 5) | — | — |
| Tools + whole sentences | 60/85 (6 / 1) | 101/190 (17 / 15) | 100/120 (3 / 6) | — | — |
| Scoped product/sentence repair | 273/400 (5 / 1; routed 16) | 98/190 (1 / 2; routed 4) | 102/120 (0 / 1; routed 12) | — | — |

Parentheses denote fixes/regressions versus the frozen actor. Baselines: train55/85 for the first three arms; the scoped arm separately uses all400 training cases, baseline269/400. Proposal baselines are99/190 RxSafe and103/120 MedQA; guard104/197 and102/120. The85-case diagnostic contains80 hash-selected training cases plus5 selected failures. It is not an independent random test, and its score is not directly comparable with the400-case scope analysis.

The fourth candidate routes to the sentence-preserving tool only when original source metadata explicitly classifies a selected label as homeopathic, or the original plan identifies a joint-regimen option. Otherwise it preserves the original evidence and requests. Routing reads no reference answer or correctness outcome. It was designed after observing the global-repair development scores; this exposure is disclosed. Unknown product classifications do not activate it, so detection is incomplete.

Before new inference, the gate required no per-task proposal regression, strictly positive pooled gain, and no invalid-output increase; a selected candidate then faces separate per-task guard non-regression. Both are historically reused development cohorts. Gate outcomes: {"45": false, "46": false, "47": false}. Failed proposal candidates do not run guard. The current main actor and test scores are not replaced by these development findings.

All arms reuse the same initial planning request and allow3×1,536 output tokens and18,000 source characters. Source-query volume and actual input costs differ. These are researcher-authored failure-directed repairs, not successful autonomous RSI. A real evolution claim still requires retained executable changes and benefits on an independent task, beyond reflection-ledger growth.

## 5. Deliverables

Released: code, five paired case studies, 1185 global-repair prediction rows plus710 routed prediction rows (cases repeat across conditions), verification of 12279 global-repair source spans, and a local three-seed MIMIC recount. Incremental successful-response ledger cost: USD3.1920. Patient/source prose and restricted individual records remain local. Main-table scores retain their frozen provenance.

The full-source cache has800 requests with statuses {"http_404": 382, "retrieved": 418}. Requests beyond the800-query cap remain unavailable. Source failures and caps may limit outcomes. The global repair also changes source windows/ranking and metadata jointly; its aggregate effect is not an isolated causal estimate of a single patch.

The next substantive prescribing work is to connect the current agent to the recorded-time MIMIC order protocol, improve identity/candidate coverage and observable order fields, and compare with strong supervised, retrieval and medical-agent controls. QA accuracy alone cannot establish complete prescribing.

## Sources

- [RxSafeBench, original three-option protocol](https://arxiv.org/html/2511.04328v1)
- [RxQA author repository: 300 released OpenFDA questions; BNF unavailable](https://github.com/Google-Health/rxqa)
- [MedPIC-Bench paper](https://arxiv.org/abs/2608.03028)
- [MIMIC-IV prescriptions fields](https://mimic.mit.edu/docs/iv/modules/hosp/prescriptions.html)
- [FDA: homeopathic products](https://www.fda.gov/drugs/information-drug-class/homeopathic-products)
- [BiDil combination label, including adjunct-therapy qualification](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=e1e63cd5-d1e4-4af5-bad5-1ad41ea46b00)
- [CDC diphtheria clinical guidance](https://www.cdc.gov/diphtheria/hcp/clinical-guidance/index.html)
