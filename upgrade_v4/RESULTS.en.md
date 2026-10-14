# PRISMATIC v4: executed experimental results

14 October 2026, execution batch r1 and order normalization r2. [Chinese report](RESULTS.zh.md). Generated from aggregate JSON. All results are developmental; clinical correctness is unreviewed.

## 1. Completed work

Executed a train-40k-only fallback mapper, route coverage audit, dual-timestamp laboratory filter, 4,000-case baselines and input sensitivity, three-seed GAMENet admission-text adaptation, four local LLM methods on identical 50 cases, and a ten-case complete-order draft/revision probe. Seven critical order-contract tests pass. No restricted MIMIC input went to OpenRouter.

## 2. Main method panel: identical 4,000 admissions

MIMIC-IV 3.1 plus ED 2.2; 40k/4k/4k patient-disjoint samples, the same admission-proxy fields, top-80 training classes and exactly five predictions. These are observed historical-label overlap metrics; training compute differs.

| Method / 方法 | N | Precision@5 | Recall@5 | F1@5 | Seed SD |
| --- | ---: | ---: | ---: | ---: | ---: |
| Training prevalence | 4,000 | 0.2432 | 0.3408 | 0.2839 | — |
| Case retrieval (30 neighbors) | 4,000 | 0.2812 | 0.3940 | 0.3281 | — |
| TF-IDF/SGD (3 seeds) | 4,000 | 0.3310 | 0.4639 | 0.3864 | 0.0007 |
| GAMENet text/single-visit adaptation (3 seeds) | 4,000 | 0.2944 | 0.4125 | 0.3436 | 0.0022 |

The GAMENet adaptation retains author graph/readout modules, replacing diagnosis/procedure channels with complaint/acuity and home-medication tokens. Single-visit inputs remove longitudinal dynamic-memory reading. Three seeds ran five epochs, with validation scores still rising at the budget boundary. This does not establish that faithfully reproduced GAMENet is inferior to SGD. Batched inference agrees with the author's single-case computation within 1e-5.

## 3. Same 50 cases, including the local harness

Every row uses the same 50 test patients and targets, with at most five output classes. Traditional methods output five; LLMs may abstain. All four LLM arms use the same pinned Qwen3-4B-Instruct-2507-4bit weights. Do not mix these scores with the 4,000-case panel.

| Method / 方法 | N | Observed F1 | Mean classes | Calls | Valid output |
| --- | ---: | ---: | ---: | ---: | ---: |
| Prevalence | 50 | 0.3763 | 5.00 | — | — |
| 30-neighbor voting | 50 | 0.3721 | 5.00 | — | — |
| SGD seed 42 | 50 | 0.4271 | 5.00 | — | — |
| GAMENet adaptation seed 42 | 50 | 0.4144 | 5.00 | — | — |
| Local LLM direct | 50 | 0.2445 | 4.70 | 1 | 94% |
| Ordinary repeat | 50 | 0.2445 | 4.70 | 2 | 94% |
| Local LLM + case retrieval | 50 | 0.2871 | 4.04 | 1 | 90% |
| PRISMATIC bounded harness | 50 | 0.2082 | 1.88 | 2 | 100% |

The bounded harness does not improve observed F1. Its paired difference versus ordinary repeat is −0.03634 (95% patient-bootstrap interval −0.11168 to 0.03931), and versus retrieval is −0.07886 (−0.13372 to −0.02355). Precision is 0.3511, recall 0.1480 and empty-output frequency 50%. Better structural validity accompanies lower recall; this is not evidence of safety improvement.

Repeat and harness share two calls and the same per-call output cap, but consume 199,348 and 234,313 input tokens respectively. Total token budgets are not identical. Their accumulated arm times are approximately 286.44 and 324.24 seconds. Shared first responses are charged to each logical arm in usage reporting.

## 4. Timing and mapping

The revised mapper covers 814,254/1,788,195 orders (45.535%). Coverage is slightly lower than v0.3 after restricting fallback learning to actual training admissions. IV coverage is 19.518%; PO/NG coverage is 81.874%. All 240,310 saline-name proxy rows are unmapped, so ATC overlap cannot evaluate saline behavior. Name matches are not clinical-purpose labels.

The development test retains 1,144 admissions with no recorded window order, 152 with unmapped-only orders and 2,704 with mapped labels. Mapped-label-only sensitivity is conditional on future label availability, not an unbiased clinical evaluation.

Of 171,455 selected same-admission blood-lab rows charted within 24 hours before admission, 2,127 were stored after the decision and excluded. Numeric results satisfying both time constraints cover 33,393 admissions; post-filter violations are zero. They are not added post hoc to this comparison. Triage lacks row timestamps and medrecon lacks storetime, so full availability remains unverifiable.

| Input / 输入 | Retrieval F1 | SGD mean F1 (3 seeds) |
| --- | ---: | ---: |
| admission_proxy | 0.3281 | 0.3864 |
| home_meds_only | 0.3139 | 0.3695 |
| no_patient_text | 0.2653 | 0.2772 |

The no-text condition is an information ablation. Optimization variation is retained: seed 42 underperforms prevalence in that condition. The table reports all three seeds rather than selecting the best.

## 5. Complete-order execution

The contract includes ingredient, formulation, concentration, dose/unit, route, frequency, duration, indication, evidence and uncertainty, plus fluid purpose/volume/rate/reassessment. Unknowns remain null and absent clinical knowledge is always disclosed.

| Arm / 方法 | Cases | Raw schema valid | Normalized valid | Orders in valid bundles | Clinical ratings |
| --- | ---: | ---: | ---: | ---: | --- |
| direct | 10 | 4/10 | 9/10 | 13 | Pending / 待评 |
| retrieval_harness | 10 | 4/10 | 9/10 | 13 | Pending / 待评 |

Only 4/10 raw responses per arm satisfy the full schema. Main failures are wrong ATC granularity and one truncated JSON response. In r2, unresolved ATC strings become null with the raw value retained in uncertainty; no code is inferred. Normalized validity is 9/10, not an increase in correct model generation from 40% to 90%. Both versions remain available. The revised harness has 11 fluid-information findings and one order without patient evidence. Clinical correctness remains unscored. Seven contract tests pass.

## 6. Outstanding gates

SafeDrug's bundled 112 molecular keys are ATC-L3 and are not a verified mapping for the common 80-class ATC-L4 space. The DDI resource is now available, but molecular/substructure compatibility remains unresolved; no zero-molecule substitute is called complete SafeDrug.

[SafeRx-Agent](https://arxiv.org/html/2605.29146v1) uses MIMIC-III/IV, current diagnoses/procedures, longitudinal context and clinical knowledge. A compatible admission adapter and confirmed executable reference are outstanding. Our bounded retrieval/critique prototype is not labeled its reproduction.

The current harness implements retrieval, state, structural checks, bounded revision and abstention. Validated ingredient-level DDI/renal knowledge, adjudicated experience updates and clinical ratings remain missing. Confirmatory patients, larger complete-order evaluation, case growth, real FHIR and extended secondary benchmarks remain pending. Repair schema truncation and over-abstention on validation data before claiming improvement on fresh confirmation.

## 7. Reproduce

```bash
# Use the research Python environment with upgrade_v4/requirements.txt.
python upgrade_v4/build_protocol_data.py
python upgrade_v4/build_verified_labs.py
python upgrade_v4/run_protocol_methods.py
python upgrade_v4/fetch_ddi_resource.py
python upgrade_v4/build_graph_resources.py
python upgrade_v4/run_gamenet_adaptation.py
# Use the separate local MLX environment for the following two commands.
python upgrade_v4/run_local_harness.py
python upgrade_v4/run_order_probe.py
# Return to the research environment.
python upgrade_v4/evaluate_order_probe.py
python -m unittest discover -s upgrade_v4 -p 'test_order_protocol.py' -v
python upgrade_v4/render_results.py
```
The graph script requires the author-linked `drug-DDI.csv` and pinned author checkouts. The local model must already exist. Resume logs must match protocol and input hashes; use a new private output directory for a new experiment.


## Artifacts / 证据文件

- [Frozen protocol 中文](PROTOCOL.md) / [English](PROTOCOL.en.md), [machine config](protocol.json), [complete order schema](order_schema.json)
- [Mapping audit](results/mapping_protocol_audit.json), [verified lab audit](results/verified_labs_audit.json)
- [Baselines and sensitivity](results/protocol_method_results.json), [GAMENet adaptation](results/gamenet_adaptation_results.json)
- [Same-case local harness](results/local_harness_results.json), [original order probe](results/order_probe_results.json), [normalization revision](results/order_probe_normalized_results.json)
- [Graph coverage](results/graph_resource_audit.json), [method readiness](method_readiness.json), [run manifest](results/run_manifest.json)
