# RxRSIAgent: current method tables, evolution evidence and execution status

Updated 14 October 2026. This maintained entry point links versioned protocols, failures and results. Funding recovery resolved all previously missing API requests. **Our method has not yet surpassed the strongest completed control.**

## 1. Main method comparisons

### A. Medication and structured-order agreement

Same MIMIC-IV/ED preprocessing, 40,000 training and 4,000 test admissions (3,440 patients), three seeds. The frozen vocabulary contains 128 raw drug names; joint orders match drug, route, dose string and unit. This is not the original ATC-L4/RxNorm protocol. Saline-presence F1 is absent.

| Method | Drug micro-F1 | Core-order micro-F1 |
|---|---:|---:|
| Word/character ensemble + tools | 0.40209 ± 0.00058 | 0.28110 ± 0.00062 |
| RxRSI selected state | 0.39920 ± 0.00251 | 0.27865 ± 0.00142 |
| Freeze initial memory | 0.39976 ± 0.00224 | 0.27926 ± 0.00113 |
| Freeze initial order tool | 0.39920 ± 0.00251 | 0.27494 ± 0.00142 |

[Full 12-row comparison and trajectories](../upgrade_v7/RESULTS.en.md). Existing GT enables automatic scoring without mandatory new clinician annotation.

### B. Public prescription-option method comparison

2,000 deduplicated RxSafeBench questions, scenario-group split 625/190/197/988 train/proposal/guard/test. This is a labeled three-option derived task. Every row uses DeepSeek-V4.1-Flash; rows compare methods. ± denotes SD over three evolution orders; fixed outputs are reused. Author-core results use seed 42. Inference calls differ and development costs are separately recorded, so not every row has an equal budget.

| Method | Accuracy (%) | Calls/case | Evidence |
|---|---:|---:|---|
| Direct LLM | 46.15 ± 0.00 | 1 | [v0.8](../upgrade_v8/RESULTS.en.md) |
| CoT | 47.27 ± 0.00 | 1 | [v0.8](../upgrade_v8/RESULTS.en.md) |
| Self-Refine | 47.57 ± 0.00 | 2 | [v0.8](../upgrade_v8/RESULTS.en.md) |
| Case RAG | 49.09 ± 0.00 | 1 | [v0.8](../upgrade_v8/RESULTS.en.md) |
| Reflexion task adaptation | 47.64 ± 0.64 | 1 | [v0.8](../upgrade_v8/RESULTS.en.md) |
| GRASP task adaptation | 48.01 ± 1.29 | 1 | [v0.8](../upgrade_v8/RESULTS.en.md) |
| EvoTool task adaptation | 47.27 ± 0.00 | 1 | [v0.8](../upgrade_v8/RESULTS.en.md) |
| RxRSI language artifacts | 47.27 ± 0.00 | 1 | [v0.8](../upgrade_v8/RESULTS.en.md) |
| Author GRASP core + task adapter | **50.81** | 1 | [v0.10](../upgrade_v10/RESULTS.en.md) |
| Fixed balanced evidence review | 48.99 | 2 | [v0.11](../upgrade_v11/RESULTS.en.md) |
| Fixed safety evidence review | 49.29 | 2 | [v0.11](../upgrade_v11/RESULTS.en.md) |
| Fixed indication evidence review | 48.38 | 2 | [v0.11](../upgrade_v11/RESULTS.en.md) |
| Outcome verifier: uniform | 49.12 ± 0.23 | 2 | [v0.13](../upgrade_v13/RESULTS.en.md) |
| Outcome verifier: error_prioritized | 49.02 ± 0.06 | 2 | [v0.13](../upgrade_v13/RESULTS.en.md) |
| One-call fixed grounding | 50.51 | 1 | [v0.17](../upgrade_v17/RESULTS.en.md) |
| Grounded skill evolution | 50.71 | 1 | [v0.17](../upgrade_v17/RESULTS.en.md) |

The author GRASP core is the strongest completed control. Named task adaptations are not original implementations. The author-core source is unchanged, with our task adapter. Cross-paper original numbers appear only in the manuscript's separate literature panels.

## 2. What actually evolves?

| Study | Changing object | Evidence and interpretation |
|---|---|---|
| v0.7 | Supervised policy parameters, episodes, joint-order templates | Three seeds/five checkpoints improve with data; the static same-data ensemble is stronger |
| v0.8 | Proposed LLM skills, memories, evidence-focus terms | Full RxRSI rejects every candidate in all three orders; no successful final-state evolution |
| v0.10 | Author-core GRASP skill files | 50.81% on the derived task; RxQA transfer declines from 193 to 189/300 |
| v0.12–13 | Router/verifier coefficients and thresholds | Actual updates, some acceptances and test regressions; no stable error-priority advantage |
| v0.9 | Local Qwen LoRA parameters | All 500-case checkpoint tests completed; both arms trail direct top-8 tools |
| v0.15 | LoRA under explicit binary inclusion supervision | Predeclared intervention against over-selection; local training has started |
| v0.17 | GRASP skills over frozen label evidence | Complete: 501/988 versus fixed grounding 499 and author core 502; transfer declines |

Hashes, promotions/rejections and case repairs/regressions accompany the artifacts.

![Structured case-growth trajectories](../upgrade_v7/round_curves.png)

![Public language-artifact trajectories](../upgrade_v8/round_curves.png)

## 3. New executed evidence after funding recovery

- Indication review: **478/988, 48.38%**; all missing requests recovered with the original selection protocol.
- Gemini development repair: on the same 190 questions, CoT improves 72→105 correct and 69→2 invalid; evidence improves 62→100 correct and 85→1 invalid. Reasoning effort and completion cap change jointly. These are development/budget measurements, not test or RSI gains. [Report](../upgrade_v16/RESULTS.en.md).
- Real FHIR: five integration checks pass. Direct tools score 10/16 and a fixed verified harness 8/16 on development tasks. All 11 created resources pass readback and cleanup; independent grading agrees. [Report](../upgrade_v14/RESULTS.en.md).

## 4. Execution order and completion criteria

1. v0.9 all-checkpoint tests, independent recount and patient-cluster intervals are complete; see the new parameter table below.
2. v0.15 has started with matching patients and step budgets, testing explicit negative decisions against over-selection.
3. The Gemini budget check is complete, freezing 2,048 tokens/low reasoning. Finish v0.17 fixed/evolving evidence and RxQA, then v0.18 four-method frozen-skill transfer on Gemini.
4. Repair FHIR retrieval/action failures from development, then evaluate full ID and held-out-task-type splits. The 16-case pilot cannot substitute for those tests.
5. Retain an unobserved confirmation test, multiple orders, ablations, costs and regressions. Negative superiority outcomes remain visible rather than selecting favorable controls or changing test labels.

[English paper](latex/v0.3/prismatic_v03_en.tex) · [Maintained plan](COMPLETION_PLAN.en.md) · [History](CHANGELOG.md). Restricted records, checkpoints, raw patient traces and credentials remain outside GitHub.

## Newly completed table: local parameter evolution on 500 admissions

Separate from the 4,000-admission table: 500 reserved admissions, 494 patients, same initial-8k candidate tools. Mean gold/reachable drugs are 6.784/3.802. All selection was frozen before test scoring.

| Method | Drug F1 | Core-order F1 | Mean drugs |
|---|---:|---:|---:|
| base | 0.23399 | 0.13593 | 5.46 |
| uniform_sft | 0.28694 | 0.19115 | 17.42 |
| error_prioritized_sft | 0.28432 | 0.19137 | 18.98 |
| all_20_candidate_tools | 0.28390 | 0.19181 | 20.00 |
| guard_selected_top_k_tools | 0.31169 | 0.20739 | 8.00 |

[Full local results / 完整本地结果](../upgrade_v9/RESULTS.en.md)

## New temporal-protocol audit

Among 1,788,195 historical target rows, 42,005 matching provider orders precede admission and 276,269 occur after the original six-hour horizon. Timestamp counts exclude 438 admission-link conflicts. Source linkage paths agree, but the differing pharmacy/provider clocks still require an explicit prospective availability protocol. [Full results](../upgrade_v20/RESULTS.en.md).
