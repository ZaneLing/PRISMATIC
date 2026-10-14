# v0.28 — Answer contracts and evidence-preserving tool statistics

## 1. Question and registered comparison

The v0.19 failures motivate two fixed execution repairs: **C**, an instruction-derived answer schema with budgeted rejection/retry; **S**, paginated Observation retrieval and source-bound latest/24h arithmetic grouped by code and unit. **K** is the unchanged pair of v0.19 learned skills. All8 combinations are registered before their execution. Neither C nor S is autonomously evolved code.

All conditions keep the same backbone, eight actor calls and512 output tokens per call, real FHIR service and original task/reference logic. Additional paging HTTP calls and token costs are reported. Schema rejection requests another model decision; it never extracts a favorable value after scoring. Complete page receipts support each statistic; missing units/times and future/non-numeric values are flagged. No dose or clinical guideline is invented by the reducer.

All splits were used in prior work: this is a post-test-motivated exploratory repair study. All conditions remain fixed; validation/test scores do not promote a winner. Model/API cache reuse is exact; logical costs are not fresh physical-spend estimates. The shared ledger includes concurrent studies.

## 2. Audited actual results

Status / 状态：**partial**. Pending / 未完成 cells are not scored as zero.

| C: schema | S: statistics | K: frozen skills | Validation /80 | ID /64 | Held-out types /60 |
|---|---|---|---:|---:|---:|
| 0 | 0 | 0 | 45 | 38 | pending |
| 0 | 0 | 1 | 53 | 45 | pending |
| 0 | 1 | 0 | 49 | pending | pending |
| 0 | 1 | 1 | 59 | pending | pending |
| 1 | 0 | 0 | 52 | pending | pending |
| 1 | 0 | 1 | 54 | pending | pending |
| 1 | 1 | 0 | 57 | pending | pending |
| 1 | 1 | 1 | 66 | pending | pending |

| Split | Declared contrast | Difference (pp) | Patient/query-cluster interval (pp) |
|---|---|---:|---:|
| val | contract_main_effect | +7.19 | [+1.51, +13.13] |
| val | statistics_main_effect | +8.44 | [+4.69, +12.18] |
| val | frozen_skills_main_effect | +9.06 | [+2.74, +15.82] |
| val | skills_on_full_repair | +11.25 | [+2.47, +20.00] |
| val | full_repair_no_skills_minus_original_fixed | +15.00 | [+6.94, +23.26] |
| val | contract_statistics_interaction | +4.38 | [-2.56, +10.44] |

Validation has 62 explicit patients plus two deliberately nonexistent-patient lookup queries; those queries form separate resampling units (64 total). No patient ID is invented. Both test splits have complete explicit patient identities.

Only completed cells that pass independent reference regrading, persisted-field/cleanup checks and raw-page arithmetic reconstruction appear above. One frozen run per condition, overlapping patients and descriptive intervals do not establish general RSI superiority. The earlier v0.19 table remains unchanged.

## Evidence / 证据

- [Preregistered factorial](protocol.json)
- [Executed runtime probes](results/runtime_probe.json)
- [Independent cell audits and contrasts](results/summary.json)
- [Full execution counts](results/method_results.json)
