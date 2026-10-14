# v0.12 — Does a different update gate make RSI work?

## Abstract

We replay complete, previously executed public model traces to isolate the update gate and action set. Three training orders and four rounds produce genuine changes to routing parameters, but neither gate improves over the validation-selected fixed tool on average. Some accepted updates regress on test. This is an exploratory development extension, not an untouched confirmation study.

## Data and controlled protocol

RxSafeBench-derived option selection: 625 train / 190 proposal / 197 guard / 988 test; scenario groups are disjoint. DeepSeek-V4.1-Flash, 512 output tokens per call. Actions share an identical CoT draft: retain it, review balanced label evidence, or review safety label evidence. Runtime requires one or two model calls. The indication action is excluded because 153 requests were not answered after HTTP 402; its observed score was not used for exclusion. Both gates receive the same remaining actions and 387 development labels.

Each round exposes 156/312/468/625 training cases. A fixed hashing representation encodes the question, options and initial answer. Ridge routing weights learn the observed improvement of each evidence action over CoT. The 3 regularizers × 3 thresholds are chosen using either proposal selection plus an independent guard, or all 387 validation cases jointly. The latter reduces validation fragmentation but has no separate regression check. Every round choice was frozen before this script scored test outputs; the test had already been observed in prior increments.

## Same-task comparison

| Method | Accuracy (%) | Seed SD (pp) | Mean model calls |
|---|---:|---:|---:|
| Frozen CoT | 47.27 | — | 1 |
| Validation-selected fixed evidence review | 48.99 | — | 2 |
| Fixed safety evidence review | 49.29 | — | 2 |
| Evolving router: independent guard | 48.68 | 0.61 | 1.710 |
| Evolving router: joint validation | 48.79 | 0.54 | 1.490 |

The selected fixed review is balanced, chosen without test labels. The safety row is a prespecified fixed control, not a test-selected winner. SD measures order sensitivity across three seeds. All rows use complete received responses; malformed received answers count wrong. No new model requests were made for this replay. Counterfactual action generation during development has a higher cost than the one/two-call runtime, and is not free training feedback.

## What actually evolves

Only the routing coefficients, intercepts and decision threshold change. The LLM weights, label corpus, retrieval code and feature transform stay fixed. The version journal records parameter hashes, training counts, candidates, guard fixes and regressions. This is learned tool routing; it is not tool-source-code evolution or medical knowledge discovery.

![Round trajectories](round_curves.png)

| Gate / seed | Round | Seen cases | Promoted | Active training cases | Correct / 988 | Fixes / regressions vs previous |
|---|---:|---:|---|---:|---:|---:|
| independent_guard_seed_42 | 1 | 156 | True | 156 | 481 | 116 / 102 |
| independent_guard_seed_42 | 2 | 312 | False | 156 | 481 | 0 / 0 |
| independent_guard_seed_42 | 3 | 468 | False | 156 | 481 | 0 / 0 |
| independent_guard_seed_42 | 4 | 625 | False | 156 | 481 | 0 / 0 |
| joint_validation_seed_42 | 1 | 156 | True | 156 | 481 | 116 / 102 |
| joint_validation_seed_42 | 2 | 312 | True | 312 | 484 | 66 / 63 |
| joint_validation_seed_42 | 3 | 468 | False | 312 | 484 | 0 / 0 |
| joint_validation_seed_42 | 4 | 625 | False | 312 | 484 | 0 / 0 |
| independent_guard_seed_137 | 1 | 156 | False | 0 | 467 | 0 / 0 |
| independent_guard_seed_137 | 2 | 312 | True | 312 | 487 | 108 / 88 |
| independent_guard_seed_137 | 3 | 468 | False | 312 | 487 | 0 / 0 |
| independent_guard_seed_137 | 4 | 625 | False | 312 | 487 | 0 / 0 |
| joint_validation_seed_137 | 1 | 156 | True | 156 | 470 | 24 / 21 |
| joint_validation_seed_137 | 2 | 312 | False | 156 | 470 | 0 / 0 |
| joint_validation_seed_137 | 3 | 468 | True | 468 | 486 | 56 / 40 |
| joint_validation_seed_137 | 4 | 625 | False | 468 | 486 | 0 / 0 |
| independent_guard_seed_2026 | 1 | 156 | False | 0 | 467 | 0 / 0 |
| independent_guard_seed_2026 | 2 | 312 | True | 312 | 475 | 16 / 8 |
| independent_guard_seed_2026 | 3 | 468 | False | 312 | 475 | 0 / 0 |
| independent_guard_seed_2026 | 4 | 625 | False | 312 | 475 | 0 / 0 |
| joint_validation_seed_2026 | 1 | 156 | False | 0 | 467 | 0 / 0 |
| joint_validation_seed_2026 | 2 | 312 | True | 312 | 480 | 31 / 18 |
| joint_validation_seed_2026 | 3 | 468 | True | 468 | 476 | 24 / 28 |
| joint_validation_seed_2026 | 4 | 625 | False | 468 | 476 | 0 / 0 |

## Interpretation and next experiment

Seed 2026 pooled selection moves from 480 to 476 correct after an accepted update: validation improvement does not guarantee test improvement. In seed 42, pooled selection matches the fixed tool at 484 correct while averaging 1.538 calls, but the other seeds do not establish a stable accuracy advantage. Independent recount and scenario-cluster paired intervals are in `results/summary.json`. The small train set and weak text-based routing signal remain plausible limitations. The next increment should add an outcome verifier with matched supervised and non-evolving controls, then confirm a frozen design on an untouched dataset or split. Reusing this test cannot establish confirmatory superiority.
