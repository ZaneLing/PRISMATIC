# PRISMATIC 2: local preliminary experiments

The [versioned research paper](../paper/README.md) is the current entry point.
Its Table 2 contains the same-question RxSafeBench harness comparison. The
older `REPORT_ZH.md` and `REPORT_EN.md` are retained as v0.1 snapshots.

This directory contains reproducible **research** code for a first pass over the
credentialed datasets under `~/Desktop/MedTreeBench/dataset/restricted`.
It does not generate clinical orders or claim to evaluate patient safety.

## What has run

1. `build_cohort.py` joins MIMIC-IV v3.1 hospital admissions and prescriptions
   with MIMIC-IV-ED v2.2 stays, triage, and medication reconciliation. The
   decision time is hospital admission. Only reconciliation rows charted
   between ED arrival and admission enter the input. The target is the set of
   oral-route GSN codes with a prescription start time in the following 6 or
   24 hours. Discharge notes and discharge diagnoses are excluded.
2. `train_baselines.py` uses a deterministic patient-disjoint 80/10/10 split,
   then samples at most 40,000/4,000/4,000 admissions. The label vocabulary is
   the 64 most frequent training-only codes. It compares popularity, TF-IDF
   plus one-vs-rest Naive Bayes, and TF-IDF plus one-vs-rest SGD logistic loss.
   Each method outputs five codes per case.
3. `prepare_llm_pilot.py` and `run_local_llm_pilot.py` run a 32-case local
   interface test using an MLX 4-bit Qwen3-4B-Instruct-2507 snapshot. The
   model selects from the same 64 training-derived candidate codes. The test
   assesses JSON compliance and historical matching only.
4. `harness.py` defines a structured review contract with versioned rule
   provenance, missing-information states, bounded one-order replacement, and
   no claim of safety when no rule fires. `test_harness.py` checks synthetic
   invariants. `evolution_gate.py` is an offline policy-promotion sketch.
5. `build_supportive_cohort.py` attaches three descriptive six-hour labels to
   the admission cohort: IV isotonic saline (excluding named flushes/carriers),
   ondansetron, and senna/docusate. `evolution_curve.py` adds cases in
   cumulative batches of 250, 1,000, 4,000, 16,000, and 40,000 and compares
   a case memory with incremental logistic SGD and a prevalence baseline on
   a fixed 1,000-case patient-disjoint test sample.
6. `run_public_openrouter.py` evaluates current API models on a deterministic
   subset of the **public, simulated** RxSafeBench. `run_rxqa_openrouter.py`
   evaluates the public RxQA OpenFDA questions. Both use OpenRouter ZDR routing
   and deny provider data collection; neither reads restricted patient files.
7. `run_public_harness.py` adds a paired two-call comparison on the same public
   RxSafeBench questions and archived initial answers: ordinary reconsideration
   versus a structured evidence review with a bounded revision gate. This is a
   multiple-choice scaffold pilot, distinct from the structured order-review
   interface in `harness.py`.

## Privacy boundary

All patient-level cohorts, model artifacts trained on patient-level data,
prompts, and predictions are stored under
`~/Desktop/MedTreeBench/dataset/restricted/prismatic-v2/`.
Set `PRISMATIC_RESTRICTED_ROOT` and optionally `PRISMATIC_ARTIFACT_DIR` to use
a different credentialed local storage location.
This project directory contains code, aggregate results, local public model
weights, and local Python environments. No patient data are sent to a remote
inference API. The model download retrieves public weights only.
For restricted MIMIC data and online services, follow the current
[PhysioNet guidance](https://physionet.org/news/post/llm-responsible-use/).

## Reproduce

Use Python 3.9+ with `requirements.txt`; the local LLM pilot requires Python
3.12+ and `requirements-llm.txt` on Apple silicon.

```bash
python build_cohort.py --hours 6
python train_baselines.py
python build_cohort.py --hours 24 --output ~/Desktop/MedTreeBench/dataset/restricted/prismatic-v2/cohort_24h.parquet
python train_baselines.py --cohort ~/Desktop/MedTreeBench/dataset/restricted/prismatic-v2/cohort_24h.parquet --output-dir ~/Desktop/MedTreeBench/dataset/restricted/prismatic-v2/24h
python -m unittest -v test_harness.py
python build_supportive_cohort.py
python evolution_curve.py
```

For the public, paired RxSafeBench Table 2, first reproduce the pinned direct
answers, then run the second-call arms on exactly the same cases. Provide a
public RxSafeBench checkout at commit
`a25f9a1f173cf034b678c60f051901e86fbbbbb2`; the runners reject files
whose SHA-256 differs from the pinned public release. Use an OpenRouter key in
the process environment; do not pass restricted patient files to these scripts.

```bash
export OPENROUTER_API_KEY='your-key'
python run_public_openrouter.py --data-dir /path/to/public/RxSafeBench/data
python run_public_harness.py --data-dir /path/to/public/RxSafeBench/data
python render_harness_table.py --language zh
python render_harness_table.py --language en
python -m unittest -v test_public_harness.py
```

The optional local LLM model is pinned at revision
`50d427756c6b1b2fe0c0a10f67fbda1fc8e82c1b` of
[`mlx-community/Qwen3-4B-Instruct-2507-4bit`](https://huggingface.co/mlx-community/Qwen3-4B-Instruct-2507-4bit).
Install `mlx-lm` in a Python 3.12 environment, then run:

```bash
python prepare_llm_pilot.py
python run_local_llm_pilot.py
python compare_llm_pilot.py
```

The last command uses the general experiment environment, not the MLX
environment. Aggregate results are copied into `results/`; patient-level
outputs remain in the restricted directory.

For public OpenRouter benchmarks, clone the upstream public repositories at
the commits recorded in the result JSON files, set `OPENROUTER_API_KEY` in the
process environment, and run:

```bash
python run_public_openrouter.py --data-dir /path/to/RxSafeBench/data --per-type 30
python run_rxqa_openrouter.py --csv /path/to/rxqa/rxqa_openfda.csv --count 100
```

Keep the API key outside this repository. These public benchmark calls do not
have the same task definition or score as the local MIMIC order prediction.
Both runners fail closed unless the input files match the pinned public
repository commit checksums, preventing accidental submission of a local
patient file through the benchmark CLI.

## Interpretation boundary

The target is **what clinicians ordered**, not what an independent expert
judged appropriate. The ED triage table lacks a per-row chart time, so this
pilot treats triage content as available by admission based on its workflow
position; that assumption needs source-level verification. GSN coverage is
restricted to the top 64 training codes. None of these results estimates
adverse drug events, contraindication sensitivity, or clinical utility.

The supportive-order pilot is further conditioned on an oral GSN order in the
first six hours, since it reuses the first cohort. The saline label excludes
strings explicitly naming flushes but may still include IV carriers; volume,
rate, and intent are not adjudicated. A growing historical-order score does
not demonstrate learning a clinician's reasoning or improved patient care.

See [EXPERIMENT_PLAN.md](EXPERIMENT_PLAN.md) and the bilingual reports
`REPORT_ZH.md` / `REPORT_EN.md` for the research plan and results.
