# eICU: audited development learning curves

## Scope

This retrospective analysis reexecutes 45 already completed checkpoints: three seeds × three feedback arms × five rounds. It opens only the development bundle. The guard contains 2,000 stays, 1,912 patients and 17 hospitals, including 1,001 stays with no target medication. The separate 8,005-stay test remains behind the original complete-selection gate.

The original parameter hashes, 60-epoch records, seen-only tool memberships, seven proposal thresholds and all guard accept/reject decisions are checked. Saved policies and tools are reexecuted; set metrics are counted without calling the training scorer. This is not an independent refit of the optimizer or tool implementation. The final registered audit separately checks feedback weights and test predictions.

## Case-growth curves

![Raw and guard-accepted development curves](development_round_curves.png)

Shading is sample standard deviation over three seeds, not a confidence interval. The horizontal axis counts cases encountered; a rejected update retains an earlier policy/tool bundle. Accepted curves are evaluated on the same guard that selects them and cannot establish generalization.

### Raw checkpoints

| Round | Stays encountered | Uniform drug / order | Own-error drug / order | Shuffled drug / order |
|---|---:|---:|---:|---:|
| 0 | 8,000 | 0.10840 ± 0.00111 / 0.01573 ± 0.00114 | 0.10840 ± 0.00111 / 0.01573 ± 0.00114 | 0.10840 ± 0.00111 / 0.01573 ± 0.00114 |
| 1 | 16,000 | 0.12684 ± 0.00203 / 0.02375 ± 0.00141 | 0.11725 ± 0.00107 / 0.02073 ± 0.00170 | 0.12095 ± 0.00176 / 0.02204 ± 0.00238 |
| 2 | 24,000 | 0.13636 ± 0.00240 / 0.02734 ± 0.00180 | 0.12530 ± 0.00319 / 0.02467 ± 0.00332 | 0.12941 ± 0.00263 / 0.02604 ± 0.00234 |
| 3 | 32,000 | 0.13755 ± 0.00421 / 0.02679 ± 0.00165 | 0.13192 ± 0.00627 / 0.02501 ± 0.00357 | 0.13438 ± 0.00684 / 0.02674 ± 0.00296 |
| 4 | 40,000 | 0.13936 ± 0.00287 / 0.02653 ± 0.00090 | 0.13281 ± 0.00429 / 0.02388 ± 0.00285 | 0.13770 ± 0.00223 / 0.02606 ± 0.00032 |

### Guard-accepted states

| Round | Stays encountered | Uniform drug / order | Own-error drug / order | Shuffled drug / order |
|---|---:|---:|---:|---:|
| 0 | 8,000 | 0.10840 ± 0.00111 / 0.01573 ± 0.00114 | 0.10840 ± 0.00111 / 0.01573 ± 0.00114 | 0.10840 ± 0.00111 / 0.01573 ± 0.00114 |
| 1 | 16,000 | 0.12684 ± 0.00203 / 0.02375 ± 0.00141 | 0.11725 ± 0.00107 / 0.02073 ± 0.00170 | 0.12095 ± 0.00176 / 0.02204 ± 0.00238 |
| 2 | 24,000 | 0.13636 ± 0.00240 / 0.02734 ± 0.00180 | 0.12530 ± 0.00319 / 0.02467 ± 0.00332 | 0.12941 ± 0.00263 / 0.02604 ± 0.00234 |
| 3 | 32,000 | 0.13866 ± 0.00319 / 0.02696 ± 0.00136 | 0.13192 ± 0.00627 / 0.02579 ± 0.00415 | 0.13438 ± 0.00684 / 0.02674 ± 0.00296 |
| 4 | 40,000 | 0.14021 ± 0.00347 / 0.02769 ± 0.00011 | 0.13402 ± 0.00594 / 0.02784 ± 0.00066 | 0.13601 ± 0.00594 / 0.02769 ± 0.00131 |

## Final-round paired differences

| State | Own-error minus | Drug F1 Δ | Joint-order F1 Δ |
|---|---|---:|---:|
| raw | Uniform updates | -0.00655 | -0.00264 |
| raw | Shuffled priorities | -0.00488 | -0.00217 |
| accepted | Uniform updates | -0.00619 | +0.00015 |
| accepted | Shuffled priorities | -0.00199 | +0.00014 |

**Observed finding:** raw final own-error-minus-uniform drug/order F1 is -0.00655/-0.00264; for guard-accepted states it is -0.00619/+0.00015. Case-growth gains alone do not establish a benefit from assigning priorities to the model's own errors. A small positive order difference must be considered alongside the drug difference and guard selection.

Differences pair the same seed, cases, round budget and outcome protocol, then average three seed differences. All individual seed values remain in the JSON. These are descriptive development comparisons without significance claims.

## Raw regressions and final selection

| Method | Raw drug declines / 12 | Raw order declines / 12 | Accepted rounds, seeds 42 / 137 / 2026 |
|---|---:|---:|---|
| Uniform updates | 2 | 4 | 4 / 3 / 3 |
| Own-error priorities | 1 | 4 | 4 / 3 / 2 |
| Shuffled priorities | 1 | 4 | 4 / 3 / 3 |

## Final accepted-state output behavior

| Method | Drug precision | Drug recall | Empty % | Mean predicted codes |
|---|---:|---:|---:|---:|
| Uniform updates | 0.16113 | 0.12420 | 44.55 | 1.142 |
| Own-error priorities | 0.14413 | 0.12544 | 36.13 | 1.294 |
| Shuffled priorities | 0.15386 | 0.12195 | 42.95 | 1.174 |

## What this does and does not show

Read improvement over the initial 8k state separately from the benefit of own-error feedback over uniform or shuffled training. The guard promotion rule creates selection effects, and individual raw rounds can regress. No language model or API is used in this study. These native HICL/route/dosage/frequency results measure agreement with documented orders, not clinical safety or ATC benchmark superiority. Static controls and the held-out hospital test will be reported only after their registered execution and audits finish.

[Source-bound replay results](results/development_curves.json) · [Full study](RESULTS.en.md)
