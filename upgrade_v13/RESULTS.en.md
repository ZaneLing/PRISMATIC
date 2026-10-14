# v0.13 — Outcome-aware revision verification

## Motivation and executed mechanism

The v0.12 router chooses a tool before observing its output. This increment instead learns whether to retain the initial answer or accept the completed grounded revision. It uses the same complete CoT/balanced traces on 625 train / 190 proposal / 197 guard / 988 test cases. Every verifier consumes two model calls; returning the initial answer does not erase the review cost. No new network calls are needed for replay.

The verifier combines option-mention/negation/positive-word relations with optional separate fixed word/bigram hashes of the question, draft and revision. Ridge predicts the revision's correctness gain. Four rounds expose 156/312/468/625 training cases. Uniform and error-prioritized arms have identical examples and 18 candidate settings per round. Error priorities are measured before updates and target only reachable answer-selection failures; each old weight retains its pre-update value. The 190-case proposal set chooses settings and the 197-case guard requires net repairs. A full-data, ordinary supervised verifier is an additional strong control. All choices freeze before this increment's test scoring; this test was already observed in prior development.

## Common-task results

| Method | Accuracy (%) | Seed SD (pp) | Calls |
|---|---:|---:|---:|
| CoT | 47.27 | — | 1 |
| Fixed balanced review | 48.99 | — | 2 |
| Full-data ordinary verifier | 47.87 | — | 2 |
| Incremental uniform verifier | 49.12 | 0.23 | 2 |
| Incremental error_prioritized verifier | 49.02 | 0.06 | 2 |
| Author GRASP core + task adapter (v0.10) | 50.81 | — | 1 |

All rows use the same public derived option task and DeepSeek-V4.1-Flash traces. The GRASP row is the already completed unmodified author core with our task adapter; its development mechanism/budget differs. It remains the strongest executed row here. Incremental uniform verification slightly improves the point estimate over fixed review, while error prioritization does not outperform uniform updates.

## Actual evolution and trajectories

Only verifier coefficients/intercepts/threshold and training feedback weights change. Backbone parameters, tool implementation and evidence corpus do not change. Parameter and feedback hashes are released, along with every accepted/rejected candidate.

![Test trajectories](round_curves.png)

| Arm / seed | Correct across rounds 0→4 | Promoted rounds |
|---|---|---|
| uniform / 42 | 484 → 484 → 484 → 484 → 484 | none |
| uniform / 137 | 484 → 484 → 488 → 488 → 488 | 2 |
| uniform / 2026 | 484 → 484 → 484 → 484 → 484 | none |
| error_prioritized / 42 | 484 → 485 → 485 → 485 → 485 | 1 |
| error_prioritized / 137 | 484 → 484 → 484 → 484 → 484 | none |
| error_prioritized / 2026 | 484 → 484 → 484 → 484 → 484 | none |

The union of the two answers contains a correct answer in 586/988 cases. This label-dependent upper bound is a diagnostic only, never an evaluated agent. It suggests selection headroom but does not show that the current features can identify it.

## Verification and limitations

Independent recount checks case alignment, every count, transition and two-response cost. Scenario-cluster paired intervals are in `results/summary.json`; they are descriptive and unadjusted for multiple comparisons. Three leakage/accounting tests pass. During 150 fits, the numerical backend issued 225 dense-multiplication warnings; all coefficients, intercepts and scored predictions remained finite. An independent elementwise weighted-intercept recount differs by at most 1.12e-16. This audit is retained rather than interpreting warnings as silent valid predictions.

This small, repeatedly used development benchmark still does not establish an RSI advantage. Further tuning on it should be treated as exploratory; final claims require a frozen design and untouched confirmation. The ongoing local QLoRA study separately tests actual language-model parameter updates.
