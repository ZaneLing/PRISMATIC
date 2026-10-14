# RxRSIAgent v0.6: prescription generation and GT-supervised evolution

14 October 2026. See the [design and execution plan](DESIGN.en.md).

![Implemented prescription and training loop](architecture.png)

## Revised scope

Outperforming prior methods is the paper's hypothesis, not an inference instruction. Outputs now include drug names, route, dose, unit and frequency, including saline records absent from the old ATC map. Existing ground truth drives automatic evaluation; human review is optional for claims absent from those labels. Published baseline scores are imported with sources and protocol-specific grouping, without requiring baseline reimplementation.

The experiment uses the same patient-disjoint MIMIC-IV/ED 40k/4k/4k admissions. The 128-name vocabulary is fixed from the first 8k training cases and covers about 85.34% of test orders. This new raw-name task is not numerically interchangeable with prior ATC-L4 results. Core orders require exact drug/route/dose-string/unit agreement; 33,377 complete reference tuples are available. Unobserved frequency is excluded from field-accuracy denominators. Saline presence is an occurrence endpoint, not an indication endpoint.

### A. Executed same-4,000-case method comparison

| Method, 4,000 cases | Drug F1 | Core-order F1 | Saline occurrence F1 | Mean drugs |
| --- | --- | --- | --- | --- |
| retrieval_40k | 0.34742 | 0.24761 | 0.83236 | 7.19 |
| static_8k | 0.35841 | 0.24304 | 0.83090 | 10.37 |
| full_data_global_templates | 0.40668 | 0.28003 | 0.83563 | 8.57 |
| rxrsi_promoted | 0.40668 | 0.27255 | 0.83563 | 8.57 |
| RxRSIAgent r2 selected | 0.40668 | 0.28003 | 0.83563 | 8.57 |

### B. r1 growth with similar-case order templates

| Training cases | Drug F1 | Core-order F1 | Promoted |
| --- | --- | --- | --- |
| 8000 | 0.35841 | 0.24304 | True |
| 16000 | 0.38211 | 0.25954 | True |
| 32000 | 0.40428 | 0.27329 | True |
| 40000 | 0.40668 | 0.27255 | True |


Drug F1 rises from 0.35841 to 0.40668. Core-order F1 is not strictly monotonic in r1. The r2 validation-selected global template policy reaches 0.28003 core-order F1; the same-40k ordinary policy/global-template control matches it. The current evidence therefore supports additional supervised data, but does not establish a unique error-replay advantage.

Independent set counts reproduce the scores. A 2,000-replicate paired bootstrap over 3,115 test patients gives r2-minus-8k drug F1 +0.04827 (95% interval 0.04447–0.05234) and core-order F1 +0.03698 (0.03321–0.04082). These developmental intervals describe data growth, not a unique evolution-mechanism benefit.

### C. Actual local LLM agent pilot

| 20-case local agent | Drug F1 | Core-order F1 | Mean drugs |
| --- | --- | --- | --- |
| catalogue_planner | 0.27350 | 0.21667 | 3.00 |
| experience_planner | 0.32000 | 0.24199 | 5.05 |
| learned_policy | 0.42997 | 0.30671 | 6.65 |
| rxrsi_selected | 0.42997 | 0.30671 | 6.65 |


Validation selects `learned_policy`. There are 20 validation and 20 development-test cases. The local frozen Qwen3-4B planner identifies problems and selects learned order tools; a compiler expands their structured fields. This is template-based generation, not free dose invention. Restricted patient text never leaves the local machine.

### D. Executed updates and negative ablations

The pre-update error ledger contains 32,000 later training cases. Policy weights, case memory and joint order templates are updated; the initial vocabulary and input representation remain frozen. r2 selects replay weight 0, mode global and threshold 0.2 using validation only. The error-weighted alternatives do not win. Original r1 outputs and failed configurations remain available. LLM fine-tuning and natural-language skill editing are not completed capabilities.

## Literature dataset and experiment registry

| Paper | Data / task | Experiments |
| --- | --- | --- |
| [GAMENet](https://arxiv.org/pdf/1809.01852) | MIMIC-III: 6,350 patients; 15,016 visits; 145 medications | Medication sets, DDI, memory ablations |
| [SafeDrug](https://arxiv.org/pdf/2105.02711) | MIMIC-III: 6,350 patients; 14,995 visits; 131 medications | Medication sets, DDI, molecular ablations, efficiency |
| [SafeRx-Agent](https://arxiv.org/html/2605.29146v1) | MIMIC-IV: 100 dev / 1,586 test; MIMIC-III: 901 patients | ATC-L4, expert routing, safety filtering |
| [RxEval](https://arxiv.org/html/2605.14543v1) | MIMIC-IV: 1,547 questions; 584 patients | Medication-dose-route options, exact match, macro F1 |
| [MedAgentSim](https://arxiv.org/html/2503.22678v1) | NEJM 15 / extended 120; MedQA 106 / extended 214; MIMIC-IV 288 | Diagnosis, measurement/memory/reasoning/ensemble ablations |
| [MedAgentBench](https://arxiv.org/abs/2501.14654) | 300 FHIR tasks; 100 patients | Tool-task success by task type |
| [GRASP](https://arxiv.org/html/2605.29668v1) | MedAgentBench and v2: dev/val/test/OOD = 96/80/64/60 | Skill edits, regressions, OOD, cross-model transfer |


## Imported author-reported baselines

All rows below are directly cited, not locally reproduced. Protocol groups retain their source table and metric units. Our raw-name development experiment is not ranked against these different datasets or metrics. RxRSIAgent's matched-protocol rows remain to be measured.

| Source | Protocol | Reported method | Reported metrics | Source location |
| --- | --- | --- | --- | --- |
| [GAMENet](https://arxiv.org/pdf/1809.01852) | GAMENet-145-ATC3 | GAMENet | f1=0.6081; jaccard=0.4509; prauc=0.6904; ddi=0.0749 | Tables 2 and 3 |
| [SafeDrug](https://arxiv.org/pdf/2105.02711) | SafeDrug-131-ATC3 | GAMENet as reported by SafeDrug | f1=0.6626; jaccard=0.5067; prauc=0.7631; ddi=0.0864 | Tables 1 and 2 |
| [SafeDrug](https://arxiv.org/pdf/2105.02711) | SafeDrug-131-ATC3 | SafeDrug | f1=0.6768; jaccard=0.5213; prauc=0.7647; ddi=0.0589 | Tables 1 and 2 |
| [SafeRx-Agent](https://arxiv.org/html/2605.29146v1) | SafeRx-ATC4 | GAMENet (reported in SafeRx) | mimiciv_f1=0.3356; mimiciii_f1=0.2153 | Section 5, Table 2 |
| [SafeRx-Agent](https://arxiv.org/html/2605.29146v1) | SafeRx-ATC4 | SafeDrug (reported in SafeRx) | mimiciv_f1=0.3519; mimiciii_f1=0.2361 | Section 5, Table 2 |
| [SafeRx-Agent](https://arxiv.org/html/2605.29146v1) | SafeRx-ATC4 | SafeRx / GPT-5.2 / no safety filter | mimiciv_f1=0.4138; mimiciii_f1=0.2812 | Section 5, Table 2 |
| [SafeRx-Agent](https://arxiv.org/html/2605.29146v1) | SafeRx-ATC4 | SafeRx / GPT-5.2 / safety filter | mimiciv_f1=0.3934; mimiciii_f1=0.2641 | Section 5, Table 2 |
| [SafeRx-Agent](https://arxiv.org/html/2605.29146v1) | SafeRx-ATC4 | SafeRx / Claude Sonnet-4.6 / no safety filter | mimiciv_f1=0.4325; mimiciii_f1=0.2758 | Section 5, Table 2 |
| [SafeRx-Agent](https://arxiv.org/html/2605.29146v1) | SafeRx-ATC4 | SafeRx / Claude Sonnet-4.6 / safety filter | mimiciv_f1=0.4229; mimiciii_f1=0.2667 | Section 5, Table 2 |
| [MedAgentSim](https://arxiv.org/html/2503.22678v1) | MedAgentSim-diagnosis | MedAgentSim / Llama-3.3-70B | mimiciv_diagnosis_accuracy_percent=79.5 | Section 4, Tables 1 and 2 |
| [MedAgentBench](https://arxiv.org/abs/2501.14654) | MedAgentBench-300 | Claude-3.5-Sonnet-v2 | success_percent=69.67 | 300-task version abstract |
| [GRASP](https://arxiv.org/html/2605.29668v1) | GRASP-MAB-split | GRASP / gpt-oss-120b | mab_test_percent=88.8; mab_test_sd=5.8; mab_v2_test_percent=76.9; mab_v2_test_sd=4.0 | Tables 1 and 8 |
| [RxEval](https://arxiv.org/html/2605.14543v1) | RxEval-prescription-MCQ | Gemini-3.1-Pro | f1_percent=77.1; exact_match_percent=46.1 | Table 2 |
| [RxEval](https://arxiv.org/html/2605.14543v1) | RxEval-prescription-MCQ | Qwen3.6-27B | f1_percent=71.7; exact_match_percent=40.0 | Table 2 |


## Next acceptance gates

Prioritize the 1,547-question RxEval protocol, followed by SafeRx ATC-L4 MIMIC evaluation. Reuse reported baseline scores without retraining those methods. Compare our own matched-protocol row only after its inputs/splits/metric are aligned. Then run equal-data replay/skill/SFT ablations, multi-seed robustness and independent patient confirmation. Clinical review is an optional secondary evaluation of unobserved attributes, never a prerequisite for these GT-based experiments.
