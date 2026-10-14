# RxRSIAgent: evolving structured prescription generation

Version v0.6, 14 October 2026. The system builds on PRISMATIC's experimental assets.


![Implemented system. Current inputs and unimplemented mechanisms are distinguished below.](architecture.png)

## Research objective

The paper aims to outperform existing prescription methods under comparable benchmark protocols and improve prescription quality as training feedback accumulates. This is a research hypothesis, never an instruction to the inference agent. Equal-data and equal-budget ablations must distinguish mechanism gains from the benefit of additional supervised examples.

## Inference workflow

Patient snapshot → patient state and treatment problems → retrieve drug candidates, joint order templates and training episodes → plan a prescription → compile drug, route, dose, unit and frequency → check structure and unresolved information → return structured research orders.

The evaluated local Qwen planner identifies problems and selects order tools from a learned catalogue. The compiler expands template IDs into recorded field combinations. The implemented inputs remain chief complaint, acuity and home medications; complete clinical timelines and ingredient-level knowledge are future extensions. The policy vocabulary contains 128 names selected from the initial 8,000 training admissions. The statistical policy may return up to 20 orders; the LLM pilot uses 12 candidate tools. This is constrained template-based generation, not unrestricted dose generation. Validation selected direct learned-policy output over the LLM selectors, so the LLM branch is an evaluated alternative rather than the active winner.

The agent performs prescription planning and tool selection. Its harness manages time boundaries, tool interfaces, state, compilation, evaluation and versions.

## Ground-truth evolution loop

1. Predict a new training case using the current policy before reading that case's target.
2. Compare with the recorded prescription: missing drugs, extra drugs and known field mismatches.
3. Add the case and joint order fields to memory; update the drug-selection policy on accumulated training examples.
4. Try error-prioritized replay using the pre-update failure ledger.
5. Replay fixed validation cases; select thresholds, memory mode and replay weights. Retain unsuccessful revisions for analysis.
6. Freeze the selected version before test evaluation; test outcomes never enter training feedback.

Executed growth checkpoints are 8k, 16k, 32k and 40k admissions. The fixed text representation and name vocabulary are learned from the initial 8k. The feedback ledger contains 32k later training cases. Policy weights and case/template memory change; LLM weights do not. Natural-language skill editing and SFT/DPO are distinct future experiments, not completed capabilities.

The r2 development revision explicitly tests replay strengths 0, 0.25 and 1, and global versus similar-case joint templates. Validation selected zero extra weighting and global templates. This negative result is retained: an error-driven update proposal need not be accepted.

## Ground truth removes the annotation prerequisite

Drug-set agreement, dose/route/unit/frequency agreement, exact core-order matching and saline occurrence are automatically scored from existing recorded targets. Human review is not required to train or run these experiments. Fields absent from the source, including fluid purpose, infusion rate and indication rationale, remain unscored. Clinician evaluation is an optional secondary assessment of such clinical claims, not a gate on benchmark experiments.

Core order means the exact normalized tuple (drug name, route, dose string, dose unit). Only complete reference tuples contribute to that endpoint, and reference/prediction counts are reported. Frequency is included in known-field agreement when observed. Saline occurrence is not a fluid-indication endpoint.

## Published results without baseline reimplementation

Use the source-linked registry in [reported_baselines.json](reported_baselines.json). Mark imported values as author-reported and retain source table, task, code space, split and metric definitions. Our benchmark row can be compared directly when it follows the same protocol. Current ED6 raw-name micro-F1 belongs in its own panel.

Priorities: RxEval prescription-level option selection; SafeRx ATC-L4 MIMIC protocols; richer raw complete-order generation; fixed-budget memory/skill/parameter evolution ablations; then independent confirmation. Reimplementing every baseline is no longer a prerequisite. Existing reports on MedAgentSim diagnosis and MedAgentBench/GRASP tool success remain useful evidence under their own task labels.

## Next mechanism experiments

- Propose typed prescription skills from training failures; test each edit on prior passing and failing development cases, with a regression budget before promotion.
- Compare raw case retrieval, reviewed error memories, skill editing, SFT and GT-based preference optimization at equal data/model/budget.
- Add timestamp-valid trajectories and ingredient identifiers; measure supportive orders and complete prescription fields without losing saline at ATC conversion.
- Run our system on published benchmark protocols and cite the reported baselines directly. Resolve dataset/split access before claiming a numerical win.

Primary sources: [SafeRx-Agent](https://arxiv.org/html/2605.29146v1), [MedAgentSim](https://arxiv.org/html/2503.22678v1), [GRASP](https://arxiv.org/html/2605.29668v1), [RxEval](https://arxiv.org/html/2605.14543v1).
