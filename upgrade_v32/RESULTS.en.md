# v0.32 — Controlled binary-decision repair: execution and results

## 1. What this experiment tests

The failed first v31 update emits valid all-zero prescriptions. This four-arm pilot tests training-prefix exposure and class imbalance with the same 400 training examples and 100 optimizer steps per arm. All four new adapters, the frozen backbone and the failed adapter use the same label-free zero-prefix scorer. Original retrieval top-8 and all-20 candidates are direct controls.

A fixed 0.5 threshold measures the uncalibrated decision behavior. A second endpoint calibrates one global threshold on the 100 proposal admissions, shared across ranked and permuted views. It applies the same calibration to every neural state. Calibration-only gains are reported separately from weight-update contrasts. Both endpoints retain drug precision, recall and mean prescription size alongside F1 and empty outputs, so selecting more medications cannot be mistaken for an unqualified improvement.

## 2. Actual completion

- Completed fits: **4/4**
- Independently audited score panels: **none yet**
- API requests: **0**

| Arm | Steps | Fit seconds | Adapter SHA-256 (prefix) |
|---|---:|---:|---|
| teacher_uniform | 100 | 1739.2 | 03e345d3b72d |
| zero_uniform | 100 | 1505.8 | 200340a805f8 |
| teacher_balanced | 100 | 1569.2 | a852a5c31571 |
| zero_balanced | 100 | 1579.0 | d1e56ac1bd2c |

Fit completion is checked against the saved original adapter hash. A separate audit reconstructs all 8,000 binary labels and checks all four training receipts before proposal inference. The scoring preflight passed 120 synthetic case/probability bindings, all threshold choices, source recounting and byte-identical resume; these synthetic checks are not clinical results.

**Training audit passed for all four arms.** It reconstructed the 8,000 targets (1,604 positives), checked the 100-step training logs, verified 3,670,016 finite adapter parameters and a nonzero LoRA update per arm, and confirmed no patient overlap between the 400 training examples and 100 proposal cases. Optimizer trajectories were not independently replayed. Proposal inference is now permitted; completed training is not evidence of improved prescribing.

[Training audit](results/training_audit.json)

## 3. proposal

No independently audited score is available. Pending prerequisites: evaluation_and_recount.

## 4. guard

No independently audited score is available. Pending prerequisites: frozen_thresholds, proposal_summary, proposal_audit, v31_seed42_frozen_selection.

## 5. Interpretation boundary

This pilot is one-seed, one-round supervised repair. It does not by itself show recursive self-improvement. Fixed candidate retrieval and dose templates do not evolve. After the four training states and ordinary thresholds freeze, the guard waits for all original v31 seed42 selections to freeze as well; guard scores cannot choose a winning repair. Multi-round own-error, shuffled-error and uniform controls remain necessary.

[Protocol](protocol.json) · [Evaluation addendum](evaluation_addendum.json) · [Execution progress](results/progress.json) · [Synthetic scoring preflight](results/evaluation_probe.json) · [Earlier collapse diagnosis](../upgrade_v31/COLLAPSE.en.md)
