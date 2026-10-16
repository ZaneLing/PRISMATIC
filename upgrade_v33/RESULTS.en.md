# RxRSIAgent: no GRASP advantage; retrieval intervention rejected

Date: 2026-10-16. Completed development experiment, independently recounted. The intervention was not promoted.

## Current test evidence

| Method | RxSafeBench, 988 | RxQA OpenFDA, 300 |
|---|---:|---:|
| CoT without evidence or learned skills | 467 (47.27%) | **193 (64.33%)** |
| Adapted GRASP author core | **502 (50.81%)** | 189 (63.00%) |
| Fixed label grounding, no learned skills | 499 (50.51%) | 188 (62.67%) |
| RxRSIAgent | 501 (50.71%) | 183 (61.00%) |

[Saved test source](../upgrade_v17/results/summary.json). RxRSIAgent answers one and six fewer questions than GRASP. Paired intervals include zero: neither a significant inferiority claim nor a superiority claim is supported. The simpler CoT control is also stronger on RxQA. MedAgents, MDAgents and SafeRx-Agent have not been run under this protocol; naming them is not an executed comparison.

## Executed development intervention

The [protocol](protocol.json) was saved before inference: identical 190 RxSafeBench development questions, DeepSeek V4.1 Flash, one call and 512 output tokens per question, crossed retrieval and frozen skill presence. Original retrieval reuses 380 exact-request historical cached outputs; repaired retrieval makes 380 new calls. All 760 outputs were independently checked against case identities, gold labels, response hashes and source code.

| Retrieval | Frozen skill | Correct | Accuracy | Invalid | Excerpts available |
|---|---|---:|---:|---:|---:|
| Original | Absent | 90/190 | 47.37% | 1 | 190/190 |
| Original | Present | **99/190** | **52.11%** | 0 | 190/190 |
| Repaired | Absent | 92/190 | 48.42% | 0 | 181/190 |
| Repaired | Present | 98/190 | 51.58% | 0 | 181/190 |

With skills held fixed, repaired retrieval fixes 29 answers and regresses 30: −0.53 percentage points, exploratory item-paired bootstrap 95% interval [−8.42, 7.37]. Input tokens rise from 517,261 to 809,651. Both skill conditions answer six of the nine newly uncovered questions correctly, so missing excerpts alone do not explain the net loss.

The prespecified gate requires strictly more correct answers and no increase in invalid answers on proposal, followed by the same requirement on the 197-question development guard. The first gate fails. Guard and test stages are not executed, and the main-table checkpoint is unchanged. Incremental cost is **USD0.294**. An execution check confirms the failed gate prevents subsequent evaluation without additional charges.

[Results](results/proposal.json) · [Audit](results/audit.json) · [Runner](run_retrieval_factorial.py) · [Recount code](audit_results.py)

## Diagnosis and next decisions

Established findings are development-to-transfer skill regression, the original RxQA lookup/dosage defect, failure of this repaired retriever to improve the complete agent on development, and dependence on the credited GRASP optimizer. A new beneficial self-improvement mechanism has not been demonstrated.

Code-level hypotheses require separate testing: global top-eight passage ranking may crowd out candidate drugs; formulation and route remain unverified; the skill's broad applicability may impose indication/label checks on unsuitable tasks. These mechanisms are plausible, not causally established by aggregate scores.

Next experiments should:

1. Execute available MedAgents/MDAgents author workflows, with explicit task adaptations and both native and matched total-token budgets. Establish SafeRx-Agent implementation/data availability before claiming comparability.
2. Test candidate-balanced, formulation-aware retrieval and task-specific dosage queries; assess relevance and answer outcomes separately under a new protocol.
3. Learn scoped procedures from training feedback, including required patient facts, tool choice and counterexamples. Distinguish researcher engineering from agent-generated updates.
4. Compare frozen skills, ordinary feedback, shuffled feedback, gate removal and RxRSIAgent across at least three seeds on a newly frozen evaluation task, recording experience, module edits, fixes, regressions and transfer. No parameter-update claim applies to fixed model weights.

These next experiments are not completed by this report. The present work is a rejected diagnostic intervention, not a successful upgrade or a new superiority result.

## Boundaries and reproduction

Only public fictional QA was sent; restricted records and raw receipts are not published. Old long-running queues remain paused. Development and test benchmarks have historical exposure, making findings exploratory. Cached controls are not contemporaneous provider reruns; the model service may change over time. In the existing local environment, run `python upgrade_v33/run_retrieval_factorial.py --stage proposal` to replay cached outputs and `python upgrade_v33/audit_results.py` to recount without model calls. Guard is blocked by the failed gate.
