# PRISMATIC: ***P***rescription ***R***isk ***I***nspection ***S***ystem for ***M***ulti-***A***gent ***T***actical ***I***nteraction in ***C***linical Decision

## Current research status — ACL 2027 / RxRSIAgent v0.7–v0.9

[中文流程图](paper/RXRSI_DESIGN.zh.md) · [English design](paper/RXRSI_DESIGN.en.md) · [中文实测结果](upgrade_v7/RESULTS.zh.md) · [English results](upgrade_v7/RESULTS.en.md) · [English ACL paper](paper/latex/v0.3/prismatic_v03_en.tex) · [Versioned plan](paper/COMPLETION_PLAN.md)

**v0.7 is complete; v0.8/v0.9 are running.** The completed three-seed comparison uses 40k training and 4k new test admissions, five checkpoints, 12 method/ablation rows, artifact hashes and repair/regression counts. Mean drug/order F1 is 0.39920/0.27865 for the selected evolving state versus 0.40209/0.28110 for the strongest same-data word/character control. Curves improve with case growth, but unique RSI superiority is not established.

We continue with [LLM-authored skill/memory/tool-configuration evolution](upgrade_v8/README.md) and [actual local QLoRA parameter updates](upgrade_v9/README.md). Missing official RxEval/SafeRx test packages do not block runnable experiments. The active paper uses the official ACL review style and keeps the existing editor path. Only aggregate restricted-data results are public.

The 2025 description below is retained as historical project context, not evidence for the current evaluation.

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
