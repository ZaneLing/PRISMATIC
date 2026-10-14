# RxRSIAgent v0.8: executed language-artifact evolution

Completed evolution-order seeds: 42, 137, 2026. Missing seeds are not counted as completed. The fixed backbone is DeepSeek-V4.1-Flash. All methods share the scenario-group split: 625 train / 190 proposal / 197 guard / 988 test cases. This is a derived medication-option task; original free-generation paper scores are not directly comparable.

## Method comparison

| Method | Accuracy (%) | Seed SD (pp) | Invalid outputs |
|---|---:|---:|---:|
| Direct | 46.15 | 0.00 | 3 |
| CoT | 47.27 | 0.00 | 0 |
| Self-Refine | 47.57 | 0.00 | 0 |
| Case RAG | 49.09 | 0.00 | 0 |
| Reflexion adaptation | 47.64 | 0.64 | 0 |
| GRASP adaptation | 48.01 | 1.29 | 2 |
| EvoTool adaptation | 47.27 | 0.00 | 0 |
| RxRSI | 47.27 | 0.00 | 0 |

The named Reflexion, GRASP and EvoTool rows are independent task adaptations, not official reproductions. All evolution methods receive four candidate-evaluation slots per round; proposal costs can differ. Invalid outputs count as wrong. Across-seed SD measures training-order sensitivity, not independent patient sampling uncertainty.

## What changed and what improved

![Fixed-test trajectories](round_curves.png)

| Round | Accepted | Changed artifacts | Guard fixes / regressions | Test accuracy (%) |
|---|---|---|---:|---:|
| 0 | True | none | 0 / 0 | 47.27 |
| 1 | False | none | 12 / 19 | 47.27 |
| 2 | False | none | 11 / 16 | 47.27 |
| 3 | False | none | 12 / 18 | 47.27 |
| 4 | False | none | 13 / 14 | 47.27 |

The table above shows the first completed seed. Full before/after text and rejected candidates are released in version journals. A rejected proposal leaves the active state unchanged. Backbone weights and tool source code remain fixed; focus terms change only the evidence tool's configuration.

## Object ablations

| Variant | Accuracy (%) |
|---|---:|
| without_memory | 47.27 |
| without_skills | 47.27 |
| without_tool_update | 47.27 |

## RxQA transfer (all 300 public OpenFDA questions)

CoT: 193/300 (64.33%); RxRSI: 193/300 (64.33%). Fixes/regressions: 0/0. No RxQA labels are used to update the artifacts.

## Verification and interpretation

Saved predictions were independently recounted with exact case alignment and version-hash checks. Scenario-cluster paired intervals and all method contrasts are in `results/summary.json`; these intervals are descriptive and not multiplicity-adjusted. Per-method cost denotes logical inference use; the API ledger separately records actual calls, including evolution. Repeated guard reuse is development selection. A gain, a flat curve or a regression is retained exactly as observed; none establishes unrestricted clinical prescribing ability.
