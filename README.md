# RxRSIAgent — PRISMATIC research repository

## Current paper and implementation — 15 October 2026

New: [clinician-oriented evaluation](paper/CLINICAL_EVALUATION.en.md) / [医生视角指标](paper/CLINICAL_EVALUATION.zh.md), and [audited evolution rounds](paper/EVOLUTION.en.md) / [逐轮进化证据](paper/EVOLUTION.zh.md). The Introduction now discusses scoped Utah prescribing pilots; Figure2 and Tables8–9 connect artifact changes, outcomes and module attribution.

**RxRSIAgent** is the method name. The current English ACL manuscript retains one development-selected agent, a complete architecture figure, a named-method main table, component ablations, learning rounds, and two public case studies. Historical prototypes remain in archived reports, outside the paper.

- [English ACL manuscript](paper/latex/v0.3/prismatic_v03_en.tex) — existing editor path; official ACL review style.
- [中文当前结果与主表](paper/CURRENT_RESULTS.zh.md) / [Current English results](paper/CURRENT_RESULTS.en.md).
- [中文结构与18类临床问题](paper/RXRSI_DESIGN.zh.md) / [English architecture and risk map](paper/RXRSI_DESIGN.en.md).
- [RxRSIAgent implementation](rxrsiagent/README.md), [selected profile](rxrsiagent/evaluated_profile.json), [evidence manifest](paper/latex/v0.3/manuscript_evidence.json).
- [Paper reading index and historical versions](paper/README.md).

**Measured agent:** 501/988 on the derived RxSafeBench task and 183/300 on public RxQA. The main table explicitly names MedAgents, MDAgents, SafeRx-Agent and GRASP. The first three are unmeasured under the local protocol; overall superiority is not established.

**New measured tool repair:** on all300 public RxQA questions, excerpt coverage rises from1 to214;193 receive dosage material. All1,666 returned source spans are independently checked. Twelve synthetic software tests pass. These results do not replace the saved agent scores or establish clinical safety. Product applicability and clinical rule integrations remain incomplete.

The long-running research queues remain paused. This increment makes no new provider calls. [Pre-consolidation experiment archive](paper/RESULTS_ARCHIVE_2026-10-15.en.md) preserves earlier counts, failures and partial studies.

---

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
