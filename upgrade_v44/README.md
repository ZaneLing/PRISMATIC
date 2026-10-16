# Experiment 44

Current final learner: cumulative past roots and promising rejected interventions are replayed, with explicit no-edit handling and an external proposer.

This is a real development experiment, not a renamed paper method. The paper method is RxRSIAgent. All experiments reuse the same400 public training cases (200 RxSafe +200 MedQA) and the same development cohorts. No additional unique-case count or independent-seed replication is implied.

- Shared data/source/budget protocol: `../upgrade_v37/protocol.json`.
- Exact update protocol and learner hash: `learning_protocol.json`.
- Completed states and all rejection/decline outcomes: `results/learning.json`.
- Raw inputs, full traces and API receipts stay in the external local cache; no restricted clinical data are sent.
- Runtime: the existing `upgrade_v2/.venv` Python environment with NumPy, scikit-learn and PyArrow. Preparation requires the previously pinned public-data/source caches from experiments8,11,35 and36; this is not a standalone one-command data installer.
- The shared35USD incremental successful-response cap covers all experiments37–44 and evaluation, not35USD each.

## Current reproduction sequence

Run from the repository root with the existing configured environment. `learn.py` resumes its immutable local caches and refuses a changed learner hash. Do not overwrite protocol or source files to rerun a result.

```bash
python upgrade_v44/learn.py
python upgrade_v37/evaluate.py --experiment 44 --mode freeze
python upgrade_v37/evaluate.py --experiment 44 --mode independent
python upgrade_v37/evaluate.py --experiment 44 --mode main --split test_rx
python upgrade_v37/evaluate.py --experiment 44 --mode main --split test_qa
python upgrade_v37/evaluate.py --experiment 44 --mode shortcuts
python upgrade_v44/resume.py
python upgrade_v37/audit.py --experiment 44
python upgrade_v44/report.py
python paper/render_acl.py
```

The current actor is `actor44.py`: single-choice inference matches the fixed training actor; a pre-test multi-answer adapter removes conflicting single-answer JSON examples for MedPIC. Its implementation and test freeze bind both code paths. The inference actor contains no numerical calibration. Ordinary supervised calibration remains runnable as `upgrade_v35/supervised_control.py`, with its archived profile.

[中文完整结果](RESULTS.zh.md) · [Full English results](RESULTS.en.md).

A declared post-freeze runtime amendment (`runtime.py`, `runtime_amendment.json`) normalizes only malformed search-focus types. It completed two missing RxSafe cases and hashes the other986 unchanged files. The original test freeze is preserved. This is a parser repair, not learned improvement.
