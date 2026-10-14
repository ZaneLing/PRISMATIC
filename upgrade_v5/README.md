# PRISMATIC v0.5 execution

[中文结果](RESULTS.zh.md) · [English results](RESULTS.en.md) · [Architecture / 结构图](ARCHITECTURE.md)

This increment diagnoses the v4 50% empty-output failure, repairs historical/clinical state separation and parsing, executes validation-selected ranking and residual-memory growth, and reruns the fixed local LLM. It does not claim a clinically complete harness or a faithful SafeRx-Agent reproduction.

## Reproduction

Run from the repository root. Python environments and restricted inputs must already exist. No secrets or restricted text are needed in this repository.

```bash
PY=/Users/bytedance/Desktop/PRISMATIC/upgrade_v2/.venv/bin/python
MLX_PY=/Users/bytedance/Desktop/PRISMATIC/upgrade_v2/.venv-llm/bin/python
$PY upgrade_v5/audit_empty.py
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 $PY upgrade_v5/run_rankers.py
OPENBLAS_NUM_THREADS=2 $PY upgrade_v5/run_memory_fusion.py
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 $PY upgrade_v5/run_seed_robustness.py
$MLX_PY upgrade_v5/run_llm_repair.py
$PY upgrade_v5/ablate_parser.py
$PY -m unittest discover -s upgrade_v5 -p 'test_*.py' -v
$PY upgrade_v5/render_results.py
$PY upgrade_v5/plot_results.py
$PY upgrade_v5/update_paper.py
$PY upgrade_v5/update_indexes.py
$PY upgrade_v5/verify_results.py
```

`run_llm_repair.py` resumes only matching source/configuration/input fingerprints. Its validation gate is written before test inference. Run ranking and fusion first; do not alter their inputs mid-run. The original v4 raw RAG proposals are replayed for test repair and their original generation costs included.

## File map

| File | Purpose |
| --- | --- |
| `protocol.json` | Pre-execution fixed grids and development-test disclosure |
| `audit_empty.py` | Aggregate root-cause audit of original 50 cases |
| `core.py` | Partial parsing, separate clinical state, train-only experience ledger and promotion |
| `run_rankers.py` | Word/character validation grid; frozen 8k base + nested residual memory; 4k evaluation |
| `run_memory_fusion.py` | Validation-select static/memory fusion, retain negative test outcome |
| `run_seed_robustness.py` | Three seeds with frozen selected static configuration |
| `run_llm_repair.py` | 50 validation + 50 test; RAG repair; risk-flag/anchor review; validation gate |
| `test_core.py` | Eight regression and leakage contracts |
| `ablate_parser.py` | Same-generation old/new parsing control; no extra inference |
| `results/*.json` | Aggregate results and frozen selection provenance |

## Boundaries

- The current word/character/memory scorer predicts historical ATC classes. Empty targets and missing mappings do not mean absence of clinical need.
- `clinical_review` marks candidates unknown or blocked with verified evidence; it never authorizes administration. The experiment has no verified ingredient-level contraindication resource.
- Coarse TWOSIDES flags are queried in the LLM arm, not treated as clinical DDI truth.
- Memory grows from training-only observational feedback. It does not update LLM weights, learn saline indications, or prove clinical improvement.
- Main 4k comparisons use statistical rankers only. The LLM/state pipeline has 50 test cases; do not extrapolate its score to 4k.
- The selected memory mixture worsens the strong static ranker on test. Keep this negative result; do not select a different mixture using test outcomes.
