# Experiment 43

Treat explicit null/no-edit as a legitimate decision, retaining its diagnosis rather than forcing a repair.

This is a real development experiment, not a renamed paper method. The paper method is RxRSIAgent. All experiments reuse the same400 public training cases (200 RxSafe +200 MedQA) and the same development cohorts. No additional unique-case count or independent-seed replication is implied.

- Shared data/source/budget protocol: `../upgrade_v37/protocol.json`.
- Exact update protocol and learner hash: `learning_protocol.json`.
- Completed states and all rejection/decline outcomes: `results/learning.json`.
- Raw inputs, full traces and API receipts stay in the external local cache; no restricted clinical data are sent.
- Runtime: the existing `upgrade_v2/.venv` Python environment with NumPy, scikit-learn and PyArrow. Preparation requires the previously pinned public-data/source caches from experiments8,11,35 and36; this is not a standalone one-command data installer.
- The shared35USD incremental successful-response cap covers all experiments37–44 and evaluation, not35USD each.
