# v0.18 — Cross-backbone frozen-skill transfer

## Research question and protocol

Do DeepSeek-learned skills improve a different backbone without additional learning? Four methods use Gemini-3.8-Flash, the same 988 derived RxSafeBench questions, one call per case, low reasoning and a 2,048-token completion cap. This configuration was frozen using development results before test inference. Skill files and the openFDA snapshot are unchanged from v0.10/v0.17, with hashes checked before and after evaluation. Gemini test labels do not select skills or prompts.

## Same-backbone method comparison

| Method | Correct / 988 | Accuracy (%) | Invalid | Logical inference USD |
|---|---:|---:|---:|---:|
| CoT | 532 | 53.85 | 4 | 1.9454 |
| Frozen author-GRASP skills | 527 | 53.34 | 5 | 2.6209 |
| Fixed grounded harness | 538 | 54.45 | 5 | 2.5229 |
| Frozen grounded skills | 510 | 51.62 | 24 | 3.9129 |

## Paired contrasts / 配对差异

| Contrast | Difference (pp) | Scenario-cluster 95% interval (pp) | Fixes / regressions |
|---|---:|---:|---:|
| frozen_author_grasp__minus__cot | -0.51 | [-2.23, 1.21] | 34 / 39 |
| fixed_grounded__minus__cot | 0.61 | [-2.13, 3.24] | 99 / 93 |
| frozen_grounded_grasp__minus__cot | -2.23 | [-5.26, 0.81] | 108 / 130 |
| frozen_grounded_grasp__minus__fixed_grounded | -2.83 | [-4.85, -0.81] | 38 / 66 |
| frozen_grounded_grasp__minus__frozen_author_grasp | -1.72 | [-4.86, 1.32] | 112 / 129 |

## Post-hoc failure diagnosis

Grounded skills regress by 2.83 percentage points versus fixed grounding, with paired interval [-4.85,-0.81]. Of 24 invalid skill outputs, 23 end at the length cap. Ten formerly correct cases become invalid. However, among 961 cases where both outputs are valid, correct answers still fall from 528 to 508; truncation alone does not explain the loss. This conditional subset is diagnostic, not a replacement leaderboard. Mean prompt length rises from 1,666.81 to 2,831.81 tokens. No test-driven change is applied to this frozen comparison.

## Interpretation and verification

This tests transfer of persistent language artifacts. LLM weights, tool code and skill text do not evolve during this test. Completion cap and call count match within this table; input lengths and returned usage differ. Costs are logical successful-response usage, including cache reuse, rather than reconciled provider bills; transport retries can add charges with no returned usage. The DeepSeek source studies used a different completion cap, so raw cross-backbone scores are not an equal-compute comparison. One frozen skill-learning path does not establish seed robustness.

Every prediction was aligned to its case and independently rescored. Received malformed answers count as wrong; incomplete transport responses cannot enter the table. Paired intervals resample source-scenario clusters (4,000 draws); they are descriptive and not corrected for multiple comparisons. Negative transfers and regressions are retained. The repository contains aggregates and code; no restricted patient data entered these requests.
