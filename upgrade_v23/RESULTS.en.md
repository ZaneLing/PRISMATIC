# v0.23 — Does own-error feedback outperform ordinary learning?

## Question and matched controls

Following v0.22, freeze word+numeric features and 128 drug names. Three seeds run 8k/16k/24k/32k/40k cumulative cases, comparing uniform updates, priorities from the currently accepted policy's errors, and the same block's weights randomly permuted. Error weights are 1+3×reachable-drug-F1 error, normalized to mean 1 during fitting. The two priority arms have the same weight distributions; only case assignments differ.

Every arm trains 128 classifiers for exactly 60 epochs per round, without early stopping. Within each seed, cases, exposure order and update counts match. The initial 8k model is shared. Order tools use only currently observed cases and are shared within seed/round; rejected versions retain the previous policy/tool bundle. Seven thresholds compete on proposal, followed by a separate guard. All seeds/arms freeze before new test inference.

Changing objects are selection parameters, persistent case-feedback weights and conditional-tool parameters. LLM weights and executable code stay fixed. This tests supervised feedback updates, not autonomous LLM evolution. Rounds are retrospective case blocks rather than calendar deployment; training patients may occur in several rounds.

## Completed method comparison

Same 1,082 test admissions and 1,024 patients. **The v0.21 test was previously observed; this is exploratory reuse and still requires untouched confirmation.** The older word/character row has a different early-stopping/search budget and is contextual only. The three present feedback arms have strictly matched epochs and case exposures.

| Method / 方法 | Drug F1 mean ± SD | Core-order F1 mean ± SD | Empty (%) |
|---|---:|---:|---:|
| Initial 8k state | 0.16840 ± 0.00076 | 0.10130 ± 0.00101 | 1.26 |
| Full-data uniform state | 0.20446 ± 0.00098 | 0.12403 ± 0.00054 | 1.85 |
| Uniform round updates | 0.20446 ± 0.00098 | 0.12403 ± 0.00054 | 1.85 |
| Own-error-prioritized updates | 0.20143 ± 0.00143 | 0.12219 ± 0.00050 | 2.53 |
| Same-distribution shuffled priorities | 0.20204 ± 0.00083 | 0.12197 ± 0.00291 | 1.51 |
| Error priorities, initial tool frozen | 0.20143 ± 0.00143 | 0.11909 ± 0.00177 | 2.53 |
| v0.21 word/character reference (different optimization budget) | 0.20096 ± 0.00255 | 0.12071 ± 0.00283 | 4.10 |

## Findings

Uniform updates score 0.20446/0.12403, own-error priorities 0.20143/0.12219 and shuffled priorities 0.20204/0.12197. Priorities do not outperform uniform updates. Drug and order intervals include zero in all three seeds, so established inferiority is not claimed either. The shuffled-assignment contrast shows no consistent advantage. The uniform point estimate exceeds the older word/character reference, but different optimization budgets prevent attributing that difference solely to numerical representation.

Own-error round means rise from 0.16840/0.10130 to 0.20143/0.12219, with regressions in individual seed/endpoint trajectories. Freezing the initial tool yields order F1 0.11909: the updated-tool mean difference is+0.00311, with an interval excluding zero in only one seed. These are actual parameter/tool changes without an established unique RSI benefit or stable tool effect. Full-data uniform and the final accepted uniform state coincide because every seed accepts its last checkpoint.

## Fixed-test trajectories / 固定测试轨迹

| Round | Cumulative cases | Uniform drug/order F1 | Own-error drug/order F1 | Shuffled drug/order F1 |
|---|---:|---:|---:|---:|
| 0 | 8,000 | 0.16840/0.10130 | 0.16840/0.10130 | 0.16840/0.10130 |
| 1 | 16,000 | 0.18966/0.11359 | 0.18009/0.10651 | 0.18443/0.11016 |
| 2 | 24,000 | 0.19823/0.11994 | 0.19332/0.11624 | 0.19547/0.11910 |
| 3 | 32,000 | 0.20261/0.12242 | 0.19956/0.12021 | 0.20214/0.12149 |
| 4 | 40,000 | 0.20446/0.12403 | 0.20143/0.12219 | 0.20204/0.12197 |

![Accepted-state curves](round_curves.png)

## Paired causal controls / 配对机制对照

| Seed | Contrast | Drug Δ | Order Δ | Drug 95% interval | Order 95% interval |
|---|---|---:|---:|---:|---:|
| 42 | Error priority − uniform | -0.00236 | -0.00123 | [-0.00705,+0.00205] | [-0.00466,+0.00214] |
| 42 | Error priority − permuted_priority | +0.00190 | +0.00341 | [-0.00191,+0.00554] | [+0.00072,+0.00600] |
| 42 | Error priority − full_data_uniform | -0.00236 | -0.00123 | [-0.00705,+0.00205] | [-0.00466,+0.00214] |
| 137 | Error priority − uniform | -0.00229 | -0.00177 | [-0.00654,+0.00174] | [-0.00532,+0.00154] |
| 137 | Error priority − permuted_priority | -0.00123 | -0.00180 | [-0.00524,+0.00254] | [-0.00489,+0.00121] |
| 137 | Error priority − full_data_uniform | -0.00229 | -0.00177 | [-0.00654,+0.00174] | [-0.00532,+0.00154] |
| 2026 | Error priority − uniform | -0.00444 | -0.00252 | [-0.00931,+0.00043] | [-0.00641,+0.00138] |
| 2026 | Error priority − permuted_priority | -0.00249 | -0.00096 | [-0.00674,+0.00139] | [-0.00425,+0.00217] |
| 2026 | Error priority − full_data_uniform | -0.00444 | -0.00252 | [-0.00931,+0.00043] | [-0.00641,+0.00138] |

## Independent verification and interpretation

Re-infer every feedback block with the prior accepted checkpoint, independently recount set errors, verify shuffled distributions, every classifier's 60 epochs, seen-only tool members, frozen selections and every test prediction. Per-case repairs/regressions, promotions/rejections and parameter/tool/weight hashes are retained in `results/summary.json` and journals. Freezing the initial tool does not retune other components and measures conditional dependence within the final state.

Shading shows SD across three seeds. Paired patient-cluster intervals use 2,000 descriptive bootstrap draws without multiplicity correction. Error prioritization must be compared with both uniform and shuffled-weight controls; improvement over the initial model alone is insufficient. Restricted cases, weights and predictions remain local.
