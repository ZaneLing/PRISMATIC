# v0.27 — Standard medication-method compatibility audit

## 1. Executed cohort

A separate retrospective visit-set task uses adult MIMIC-IV 3.1 hospital admissions with an ICU stay, at least one diagnosis/procedure/mapped medication, and at least two eligible visits per patient. Inputs are completed-visit diagnosis/procedure codes plus prior visits; this is not an admission-time or six-hour new-order task.

| Split | Patients | Visits | Medication targets | Targets outside train vocabulary |
|---|---:|---:|---:|---:|
| train | 7,115 | 18,429 | 227,151 | 0 |
| proposal | 433 | 1,095 | 13,300 | 3 |
| guard | 467 | 1,231 | 14,878 | 3 |
| test | 890 | 2,422 | 30,004 | 5 |

Training-only vocabularies contain 10,726 diagnosis codes, 5,330 procedure codes and 271 true five-character ATC-L4 classes. Unseen test labels remain in recall denominators. Patient overlap across partitions is zero. The public NDC mapping covers **27.23%** of 2,734,635 selected source prescription rows; the target is the mapped subset. This coverage is not complete prescription ground truth.

## 2. Independent audit

Reconstruction of all 23,177 selected visits verifies diagnoses, procedures, medication sets, adult ICU membership, visit order, patient partition and training vocabularies. The full population selection flow is produced by the builder and is not independently rescanned. Test patients overlap earlier observed v0.9/v0.21 tests by 20/50 respectively; this panel is exploratory.

## 3. Public molecule and code execution results

All **746/746** public CIDs return valid RDKit structures, spanning 399 ATC-L4 classes. This covers **219/271** training classes and 24,391/30,004 test target occurrences. The 52 uncovered classes are listed in the audit, never assigned invented structures.

Pinned author ARMR-2025, GAMENet and SafeDrug cores actually pass synthetic forward/backward probes. GAMENet is invariant to changing the hidden current-medication field. The SafeDrug probe uses real public molecules and a clearly synthetic identity substructure mask only to check execution; it is not a trained model or a scientific baseline score. The subsequent complete study resources contain627 real molecular graphs,863 BRICS fragments and326 fingerprint types, with no uncovered projection row. The synthetic probe mask is never used for training.

## 4. Registered method training is running

The full271-class and common molecular219-class panels each retain the same patients/visits. The latter explicitly excludes5,613 test targets and retains3 empty-target visits; its scores cannot be pooled with the full panel. Each neural architecture receives50 full training epochs for seeds42/137/2026. ARMR and GAMENet run in both panels; SafeDrug runs in the molecular panel. Proposal patient-average Jaccard selects epoch/threshold; guard is report-only. Equal case exposure is not equal optimizer steps or FLOPs. Tests remain gated until all baseline and subsequently registered RxRSI states freeze.

The sparse SafeDrug adjacency, persisted fixed molecular embedding and CPU/MPS ARMR execution pass numeric/gradient/checkpoint probes. The current released SafeDrug training script uses `min` where published Eq19 uses `max`; this independently adapted reproduction uses the published formula and discloses the difference. [SafeDrug paper](https://arxiv.org/pdf/2105.02711). No original-paper reproduction score is claimed.

| Panel | Method | Seed | Finished epochs / 50 | Status |
|---|---|---:|---:|---|
| full | ARMR | 137 | 10 | training |
| full | ARMR | 42 | 50 | selection_frozen |
| full | GAMENet | 42 | 45 | training |
| molecular | SafeDrug | 42 | 47 | training |

Queued seeds/panels are not counted as completed. Snapshot of saved epoch receipts; no provisional neural test score.

## 5. Completed conventional controls: guard only

These are genuine fitted-method comparisons on1,231 development visits/467 patients. All four choices are frozen by separate proposal data; independent reconstruction from the original visit source verifies features, saved predictions and set metrics. They are not the requested final test main table.

| Panel | Method | Patient-average F1 | Patient-average Jaccard | Mean medications |
|---|---|---:|---:|---:|
| full | prevalence | 0.45794 | 0.30680 | 11.00 |
| full | last_visit | 0.30154 | 0.21585 | 7.26 |
| full | cosine_knn | 0.55081 | 0.39614 | 13.10 |
| full | structured_logistic | 0.61151 | 0.45742 | 12.48 |
| molecular | prevalence | 0.42555 | 0.28089 | 15.00 |
| molecular | last_visit | 0.28971 | 0.20613 | 5.81 |
| molecular | cosine_knn | 0.51751 | 0.36710 | 10.43 |
| molecular | structured_logistic | 0.58113 | 0.42971 | 9.86 |

## 6. Executable rule-memory RSI is running

Five rounds expose20/40/60/80/100% of training patients. A common supervised policy is refit; patient-disjoint cross-fitting produces error evidence. The language agent sees only aggregate candidate-rule descriptors and chooses up to4 edits. A separate20% training-patient witness partition accepts beneficial edits; validation/test never supplies candidate feedback. Runtime rules only read observed features and model probabilities. Compared arms are uniform policy, greedy rules, random rules, own-error agent, shuffled-evidence agent and matched proposals without verification. Ordinary coefficient fitting is not called autonomous weight evolution; the changed agent artifact is a typed rule memory. This task predicts classes, not full doses.

Source files, actual proposals, accepted/rejected operations and state hashes are saved. Original fold probabilities were retained but original fold weights were not; a separate raw-source reconstruction explicitly refits the folds and checks probability/decision equality. Scalar witness audits investigate numeric-library warnings without treating warnings as incorrect model predictions. No superiority claim is made from provisional development gains.

| Panel | Seed | Completed rounds /5 | Own-error retained rules | Status |
|---|---:|---:|---:|---|
| full | 137 | 5 | 8 | selection_frozen |
| full | 2026 | 5 | 17 | selection_frozen |
| full | 42 | 5 | 8 | selection_frozen |
| molecular | 137 | 5 | 9 | selection_frozen |
| molecular | 2026 | 5 | 12 | selection_frozen |
| molecular | 42 | 5 | 10 | selection_frozen |

[Registered mechanism and controls / 机制与对照登记](rsi_addendum.json) · [Scalar decision audit / 标量决定核验](results/rule_decision_audit.json)

The own-error agent actually changed the following amounts of memory (accepted operations, including later deletions):

| Panel | Seed | Accepted ADD | Accepted DELETE | Retained rules by round |
|---|---:|---:|---:|---|
| full | 137 | 8 | 0 | 3 → 5 → 5 → 7 → 8 |
| full | 2026 | 17 | 0 | 4 → 7 → 10 → 14 → 17 |
| full | 42 | 9 | 1 | 1 → 5 → 6 → 6 → 8 |
| molecular | 137 | 9 | 0 | 3 → 5 → 5 → 9 → 9 |
| molecular | 2026 | 12 | 0 | 2 → 5 → 8 → 10 → 12 |
| molecular | 42 | 11 | 1 | 2 → 5 → 7 → 8 → 10 |

For example, a retained rule uses observed prior medication history for class `N02BE` to include that same class when its probability is just below the common threshold. Other candidates use diagnosis or prior-drug features. The log records each exact predicate, drug code, witness score change and rule hash; these statistical associations are not prescribing guidelines.

## 7. Audited author-model development results

Only completed 50-epoch runs whose selected checkpoint has been reloaded and independently recounted appear here. These are guard results; unfinished seeds remain pending.

| Panel | Method | Seed | Guard F1 | Guard Jaccard |
|---|---|---:|---:|---:|
| full | ARMR | 42 | 0.60738 | 0.45214 |

## 8. Audited rule-memory comparison and experience curves

The table uses the same 1,231 guard visits from 467 patients. Models/rounds are chosen on proposal data only. Each included seed passes raw-source feature reconstruction, fresh cross-fit reproduction, candidate-effect and saved prediction checks. Three-seed standard deviations and paired patient intervals are separate: intervals average the observed seeds first and do not estimate new-seed variability. This is still development evidence.

Witness patients are excluded from candidate induction, but their labels can train policies used for other folds. The shared C hyperparameter is selected through proposal performance of full seen-patient fits. Thus cross-fitting prevents direct fitting of a case's own predictor to its label; it is not a wholly isolated nested validation experiment. The repeated witness gate is training validation, not independent clinical confirmation.

| Panel | Method | Audited seeds | Guard F1 ± seed SD | Guard Jaccard ± seed SD |
|---|---|---:|---:|---:|
| full | uniform_policy | 3 | 0.61151 ± 0.00000 | 0.45742 ± 0.00000 |
| full | greedy_error_rules | 3 | 0.61267 ± 0.00066 | 0.45863 ± 0.00064 |
| full | random_candidate_rules | 3 | 0.61205 ± 0.00031 | 0.45791 ± 0.00027 |
| full | own_error_rule_agent | 3 | 0.61260 ± 0.00057 | 0.45856 ± 0.00057 |
| full | shuffled_evidence_rule_agent | 3 | 0.61219 ± 0.00038 | 0.45811 ± 0.00044 |
| full | matched_proposals_without_witness_gate | 3 | 0.61251 ± 0.00087 | 0.45840 ± 0.00102 |
| molecular | uniform_policy | 3 | 0.58113 ± 0.00000 | 0.42971 ± 0.00000 |
| molecular | greedy_error_rules | 3 | 0.58230 ± 0.00042 | 0.43084 ± 0.00039 |
| molecular | random_candidate_rules | 3 | 0.58220 ± 0.00055 | 0.43078 ± 0.00058 |
| molecular | own_error_rule_agent | 3 | 0.58198 ± 0.00014 | 0.43049 ± 0.00014 |
| molecular | shuffled_evidence_rule_agent | 3 | 0.58255 ± 0.00029 | 0.43105 ± 0.00027 |
| molecular | matched_proposals_without_witness_gate | 3 | 0.58202 ± 0.00067 | 0.43050 ± 0.00070 |

| Panel | Own agent minus control | F1 difference (pp) | Patient interval (pp) |
|---|---|---:|---:|
| full | uniform_policy | +0.109 | [+0.050, +0.173] |
| full | greedy_error_rules | -0.007 | [-0.020, +0.006] |
| full | random_candidate_rules | +0.055 | [+0.020, +0.094] |
| full | shuffled_evidence_rule_agent | +0.041 | [-0.000, +0.086] |
| full | matched_proposals_without_witness_gate | +0.009 | [-0.038, +0.057] |
| molecular | uniform_policy | +0.086 | [+0.002, +0.175] |
| molecular | greedy_error_rules | -0.031 | [-0.061, -0.000] |
| molecular | random_candidate_rules | -0.022 | [-0.085, +0.045] |
| molecular | shuffled_evidence_rule_agent | -0.056 | [-0.112, -0.001] |
| molecular | matched_proposals_without_witness_gate | -0.003 | [-0.056, +0.046] |

| Panel | Round | Training patients | Shared policy proposal F1 | Own-agent proposal F1 | Own retained rules by seed |
|---|---:|---:|---:|---:|---|
| full | 1 | 1423 | 0.56896 | 0.56958 | 1, 3, 4 |
| full | 2 | 2846 | 0.58492 | 0.58562 | 5, 5, 7 |
| full | 3 | 4269 | 0.59287 | 0.59323 | 6, 5, 10 |
| full | 4 | 5692 | 0.59804 | 0.59863 | 6, 7, 14 |
| full | 5 | 7115 | 0.60142 | 0.60190 | 8, 8, 17 |
| molecular | 1 | 1423 | 0.54232 | 0.54262 | 2, 3, 2 |
| molecular | 2 | 2846 | 0.55987 | 0.56008 | 5, 5, 5 |
| molecular | 3 | 4269 | 0.56816 | 0.56824 | 7, 5, 8 |
| molecular | 4 | 5692 | 0.57481 | 0.57559 | 8, 9, 10 |
| molecular | 5 | 7115 | 0.57926 | 0.57996 | 10, 9, 12 |

Increasing case counts improve the shared supervised predictor; the small incremental memory effect must be compared against greedy and shuffled controls before attributing it to language-agent evolution. These rules represent associations, not validated prescribing indications.

![Audited development curves and paired increments](../paper/figures/rule_memory_development.png)

[Editable vector figure](../paper/figures/rule_memory_development.svg)

## Artifacts / 交付文件

- [Registered protocol](protocol.json) and [training addendum](training_addendum.json)
- [Implementation details](implementation_notes.json)
- [Cohort manifest](results/cohort_manifest.json)
- [Independent audit and missing classes](results/cohort_audit.json)
- [Public molecule receipts](results/molecular_resource_audit.json)
- [Actual molecular/graph resources](results/model_resource_manifest.json)
- [Author-core execution probe](results/author_core_probe.json) and [training runtime equivalence](results/training_runtime_probe.json)
- [Independent control audit](results/control_audit.json)
- [Recent-method source audit](../paper/LATEST_METHODS.en.md)

Restricted cases, fitted artifacts and patient-level outputs remain local. Public reports contain aggregates and hashes.
