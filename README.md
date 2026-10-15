# PRISMATIC: ***P***rescription ***R***isk ***I***nspection ***S***ystem for ***M***ulti-***A***gent ***T***actical ***I***nteraction in ***C***linical Decision

<!-- RXRSI_CURRENT_EXECUTION_START -->
## Paused research snapshot / English ACL manuscript — 15 October 2026

The research goal and experiment queues are paused at the user's request. The English manuscript has been reorganized around the saved evidence using the official ACL review template.

- [English ACL manuscript](paper/latex/v0.3/prismatic_v03_en.tex): workflow, common-data method comparison, external-hospital test, experience curves, component interventions, and failure analysis.
- **13/15** author-method runs complete; **6/6** rule trajectories complete; the final common MIMIC test remains unreported.
- External eICU test complete: **13 methods/configurations, three seeds, 8,005 stays, sixteen held-out hospitals**.
- **9/36** parameter updates complete; the precision diagnostic is complete and independently audited. Its results do not establish a neural advantage over retrieval.
- [Evidence manifest](paper/latex/v0.3/manuscript_evidence.json) · [English reading index](paper/README.md) · [中文结果](paper/CURRENT_RESULTS.zh.md) · [English results](paper/CURRENT_RESULTS.en.md).

Writing did not resume experiments. Earlier research-status paragraphs below are historical entries; this snapshot governs current status.
<!-- RXRSI_CURRENT_EXECUTION_END -->


## Current research status — ACL 2027 / RxRSIAgent, 15 October 2026

[中文总览与主表](paper/CURRENT_RESULTS.zh.md) · [Current English results](paper/CURRENT_RESULTS.en.md) · [系统流程图](paper/RXRSI_DESIGN.zh.md) · [English design](paper/RXRSI_DESIGN.en.md) · [Active English paper](paper/latex/v0.3/prismatic_v03_en.tex) · [Versioned plan](paper/COMPLETION_PLAN.md)

**New complete real-tool result:** direct/fixed/learned skills score39/38/45 of64 ID tasks, but27/17/10 of60 held-out-type tasks. The generated name skill's explanation is contradicted by actual tool behavior. [Scores, intervals and skill artifacts](upgrade_v19/RESULTS.en.md). The completed candidate-position diagnostic also finds prefix dependence after parameter learning. [Diagnostic](upgrade_v26/RESULTS.en.md).

**Latest completed mechanism comparison:** on the recorded-availability MIMIC task (1,082 test admissions, three seeds), uniform word/numeric updates score drug/order F1 **0.20446/0.12403**, own-error priorities **0.20143/0.12219**, and shuffled priorities **0.20204/0.12197**. All feedback, budgets, tool memberships and predictions are independently audited. The test was previously observed; this is exploratory reuse. Case-growth improvements do not establish a unique RSI benefit. [Full v0.23 table and curves](upgrade_v23/RESULTS.en.md).

**Gemini transfer complete:** fixed grounding scores **538/988**, frozen grounded skills **510/988**; paired difference −2.83 percentage points, interval [−4.85,−0.81]. Truncation explains part of the regression, but valid-output decisions also degrade. [Four-method table and diagnosis](upgrade_v18/RESULTS.en.md). The earlier DeepSeek author-core GRASP control remains **502/988**, compared with combined grounded skills **501/988** under that backbone's separate budget.

**External-data audit complete:** eICU hospital partitioning retains 142,485 stays with zero hospital/patient overlap across splits, including 8,188 test stays from 16 hospitals. Native-code and temporal coverage expose missing-name and late-lab issues; no eICU model score is claimed. [v0.24 audit](upgrade_v24/RESULTS.en.md).

**Binary parameter study complete:** priority updates score **0.29192/0.19329** drug/order F1, uniform **0.24094/0.15072**, and direct top-8 tools **0.31169/0.20739**. Round3 collapses and is rejected. Ten of3,600 duplicate-input feedback generations have a disclosed receipt gap; saved test outputs are fully recounted. Future generation now deduplicates requests and preserves immutable case receipts. [Results and audit](upgrade_v15/RESULTS.en.md).

**Still running:** v0.25 trains three seeds on an independently audited native-HICL eICU cohort, with8,005 test stays/6,227 patients/16 hospitals and3,842 zero-target stays. No test score yet. [Protocol](upgrade_v25/RESULTS.en.md). v0.19 main comparison and frozen single-skill attribution are complete, with no established synergy. [Results](upgrade_v19/RESULTS.en.md). Official RxEval/SafeRx test packages remain unavailable. Restricted records, predictions and fitted models stay local; public releases contain code, hashes and aggregates.

Earlier [v0.21 temporal comparison](upgrade_v21/RESULTS.en.md), [v0.7 legacy order comparison](upgrade_v7/RESULTS.en.md), [public method comparison](upgrade_v8/RESULTS.en.md), [author-core GRASP](upgrade_v10/RESULTS.en.md), [grounded skill evolution](upgrade_v17/RESULTS.en.md) and [local QLoRA results](upgrade_v9/RESULTS.en.md) retain their original protocols and negative controls. The active English paper uses the official ACL review style and preserves its editor path. The 2025 description below is historical project context, not evidence for these new evaluations.

**Standard-method training running:** a separate ATC-L4 visit-set panel includes8,905 patients/23,177 visits, with every selected clinical-code set independently reconstructed. Public molecules cover219/271 training classes; NDC row coverage is27.23%. ARMR-2025/GAMENet/SafeDrug are training for three seeds and50 epochs. Four conventional methods are fitted and independently audited on development; full-panel guard F1 is0.45794/0.30154/0.55081/0.61151 for prevalence/prior visit/retrieval/logistic. Main test remains gated. [Audit](upgrade_v27/RESULTS.en.md) · [Recent-method sources and original results](paper/LATEST_METHODS.en.md).

## Original 2025 project description

![](./resources/Prismatic_framework.jpg)

## A multi-agent architecture leveraging patient statements and clinical knowledge for prescription risk inspection. 

Medication prescribing errors remain a critical challenge in clinical practice, often stemming from incomplete patient understanding, ambiguous documentation, and suboptimal decision support. 
In this paper, we propose PRISMATIC, a 3-layer multi-agent prescription risk mitigation framework designed to generate safe, interpretable, and traceable drug regimens by analyzing unstructured patient clinical note texts.
To enhance adaptability and safety, PRISMATIC integrates two mechanisms: (1) Dynamic Self-updating Weight Adjustment (DSWA), which tunes risk factor weights over time, and (2) Differential Feedback Calibration Mechanism (DFCM), which learns from discrepancies with gold-standard prescriptions to improve future outputs.
Evaluated on a curated dataset from MIMIC-IV, PRISMATIC outperforms raw LLM outputs and prompting-based baselines (Few-Shot, Chain-of-Thought, ReAct, Tree-of-Thoughts) in reducing prescription risks. These results highlight the potential of multi-agent systems for improving clinical medication decision support.

## Setup Instructions

This project uses [Poetry](https://python-poetry.org/) to manage dependencies and the virtual environment.

### 1. Install Poetry

You can install Poetry via `pip`:

```bash
pip install poetry
```
Or using the official installer (recommended):
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### 2. Install Dependencies
Clone & Navigate to the project directory and run:
```bash
git clone https://github.com/ZaneLing/PharmAid.git
cd PharmAid
poetry install
```
This will install all required packages and set up a virtual environment.

### 3. Set OpenAI API Key
Open `.env` file and set your OpenAI API key as an environment variable:
```bash
OPENAI_API_KEY = 'your_api_key'
```
### 4. Run the Workflow
To execute the main script within the Poetry environment, run:
```bash
poetry run python workflow.py
```

## 2026 research upgrade / 2026 年研究升级

**Start with the [versioned paper index / 持续更新的论文入口](paper/README.md).**
The [archived v0.2 Chinese manuscript](paper/versions/v0.2-2026-10-14.zh.md#41-主表同题配对的-rxsafebench-结果)
and [archived v0.2 English manuscript](paper/versions/v0.2-2026-10-14.en.md#41-primary-table-paired-rxsafebench-results)
place the paired harness comparison in Table 2 and identify its public
RxSafeBench dataset. Older reports remain archived by version.

The [PRISMATIC 2 research prototype](upgrade_v2/README.md) adds a
time-bounded, patient-disjoint MIMIC pilot; a case-count learning curve for
supportive orders; structured review-harness checks; and public RxSafeBench
and RxQA model comparisons through OpenRouter. Read the
[English first report](upgrade_v2/REPORT_EN.md) or
[中文初版报告](upgrade_v2/REPORT_ZH.md) for the first-pass methods, results, and limits.
Only aggregate restricted-data results and public-benchmark predictions are
tracked in this repository. This is research software, not clinical prescribing
software.
