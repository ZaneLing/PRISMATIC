# v0.29 — Conditional program memory with isolated fresh witnesses

## 1. Question and actual mechanism

v0.27 showed tiny memory gains and no established advantage over greedy edits. This registered intervention separates ordinary per-drug calibration from language-agent rule synthesis and isolates every witness patient from all policy fits and candidate statistics. It uses the same retrospective MIMIC-IV ATC-L4 task, with full and molecular spaces kept separate. It does not generate doses or establish prospective clinical correctness.

Of the 7,115 training patients, each seed assigns 5,692 to policy fitting and 1,423 permanently to witness verification by a label-independent hash. Five rounds grow the fit cohort and expose a fresh disjoint witness batch of 285/285/285/284/284 patients. Witness labels cannot fit any coefficient or candidate statistic at any round. Fixed v0.27 vocabularies predate this partition. A witness is reused for up to four sequential edits within its one round; this is adaptive training validation, not independent confirmation.

The shared calibration control learns class-specific thresholds from cross-fitted fitting-patient predictions. The language agent receives only aggregate, supported feature/drug error contexts and synthesizes one- or two-predicate ADD/DELETE programs. Actual induction effects and fresh witnesses verify them. Greedy search enumerates both positive and negative predicate combinations; random and shuffled-evidence agents remain visible. Shuffling changes numeric support/gain assignment, while error-based focus-drug and feature selection stay fixed. No-witness uses the same own-agent proposals, not an independently learned counterfactual trajectory.

**Evolved artifact:** executable conditional rule memory. Calibration and coefficient refits are ordinary supervised updates; language-model weights and tool code stay fixed. All original base/fold models, proposals, rejected edits and raw round states are saved locally. No v0.29 test inference is performed.

## 2. Actual execution status

| Panel | Seed | Completed rounds /5 | Own-agent rules | Status |
|---|---:|---:|---:|---|
| full | 137 | 4 | 10 | training |
| full | 42 | 5 | 6 | selection_frozen |
| molecular | 137 | 5 | 8 | selection_frozen |
| molecular | 2026 | 2 | 3 | training |
| molecular | 42 | 5 | 5 | selection_frozen |

Synthetic execution probes cover strict patient roles, conjunction semantics, target-field rejection, supported program effects, accept/reject gates and calibration changes. These probes are not clinical performance scores.

## 3. Independently audited guard comparison

Same 1,231 visits/467 patients, report-only guard. Each included seed has independent raw-source reconstruction and fresh reproduction of all selected base/fold fits. Unfinished/unaudited cells remain pending.

| Panel | Method | Audited seeds | Patient F1 ± SD | Patient Jaccard ± SD |
|---|---|---:|---:|---:|
| full | raw_policy | 1 | 0.60594 (one seed) | 0.45161 (one seed) |
| full | calibrated_policy | 1 | 0.60719 (one seed) | 0.45324 (one seed) |
| full | greedy_conditional_memory | 1 | 0.60719 (one seed) | 0.45306 (one seed) |
| full | random_conditional_memory | 1 | 0.60687 (one seed) | 0.45287 (one seed) |
| full | own_error_program_agent | 1 | 0.60789 (one seed) | 0.45379 (one seed) |
| full | shuffled_evidence_program_agent | 1 | 0.60719 (one seed) | 0.45324 (one seed) |
| full | matched_proposals_no_witness | 1 | 0.60694 (one seed) | 0.45262 (one seed) |
| molecular | raw_policy | 1 | 0.57623 (one seed) | 0.42480 (one seed) |
| molecular | calibrated_policy | 1 | 0.57911 (one seed) | 0.42750 (one seed) |
| molecular | greedy_conditional_memory | 1 | 0.58026 (one seed) | 0.42835 (one seed) |
| molecular | random_conditional_memory | 1 | 0.57984 (one seed) | 0.42805 (one seed) |
| molecular | own_error_program_agent | 1 | 0.57908 (one seed) | 0.42721 (one seed) |
| molecular | shuffled_evidence_program_agent | 1 | 0.57877 (one seed) | 0.42715 (one seed) |
| molecular | matched_proposals_no_witness | 1 | 0.57887 (one seed) | 0.42683 (one seed) |

| Panel | Own agent minus comparator | F1 difference (pp) | Patient interval (pp) |
|---|---|---:|---:|
| full | raw_policy | +0.195 | [-0.099, +0.487] |
| full | calibrated_policy | +0.070 | [-0.005, +0.160] |
| full | greedy_conditional_memory | +0.070 | [+0.020, +0.123] |
| full | random_conditional_memory | +0.102 | [+0.015, +0.202] |
| full | shuffled_evidence_program_agent | +0.070 | [-0.005, +0.160] |
| full | matched_proposals_no_witness | +0.095 | [-0.006, +0.197] |
| molecular | raw_policy | +0.285 | [-0.073, +0.667] |
| molecular | calibrated_policy | -0.003 | [-0.111, +0.116] |
| molecular | greedy_conditional_memory | -0.118 | [-0.232, -0.002] |
| molecular | random_conditional_memory | -0.076 | [-0.236, +0.092] |
| molecular | shuffled_evidence_program_agent | +0.031 | [-0.095, +0.169] |
| molecular | matched_proposals_no_witness | +0.021 | [-0.098, +0.138] |

Intervals average observed seeds before patient resampling; they do not estimate new-seed variability and are unadjusted descriptive intervals. Gains versus raw policy must be separated from calibration gains and from the additional language-agent contribution.

| Panel | Round | Raw proposal F1 | Calibrated proposal F1 | Own-agent proposal F1 | Rules / conjunctions by seed |
|---|---:|---:|---:|---:|---|
| full | 1 | 0.56351 | 0.56919 | 0.56939 | 2/0 |
| full | 2 | 0.57951 | 0.58630 | 0.58582 | 3/0 |
| full | 3 | 0.58569 | 0.59365 | 0.59280 | 3/1 |
| full | 4 | 0.59183 | 0.59920 | 0.59892 | 5/1 |
| full | 5 | 0.59570 | 0.60234 | 0.60210 | 6/1 |
| molecular | 1 | 0.53828 | 0.54199 | 0.54256 | 2/0 |
| molecular | 2 | 0.55363 | 0.55621 | 0.55789 | 3/0 |
| molecular | 3 | 0.56000 | 0.57210 | 0.57221 | 4/0 |
| molecular | 4 | 0.56934 | 0.57732 | 0.57747 | 6/0 |
| molecular | 5 | 0.57055 | 0.58171 | 0.58171 | 5/0 |

| Panel | Method | Logical model calls | Logical response USD | Enumerated programs | Proposal seconds |
|---|---|---:|---:|---:|---:|
| full | raw_policy | 0 | 0.00000 | 0 | 0.0 |
| full | calibrated_policy | 0 | 0.00000 | 0 | 0.0 |
| full | greedy_conditional_memory | 0 | 0.00000 | 25448 | 67.5 |
| full | random_conditional_memory | 0 | 0.00000 | 25446 | 68.7 |
| full | own_error_program_agent | 5 | 0.00983 | 15373 | 65.9 |
| full | shuffled_evidence_program_agent | 5 | 0.00890 | 15363 | 88.6 |
| full | matched_proposals_no_witness | 0 | 0.00000 | 0 | 0.1 |
| molecular | raw_policy | 0 | 0.00000 | 0 | 0.0 |
| molecular | calibrated_policy | 0 | 0.00000 | 0 | 0.0 |
| molecular | greedy_conditional_memory | 0 | 0.00000 | 25451 | 70.2 |
| molecular | random_conditional_memory | 0 | 0.00000 | 25452 | 70.0 |
| molecular | own_error_program_agent | 5 | 0.00846 | 15375 | 53.2 |
| molecular | shuffled_evidence_program_agent | 5 | 0.00757 | 15372 | 52.6 |
| molecular | matched_proposals_no_witness | 0 | 0.00000 | 0 | 0.0 |

## 4. Executed memory carryover and edit-transfer diagnosis

This registered replay uses proposal cases only, after early development scores were observed. It changes no training decision, fits no model and makes no new API call. For each round, all compared memories use the same current policy and calibration.

| Audited run | Accepted edits with positive proposal transfer | Negative transfer | Zero transfer |
|---|---:|---:|---:|
| full-seed42 | 4 | 4 | 0 |
| molecular-seed42 | 4 | 3 | 0 |

| Audited run | Round | Prior-memory effect (F1 pp) | New-edit effect (F1 pp) |
|---|---:|---:|---:|
| full-seed42 | 1 | +0.0000 | +0.0203 |
| full-seed42 | 2 | -0.0182 | -0.0296 |
| full-seed42 | 3 | -0.1099 | +0.0249 |
| full-seed42 | 4 | -0.0077 | -0.0201 |
| full-seed42 | 5 | -0.0421 | +0.0185 |
| molecular-seed42 | 1 | +0.0000 | +0.0574 |
| molecular-seed42 | 2 | +0.1709 | -0.0036 |
| molecular-seed42 | 3 | +0.0263 | -0.0153 |
| molecular-seed42 | 4 | +0.0202 | -0.0056 |
| molecular-seed42 | 5 | -0.0099 | +0.0101 |

A positive fresh-witness edit can have a negative effect on proposal patients. Old rules can also change value after the policy/calibration changes. These findings motivate compatibility revalidation, but do not constitute an executed improved agent or an independently learned counterfactual trajectory.

## Artifacts / 交付

- [Registered protocol](protocol.json)
- [Actual pre-training probes](results/runtime_probe.json)
- [Audit-gated aggregate results](results/summary.json)
- [Registered memory diagnosis](diagnostic_addendum.json) and [actual replay effects](results/memory_diagnostic.json)
- [Historical round-selection metadata correction](../paper/round_selection_metadata_audit.json)

A rolling-export dictionary can show later best-round choices in older nested `round.best` fields. Immutable per-round receipts and per-arm `best_round` values are independently verified; corrected historical selections are linked above. Scores, rules and final model choices are unchanged. Restricted records, predictions and fitted weights stay local.
