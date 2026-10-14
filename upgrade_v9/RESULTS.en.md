# v0.9 — Actual local QLoRA parameter evolution

## Protocol

Qwen3-4B 4-bit, last eight layers with 3.670M trainable adapter parameters. Three patient-disjoint 600-case feedback blocks; uniform and pre-update-error-prioritized sampling train on 400 cases for 100 steps each round. Both arms share the frozen initial-8k candidate/order tools, loss validation (100), guard (200), and new test (500 admissions / 494 patients). All selections were frozen before test evaluation. Optimizers reset per round while the latest adapter continues training. The chosen inference adapter is the best guard checkpoint. Model weights, feedback and patient data remain local.

## Matched method results

| Method | Drug F1 | Core-order F1 | Mean predicted drugs |
|---|---:|---:|---:|
| base | 0.23399 | 0.13593 | 5.46 |
| uniform_sft | 0.28694 | 0.19115 | 17.42 |
| error_prioritized_sft | 0.28432 | 0.19137 | 18.98 |
| all_20_candidate_tools | 0.28390 | 0.19181 | 20.00 |
| guard_selected_top_k_tools | 0.31169 | 0.20739 | 8.00 |

## Round trajectories / 逐轮轨迹

![Accepted-state trajectories](round_curves.png)

| Arm | Round | Selected checkpoint | Drug F1 | Order F1 | Cases improved / regressed |
|---|---:|---:|---:|---:|---:|
| uniform_sft | 0 | 0 | 0.23399 | 0.13593 | 0 / 0 |
| uniform_sft | 1 | 1 | 0.28695 | 0.19253 | 257 / 79 |
| uniform_sft | 2 | 2 | 0.28694 | 0.19115 | 143 / 155 |
| uniform_sft | 3 | 2 | 0.28694 | 0.19115 | 0 / 0 |
| error_prioritized_sft | 0 | 0 | 0.23399 | 0.13593 | 0 / 0 |
| error_prioritized_sft | 1 | 1 | 0.28432 | 0.19137 | 248 / 84 |
| error_prioritized_sft | 2 | 1 | 0.28432 | 0.19137 | 0 / 0 |
| error_prioritized_sft | 3 | 1 | 0.28432 | 0.19137 | 0 / 0 |

## What evolves and what it means

Adapter files and sampling membership hashes change at each round. Candidate retrieval and joint-order templates are fixed. The model selects recorded templates; it does not learn novel dose generation. Clinical indication, DDI and renal safety are not established by agreement with historical orders. Ground truth supports automatic scoring without requiring new clinician review.

Strict versus normalized validity is retained: only an empty Qwen reasoning envelope is stripped. The pre-test parser/cache repair preserves raw outputs. Test predictions were independently recounted using drug sets and complete drug/route/dose/unit tuples, with patient-cluster paired intervals. Unknown fields remain unscored. A higher score than the initial model alone is insufficient evidence of an RSI benefit; error-prioritized updates must be compared with ordinary updates and direct use of the same tools.
