# v0.32 — Controlled repair of binary prescription decisions

## Why this intervention

The [completed v31 diagnosis](../upgrade_v31/COLLAPSE.en.md) finds valid all-zero prescriptions, low positive-decision probabilities and dependence on previous ground-truth answer tokens. It does not establish a unique cause. This pilot isolates two proposed causes before extending a repaired architecture to RSI rounds.

## Executed preparation and running fits

The protocol was committed before preparation, inference or fitting. Data reconstruction verifies the exact same400 training examples (393 patients) as the failed v31 update and100 proposal admissions (97 different patients), with zero patient overlap and no target truncation. Each example contains20 binary drug decisions. The training-only positive weight is6396/1604=3.98753.

Four fresh Qwen3-4B QLoRA fits cross two factors:

| Arm | Previous decision tokens during training | Binary loss |
|---|---|---|
| teacher_uniform | Ground-truth prefix | Equal decision weights |
| zero_uniform | All-zero prefix, independent of labels | Equal decision weights |
| teacher_balanced | Ground-truth prefix | Positive/negative balancing |
| zero_balanced | All-zero prefix, independent of labels | Positive/negative balancing |

Each arm uses exactly400 examples,100 steps, batch4, the same learning rate and adapter size, and seed42. Only the20 decision positions contribute to conditional binary loss; syntax tokens do not. All arms use the same zero-prefix inference scaffold. No forced nonempty prediction or fallback medication is added.

The implementation projects only the selected decoder positions through the original vocabulary head. Synthetic forward comparisons on both the base and failed adapter give zero measured probability difference from the full forward calculation in all four checks. Nine synthetic checks cover alignment, label blindness, untouched prompt tokens, gradients, padding and decision accounting. These validate implementation, not prescription quality.

[Actual training progress](results/training_progress.json) is updated from saved optimizer completions. Performance evaluation remains to be completed; no gain is claimed.

## Scoring and controls fixed before evaluation

Report fixed0.5 decisions and ordinary proposal-calibrated decisions separately for every state, including the frozen base and original failed adapter. A single global threshold from0.01 to0.99 is shared across both proposal views; it maximizes the mean drug/order micro-F1 objective, preferring the higher threshold on ties. Direct original-rank top8 and all20 candidate tools are controls. Keep all four arms, raw scores and calibration-only effects.

Every pilot state and threshold must freeze, and v31 seed42 must freeze all its original selections, before the reused200-case guard is evaluated. No old test data is used. Guard results cannot choose a winning arm. Candidate drug identity, routes and recorded dose templates remain unchanged; the model scores supplied candidates and the compiler constructs the output.

## Scope

This is a one-seed, one-round supervised mechanism repair. It does not establish self-improvement, clinical safety or superiority. A viable repair still needs matched uniform/own-error/shuffled-error multi-round experiments. The ongoing v31 study retains its original code, trajectories and failures.

[Registered protocol](protocol.json) · [Actual data audit](results/data_audit.json) · [Runtime checks](results/runtime_probe.json) · [Training implementation](run_training.py)
