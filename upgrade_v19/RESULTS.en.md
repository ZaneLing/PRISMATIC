# v0.19 — Real FHIR execution: complete method comparison

## 1. Result and interpretation

**Skill learning improves the observed ID count but harms held-out task types. It does not demonstrate overall evolution success.** The same backbone, eight-call cap, 512-token actor cap and actual local FHIR service apply to all arms. The fixed harness also changes workflow instructions, so direct-versus-fixed differences cannot be attributed only to the write compiler.

| Method | ID success (64) | Held-out type success (60) | ID / transfer model calls |
|---|---:|---:|---:|
| Direct tools | 39 | 27 | 133 / 120 |
| Fixed compiled harness | 38 | 17 | 174 / 139 |
| Learned skills + compiled harness | 45 | 10 | 207 / 124 |

ID skills-minus-fixed is +10.94 pp, but its patient-cluster interval includes zero. Transfer is −11.67 pp against fixed and −28.33 pp against direct tools; both intervals are negative. On held-out task7 the learned arm scores 0/30 (fixed 5/30; direct 14/30). All held-out-type arms make zero writes, so write serialization itself is not an explanation for this transfer regression.

| Split | Contrast | Difference (pp) | Patient-cluster 95% interval (pp) | Fixes / regressions |
|---|---|---:|---:|---:|
| id_test | fixed compiled  minus  direct tools | -1.56 | [-11.86, +8.70] | 5 / 6 |
| id_test | evolving compiled  minus  fixed compiled | +10.94 | [+0.00, +20.55] | 9 / 2 |
| id_test | evolving compiled  minus  direct tools | +9.38 | [-1.72, +19.30] | 11 / 5 |
| test | fixed compiled  minus  direct tools | -16.67 | [-26.23, -8.20] | 0 / 10 |
| test | evolving compiled  minus  fixed compiled | -11.67 | [-22.95, -1.64] | 2 / 9 |
| test | evolving compiled  minus  direct tools | -28.33 | [-40.68, -16.67] | 1 / 18 |

Intervals use 4,000 descriptive paired patient-cluster resamples (47 ID patients / 53 transfer patients); one learning seed, overlapping patients across study splits, no multiplicity correction. Task-level intervals are also retained in JSON. These are revised execution-endpoint scores, not an unmodified official leaderboard score.

## 2. What actually evolved

The unchanged GRASP optimizer processes 96 training tasks in four 24-case batches with four proposal slots and 12-case training probes. Round1 adds `fhir_patient_name_search_url_encoding`; round2 adds `lab_code_text_fallback_probe`; rounds3/4 retain the state. Validation on80 tasks rises45/80→53/80 and selects the state before64 ID/60 transfer tasks. Language-skill files change; backbone weights, compiler, protocol feedback and evaluator remain fixed. This study does not demonstrate autonomous tool-code evolution.

The [exact generated skills](artifacts/model_authored_skills/README.md) retain their frozen SHA-256 hashes. Their example observations are model-authored illustrations, not actual tool receipts. A post-test, read-only claim audit finds that raw and percent-encoded name queries become the identical URL because the existing HTTP adapter already encodes spaces; both return the same empty public-fixture result. Thus the claimed causal explanation is false for this adapter. Global A1C code/text searches return244/258 matches and MG3538/3538; these counts do not validate a patient-specific fallback. Medication route compilation does not establish lab encoding. The name/date illustration also violates the updater's instruction against memorizing such values. No replacement skill is selected by this audit.

## 3. Frozen skill attribution

Single-skill states were registered before their own execution, after direct/fixed test outcomes had been observed. The four conditions are neither/name/lab/both, with identical budgets. This is exploratory attribution, not new untouched confirmation. No retraining or revised prompt is allowed in the ablation.

Status: **complete**. Each numeric cell below has finished and passed the independent reference/receipt audit; unfinished cells stay pending.

| Skill condition | ID (64) | Held-out type (60) |
|---|---:|---:|
| name_only | 44 | 14 |
| lab_only | 39 | 11 |
| neither | 38 | 17 |
| both | 45 | 10 |

| Split | Contrast | Difference (pp) | Patient-cluster interval (pp) |
|---|---|---:|---:|
| id_test | both_minus_name_only | +1.56 | [-6.35, +9.68] |
| id_test | both_minus_lab_only | +9.38 | [+0.00, +17.74] |
| id_test | name_only_minus_neither | +9.38 | [-3.13, +20.31] |
| id_test | lab_only_minus_neither | +1.56 | [-3.33, +6.85] |
| id_test | interaction | +0.00 | [-10.35, +10.77] |
| test | both_minus_name_only | -6.67 | [-15.00, +1.52] |
| test | both_minus_lab_only | -1.67 | [-8.62, +5.26] |
| test | name_only_minus_neither | -5.00 | [-14.52, +4.84] |
| test | lab_only_minus_neither | -10.00 | [-20.69, +0.00] |
| test | interaction | +3.33 | [-8.62, +15.25] |

ID interaction is0.00 pp and transfer interaction+3.33 pp; both patient intervals include zero. Individual removal contrasts likewise have intervals containing zero. The observed counts do not establish robust synergy or a universally beneficial skill. / 同类交互0.00个百分点，迁移交互+3.33个百分点，两个患者区间均含零；单项移除的区间同样含零，不能据此宣称稳健协同或某项技能普遍有效。

## 4. Actual execution and grading revision

The official public MedAgentBench application/database runs on native HAPI FHIR7.6.0. Five original CRUD/atomic-failure probes passed. A synthetic medication-order probe showed HTTP201 alone can hide lost dosage fields; converting a route string to CodeableConcept text preserved those fields. An induced-loss probe verified rollback and feedback. These are fixed engineering repairs, not learned gains.

The first learning run was stopped during development after13 false negatives from legacy object-shaped `ServiceRequest.note` grading. The revised run starts from empty skills and applies the same lossless singleton-note/text-route views to all methods; raw reference grades remain available. Original, live and revised reference scores happen to agree on every completed final main arm. Independent audits regrade all tasks and recount real writes/readbacks/rollbacks/cleanup:14/23/21 ID writes for direct/fixed/learned, zero readback failures. Original resource counts are restored. Legacy rate-unit semantics remain unvalidated.

Costs in JSON are logical episode costs; exact code/case/skill cache replays preserve first-execution receipts. Cleanup operations are counted separately. The experiment is research execution on public benchmark fixtures, not clinical deployment.

## 5. Why task7 is0/30: answer contract versus numeric error

A post-test read-only audit retrieves the complete original reference records. All30 learned-skill answers contain `[value, timestamp]`, while task7 requires a single numeric list element. In15 cases the first value is correct but the extra timestamp causes strict failure; the other15 first values are wrong as well. The name-only condition instead emits30 prose strings. Thus0/30 is not equivalent to30 wrong glucose values. This output-contract failure is not repaired by merely validating JSON syntax.

Projecting a saved answer to its first numeric field is diagnostic only: it does not replace the main score or constitute an executed repaired-agent result. The next registered intervention needs an explicit answer schema and action-budget accounting, evaluated across all methods. [Independent shape/value audit](results/answer_contract_audit.json).

## Evidence / 证据

- [Complete scores, paired intervals, task types and independent audits](results/summary.json)
- [Frozen skills and original selection protocol](results/frozen_skills.json)
- [Read-only claim audit](results/skill_claim_audit.json)
- [Skill attribution protocol](ablation_protocol.json)
- [Development grading revision](results/grading_revision.json)
