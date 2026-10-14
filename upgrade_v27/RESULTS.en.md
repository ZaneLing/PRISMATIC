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

Pinned author ARMR-2025, GAMENet and SafeDrug cores actually pass synthetic forward/backward probes. GAMENet is invariant to changing the hidden current-medication field. The SafeDrug probe uses real public molecules and a clearly synthetic identity substructure mask only to check execution; it is not a trained model or a scientific baseline score. Complete BRICS/graph resources and a common covered-label panel are still required.

## 4. Next execution gate

Freeze a method-training addendum after resolving molecular coverage; compare full ATC-L4 nonmolecular methods and a separately disclosed common molecular space. Run genuine author cores, matched controls and the RxRSI prescription tool. Select checkpoints on development only, then compute patient-averaged and micro set metrics, coverage, prescription sizes and patient-cluster intervals. No method has been trained or scored in v0.27 yet.

## Artifacts / 交付文件

- [Registered protocol](protocol.json)
- [Cohort manifest](results/cohort_manifest.json)
- [Independent audit and missing classes](results/cohort_audit.json)
- [Public molecule receipts](results/molecular_resource_audit.json)
- [Author-core execution probe](results/author_core_probe.json)
- [Recent-method source audit](../paper/LATEST_METHODS.en.md)

Restricted cases, fitted artifacts and patient-level outputs remain local. Public reports contain aggregates and hashes.
