# RxRSIAgent: conditional executable memory on new eICU patients

**Outcome: the full hypothesis is not established. The compatible runtime changes drug F1 from7.38% to7.20% after learning and loses6 correct targets. The learned memory is not enabled by default.**

## 1. Research question and completed experiment

Can feedback induce conditional prescription-repair procedures that reduce omissions, extras and joint-order discrepancies on new patients? This delivery completes **6 rounds × 32 feedback patients**, two stream orders, **64 proposal + 64 guard patients**, a frozen **256-patient audit**, and **128-patient Llama transfer**. Every selected patient is absent from all v25 training/development/test membership. Source hospitals separate reflection, development and audit; audit hospitals had been used previously for other patients' development.

**Main result:** drug F1 7.13% → 6.94%; native4 F1 1.23% → 1.17%. The learner retains 3 rules and changes 59/256 patients; 53 improve without increasing another primary error, while 6 worsen on at least one primary component. This is a bounded procedural-memory experiment; improvements in every endpoint, every round, or every model must be checked below rather than presumed.

## 2. What is predicted?

Input: demographics, recorded prior orders, available/revised labs and diagnosis entries by ICU hour6. Target: new/changed order records entered in hours6–12. Zero-target patients remain. Native HICL identity is used; no direct pooling with MIMIC raw-name/Core4 scores. The multisystem stratum means at least 2 recorded disease-system categories, not confirmed chronic multimorbidity. The [official source contract](https://github.com/MIT-LCP/eicu-code/blob/main/website/content/eicutables/diagnosis.md) supplies diagnosis entry timing but not resolution/ruled-out state. Diagnosis discharge activity is excluded. Storage-time and complete medication revision histories remain unavailable.

Common catalogue covers 54.21% of target drug instances and 11.30% of complete target joint tuples. Complete target field coverage is 79.37%. Missing/out-of-catalogue drugs stay in the drug denominator. Complete-joint scoring excludes incomplete GT and prediction tuples; its coverage must accompany its score. Qwen has 11/256 invalid audit outputs; Llama has 73/128.

## 3. Method and controls

Every actor sees the same frozen predictor draft and training-only diagnosis-aware retrieval catalogue. All order IDs are stable hashes of joint tuples. Qwen/Llama use1 call with256 output tokens; repair programs add no LLM calls. Actual input length and backbone compute differ; the predictor-only arm uses no LLM. Static all-repair executes4 operators; retained programs execute according to their scopes.

Failure-guided symbolic induction searches observable predicates and empirical exceptions. Minimum4 active and2 negative training cases; an empirical exception needs2 harmful training applications. Training, proposal and guard must each show strict total discrepancy reduction and no aggregate increase in any of the3 primary components. At most 3 proposal-ranked candidates reach the guard and at most1 is retained per round. Learned states freeze before audit inference. No audit score selects a checkpoint.

The operator implementations and hypotheses are researcher specified. The learner automatically selects scopes, exception clauses and retained compositions from feedback; it does not discover arbitrary new medical tools. No drug-name predicate or newly fitted drug score is allowed, but frozen supervised and pretrained drug priors remain. Scope removal and shuffled-feedback controls test narrower alternatives; they cannot eliminate every shortcut. Native4 completeness is syntactic availability of HICL, route, dosage string and frequency, not clinical correctness or all required order fields.

## 4. Comparison table

| Method | N | Drug F1 % | Native4 F1 % | Missed/patient ↓ | Extra/patient ↓ | Joint errors/patient ↓ |
|---|---:|---:|---:|---:|---:|---:|
| Frozen supervised predictor | 256 | 12.98 | 2.93 | 1.305 | 1.105 | 2.074 |
| Fixed Qwen prescription agent | 256 | 7.13 | 1.23 | 1.172 | 6.965 | 6.914 |
| RxRSIAgent (case order A) | 256 | 6.94 | 1.17 | 1.195 | 6.555 | 6.602 |
| RxRSIAgent (case order B) | 256 | 6.94 | 1.17 | 1.195 | 6.555 | 6.602 |
| Shuffled-feedback learner | 256 | 7.13 | 1.23 | 1.172 | 6.965 | 6.914 |
| Conditional repair of predictor (no LLM) | 256 | 12.41 | 2.99 | 1.316 | 1.055 | 2.031 |
| Learned repairs without scopes/exceptions | 256 | 8.24 | 1.04 | 1.258 | 3.785 | 4.469 |
| Static all-repair bundle | 256 | 7.21 | 0.72 | 1.242 | 4.992 | 5.422 |
| Fixed Llama (128 patients) | 128 | 3.61 | 0.44 | 1.164 | 7.594 | 6.992 |
| Llama + frozen Qwen memory (128 patients) | 128 | 3.69 | 0.45 | 1.164 | 7.406 | 6.891 |

These are matched local controls and ablations. Original medical-agent paper scores are not inserted here. Previous MIMIC and public-QA comparisons remain unchanged; this eICU study is additional evidence, not a replacement claim of superiority.

## 5. Actual round-by-round updates

| Round | Feedback cases | Retained rules | Exception clauses | Drug F1 % | Native4 F1 % | Missed | Extra | Joint errors |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 | 7.13 | 1.23 | 1.172 | 6.965 | 6.914 |
| 1 | 32 | 0 | 0 | 7.13 | 1.23 | 1.172 | 6.965 | 6.914 |
| 2 | 64 | 0 | 0 | 7.13 | 1.23 | 1.172 | 6.965 | 6.914 |
| 3 | 96 | 1 | 0 | 6.98 | 1.14 | 1.188 | 6.727 | 6.746 |
| 4 | 128 | 2 | 0 | 6.85 | 1.15 | 1.195 | 6.668 | 6.688 |
| 5 | 160 | 3 | 0 | 6.94 | 1.17 | 1.195 | 6.555 | 6.602 |
| 6 | 192 | 3 | 0 | 6.94 | 1.17 | 1.195 | 6.555 | 6.602 |

![Frozen round trajectories](results/trajectory.png)

Retained programs:

- `prune_unsupported` when `dx:gastrointestinal`, unless `none established`; round 3, 96 feedback patients, 14 scope-positive training cases, 0 observed harmful training exceptions.
- `prune_unsupported` when `dx:burns/trauma`, unless `none established`; round 4, 128 feedback patients, 7 scope-positive training cases, 0 observed harmful training exceptions.
- `prune_unsupported` when `labs_missing`, unless `none established`; round 5, 160 feedback patients, 7 scope-positive training cases, 0 observed harmful training exceptions.

Second stream final drug/native4 F1: 6.94% / 1.17%. Full proposal/guard outcomes and rejection counts are in `results/qwen-52-learning.json` and `results/qwen-152-learning.json`. Frozen same-state evaluations are not independent replications.

## 6. Transfer, strata and uncertainty

| Stratum | N | Drug F1 % | Missed/patient | Extra/patient | Joint errors/patient |
|---|---:|---:|---:|---:|---:|
| single | 128 | 7.45 → 7.44 | 1.047 → 1.062 | 6.719 → 6.328 | 6.789 → 6.445 |
| multi | 128 | 6.84 → 6.49 | 1.297 → 1.328 | 7.211 → 6.781 | 7.039 → 6.758 |
| zero_target | 135 | 0.00 → 0.00 | 0.000 → 0.000 | 7.674 → 7.193 | 5.837 → 5.467 |
| nonzero_target | 121 | 13.26 → 12.75 | 2.479 → 2.529 | 6.174 → 5.843 | 8.116 → 7.868 |

Paired patient-bootstrap 95% intervals for final minus initial; negative primary-error differences favor the learner, positive F1-point differences favor it:

- missed_drugs_per_patient: [0.0078, 0.0430]
- extra_drugs_per_patient: [-0.5039, -0.3203]
- joint_errors_per_patient: [-0.3945, -0.2344]
- drug_f1_pp: [-0.6331, 0.1710]
- joint_f1_pp: [-0.3291, 0.0843]

Llama drug F1 3.61% → 3.69%, joint F1 0.44% → 0.45%; its full intervals are in `results/evaluation.json`. Intervals use2000 draws and are exploratory, without multiple-testing adjustment. These observations do not guarantee monotonic progress or transfer to arbitrary LLMs.

## 7. Case studies and mechanism limits

Actual improvement, regression and unchanged-failure cases are stored **locally** in the restricted `prismatic-v52/case_studies.json` and `CASE_STUDIES.md`. They contain the recorded inputs, GT, before/after orders and active rules. They are not copied into GitHub. Scope-negative examples and empirically harmful exceptions are recorded separately. Audit exception activation and counterfactual harm/help counts appear in `results/evaluation.json`.

Four hypotheses distinguish missing identities, unsupported additions, wrong joint fields and copying prior therapy into the next time window. They are procedural failure hypotheses, not adjudicated clinical causes. Correct drug identity with wrong route/dose/frequency contributes a missing and an extra joint tuple. A gain from removing extras alone does not demonstrate better treatment coverage. Neither a fuller skill store nor a successful gate proves independent usefulness.

## Additional mechanism audit and updater repair

Final-minus-initial set transitions: recovered correct drugs **0**, lost correct drugs **6**, removed extras **105**, added extras **0**. Recovered complete target tuples: **0**; lost complete target tuples: **1**. These counts distinguish genuine coverage or field correction from output shrinkage. All three primary errors strictly decrease: **False**.

Development inspection found an objective mismatch: the initial counterexample detector marks cases harmful only when total discrepancy rises, whereas the gate rejects an increase in any component. Losing one correct drug can therefore be concealed by removing other extras. It also repeatedly submits rejected state/program pairs. Before any audit metric was calculated, we froze an explicitly exploratory amendment with componentwise counterexamples and rejected-program memory, including each change alone and two streams of both changes. Audit actor generation had already started, but its predictions and outcomes were not used by the amendment. The original primary study remains unchanged; the amendment is a researcher repair, not an automatically evolved learning algorithm.

| Updater | Rules | Exception clauses | Drug F1 % | Native4 F1 % | Missed/patient | Extra/patient |
|---|---:|---:|---:|---:|---:|---:|
| Both updater repairs (order A) | 1 | 0 | 6.98 | 1.14 | 1.188 | 6.727 |
| Both updater repairs (order B) | 4 | 0 | 7.12 | 1.07 | 1.191 | 6.453 |
| Componentwise counterexamples only | 0 | 0 | 7.13 | 1.23 | 1.172 | 6.965 |
| Rejected-program memory only | 3 | 0 | 6.94 | 1.17 | 1.195 | 6.555 |

The amended detector can identify more harmful cases without yielding a transferable exception rule. Conditions are currently patient-level, while the action changes individual drug orders; a broad patient exclusion may suppress useful edits along with harmful ones. This is a granularity hypothesis motivated by the implemented rule language, not a demonstrated clinical mechanism. Raw subgroup associations do not prove a disease-specific prescribing principle.

Source audit also finds7 cancelled rows among473 audit target source rows (distinct from unique drugs). Cancellation time is unavailable and cancellation status is not an input or a target filter. The [official medication contract](https://raw.githubusercontent.com/MIT-LCP/eicu-code/main/website/content/eicutables/medication.md) describes orders, not guaranteed administrations. This further limits interpretation of GT as clinical correctness.

## Compatible runtime, regated learning and current decision

Complete JSON with a mixture of known and unknown IDs previously lost the entire output. The compatible runtime retains only verified IDs, logs unknown IDs, accepts complete fenced JSON, and never completes a truncated structure. It restores nonempty outputs for8 Qwen audit patients and13 Llama patients. **All development gates were rerun using this same decoder before audit metrics**, rather than attributing an output-parser change to learned improvement. No new LLM inference was needed.

| Method | Drug F1 % | Native4 F1 % | Missed/patient | Extra/patient | Joint errors/patient |
|---|---:|---:|---:|---:|---:|
| Fixed Qwen, compatible runtime | 7.38 | 1.64 | 1.152 | 7.184 | 7.035 |
| RxRSIAgent, compatible runtime + gated memory | 7.20 | 1.60 | 1.176 | 6.773 | 6.723 |
| Reflection-label shuffle, true development gates | 7.32 | 1.49 | 1.172 | 6.746 | 6.707 |
| Static all repairs, compatible runtime | 7.48 | 1.12 | 1.227 | 5.148 | 5.512 |
| Fixed Llama, compatible runtime (128) | 3.17 | 0.37 | 1.156 | 9.352 | 8.305 |
| Llama + transferred memory, compatible runtime (128) | 3.24 | 0.38 | 1.156 | 9.102 | 8.172 |

The compatible learner also loses6 correct drug targets; the omission-rate difference95% interval is [0.0078, 0.0430] per patient. 6 patients worsen on at least one primary component. A lower summed error count must not conceal these trade-offs. The reflection-label-shuffle control permutes **only reflection labels**; proposal and guard references remain correct, so it does not eliminate development supervision. After decoder repair it also retains3 rules. This weakens attribution to patient-specific reflection learning.

**The strong hypothesis is not established.** We observed automatic conditional rule selection, but no accepted explicit exception, no recovery of a previously missed correct drug, and no jointly improving three-endpoint trajectory. The current catalogue reaches only54.21% of target drugs and11.30% of complete target order tuples. No bounded selector can recover a target absent from its action space. The next scientific target is order-level applicability and joint-field construction with independently verified evidence, followed by a new patient lock; this audit is now exposed and must not be reused as unseen confirmation.

The learned memory is **not promoted**. `serve.py` uses the compatible initial actor by default; `--experimental-memory` reproduces the failed memory for research. This rollback does not retrospectively change the frozen result table or count as a positive evolution result.

## 8. What is still unproved?

The requested strong claim requires reproducible reductions in all3 error types, clinically meaningful disease-specific exceptions, retained benefits across streams/models and clinician adjudication of appropriateness. Model weights, tool code and the update algorithm did not evolve. The experiment therefore does not establish recursive improvement of the optimizer, invention of new pharmacological knowledge, unrestricted prescribing competence, or superiority over the strongest published agents.

## 9. Cost and artifacts

New API spend **USD 0**. Successful local calls: 704; input/output tokens: 1,312,065/81,438. Local hardware time is unpriced. The current USD10 authorization still has only the previous USD 0.085203 API receipts charged; historical located study receipts remain approximately USD89.53 separately.

See `protocol.json`, `results/cohort.json`, `results/contract_audit.json`, `results/selection_lock.json`, `results/evaluation.json` and executable source files. The English ACL manuscript is updated in place. No restricted patient data or credentials are exported.
