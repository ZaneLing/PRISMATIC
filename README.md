# RxRSIAgent — PRISMATIC research repository

## Current repair pilot — 2026-10-20

Candidate coverage loss is attributed to the 128-name vocabulary and top-24 truncation. The repaired updater now changes candidate recall, evidence tools and conditional procedural memory. Three-round studies compare local and aggregate-only stronger proposers on the same 72 training admissions, with a separate 48-admission exploratory audit. New paid API spend: USD 0.085203 / USD 10. These pilot scores do not replace the full 1,082-admission table.

- [中文修复结果](upgrade_v51/RESULTS.zh.md) · [English repair results](upgrade_v51/RESULTS.en.md) · [Code and protocol](upgrade_v51/README.md).

## Complete-cohort evidence — 2026-10-17

**New complete local MIMIC-IV experiment: 1,082 admissions. RxRSIAgent drug F1 7.19%; Core4 F1 4.22%.** The corrected-interface trajectory retains 0 conditional update(s); paired intervals, component ablations and frozen-state transfer are reported. This is a catalogue-constrained local Qwen3-4B prescription adapter.

- [中文完整结果与跨方法主表](paper/CURRENT_RESULTS.zh.md) · [Full English results](paper/CURRENT_RESULTS.en.md).
- [Local experiment and comparator fidelity](upgrade_v50/README.md) · [aggregate audit](upgrade_v50/results/audit.json) · [round trajectory](upgrade_v50/results/round_curve.json).
- [English ACL manuscript](paper/latex/v0.3/prismatic_v03_en.tex) · [paper index and archives](paper/README.md).
- [Prescription actor](upgrade_v50/actor.py) · [frozen prescription state](upgrade_v50/test_freeze_scope.json).
- [Hosted QA actor](rxrsiagent/selected_agent.py) · [QA profile](rxrsiagent/selected_profile.json).

SafeRx-Agent is a limited independent task adaptation; SkeMex executes the pinned author memory core with a common actor; FLAME transfers the actual released trained list-policy component. Complete original workflows are not reproduced, and no superiority over the original papers is claimed. Published reference scores stay in a separate protocol-qualified file.

Public QA remains RxSafe 491/988 (49.70%), RxQA 196/300 (65.33%), and MedPIC 274/467 (58.67%). The QA learner retains no change. Historical supervised calibration is a separate control.

**The complete-cohort local experiment incurred USD 0 in API charges; the new repair pilot cost is reported above.** Restricted records, raw responses, private case studies and checkpoints stay local. Local compute is unpriced; historical located response expenditure remains about USD 89.53. Older queues remain paused.

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
