# RxRSIAgent: current manuscript and measured results

Updated 2026-10-16. **The large-gain objective remains unmet.** The current paper retains one development-selected RxRSIAgent. Two medical-agent author workflows are now fully evaluated on identical questions, with explicitly different budgets. No historical test checkpoint is replaced by a test-selected candidate.

## Main comparison — paper Table 2

| Method | RxSafeBench | RxQA OpenFDA | Mean calls: RxSafe / RxQA |
|---|---:|---:|---:|
| MedAgents | 468/988 (47.37%) | 208/300 (69.33%) | 20.05 / 18.88 |
| MDAgents | 478/988 (48.38%) | 199/300 (66.33%) | 4.47 / 5.03 |
| GRASP | 502/988 (50.81%) | 189/300 (63.00%) | 1 / 1 |
| **RxRSIAgent** | **501/988 (50.71%)** | **183/300 (61.00%)** | 1 / 1 |
| SafeRx-Agent | — | — | — |

The same served DeepSeek V4.1 Flash identifier is used. MedAgents/MDAgents are task adapters of pinned author workflows, with declared source repairs, not reproductions of original paper scores. GRASP and the retained RxRSIAgent use one512-token actor call; multi-agent workflows use more calls. SafeRx-Agent remains unexecuted. RxSafeBench is the local three-option task; RxQA comprises all300 public OpenFDA questions, excluding unavailable BNF data.

## What changed and did it work?

- Skills now declare positive conditions, exclusions, procedures, training-error support and successful counterexamples. Runtime activation requires an exact input quotation.
- Three training orders, four rounds and625 unique cases produce1/0/2 retained cards. Model weights, tools and optimizer code stay fixed.
- A200-question MedQA task was frozen before learning; all state sequences froze before evaluation. Initial166/200 becomes167/166/170. Mean gain: **0.83pp**; MedAgents172/200 and MDAgents173/200 remain stronger.
- These are general medical-reasoning results, not complete-prescription quality. Equal-data, shuffled-feedback and matched-budget controls remain missing. No mature-RSI or superiority claim is supported.
- The +10 absolute-point objective is an engineering target, not a promised result. Missing evidence, applicability-aware tools and executable clinical checks are the next mechanism priorities.

## Paper and evidence map

Table2: named methods and costs; Tables3–4: retained-agent ablations and trajectory; Table10: rejected retrieval repair; Table11: three scoped-memory trajectories; Table12: independent MedQA task. Figure1 shows the full architecture. Tables5–9 preserve separate order-tool evidence, cases, retrieval, clinical rubric and module attribution. Clinical ratings are still pending.

[Full bilingual experiment report](../upgrade_v34/RESULTS.en.md) · [中文报告](../upgrade_v34/RESULTS.zh.md) · [Audited results](../upgrade_v34/results/audit.json) · [Code and reproduction](../upgrade_v34/README.md) · [English ACL manuscript](latex/v0.3/prismatic_v03_en.tex) · [Architecture](RXRSI_DESIGN.en.md) · [Clinical endpoints](CLINICAL_EVALUATION.en.md) · [Previous report](versions/v0.33-2026-10-16.en.md).

This batch's incremental successful-response ledger is approximately USD15.405, including development attempts; it is not a reconciled provider bill. Public QA only. Older research queues remain paused.
