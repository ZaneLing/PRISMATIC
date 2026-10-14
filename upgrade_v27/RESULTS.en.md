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
| full | ARMR | 42 | 13 | training |
| full | GAMENet | 42 | 10 | training |
| molecular | SafeDrug | 42 | 10 | training |

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
