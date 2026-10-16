# RxRSIAgent: comparison coverage, prescribing gaps and research claims

Updated 2026-10-16. Target: ACL 2027. This is a living assessment; earlier experiments remain archived.

[中文](RESEARCH_ASSESSMENT.zh.md) · [Current results](CURRENT_RESULTS.en.md) · [Cumulative cost](TOTAL_COST.en.md) · [Failure cases](TASKS_CASES_AND_MIMIC.en.md)

## 1. Research objective and deployment motivation

**Generate prescriptions that better match patient needs and recorded clinician actions using information available at the decision time, then turn reference discrepancies into scoped, persistent improvements that survive counterexamples and transfer to new patients.** Accuracy, completeness, safety, edit burden and learning gains require separate endpoints.

Utah's official registry distinguishes Doctronic maintenance renewals, still requiring practitioner authorization for every request in Phase 1, from Nolla Health's adult topical-acne pilot, whose term started on **October 5, 2026** and permits specified initial prescriptions and refills with initial two-physician review. These bounded pilots motivate evaluation; they do not establish unrestricted autonomous prescribing authority or validate our system. Inpatient new-order prediction is not an evaluation of these outpatient services. [Official registry](https://commerce.utah.gov/ai/regulatory-relief-4/authorized-pilots/)

Human alignment means agreement with observed actions, coverage of independently established clinical needs, and appropriate responses to changed patient conditions. Historical GT reveals clinician actions, not the complete reasoning process or a unique clinically acceptable regimen. Automatic reference metrics need no clinician approval; claims about clinical appropriateness need additional adjudicated evidence. Our two-reviewer assessment remains pending.

## 2. Current scores: distinguish method, task and split

| Task | Available result | Boundary |
|---|---|---|
| Local RxSafe988 | **RxRSIAgent 491/988 (49.70%)** | Three-choice accuracy; GRASP 495/988 and supervised control 556/988 under the same output cap |
| Public RxQA OpenFDA300 | **196/300 (65.33%)** | Four-choice accuracy; MedAgents 200/300 at the matched cap and 208/300 at its higher allowance |
| MedPIC467 | **274/467 (58.67%)** | Exact answer sets; both answers correct in only 3/35 strict counterfactual pairs |
| Decision-time MIMIC-IV orders | **Current LLM actor: not yet evaluated completely** | Do not relabel historical supervised pipelines as current RxRSIAgent |
| Historical MIMIC order pipeline | Drug P/R/F1 **15.85/24.16/19.14%**; Core4 F1 **11.53%** | Three seeds; stronger text ensemble drug F1 20.10% |
| Retrospective MIMIC ATC-L4 visit sets | Earlier rule agent **61.26%**, logistic regression 61.15%, ARMR 60.86%, GAMENet 52.71% | Guard patient-averaged F1, 271 classes; final test incomplete; not the current LLM actor |

The rule-agent gain over logistic regression is only 0.109 percentage points and does not exceed all mechanism controls. These numbers do not establish superiority on both public tasks, successful RSI, or a complete prescription capability. [Main results](CURRENT_RESULTS.en.md), [common visit-set development comparison](../upgrade_v27/DEVELOPMENT_METHODS.en.md).

## 3. New empirical decomposition of the low MIMIC score

We recount three seeds of frozen historical predictions on 1,082 test admissions. No fitting, inference, API call or patient-level export occurs. This is a **post hoc descriptive test analysis**, not selection evidence for a new method. [Executable audit](audit_prescription_gap.py), [aggregate data](prescription_gap_audit.json).

| Diagnostic | Historical artifact pipeline |
|---|---:|
| Predicted / reference distinct drugs per admission | 5.35 / 3.51 |
| Reference omissions / reference-relative extras per admission | 2.66 / 4.51 |
| False negatives whose drug is already in the vocabulary | **75.12%** |
| Recall for targets present in prior available orders | 39.13% |
| Recall for targets absent from prior available orders | **20.87%** |
| Core4 reference-tuple recall conditional on the drug being predicted | **55.56%** |
| Admissions with no available blood-laboratory context | 584/1,082 |
| Empty output rate | 2.74% |

Extra predictions are not automatically clinically inappropriate. In-vocabulary misses identify a selection gap but do not prove its clinical cause. More predicted drugs alone cannot fix the simultaneous low precision and recall. Even correct drug selection leaves substantial route/dose/unit errors.

Earlier proposal-only diagnostics show 80.80% vocabulary coverage and 75.36% joint-template coverage; perfect reference-informed drug selection has a support ceiling of 89.25% F1. This **oracle is not a model result**. The remaining gap is too large to attribute to vocabulary alone. Inputs contain age bands, sex, available prior orders and blood tests, but no complete time-available clinical problem list or treatment plan. The causal effect of that limited context remains untested. A typed-numeric-state pilot improves guard F1 by 0.514 pp, with an interval crossing zero. [Capacity audit](../upgrade_v21/results/development_capacity_audit.json), [numeric pilot](../upgrade_v22/RESULTS.en.md).

Prioritize time-available state and validated ingredient/form mapping; then measure loss at candidate generation, selection, joint-order construction and final verification separately. Longer reflection and larger memories have no demonstrated guarantee of improvement.

## 4. External comparisons that cover the relevant families

This list covers major families and direct competitors, not every published paper. New candidates below have no local score. Original-paper results may appear in a clearly labeled literature table, never as our same-protocol measurements.

| Method family | Purpose / original task | Local status and primary source |
|---|---|---|
| Prevalence, last visit, kNN, logistic regression, text ensemble | Priors, historical copying, retrieval and supervised selection | Already executed in the corresponding local tasks |
| GAMENet / SafeDrug | Historical memory, medication graphs / molecular structure and interactions; MIMIC sets | Audited author-core development runs; [GAMENet](https://github.com/sjy1203/GAMENet), [SafeDrug](https://github.com/ycq091044/SafeDrug) |
| ARMR (2025) | Changing old/new treatment requirements; MIMIC-III/IV | Three full-space seeds complete; [paper](https://www.ijcai.org/proceedings/2025/0871.pdf) |
| MICRON / COGNet | Medication change / copy-or-predict generation | Author code available, unrun; [MICRON](https://github.com/ycq091044/MICRON), [COGNet](https://github.com/BarryRun/COGNet) |
| MoleRec / RAREMed | Molecular substructure combinations / rare and common disease recommendation | Author code available, unrun; [MoleRec](https://github.com/yangnianzu0515/MoleRec), [RAREMed](https://github.com/zzhUSTC2016/RAREMed) |
| LEAP / RETAIN | Sequential treatment generation / historical attention | Classical coverage candidates; RETAIN requires task adaptation; [LEAP](https://www.kdd.org/kdd2017/papers/view/leap-learning-to-prescribe-effective-and-safe-treatment-combinations-for-mu), [RETAIN](https://arxiv.org/abs/1608.05745) |
| **FLAME** | List-wise LLM medication generation with step-wise RL; MIMIC-III, transfer to MIMIC-IV/eICU | Priority prescription comparator; author training code exists; [paper](https://arxiv.org/html/2505.20218v1), [code](https://github.com/cxfann/Flame) |
| LAMO | Fine-grained alignment and overprescription | Author code linked; discharge-note-derived inputs require a decision-time availability audit; [paper](https://arxiv.org/html/2503.03687v2), [code](https://github.com/zzhUSTC2016/LAMO); distinguish from CIKM LAMRec |
| HADRec | Hierarchical medication recommendation | Released hierarchy inconsistency requires audit; [existing source audit](LATEST_METHODS.en.md) |
| **SafeRx-Agent** | Specialty/supportive-care experts, evidence and safety verification; MIMIC-III/IV ATC-L4 | Direct competitor; paper algorithms/prompts available, no compatible runnable official package located; label an independent implementation explicitly; [paper](https://arxiv.org/html/2605.29146v1) |
| **RareAgents** | Tool-supported multidisciplinary diagnosis/treatment; MIMIC-IV-Ext-Rare medication sets | Author repository located; executable completeness not established; [paper](https://arxiv.org/abs/2412.12475), [repository](https://github.com/chenxz1111/RareAgents) |
| MedAgents / MDAgents | Expert consensus / adaptive collaboration; medical reasoning QA | Local task adaptations already evaluated; [MedAgents](https://aclanthology.org/2024.findings-acl.33/), [MDAgents](https://arxiv.org/abs/2404.15155) |
| **GRASP / SkeMex** | Regression-aware skill acceptance / utility-based skill retrieval and governance | GRASP adapted; SkeMex implementation newly verified, unrun; [GRASP](https://arxiv.org/abs/2605.29668), [SkeMex v4](https://arxiv.org/html/2606.09365v4), [SkeMex code](https://github.com/manglu097/SkeMex) |
| ReAct with identical tools, Self-Refine, Reflexion | Tool interaction, within-case revision, persistent verbal feedback | Required mechanism controls; [Self-Refine](https://arxiv.org/abs/2303.17651), [Reflexion](https://openreview.net/forum?id=vAElhFcKW6) |

AgentRx evaluates mortality and length of stay; its name does not make AUROC a prescription comparator. [Original study](https://arxiv.org/html/2605.10286v1).

Use three tables: common MIMIC prescription sets/orders, secondary public QA, and evolution methods on a fixed underlying agent. Label author implementation, independent implementation and task adaptation. Match or report data exposure, feedback, proposal attempts, evidence/tools, input/output tokens, calls, cost and latency. An output cap alone is not equal compute; preserve author-recommended-budget results separately.

## 5. From failures to falsifiable workflow mechanisms

These are **workflow-level hypotheses**, not neural-circuit discoveries or established first-in-literature findings. Patient-condition overgeneralization is already studied by MedPIC, and memory regressions by GRASP/SkeMex. [MedPIC](https://arxiv.org/html/2608.03028v1).

| Hypothesis | Existing observation | Controlled intervention and endpoint |
|---|---|---|
| Evidence loses a necessary applicability condition | Same-ingredient homeopathic source; truncated population condition in combination label | Original versus condition-complete versus equal-length irrelevant context; condition retention and independent fixes/regressions |
| Genuine quotations coexist with unsupported patient premises | Dialysis inferred from transfusions; quote contract fails to prevent it | Known/unknown/negated premise checks; condition-flip and invariant pairs |
| Treatment-phase knowledge is not supplied by drug labels | Active infection treatment confused with pre-exposure vaccination | Change only treatment phase; compare phase-specific guideline retrieval with labels under matched access |
| Expansion and review can both miss appropriate treatment | Simultaneous low recall/precision; some QA repairs regress | Freeze candidate pool, ablate selection and critique separately; missing GT candidates, removed TPs and retained FPs |
| Memory utility depends on executor and context | Gemini fixed grounding 54.45%, transferred skills 51.62% | Frozen cross-model transfer; equal-length placebo memory and tool-specific skills |
| Correct medication identity does not ensure a complete order | Conditional Core4 recall only 55.56% | Generative fields versus structured verification; joint/field correctness, unknown and abstention coverage |

A repaired example proposes a mechanism. Establish it using predeclared error definitions, recurring training cases, successful counterexamples, single-component interventions, intermediate-state changes and independent matched cases. Test drug/disease/executor transfer. The recent routed repair changes training 269/400 to 273/400 but loses on both proposal tasks; it is not an accepted RSI update. The 112 earlier proposal attempts retain no update. Root-log growth is not capability growth.

## 6. Backbone portability and longitudinal evaluation

Preselect at least three model families spanning capabilities, and compare direct, fixed tools, the strongest applicable external agent and RxRSIAgent on identical cases and resources. Distinguish **frozen A-to-B/C skill transfer** from **separate learning for each backbone**. Existing Gemini negative transfer must remain visible; it does not support universal improvement.

For the next registered study, consider 0/100/200/400/800/1,600 unique cases and three case-order seeds. These are proposed, not completed, checkpoints. Record proposed and retained module diffs, activation, corrections, regressions and costs. Controls include frozen components, equal-length memory, shuffled feedback, ordinary supervised calibration and equal-feedback search. Freeze all states before independent evaluation; do not pick the best test checkpoint. A development-selected acceptance curve is optimistically biased.

Use [clinical endpoints](CLINICAL_EVALUATION.en.md): treatment-goal coverage, major-error case rate, jointly correct orders, omissions/extras, constraints, applicable evidence, monitoring and clinician edit burden. Add continue/start/change/stop action agreement and condition-response tests. Unknown information stays unknown, with assessment coverage. Full drug-set/order endpoints remain separate from option accuracy.

## 7. Disease scope and task scope

| Dataset | Population / disease scope | Actual endpoint |
|---|---|---|
| RxSafeBench | Simulated consultations across ten specialty categories, possibly with comorbidities/concomitant drugs | Three-choice medication safety; not full multimorbidity regimen generation |
| Public RxQA OpenFDA | Broad drug-information reasoning, not a single-disease cohort | Four-choice questions; 300 released, unreleased BNF300 untested |
| MedPIC | Conditional safety rules involving age, pregnancy, renal state and other patient information | Single/multiple-answer agreement and counterfactual response; multiple answers do not establish multimorbidity |
| MIMIC-IV | Heterogeneous hospital/ICU population, including comorbidity and polypharmacy | Future new/changed orders in one protocol; completed-visit medication sets in another |

A separate historical eICU study also exists: a heterogeneous multicenter ICU population, 8,005 test stays from 16 held-out hospitals, native HICL order targets. It trains within eICU and is not zero-shot MIMIC transfer or the current LLM actor. [Executed historical results](../upgrade_v25/RESULTS.en.md).

[RxSafeBench](https://arxiv.org/html/2511.04328v1), [RxQA](https://github.com/Google-Health/rxqa), [MedPIC](https://arxiv.org/html/2608.03028v1), [MIMIC prescription documentation](https://mimic.mit.edu/docs/iv/modules/hosp/prescriptions.html).

Do not claim every MIMIC admission has multiple diseases. Diagnosis-code counts are not disease counts. Future stratification should distinguish validated multimorbidity, rare/common conditions, medication burden and new versus continuing treatment. Retrospective diagnoses used for descriptive stratification must not enter decision-time model inputs.

## 8. Completed delivery and next execution order

Completed here: physical-response cost audit, three-seed historical MIMIC error decomposition, external method/code verification, official Utah scope check and manuscript/bilingual reporting. No new model superiority result or actor replacement is claimed.

Next: complete a compliant local decision-time prescription evaluation for the current LLM actor; add SafeRx-Agent/FLAME prescription and SkeMex evolution comparisons; validate condition preservation, premise satisfaction and joint-order interventions on training/development data; then freeze and evaluate independent cases, backbone transfer and clinician-rated needs. Preserve failures and unchanged states rather than changing test rules to manufacture a win.
