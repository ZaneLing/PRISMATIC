# RxRSIAgent v0.7: round-wise, artifact-wise evolution audit

Target: ACL 2027. The saline-presence endpoint has been removed. All prescription items use the common drug/order metrics.

## Protocol

40k training / 2k proposal validation / 2k regression guard / 4k test admissions, with 3,440 test patients. New development and test subsets exclude every patient in the corresponding v0.6 subsets. All splits are patient-disjoint. The 128-name vocabulary and text representation are frozen from the initial 8k training examples. Methods share inputs, labels, scorer and the maximum 20-order output budget.

Updated objects are drug-selection parameters, episodic memory and a context-conditioned joint-order completion tool. Each round stores hashes, candidate configurations, independent guard scores and acceptance decisions. All decisions are frozen before test scoring. LLM weights and language skills do not change in this experiment.

## Three-seed method comparison

| Method | Drug F1: mean ± SD | Core-order F1: mean ± SD |
|---|---:|---:|
| Word policy + global templates | 0.40074 ± 0.00073 | 0.27248 ± 0.00074 |
| Word policy + conditional order tool | 0.40074 ± 0.00073 | 0.27911 ± 0.00046 |
| Case retrieval + global templates | 0.35246 ± 0.00000 | 0.24522 ± 0.00000 |
| Case retrieval + conditional tool | 0.35246 ± 0.00000 | 0.25305 ± 0.00027 |
| RxRSI accepted version | 0.39920 ± 0.00251 | 0.27865 ± 0.00142 |
| Freeze initial policy parameters | 0.36112 ± 0.00460 | 0.25447 ± 0.00297 |
| Freeze initial order tool | 0.39920 ± 0.00251 | 0.27494 ± 0.00142 |
| Freeze initial episode memory | 0.39976 ± 0.00224 | 0.27926 ± 0.00113 |
| Tuned word policy + order tool | 0.39625 ± 0.00062 | 0.27887 ± 0.00043 |
| Character policy + order tool | 0.39782 ± 0.00268 | 0.27771 ± 0.00199 |
| Word/character ensemble + order tool | 0.40209 ± 0.00058 | 0.28110 ± 0.00062 |
| Naive Bayes + order tool | 0.37469 ± 0.00000 | 0.26610 ± 0.00016 |

## Fixed-test trajectory

![Round-wise held-out curves](round_curves.png)

| Round | Training cases | Seed 42 drug F1 | Seed 42 order F1 | Improved / regressed cases |
|---|---:|---:|---:|---:|
| 0 | 8000 | 0.36656 | 0.25324 | 0 / 0 |
| 1 | 16000 | 0.38120 | 0.26662 | 1458 / 1082 |
| 2 | 24000 | 0.39181 | 0.27357 | 1495 / 1088 |
| 3 | 32000 | 0.39714 | 0.27738 | 1158 / 1059 |
| 4 | 40000 | 0.40205 | 0.28026 | 1130 / 977 |

Accepted-state curves are non-decreasing for all three seeds on this test; seed 137 rejects its final update. Individual cases can still regress. A monotonic aggregate curve is not a per-patient guarantee.

## Reflection and continued iteration

The conditional order tool contributes measurable gains. Expanding episode memory is not consistently useful. The full RSI mean does not exceed the equal-data policy-plus-conditional-tool control. This increment does not establish a unique RSI advantage.

v0.8 therefore proceeds with actual LLM-authored skill and evidence-tool-configuration changes, comparing direct, CoT, Self-Refine, case RAG, explicit Reflexion/GRASP/EvoTool task adaptations and RxRSI. Restricted patient text remains local.

All saved scores were independently recomputed. Patient-cluster paired bootstrap results are in `results/summary.json`. Leave-one-object-out results freeze the specified object within the final policy without retuning other objects; they are conditional dependence tests, not optimally retrained ablations. The admission-proxy input and source-field missingness limitations persist.
