# PRISMATIC 2 experiment plan — 2026-10-14

## Research position

Primary task: at a clearly defined decision time, review a clinician's draft
medication order against the information then available. Return an auditable
finding, a bounded local revision proposal, a request for missing information,
or an explicit abstention. A clinician remains the final decision maker.

The old paper's full-regimen generation and exact historical match become
secondary tasks. The core claims to test are: (H1) independent executable
checks reduce serious errors under matched model and tool budgets; (H2) local
repair reduces irrelevant changes compared with whole-regimen regeneration;
(H3) versioned offline updates improve later cases without safety regression.
The user's additional H4 is explicit: as more adjudicated cases arrive, the
system should improve its recognition of human supportive-order patterns,
including IV saline, antiemetics, and bowel regimens. H4 must be measured on
frozen patient-disjoint cases at multiple training sizes, and separated from
the distinct question of whether those orders were appropriate.

## Completed preliminary work

| Item | 6-hour target | 24-hour sensitivity target |
| --- | ---: | ---: |
| Admissions with at least one oral GSN target | 125,853 | 150,780 |
| Distinct patients | 71,736 | 83,058 |
| Median target codes per admission | 5 | 8 |
| Tested temporal or duplicate-admission violations | 0 | 0 |
| Top-64 label coverage on sampled test cases | 66.3% | 62.5% |
| Popularity macro recall@5, sampled test | 29.95% | 23.52% |
| TF-IDF + SGD macro recall@5, sampled test | 35.47% | 29.90% |

The 6-hour sampled test uses 4,000 admissions from 3,030 patients; the 24-hour
sampled test uses 4,000 admissions from 3,062 patients. The samples are
separately drawn from different eligible cohorts, so the two columns are a
sensitivity description, not a paired treatment effect. The best 6-hour model
was selected on 4,000 validation admissions. Its patient-bootstrap 95% interval
for macro recall@5 improvement over popularity is +4.90 to +6.24 percentage
points on the exploratory test set.

The source timing audit excluded 137,060 medication-reconciliation rows charted
after admission. Zero recorded temporal violations reflects the checks we can
perform on timestamped rows; ED triage has no per-row chart time in this source.

The local 4B model completed 32 held-out cases in 53 seconds, returned valid
structured codes in 31/32, and achieved 22.56% macro recall@5. On those same
32 cases, popularity achieved 31.20% and the TF-IDF + SGD model 34.02%.
This tiny, closed-list smoke test is not a model ranking or a safety result.

## Task and model matrix

| Task | Input and output | Initial models/comparators | Main measures |
| --- | --- | --- | --- |
| T0: data feasibility (done) | Admission snapshot -> later oral GSN set | Popularity; TF-IDF+NB; TF-IDF+SGD; local 4B smoke test | Macro/micro recall@5, precision@5, vocabulary coverage, timestamp integrity |
| T0b: case-count learning curve (done, pilot) | Admission snapshot -> saline IV / ondansetron / bowel-regimen order flags | Prevalence; cosine case memory; incremental logistic SGD at 250/1k/4k/16k/40k cases | Average precision by label, macro AP, AUROC, Brier, patient-bootstrap change |
| T1: draft-order risk review | Snapshot plus draft order -> structured findings with evidence | Clinician draft alone; rule-only CDS; single LLM; LLM+evidence; LLM+independent verifier; full harness | Expert-adjudicated serious miss rate, sensitivity, false alerts, new errors |
| T2: local repair | Draft plus finding -> one bounded change, request for data, or abstention | Whole-regimen regenerate; one-shot edit; risk-routed local repair | Resolved severe errors, unintended changes, completion, time and cost |
| T3: information acquisition | Incomplete snapshot -> requested lab/history item or abstention | Static checklist; single LLM; harness | Clinically necessary information recall, unnecessary requests, safety of decisions under missing data |
| T4: offline self-evolution | Approved feedback -> candidate policy version | Fixed policy; old DSWA; memory update; gated update | Later-period improvement, safety regressions, stability, review effort |
| T5: public external tests (pilot done) | RxSafeBench three-choice scenarios and RxQA OpenFDA four-choice questions | Three current OpenRouter models under the same prompts | Accuracy, abstention/invalid response, cost; per-task breakdown |

The initial 4B model is a local interface probe. A real T1/T2 comparison needs
at least one stronger local model and a matched tool/prompt budget. A cloud
model may be added only after its MIMIC data-handling path is documented and
approved under the applicable data-use terms. Model versions, prompts,
temperature, retrieval corpus, rule-base version, and exact input snapshot
must be frozen for every comparison.
Public RxSafeBench and RxQA are separate tasks and must never be compared by
subtracting their raw accuracy from MIMIC order-set F1/AP. Restricted MIMIC
records are not sent through OpenRouter.

## Data and labels needed next

1. Define the exact clinical workflow: order selection, order signing, or
   retrospective chart review. Time `t` must be the moment the draft order
   exists, not an arbitrary admission timestamp.
2. Build an order-level time-travel dataset from MIMIC-IV `poe`, `pharmacy`,
   `prescriptions`, `emar`, and labs with **availability time** (`storetime`
   where relevant), not only specimen or order time. Add prior/home meds,
   allergies when a reliable source exists, and explicit missingness.
3. Independently adjudicate a pilot set of at least 200 enriched cases for
   severe DDI, allergy, renal dosing, dose/route/frequency, therapeutic
   duplication, and important omission. Two clinicians or pharmacists should
   review uncertain cases and resolve disagreements. Final sample size should
   follow the observed event rate and a prespecified precision target.
4. Make a versioned knowledge set with normalized ingredient/product codes,
   rule severity, source, effective date, and evidence excerpt. RxNorm is for
   normalization; it does not itself provide a current DDI checking API.
5. Freeze patient-disjoint development and test sets. Add a later-period or
   external-site test where valid chronology and permissions permit it. Keep
   all patient-level records and derived prompts in restricted storage.

## Evaluation protocol

- Primary endpoint: expert-adjudicated serious medication errors missed per
  100 cases, with paired uncertainty intervals. Prespecify a maximum
  acceptable new-error rate for any system-proposed revision.
- Secondary: alert sensitivity and positive predictive value by risk class,
  unsupported findings, abstention appropriateness, corrected-error fraction,
  unintended edits, clinician review time, tokens, tool calls, and cost.
- Report results by multimorbidity, number of drugs, renal-function
  availability, missingness, age band, and hospital/site where feasible.
- Use matched cases and matched generation budgets. Use patient-clustered
  bootstrap or appropriate paired models; avoid treating repeated admissions
  from one patient as independent. Rare severe events need event-aware power
  planning and careful upper confidence bounds.
- Publish an error taxonomy and blinded adjudication protocol. Historical
  overlap, exact match, and zero-interaction rate alone cannot validate safety.

## Required ablations and stress tests

- Remove the independent verifier, evidence retrieval, structured order schema,
  risk router, abstention, or bounded repair one at a time.
- Replace local edit with full regeneration under the same inference budget.
- Compare fixed weights, old DSWA, unreviewed memory updates, and gated
  updates on strictly later cases. Never update using frozen test labels.
- For supportive care, ablate the case memory, learned co-order patterns,
  indication/evidence features, and the final verifier. Measure both missed
  historical orders and unsupported extra suggestions. Current data labels
  only the former; clinician annotation must establish the latter.
- Perturb missing eGFR, contradictory medication lists, incomplete allergy
  coding, delayed lab results, duplicate orders, stale evidence versions,
  tool failures, and prompt-injection text embedded in notes.
- Measure risk-rule coverage separately from model accuracy. A case with no
  rule hit is not automatically safe.

## Milestones

1. **Data audit and protocol**: chart-time semantics, cohort flow, source
   permissions, clinician annotation guide, preregistered endpoints.
2. **Review harness**: typed snapshot/order/finding contracts, versioned rules,
   evidence provenance, re-check after each one-order change, bounded retries.
3. **Expert-labelled T1/T2 pilot**: calibrate labels, error taxonomy, and
   statistical sample size; run matched baselines and ablations.
4. **Offline evolution study**: propose updates from training feedback,
   evaluate on frozen later cases, review regressions, then promote a version.
5. **Paper rewrite**: foreground task definition and leakage audit, describe
   reproducible execution traces, report clinical endpoints and limitations,
   and retain historical-overlap results only as secondary evidence.

Current blockers are an expert-adjudicated prescription-risk set, a validated
drug safety rule source, and a clearly documented compliant route for any
external model API. The existing historical-order results do not substitute
for these prerequisites.

## Research comparisons to implement after labels exist

- [SafeRx-Agent](https://arxiv.org/abs/2605.29146): directly relevant
  knowledge-grounded multi-agent medication recommendation. It already has an
  always-on supportive-care expert, so a generic supportive agent is not a
  novel claim. Rebuild its ATC-L4 MIMIC-IV task before score comparison; our
  current six-hour ED task and GSN labels are not equivalent.
- [RxEval](https://arxiv.org/abs/2605.14543): prescription-level medication,
  dose, and route evaluation; useful external challenge, not a replacement
  for expert safety labels.
- [RxSafeBench](https://github.com/CAS-SIAT-XinHai/RxSafeBench): public
  synthetic contraindication and interaction scenarios, 2,443 cases; its
  three-choice data support an immediate external API pilot.
- [RxQA OpenFDA](https://github.com/Google-Health/rxqa): public 300-question
  pharmacist-reviewed medication reasoning subset; the UK BNF half is not
  publicly released due to licensing.
- [HealthFlow](https://github.com/yhzhu99/HealthFlow): 2026 self-evolving EHR
  workflow with reusable experience and public benchmark assets. Compare its
  workflow memory idea, while treating its EHR analysis tasks as distinct from
  prescription evaluation.
- [MedAgentBench](https://arxiv.org/abs/2501.14654) and
  [PhysicianBench](https://arxiv.org/abs/2605.02240): executable EHR task
  design and tool-use checkpoints for the harness evaluation.
- [MIRA](https://www.nature.com/articles/s41586-026-10675-5): recent EHR
  sandbox system with medication safety review dimensions; use its evaluation
  domains as a comparison point, not its reported score as a directly
  comparable baseline.
