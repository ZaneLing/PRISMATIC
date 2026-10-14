# RxRSIAgent v0.7 — completed structured-order audit

[中文结果](RESULTS.zh.md) · [English results](RESULTS.en.md) · [当前系统设计](../paper/RXRSI_DESIGN.zh.md) · [English design](../paper/RXRSI_DESIGN.en.md)

This increment contains executed results, including negative controls. Three seeds (42, 137, 2026), five checkpoints, and 12 method/ablation rows use the same new 4,000-admission test. The full method is not the best equal-data control.

## Evidence map

| File | Evidence |
|---|---|
| `results/data_manifest.json` | Split counts, patient disjointness, membership and vocabulary hashes |
| `results/decisions_seed_*.json` | Proposal/guard decisions and artifact hashes per round |
| `results/round_results_seed_*.json` | Baselines, object ablations, fixed-test curves and regressions |
| `results/strong_*seed_*.json` | Validation-selected word/character ensemble and Naive Bayes controls |
| `results/summary.json` | Three-seed summary, independent recount and patient-cluster bootstrap |
| `round_curves.png` | All three accepted-state test trajectories |

The order tool learns a joint observed route/dose/unit/frequency template conditional on context. It does not invent missing fields. Drug F1 and core-order F1 remain the common endpoints for all drugs. LLM parameters and language skills do not change in v0.7.

## Reproduction

Run from this directory with the research environment (NumPy, pandas, SciPy, scikit-learn, DuckDB, joblib, matplotlib). The authorized local v0.4/v0.6 data products are prerequisites. Restricted inputs and checkpoints are never committed.

```bash
python prepare_data.py
python run_rounds.py 42
python run_rounds.py 137
python run_rounds.py 2026
python run_strong_baselines.py 42
python run_strong_baselines.py 137
python run_strong_baselines.py 2026
python summarize.py
```

The strong-control extension was added after the first v0.7 test analysis. Its hyperparameters are chosen only on proposal validation, but the overall study is a development extension, not a preregistered confirmation. All saved methods are independently recounted. Order-tool training sometimes reaches the configured iteration limit; the executed settings are preserved.
