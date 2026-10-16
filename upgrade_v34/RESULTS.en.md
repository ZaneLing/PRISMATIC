# Medical-agent comparisons and counterexample-scoped skill learning

Date:2026-10-16. Completed and independently audited. **The +10 percentage-point engineering target is not met.** No large-gain or mature-RSI claim is made.

## 1. Executed named methods

| Method | RxSafeBench | RxQA | Mean calls: RxSafe / RxQA |
|---|---:|---:|---:|
| MedAgents (author workflow adapter) | 468/988 (47.37%) | 208/300 (69.33%) | 20.05 / 18.88 |
| MDAgents (author workflow adapter) | 478/988 (48.38%) | 199/300 (66.33%) | 4.47 / 5.03 |
| CoT | 467/988 (47.27%) | 193/300 (64.33%) | 1 / 1 |
| GRASP author core | 502/988 (50.81%) | 189/300 (63.00%) | 1 / 1 |
| RxRSIAgent retained checkpoint | 501/988 (50.71%) | 183/300 (61.00%) | 1 / 1 |

All rows share the DeepSeek V4.1 Flash identifier and question identities. Budgets differ. MedAgents uses its author five-stage syn_verif workflow, original stage limits and up to3 voting rounds. MDAgents uses its author adaptive workflow,1024 output tokens/call and zero demonstrations on these new tasks. Both have explicit80-call/24000-output-token per-case ceilings. Legacy controls use one512-token call. Therefore this table supplies missing method measurements, not an equal-compute superiority test. SafeRx-Agent remains unexecuted under this protocol; its ATC medication-set task must not be conflated with QA.

Sources: [MedAgents author repository](https://github.com/gersteinlab/MedAgents), [MDAgents author repository](https://github.com/mitmedialab/MDAgents). Pins, source hashes and all adaptations are in [protocol.json](protocol.json). Source repositories remain unmodified; the adapter loads pinned functions and applies declared repairs. This is an author-workflow task adaptation, not reproduction of an original paper's score.

Development preflight fixed quoted-answer parsing, MDAgents recruitment formatting and missing initial/final report handling. The same medication-choice task instruction was added to both author adapters for raw RxSafe consultations. Original debug runs and protocol hashes are retained; official test scoring starts only after [comparison freeze](comparison_freeze.json). Invalid/budget-exhausted received trajectories are included in the denominator; transport failures cannot be scored as model errors.

Development inspection also identifies explicit claims that no listed option is appropriate. These are not empty API outputs. The audit distinguishes empty final text from no-valid-option assertions; a model assertion does not establish that the reference is wrong. Both remain scored under the frozen forced-choice protocol, with clinical adjudication still needed for disputed items.

## 2. What actually evolved?

Only procedural memory cards changed. Model weights, source tools and optimizer code stayed fixed. Each card has observable positive conditions, exclusion conditions, a procedure, training-error support IDs and distinct successful counterexample IDs. At inference, a TF-IDF shortlist feeds a semantic router; at most2 cards can activate, each with an exact input quotation. The model checks exclusion conditions; this is not a proven clinical-rule validator. Activated cards include one training support and one contrasting example.

Four rounds expose156/312/468/625 unique training cases. Proposal190 and guard197 must both improve correct count without increasing invalid outputs. Every rejection is retained. Three seeds change training order; they are not three independent test cohorts. A development-only schema repair clarified case roles and allows one failed-schema correction. All three trajectories were restarted under the same repaired implementation before any MedQA inference; initial trajectories remain in development_history.

| Round | Unique training cases | Seed42: skills / MedQA correct | Seed137 | Seed2026 |
|---:|---:|---:|---:|---:|
| 0 | 0 | 0 / 166 | 0 / 166 | 0 / 166 |
| 1 | 156 | 0 / 166 | 0 / 166 | 0 / 166 |
| 2 | 312 | 0 / 166 | 0 / 166 | 2 / 170 |
| 3 | 468 | 0 / 166 | 0 / 166 | 2 / 170 |
| 4 | 625 | 1 / 167 | 0 / 166 | 2 / 170 |

Identical retained states reuse identical responses; flat repeated points are not new stochastic replications. The retained artifacts contain one general interaction/contraindication procedure in seed42, none in137, and two selection procedures in2026. One2026 procedure prefers a named active ingredient when relevant; this presents a shortcut-learning concern despite its exclusions and must not be treated as validated medical guidance.

## 3. Independent-task transfer

Two hundred MedQA questions were frozen by question-text hash before learning, excluding normalized exact overlap with the existing public cases. No answer, difficulty or method outcome selected them. They are general medical-reasoning questions, not a full-prescription benchmark; model pretraining exposure and semantic duplication are not ruled out. All three final trajectories were frozen before evaluation, and no test-selected seed replaces the main method.

| Method | MedQA correct | Accuracy | Mean calls |
|---|---:|---:|---:|
| MedAgents | 172/200 | 86.00% | 18.59 |
| MDAgents | 173/200 | 86.50% | 4.29 |
| Empty memory control | 166/200 | 83.00% | 1 |
| Scoped-memory candidate, seed42 | 167/200 | 83.50% | 2.00 |
| Scoped-memory candidate, seed137 | 166/200 | 83.00% | 1.00 |
| Scoped-memory candidate, seed2026 | 170/200 | 85.00% | 2.00 |

| Seed | Transfer gain (pp) | Paired95% interval (pp) | Fixes / regressions |
|---:|---:|---:|---:|
| 42 | +0.50 | [-1.00, +2.00] | 2 / 1 |
| 137 | +0.00 | [+0.00, +0.00] | 0 / 0 |
| 2026 | +2.00 | [+0.00, +4.50] | 5 / 1 |

Mean gain across the three observed training orders is **0.83pp**. These gains are too small for the declared target. The active-memory arm also adds a router call; equal-data retrieval and matched-budget refinement/shuffled-feedback controls are still required for a causal learning claim. We do not promote the candidate or replace the incumbent main-table checkpoint based on these scores.

## 4. Large-gain acceptance and next work

The engineering objective is +10 absolute points over the strongest fully executed same-task comparator, with a matched-budget analysis, independent-task confirmation, paired intervals and three training seeds. It is a target, not a promised outcome. A large gain over a weak or broken adapter is not sufficient.

The next mechanism should address missing evidence and executable clinical actions: candidate-balanced and formulation-aware evidence, explicit patient-fact requirements, and source-backed calculations/verification. Updates need support/counterexample execution tests and separate measurements for autonomous changes and researcher fixes. Further unconstrained textual-card growth is not supported by this experiment. Complete the missing compute/data controls and clinical endpoints before a superiority or prescribing-safety claim. Neither an unavailable resource nor an unassessed safety dimension is counted as a pass.

## 5. Artifacts and cost

[Runner](run_comparators.py) · [Author adapters](medical_agents.py) · [Memory implementation](scoped_memory.py) · [Learning runner](run_memory.py) · [Independent audit](results/audit.json) · [Summary](results/summary.json).

Incremental successful-response ledger: approximately **USD15.405**, including development/debug runs; this is not a reconciled provider bill. Logical per-method usage includes exact cache reuse. Only public QA was sent. Restricted records and raw receipts remain local. Earlier paused queues were not resumed.
