# RxRSIAgent v0.6 — executable prescription agent

**[中文设计与流程图](DESIGN.zh.md) · [English design](DESIGN.en.md) · [中文实验结果](RESULTS.zh.md) · [English results](RESULTS.en.md)**

![Implemented inference and training loop](architecture.png)

## What was actually run

- Patient-disjoint MIMIC-IV/ED: 40,000 training, 4,000 validation, 4,000 development-test admissions.
- Raw prescription names, route, dose string, dose unit and observed frequency. The fixed 128-name vocabulary is learned from the initial 8,000 training cases. Out-of-vocabulary targets remain in recall denominators.
- Cumulative policy/template learning at 8k, 16k, 32k and 40k, with validation-only version selection.
- 32k training-case pre-update feedback records; error-prioritized replay with 0 / 0.25 / 1 strengths and global/similar-case joint templates.
- Actual local Qwen3-4B planning: 20 validation plus 20 test cases, with and without two training episodes; same candidate tools, frozen backbone and 384-token cap.
- Automatic GT evaluation and independent recomputation. No clinician-review prerequisite; no restricted patient text sent to external APIs.

Drug micro-F1 grows from **0.35841 to 0.40668**. Selected core-order micro-F1 is **0.28003**. Ordinary same-40k training matches the selected policy; error prioritization did not win. The validation-selected deployed arm is the learned policy, since the tested LLM selectors were weaker. LLM weights are frozen. Natural-language skill editing and LLM fine-tuning are future work.

## Reproduce locally

The scripts expect the existing v4 cohort and raw mapped-order Parquet files under `~/Desktop/MedTreeBench/dataset/restricted/prismatic-v4/`. This restricted dataset is not in GitHub. Private checkpoints, labels, traces and error ledgers are written under `restricted/prismatic-v6/`.

Use a research Python environment with `numpy`, `pandas`, `pyarrow`, `duckdb`, `scikit-learn`, `joblib` and `matplotlib`. Run from the repository root, in order:

```bash
python upgrade_v6/run_evolution.py
python upgrade_v6/run_error_replay.py
```

Then use an Apple Silicon environment with `mlx-lm` and the local model at `~/Desktop/PRISMATIC/upgrade_v2/.local/models/qwen3-4b-instruct-2507-4bit`:

```bash
python upgrade_v6/run_local_agent.py
```

Model: `mlx-community/Qwen3-4B-Instruct-2507-4bit`, revision `50d427756c6b1b2fe0c0a10f67fbda1fc8e82c1b`. Completed inference traces are resumable only when source and input fingerprints match. To rerun a changed experiment, preserve the previous private directory as a versioned archive before generating new traces.

Finish in the research environment:

```bash
python -m unittest discover -s upgrade_v6 -p 'test_*.py' -v
python upgrade_v6/verify_results.py
python upgrade_v6/draw_architecture.py
python upgrade_v6/render_delivery.py
```

The renderer updates the **existing English paper in place**, preserving its embedded original ZIP template. Compile it with the desktop editor's built-in compiler. The repository contains aggregate metrics only.

## Evidence map

| File | Evidence |
| --- | --- |
| `protocol.json` | r1 task, inputs, update objects and selection rules |
| `results/order_evolution_results.json` | Executed growth and 4k method comparison |
| `results/frozen_selection.json` | r1 validation-selected checkpoints and thresholds |
| `results/error_replay_protocol.json` | r2 grid defined before that run |
| `results/error_replay_selection.json` | All replay/template/threshold validation candidates |
| `results/error_replay_results.json` | Selected r2 test scores, including negative replay result |
| `results/local_agent_results.json` | Local LLM arms, validation selection, costs and failures |
| `results/verification.json` | Independent counts, split checks and patient-cluster bootstrap |
| `results/run_manifest.json` | Code/result hashes, environment and model identity |
| `reported_baselines.json` | Directly cited literature results with source and protocol |

Published baseline scores require no local reproduction. Their protocols are retained as separate panels; the current raw-name development result is not a matched external-benchmark result. Ground truth measures recorded-order agreement, while missing indication, fluid purpose and infusion-rate labels remain unscored.
