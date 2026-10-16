# RxRSIAgent: evolution mechanism and round-level evidence

Updated 2026-10-15. Independently checked against original update logs,625 training records, saved skill files and predictions; no new actor calls. **The measured evolving object is persistent language skills, not every module.**

[Manuscript](latex/v0.3/prismatic_v03_en.tex) · [Audit data](../rxrsiagent/results/evolution_audit.json) · [Audit code](../rxrsiagent/audit_evolution.py) · [Clinical endpoints](CLINICAL_EVALUATION.en.md)

## 1. Credited update mechanism

We reuse the unchanged GRASP author core at `9d7d125a3e9b46ed591692475eb07aff4ae67d34`; its commit and clean core were checked. Prescription task/evidence interfaces and evaluation are our additions, not the optimizer.

1. Freeze backbone, label tool/corpus and output contract; initialize an empty skill repository.
2. Process 157/157/157/154 new training cases, retaining outputs and labeled failures.
3. Propose four edits per round. The core supports ADD/MODIFY/REMOVE; this run accepts one ADD and two MODIFY operations.
4. Compare candidates and a replayed incumbent on 40 training probes, targeting 20 failures/20 successes. The reconstructed overlap with the current proposal batch is40/0/0/0. First-round probes reuse the same training batch, not independent validation.
5. Score`S=(F−F_b)−(R−R_b)−I`, whereF/R are fixes/regressions, the subscriptb denotes replayed-incumbent values, andI counts new invalid-action regressions already included inR. Accept the highest-scoring eligible candidate only if S>0 and R≤R_b. Contrastive revisions obey the same gate.
6. Development is evaluated **only at baseline and the end of the single epoch**:190/387→206/387. No per-round development curve exists. Intermediate test/transfer readouts occur after checkpoint selection and cannot choose the retained state.

[Execution adapter](../upgrade_v17/run_grounded_skills.py) · [GRASP paper](https://arxiv.org/abs/2605.29668)

## 2. Cases, artifact changes and outcomes

| Round | Cases | Skills / body words | Recorded change | RxSafe correct/988 | RxQA correct/300 |
|---:|---:|---:|---|---:|---:|
| 0 | 0 | 0 / 0 | No learned skill; fixed label evidence. | 499 | 188 |
| 1 | 157 | 0 / 0 | All four proposals rejected by the regression gate; no retained change. | 499 | 188 |
| 2 | 314 | 1 / 711 | Adds indication matching followed by patient-triggered label cautions. | 475 | 175 |
| 3 | 471 | 1 / 645 | Revises the distinction between triggered stop language and monitoring cautions. | 493 | 175 |
| 4 | 625 | 1 / 774 | Requires checking stop clauses even for the only indication-matching option; expands output evidence instructions. | 501 | 183 |

Round 1 reuses unchanged-state predictions, not an independent evaluation. Body words are whitespace-delimited with metadata excluded; **artifact size is not capability**. Semantic descriptions concern generated text, not verified clinical rules.

### Accepted edits and their probe gates

| Round | Evaluations incl. revision | Accepted operation | Candidate fixes/regressions | Incumbent fixes/regressions | S |
|---:|---:|---|---:|---:|---:|
| 1 | 4 | NONE | — | — | — |
| 2 | 4 | ADD | 3/0 | 0/0 | 3 |
| 3 | 5 | MODIFY | 7/2 | 2/2 | 5 |
| 4 | 4 | MODIFY | 3/0 | 2/1 | 2 |

Sixteen initial proposals plus one contrastive revision produce three retained edits. Round 3 accepts a candidate with two regressions because incumbent replay also has two; this is not a guarantee of zero regressions.

[Actual round2 skill](../upgrade_v17/artifacts/round_2/label_indication_and_caution_parsing.md) · [Round 3](../upgrade_v17/artifacts/round_3/label_indication_and_caution_parsing.md) · [Round4](../upgrade_v17/artifacts/round_4/label_indication_and_caution_parsing.md)

## 3. Improvements and regressions between states

| Adjacent transition | RxSafe fixes/regressions | RxQA fixes/regressions |
|---|---:|---:|
| 0 → 1 | 0 / 0 | 0 / 0 |
| 1 → 2 | 70 / 94 | 19 / 32 |
| 2 → 3 | 74 / 56 | 17 / 17 |
| 3 → 4 | 76 / 68 | 22 / 14 |

Final versus initial paired changes are 83 fixes/81 regressions on RxSafe (net+2), and 19/24 on RxQA (net−5). Do not sum adjacent-round repairs as a final benefit: the same question can flip repeatedly. Figure2 plots the full trajectory; Table4 records cases and artifacts.

## 4. Module-level changes

| Module | Actual update | Supported interpretation |
|---|---|---|
| Language skills |0→1 retained skill; one addition, two modifications;711→645→774 words|Behavior changes; small test gain and negative transfer|
| Label retrieval |Frozen during learning; later researcher repair|Excerpt availability1→214/300 and dosage0→193; no new accuracy or autonomous tool-code evolution|
| Order tool |Separate eICU component learning|Fixed drug sets: joint-order F1 0.02334→0.02838, completeness53.67%→51.13%; not a QA-agent gain|
| Clinical review |Manual18-domain interfaces and12 structural software checks|Engineering scope, not measured clinical correctness or experience-driven growth|
| Weights/output contract |Frozen in this skill experiment|Zero updates; no invented improvement|

## 5. Required next evidence

Use at least three seeds, independent test cases and matched budgets, comparing fixed memory, ordinary feedback, shuffled feedback and gate removal. Record operations, provenance and behavioral changes, and swap one module while holding others fixed. Full-order trajectories also require the [clinician-oriented endpoints](CLINICAL_EVALUATION.en.md), establishing that broader coverage does not increase major errors. Unknowns are not passes.

These public benchmarks were historically observed, so trajectories remain exploratory. This audit did not resume long-running queues, call providers or produce new clinical-effectiveness scores.
