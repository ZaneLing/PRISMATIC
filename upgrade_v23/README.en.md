# v0.23 — Matched feedback-assignment experiment

## Purpose

Test whether feedback tied to the agent's own errors improves prescription selection beyond ordinary learning and an identical weight distribution assigned randomly. This continues the completed numerical-state pilot; it does not claim that feature engineering is autonomous RSI.

## Executed protocol

- Data: v0.21 recorded-availability cohort, 40,000 training / 2,000 proposal / 2,000 guard / 1,082 test admissions. The test was previously observed; new scores are exploratory.
- Three seeds: 42, 137, 2026. Five cumulative blocks: 8k, 16k, 24k, 32k, 40k. Seeds vary order and optimization jointly; blocks are not calendar time.
- Arms: uniform weights; accepted-parent error weights; the same error weights permuted within each new block.
- Fixed: initial-8k word/numeric representation, 128 raw drug names, updater code, seven proposal thresholds and promotion rule. No LLM or API calls.
- Equal budget: 128 classifiers, exactly 60 epochs each, same cases/order within seed. Initial models are reused identically. Order tools use currently seen cases only.
- Evolving: policy parameters, persistent case weights, order-tool parameters and accepted state. Frozen selections precede all new test inference.
- Verification: independently infer parent feedback and recount weights, verify distributions/epochs/membership, recount all predictions, and report paired patient-cluster intervals, rejected checkpoints and regressions.

All three training runs, frozen test evaluations and independent audits are complete. [Full results and trajectories](RESULTS.en.md). The protocol was pushed in commit `9550d261` before training.

## Reproduction

Use the project research Python environment with one BLAS thread. Prepare bundles with `prepare_data.py`; run `train.py 42`, `train.py 137`, and `train.py 2026`; then run `evaluate.py`, `audit.py`, and `report.py` in order. The evaluator refuses incomplete selections. Model/feedback/order data remain in the restricted local directory; GitHub receives code, hashes and aggregates only.

`protocol.json` is the exact registration. `results/journal_seed_*` records actual completed transitions. Completed results are in `RESULTS.en.md` and `RESULTS.zh.md`.
