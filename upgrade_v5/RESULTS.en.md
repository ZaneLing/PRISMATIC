# PRISMATIC v0.5 executed results: empty-output repair and experience updates

Version: 14 October 2026, v5-r1. Generated from executed result JSON; original v4 negative results are preserved.

## Abstract

**The v4 design had a genuine failure.** All 25 empty responses among 50 cases were valid arrays; 20 erased nonempty retrieval proposals, and 19 had observed mapped targets. The main cause was a blanket removal instruction conflating unavailable clinical evidence with historical-order prediction. The parser also had an independent all-or-nothing invalid-member failure.

The repaired free-output RAG review achieves **0.31130 F1** with **0% empty responses**, versus 0.20820 and 50% for v4. This arm does not force five predictions. The separate validation-gated harness achieves **0.41015 F1** with supervised ranking and memory candidates; it has different training resources from the pure LLM arms.

On 4,000 cases, the static word/character ensemble reaches seed-42 F1=0.39185 versus 0.38701 for the old seed-42 SGD, a paired gain of 0.00484 (patient-bootstrap 95% CI [0.00160,0.00803]). Three frozen-configuration seeds appear below. The independent residual-memory experiment improves from 0.34727 to 0.35281, delta 0.00554 (CI [0.00282,0.00833]); however, fusing memory into the stronger static ranker reduces F1 by 0.00163. More experience does not guarantee monotonic improvement.

## Dataset, protocol and comparability

- MIMIC-IV v3.1 + MIMIC-IV-ED v2.2; admission snapshot; six-hour all-route historical ATC-L4 targets.
- Patient-disjoint 40,000/4,000/4,000 train/validation/development-test admissions, 80 training-selected classes. The LLM uses the same old 50 test cases and a separate 50 validation cases for revision gating.
- Mapping coverage is 45.535%; saline-name proxy orders are absent from the map. Scores measure observed historical agreement, not appropriate indications, fluid quality or safety.
- Table 1 fixes five candidates; Table 2 permits up to five LLM outputs. Different sample sizes and set-size budgets are not interchangeable. No LLM was run on the 4,000-case panel.
- All new policy choices use validation only. The repeatedly inspected test is developmental, not independent confirmation.
- Same local frozen Qwen3-4B-Instruct-2507 4bit; no restricted data sent to OpenRouter. v4 generation cap was 192; v5 revision cap is 384. Actual tokens are reported; this is not an exactly cost-matched experiment.

## Table 1. Same-cohort method comparison / 同队列跨方法主表

| Method / 方法 | N | Observed micro-F1@5 | Classes/case | Scope / 范围 |
| --- | --- | --- | --- | --- |
| Training prevalence | 4000 | 0.28390 | 5 | v4 fixed |
| Case retrieval (30 neighbors) | 4000 | 0.32813 | 5 | v4 fixed |
| TF-IDF/SGD | 4000 | 0.38635 ± 0.00067 | 5 | 3 seeds |
| GAMENet text/single-visit adaptation | 4000 | 0.34357 ± 0.00219 | 5 | 3 seeds; NOT original reproduction |
| Static word + character ensemble | 4000 | 0.39176 ± 0.00012 | 5 | 3 seeds; validation-selected configuration |
| Static ensemble, seed 42 | 4000 | 0.39185 | 5 | ablation: no growing memory |
| PRISMATIC candidate ranker + residual memory | 4000 | 0.39022 | 5 | seed 42; 10% memory fusion; no LLM at 4k |
| SafeDrug compatible reproduction | — | — | — | not executed |
| SafeRx-Agent compatible reproduction | — | — | — | not executed |
| Clinically complete PRISMATIC | — | — | — | clinical ratings and full-order evidence missing |

## Table 2. Same 50-case local-LLM comparison / 相同 50 例本地模型对照

| Method / 方法 | F1 | Precision | Recall | Empty | Raw valid | Mean classes |
| --- | --- | --- | --- | --- | --- | --- |
| Training prevalence | 0.37632 | 0.35600 | 0.39910 | 0% | N/A (structured) | 5.00 |
| 30-neighbor voting | 0.37209 | 0.35200 | 0.39462 | 0% | N/A (structured) | 5.00 |
| v4 TF-IDF/SGD seed 42 | 0.42706 | 0.40400 | 0.45291 | 0% | N/A (structured) | 5.00 |
| GAMENet text adaptation seed 42 | 0.41438 | 0.39200 | 0.43946 | 0% | N/A (structured) | 5.00 |
| v4 direct | 0.24454 | 0.23830 | 0.25112 | 6% | 94% | 4.70 |
| v4 ordinary repeat | 0.24454 | 0.23830 | 0.25112 | 6% | 94% | 4.70 |
| v4 RAG | 0.28706 | 0.30198 | 0.27354 | 10% | 90% | 4.04 |
| v4 bounded harness | 0.20820 | 0.35106 | 0.14798 | 50% | 100% | 1.88 |
| v5 repaired RAG review | 0.31130 | 0.29675 | 0.32735 | 0% | 92% | 4.92 |
| v5 candidate ranker + memory only | 0.41015 | 0.38800 | 0.43498 | 0% | 100% | 5.00 |
| v5 unrestricted anchor LLM revision | 0.42038 | 0.39919 | 0.44395 | 0% | 96% | 4.96 |
| v5 validation-gated harness | 0.41015 | 0.38800 | 0.43498 | 0% | 96% | 5.00 |
| v4 RAG + parser repair only (no new call) | 0.31081 | 0.31222 | 0.30942 | 0% | 90% raw unchanged | 4.42 |

## Table 3. Frozen-base memory growth / 冻结模型病例记忆增长

| Memory episodes | Residual weight | Validation F1 | Development test F1 |
| --- | --- | --- | --- |
| 0 | 0.0 | 0.34827 | 0.34727 |
| 250 | 0.1 | 0.34833 | 0.34844 |
| 1000 | 0.5 | 0.35009 | 0.35054 |
| 4000 | 0.5 | 0.35015 | 0.35106 |
| 16000 | 0.5 | 0.35233 | 0.35334 |
| 32000 | 0.5 | 0.35368 | 0.35281 |

![Memory growth / 记忆增长](results/memory_growth.png)

## Table 4. Actual LLM budget / 实际模型预算

| Arm | Input tokens | Output tokens | Seconds (sum) |
| --- | --- | --- | --- |
| retrieval_proposal | 113861 | 1291 | 162.09 |
| repaired_review | 234013 | 2695 | 339.23 |
| anchor_llm_revision | 133933 | 1400 | 196.98 |
| gated_harness | 133933 | 1400 | 196.98 |

## Parser-only ablation: the extra review has little demonstrated benefit

Replaying the old RAG generations through the repaired parser, with **zero additional LLM calls**, gives F1=0.31081 and no empty outputs. This is almost the same as the new review's 0.31130. With the old strict parser, the new review reaches 0.30022 with 8% empty outputs. The old bounded review remains 0.20820 / 50% under either parser. Thus the repair recovers the damage caused by the old reviewer; it does not establish a useful reasoning gain over RAG plus robust parsing. New per-call generations use at most 32 tokens, so the higher 384-token cap is inactive in this run.

The selected 50-case harness (0.41015) still trails the old supervised SGD (0.42706). The unrestricted LLM edit arm happens to perform better on this test than the gated arm, despite being worse on validation. We do not change the frozen gate after seeing this result.

## Paired repair effects and gate outcome

- Repaired review minus old bounded harness: +0.10310, 95% CI [+0.03807, +0.16748].
- Repaired review minus original RAG: +0.02424, 95% CI [-0.00348, +0.05914].
- Validation F1: candidate ranker 0.36889, unrestricted LLM revision 0.34222. LLM prediction edits accepted: **False**.
- The gated arm still executes and charges the LLM review even if edits are rejected. A retained five-class ranker has zero empty outputs by construction; this does not establish drug need or clinical correctness.

## Implemented changes and evolution

See [bilingual architecture with diagram](ARCHITECTURE.md). v4 did not update experience. v5 freezes a base ranker trained on 8,000 admissions, stores residual feedback from up to 32,000 disjoint training-patient admissions, retrieves 30 episodes, and versions validation-promoted corrections. There are no LLM weight updates. Vocabulary/mapping remain fixed from the shared 40k cohort, so growth is conditional on that representation. Historical records are not clinician-rated prescriptions.

The static ensemble and growing memory are reported separately. The small validation fusion gain failed to transfer to the test; the selected 10% memory policy is retained and reported, rather than switched after inspecting test results. Only the 50-case panel executes the LLM/state/flag pipeline.

## Literature-informed scope

SafeRx-Agent motivates separating flag collection from case-specific verification; MedAgentSim motivates experience replay; MedAgentBench motivates checking real tool state. [Architecture and primary sources](ARCHITECTURE.md#4-what-we-borrowed-from-the-literature--从相关工作借鉴什么) explain the implementation boundaries. None was faithfully reproduced in this increment. Original cross-paper scores are never pasted into the method table. Beating our GAMENet adaptation does not establish superiority over the original GAMENet, SafeRx-Agent or current state of the art.

## Remaining work and acceptance criteria

1. **Full-order feedback:** obtain the two blinded reviewers' indication/fluid-role/volume/rate/renal/DDI ratings; preserve unknowns and disputed ratings. ATC-only gains do not close this endpoint.
2. **Validated knowledge:** ingredient/RxNorm mapping, timestamp-valid renal/weight/allergy facts, sourced indication/contraindication rules; coarse graph flags cannot authorize orders.
3. **Experience quality:** clinician-accepted correction episodes, fixed promotion margins, patient-disjoint nested validation and harmful-regression endpoints; compare raw case retrieval, residual memory and clinically reviewed memory.
4. **Cross-method evidence:** compatible SafeDrug molecules and independently executable SafeRx architecture; same data/input/budget, clearly named adaptations.
5. **Confirmation:** freeze the final policy and evaluate a new patient cohort; live FHIR MedAgentBench tasks and complete public secondary ablations remain required.

## Reproduction and artifacts

See [commands and file map](README.md). Aggregate JSON is in `results/`; patient-level inputs, traces, fitted models and predictions remain under the restricted `prismatic-v5` directory. Eight contract tests cover parser recovery, unknown/contradiction semantics, train-only feedback, replay and rollback. Prior v4 outputs are unchanged.
