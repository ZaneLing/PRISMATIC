# RxRSIAgent: current method tables, evolution evidence and execution status

Updated 15 October 2026. This maintained entry point links versioned protocols, failures and results. Funding recovery resolved all previously missing API requests. **Our method has not yet surpassed the strongest completed control.**


## Newly completed: binary parameter intervention (v0.15)

Same 500 admissions / 494 patients and fixed candidate tools as the earlier parameter study; the binary intervention was declared before its test scores. One learning seed, three feedback rounds, equal 400-example/100-step budgets.

| Method | Drug F1 | Joint-order F1 |
|---|---:|---:|
| Frozen model with binary prompt | 0.17414 | 0.10141 |
| Uniform binary updates | 0.24094 | 0.15072 |
| Own-error-prioritized binary updates | 0.29192 | 0.19329 |
| Direct top-8 candidate tools | **0.31169** | **0.20739** |

Priority improves over uniform in this run, with positive paired patient intervals, but remains below the strong direct-tool control. Both select round2. The raw round3 priority model emits only zeros and is rejected; 99% of selected-model masks select a prefix of the ranked candidates. This does not show learned clinical reasoning or monotonic model improvement. Six actual adapters/step logs, sampling and labels are audited; 10/3,600 duplicate-input feedback generations cannot be exactly recovered, a disclosed reproducibility gap. Saved test predictions are fully recounted.

[Full results and raw/accepted curves](../upgrade_v15/RESULTS.en.md)


## Latest order task: controlled recorded availability

Decision: actual admission plus6h; predict new/changed orders in the following6h using previously recorded orders, blood labs and demographics. Provider/pharmacy clocks and identities must agree. Split:40,000 training /2,000 proposal /2,000 guard / **1,082 test admissions (1,024 patients)**; patient-disjoint and excluding previous test patients. Independent reconstruction checks198,850 targets,589,393 prior orders and506,710 lab rows; all12 checks pass. This selected coherent-time, nonempty-target cohort does not represent all admissions.

| Method | Drug F1 mean ± SD | Core-order F1 mean ± SD |
|---|---:|---:|
| Reuse prior orders | 0.09508 ± 0.00000 | 0.05564 ± 0.00000 |
| Case retrieval + order tool | 0.15592 ± 0.00000 | 0.09518 ± 0.00077 |
| Word/character ensemble + tool | 0.20096 ± 0.00255 | 0.12071 ± 0.00283 |
| RxRSI selected state | 0.19136 ± 0.00154 | 0.11533 ± 0.00094 |
| Freeze initial order tool | 0.19136 ± 0.00154 | 0.11425 ± 0.00043 |
| Freeze initial memory | 0.19555 ± 0.00250 | 0.11832 ± 0.00109 |

All three-seed method/ablation and round predictions are independently recounted. Separate from the earlier start-time task.
Round-mean drug F1 rises from0.1660 to0.1914, but the strong control scores0.2010 and frozen initial memory is better. A unique RSI advantage is not established.

[Full protocol/results / 完整协议结果](../upgrade_v21/RESULTS.en.md)

## Latest mechanism study: does error feedback add value?

Three seeds/five rounds with fixed word+numeric features. Uniform, own-error-weighted and shuffled-weight arms share cases and exactly60 training epochs. Order tools use only cases seen by that round. Evaluation follows joint selection freeze.

| Method | Drug F1 mean ± SD | Core-order F1 mean ± SD |
|---|---:|---:|
| Initial state | 0.16840 ± 0.00076 | 0.10130 ± 0.00101 |
| Uniform updates | 0.20446 ± 0.00098 | 0.12403 ± 0.00054 |
| Own-error priorities | 0.20143 ± 0.00143 | 0.12219 ± 0.00050 |
| Shuffled priorities | 0.20204 ± 0.00083 | 0.12197 ± 0.00291 |
| Full-data uniform | 0.20446 ± 0.00098 | 0.12403 ± 0.00054 |

1,082 admissions/1,024 patients; exploratory reuse of the previously observed v0.21 test. Weight assignment, training budgets, tool members and every prediction are independently checked.

[Full results / 完整结果](../upgrade_v23/RESULTS.en.md)

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
| v0.15 | LoRA under explicit binary inclusion supervision | Complete: priority beats uniform in one seed but trails direct top-8; final raw checkpoint collapses |
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
2. v0.15 completes all checkpoints: priority 0.29192/0.19329, uniform 0.24094/0.15072, direct top-8 0.31169/0.20739. Both select round2; raw collapse and 10/3,600 incomplete feedback receipts are disclosed.
3. v0.17 four-component, all-round and RxQA evaluations are complete. v0.18 is complete and independently recounted: fixed grounding538/988 versus frozen grounded skills510/988. Transport interruptions were resumed from cache without scoring missing responses as model errors.
4. FHIR learning restarts after a development-discovered reference-format revision; original grades remain separate. All13 affected final write receipts and8 execution contracts pass. No full ID/OOD result yet. eICU v0.25 three-seed training is running; all choices freeze before testing.
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

## Frozen-method comparison on Gemini

Same988 questions, one2,048-token/low-reasoning call, no test-time learning.

| Method | Correct /988 | Accuracy (%) | Invalid |
|---|---:|---:|---:|
| cot | 532 | 53.85 | 4 |
| frozen_author_grasp | 527 | 53.34 | 5 |
| fixed_grounded | 538 | 54.45 | 5 |
| frozen_grounded_grasp | 510 | 51.62 | 24 |

[Transfer, paired intervals and costs / 迁移、区间与费用](../upgrade_v18/RESULTS.en.md)

## Continued improvement: numerical-state development pilot complete

Represent existing lab/dose values numerically with observed flags; no future context is added. The proposal-selected word+typed policy reaches guard drug/order F1 **0.22456/0.13656**, versus the same-guard control at **0.21942/0.13458**. The continuation rule passes, but both patient-paired intervals include zero. This is one-seed development evidence, with no test scoring or RSI superiority claim.

[Development protocol/results / 开发协议与结果](../upgrade_v22/RESULTS.en.md)

## External-data preparation: eICU hospital audit complete

Retain 142,485 stays, including 8,188 test stays from 16 hospitals, with zero patient/hospital overlap across splits. Of 6,283 test-window orders without names, 6,064 retain HICL codes; name-only filtering is inappropriate. Exclude 238,680 lab values revised after the decision. This is a data audit without model scores, under a different time/order-field protocol from MIMIC.

[External audit / 外部数据审计](../upgrade_v24/RESULTS.en.md)

## External method experiment now running: v0.25

The identity-complete native-HICL cohort is built and independently audited:40,000/2,000/2,000/8,005 stays,6,227 test patients and16 test hospitals, without cross-partition patient/hospital overlap. Zero-target test stays:3,842. Complete joint labels:11,853/15,594. Three seeds/five rounds compare13 methods/ablations, including matched uniform/error/shuffled feedback. No eICU model test score yet. [Protocol and cohort](../upgrade_v25/RESULTS.en.md).

FHIR revision:13 development false negatives arose from valid note arrays versus a legacy object reference. The adapted endpoint applies identical lossless views/readback criteria to all methods and preserves raw grades. Learning restarted from empty skills. This is a scoring repair, not evolution gain. [Evidence](../upgrade_v19/RESULTS.en.md).

## Development follow-up running: candidate-position sensitivity

v0.26 freezes three model states on200 existing guard cases. Four conditions compare original prompts, explicit original ranks, rank-preserving permutations and reversal. This tests order dependence while retaining rank information; no new learning or test score is claimed. Fresh deduplicated generation uses immutable case-bound receipts. [Registered protocol](../upgrade_v26/README.en.md).
