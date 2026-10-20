# RxRSIAgent: candidate and sequential-updater repairs

Date: 2026-10-20. The three-round repair pilot is complete. The existing 1,082-admission main table remains unchanged; these are separate exploratory results.

## 1. Why was candidate coverage only 51.62%?

Our preprocessing retained the 128 most frequent normalized raw names in the first 8,000 training admissions, then a classifier fitted on 40,000 admissions selected the top 24 per case. This is our engineered action space, not an official MIMIC catalogue or unconstrained LLM generation.

| 分解 / Component | 实例 / Instances | 占 GT / GT share |
|---|---:|---:|
| 可选 / Reachable | 1961 | 51.62% |
| 128 词表外 / Outside vocabulary | 717 | 18.87% |
| 词表内但被 top-24 排除 / Pruned within vocabulary | 1121 | 29.51% |

The denominator is 3,799 within-admission unique GT drug instances. Raw-name normalization is not RxNorm ingredient harmonization; brand/formulation fragmentation remains. Expanded reachability is not itself a prescription-performance gain.

On the same 48 audit admissions, candidate recall is 48.50% for top24, 67.50% for top48, and 58.00% for retrieval expansion. This is reachability, not final-order F1; it must not be compared directly with the full-cohort 51.62%.

## 2. Four repairs and their limits

1. Seven executable operators cover candidate widening, case-retrieval recall, route-filtered evidence, distinct-drug evidence, full fact checking, temporal reconciliation and access to the existing frozen predictive draft.
2. Execution-effect checks precede semantic-output checks and development evaluation.
3. Numeric counterexamples are separated from dose instructions, and typed exceptions execute at runtime.
4. Every seen case contributes cumulative root counts, six stage-stratified illustrations and the complete edit-outcome ledger.

An interrupted development attempt exposed incorrect attribution of candidate omission to fact checking. Before any audit inference, we added root/operator compatibility, earliest-stage priority and a training-gain requirement. Unchecked-fact counts are not prescription errors. The interrupted attempt is preserved.

Two further validator errors are corrected: cross-stage prose no longer triggers a substring conflict, and a JSON wrapper containing exactly one proposal is normalized. The previously rejected third-round proposal was then executed and failed the training-gain gate. The change followed development logs; an audit inference attempt had started and was interrupted, without reading or selecting on its audit scores. Original records are retained.

Weights, joint order templates and underlying tool code remain fixed. This tests LLM-proposed procedural skills and tool configurations, not autonomous tool-code rewriting. Researcher engineering is not counted as learned improvement.

The local Qwen-proposer control is retained separately. This trajectory uses a Sonnet 4.6 aggregate-only proposer with the same local actor, tools and gates. It is not same-model self-reflection. The two updater runs reuse the same 72 cases, not 144 distinct cases. Proposer model and feedback granularity both change; this is not an isolated model ablation.

![Frozen trajectories / 冻结状态轨迹](figures/evolution.png)

## 3. Measured sequential results

Core4 jointly matches drug name, route, dose value and dose unit; frequency is excluded. The following tables first retain the original strict-decoder protocol; compatible-array replay is reported separately below.

72 admissions newly presented to the reflector, three rounds of 24; they already belong to the candidate tool's 40,000-admission training resource and are not new supervision to the entire system. 24 proposal and 32 guard admissions; 48 audit admissions evaluated after all states were frozen. The audit comes from a historically exposed benchmark and is exploratory, not a pristine independent validation.

| Round | Cases seen | Error-memory cases | Retained skills | Audit drug F1 | Audit Core4 F1 |
|---:|---:|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 | 7.21% | 3.87% |
| 1 | 24 | 24 | 1 | 16.04% | 8.83% |
| 2 | 48 | 48 | 2 | 16.96% | 9.22% |
| 3 | 72 | 72 | 2 | 16.96% | 9.22% |

更新结局 / Update dispositions: `{"no_training_agreement_gain": 3, "accepted": 2, "development_gate": 1}`.

A growing error archive shows accumulated feedback, not improved prescribing. Retained changes and audit gains are distinct outcomes.

### 保留的技能 / Retained skills

- ranked_draft; when=all; unless=[]; hash=77f8a842e210

- candidate_wide48; when=all; unless=[]; hash=95fa1638af85

## 4. 固定工程对照与跨模型 / Static control and transfer

| Backbone / method | Drug F1 | Core4 F1 | Invalid output |
|---|---:|---:|---:|
| Qwen initial | 7.21% | 3.87% | 0.00% |
| Qwen local-proposer retained | 6.96% | 2.67% | 0.00% |
| Qwen RxRSIAgent retained | 16.96% | 9.22% | 10.42% |
| Qwen static repair bundle | 14.25% | 8.13% | 4.17% |
| Qwen static ranked draft only | 12.74% | 7.18% | 0.00% |
| Frozen classifier top8 + order tool | 17.81% | 10.44% | 0.00% |
| Llama initial | 6.13% | 3.94% | 12.50% |
| Llama transferred retained | 10.16% | 7.44% | 2.08% |

Qwen initial→retained: drug Δ 95% patient-bootstrap CI [3.44, 15.58] pp; changed cases=48.

Qwen static-ranked-draft→retained: drug Δ 95% patient-bootstrap CI [0.05, 8.47] pp; changed cases=47.

Llama initial→retained: drug Δ 95% patient-bootstrap CI [-1.55, 9.67] pp; changed cases=39.

Against the frozen top-eight tool without an LLM, the retained agent has a drug-F1 difference of -0.84 percentage points. Improvement over its own initial state is not superiority to the existing predictive tool.

All actors share three calls and 128/128/96 output caps; expanded catalogues increase input length. The static bundle is researcher specified, not learned. Transfer uses no Llama-specific tuning.

### 监督预测工具贡献 / Contribution of the supervised predictive tool

98.79% of retained-state predictions and 97.37% of correct drugs are inside the frozen top-eight draft. Newly recovered GT instances: 30, of which 0 were outside the original catalogue; previously correct instances lost: 4.

These counts distinguish uptake of a supervised resource from new knowledge. An F1 increase alone does not establish newly learned pharmacology, absence of drug-name priors, or superiority to a static tool.

### 漏开与多开 / Omissions and extra predictions

| State | Precision | Recall | Missed GT/admission | Extra vs GT/admission |
|---|---:|---:|---:|---:|
| initial | 9.02% | 6.00% | 3.92 | 2.52 |
| retained | 15.32% | 19.00% | 3.38 | 4.38 |

The F1 increase accompanies more predictions absent from GT. The current F1-based gate does not guarantee fewer extra orders. A GT discrepancy is not automatically clinical inappropriateness, but this trade-off is material. All newly recovered targets were already in the original catalogue; this run recovers none from outside it, so the gain cannot be attributed directly to recall expansion.

### 完整数组解码修复：统一重放 / Complete-array decoder repair: uniform replay

Final inspection found five complete Qwen identifier arrays rejected only for lacking an outer order_ids object. The compatibility decoder accepts only complete arrays containing valid catalogue identifiers; it never completes truncated text or invents orders. Every LLM control and frozen round is replayed under the same rule with no new calls. Learning gates are not rerun and states do not change: this is post hoc engineering, not additional RSI. Fresh inference is available through order_decoder.run_with_compatible_output.

| Method | Recovered outputs | Original drug F1 | Compatible drug F1 | Compatible Core4 F1 |
|---|---:|---:|---:|---:|
| qwen_initial | 0 | 7.21% | 7.21% | 3.87% |
| qwen_retained | 5 | 16.96% | 16.10% | 8.78% |
| qwen_static_bundle | 2 | 14.25% | 14.74% | 7.94% |
| qwen_static_draft | 0 | 12.74% | 12.74% | 7.18% |
| llama_initial | 0 | 6.13% | 6.13% | 3.94% |
| llama_transferred | 0 | 10.16% | 10.16% | 7.44% |

Aggregate-proposer frozen-state drug F1 after compatible decoding: 7.21% → 16.04% → 16.10% → 16.10%

The five restored Qwen prescriptions add no GT hits and add 24 extra drug predictions, lowering F1. Output failures can conceal overprediction; discarding them must not be treated as better prescribing. Passing the original gate does not establish passing after a decoder change; the next learning run must use one consistent decoder throughout.

## 5. Can learning specialize by disease category?

The implemented optional contract routes explicitly documented pre-decision diagnostic categories, allowing multiple categories and excluding future, untimed or merely suspected problems. It performs no diagnosis inference or ICD mapping. Current cases lack verified decision-time diagnoses, so routing uses observed renal, glucose/electrolyte, hematology, liver and blood-gas measurement groups. These do not establish diagnoses or abnormality. Drugs are not converted to disease labels, and discharge diagnoses are excluded. Both retained skills use global applicability; no disease-specialized skill has been retained. Disease-specific benefit remains unverified.

| Observable group | Cases | Initial drug F1 | Retained drug F1 |
|---|---:|---:|---:|
| renal_labs | 11 | 10.53% | 16.36% |
| glucose_electrolyte_labs | 12 | 9.76% | 15.93% |
| hematology_labs | 15 | 8.85% | 14.86% |
| liver_labs | 7 | 8.33% | 9.68% |
| blood_gas_labs | 4 | 0.00% | 13.95% |

Groups overlap and are small; these are descriptive subgroup results, not independent disease-stratified tests.

## 6. Case studies

Three historical training illustrations cover excluded targets, omitted available targets and wrong joint fields despite correct drug identity. New intervention improvements and regressions are retained. Patient inputs, GT and generated skill text remain local.

[本地双语病例 / Local bilingual cases](/Users/bytedance/Desktop/MedTreeBench/dataset/restricted/prismatic-v51/cloud/CASE_STUDIES.bilingual.md)

## 7. Cost / 花费

New API cost: USD 0.085203 / USD 10 authorization; 3166 local generation receipts. Local hardware time is unpriced.

## Evidence / 证据

[Protocol](protocol.json) · [Candidate audit](results/candidate_origin.json) · [Learning](results/cloud/learning.json) · [Trajectory](results/cloud/trajectory.json) · [Controls and transfer](results/cloud/controls_transfer.json) · [Module growth](results/module_growth.json) · [Reproduction](README.md)
