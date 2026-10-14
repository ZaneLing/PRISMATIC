# v0.29 — Conditional program memory with isolated fresh witnesses

## 1. Question and actual mechanism

v0.27 showed tiny memory gains and no established advantage over greedy edits. This registered intervention separates ordinary per-drug calibration from language-agent rule synthesis and isolates every witness patient from all policy fits and candidate statistics. It uses the same retrospective MIMIC-IV ATC-L4 task, with full and molecular spaces kept separate. It does not generate doses or establish prospective clinical correctness.

Of the 7,115 training patients, each seed assigns 5,692 to policy fitting and 1,423 permanently to witness verification by a label-independent hash. Five rounds grow the fit cohort and expose a fresh disjoint witness batch of 285/285/285/284/284 patients. Witness labels cannot fit any coefficient or candidate statistic at any round. Fixed v0.27 vocabularies predate this partition. A witness is reused for up to four sequential edits within its one round; this is adaptive training validation, not independent confirmation.

The shared calibration control learns class-specific thresholds from cross-fitted fitting-patient predictions. The language agent receives only aggregate, supported feature/drug error contexts and synthesizes one- or two-predicate ADD/DELETE programs. Actual induction effects and fresh witnesses verify them. Greedy search enumerates both positive and negative predicate combinations; random and shuffled-evidence agents remain visible. Shuffling changes numeric support/gain assignment, while error-based focus-drug and feature selection stay fixed. No-witness uses the same own-agent proposals, not an independently learned counterfactual trajectory.

**Evolved artifact:** executable conditional rule memory. Calibration and coefficient refits are ordinary supervised updates; language-model weights and tool code stay fixed. All original base/fold models, proposals, rejected edits and raw round states are saved locally. No v0.29 test inference is performed.

## 2. Actual execution status

| Panel | Seed | Completed rounds /5 | Own-agent rules | Status |
|---|---:|---:|---:|---|
| full | 137 | 5 | 11 | selection_frozen |
| full | 2026 | 5 | 6 | selection_frozen |
| full | 42 | 5 | 6 | selection_frozen |
| molecular | 137 | 5 | 8 | selection_frozen |
| molecular | 2026 | 5 | 9 | selection_frozen |
| molecular | 42 | 5 | 5 | selection_frozen |

Synthetic execution probes cover strict patient roles, conjunction semantics, target-field rejection, supported program effects, accept/reject gates and calibration changes. These probes are not clinical performance scores.

## 3. Independently audited guard comparison

Same 1,231 visits/467 patients, report-only guard. Each included seed has independent raw-source reconstruction and fresh reproduction of all selected base/fold fits. Unfinished/unaudited cells remain pending.

| Panel | Method | Audited seeds | Patient F1 ± SD | Patient Jaccard ± SD |
|---|---|---:|---:|---:|
| full | raw_policy | 3 | 0.60570 ± 0.00050 | 0.45138 ± 0.00060 |
| full | calibrated_policy | 3 | 0.60803 ± 0.00087 | 0.45407 ± 0.00088 |
| full | greedy_conditional_memory | 3 | 0.60801 ± 0.00072 | 0.45394 ± 0.00078 |
| full | random_conditional_memory | 3 | 0.60762 ± 0.00086 | 0.45366 ± 0.00089 |
| full | own_error_program_agent | 3 | 0.60790 ± 0.00038 | 0.45381 ± 0.00049 |
| full | shuffled_evidence_program_agent | 3 | 0.60794 ± 0.00071 | 0.45399 ± 0.00070 |
| full | matched_proposals_no_witness | 3 | 0.60742 ± 0.00046 | 0.45317 ± 0.00055 |
| molecular | raw_policy | 3 | 0.57564 ± 0.00053 | 0.42407 ± 0.00070 |
| molecular | calibrated_policy | 3 | 0.57989 ± 0.00088 | 0.42804 ± 0.00064 |
| molecular | greedy_conditional_memory | 3 | 0.58094 ± 0.00060 | 0.42903 ± 0.00059 |
| molecular | random_conditional_memory | 3 | 0.57930 ± 0.00168 | 0.42723 ± 0.00154 |
| molecular | own_error_program_agent | 3 | 0.58021 ± 0.00105 | 0.42827 ± 0.00095 |
| molecular | shuffled_evidence_program_agent | 3 | 0.57956 ± 0.00097 | 0.42769 ± 0.00070 |
| molecular | matched_proposals_no_witness | 3 | 0.58010 ± 0.00106 | 0.42801 ± 0.00102 |

| Panel | Own agent minus comparator | F1 difference (pp) | Patient interval (pp) |
|---|---|---:|---:|
| full | raw_policy | +0.220 | [+0.004, +0.450] |
| full | calibrated_policy | -0.013 | [-0.068, +0.043] |
| full | greedy_conditional_memory | -0.011 | [-0.056, +0.033] |
| full | random_conditional_memory | +0.029 | [-0.029, +0.089] |
| full | shuffled_evidence_program_agent | -0.004 | [-0.060, +0.054] |
| full | matched_proposals_no_witness | +0.049 | [-0.009, +0.103] |
| molecular | raw_policy | +0.457 | [+0.177, +0.750] |
| molecular | calibrated_policy | +0.032 | [-0.037, +0.100] |
| molecular | greedy_conditional_memory | -0.073 | [-0.148, +0.002] |
| molecular | random_conditional_memory | +0.091 | [+0.003, +0.182] |
| molecular | shuffled_evidence_program_agent | +0.065 | [-0.017, +0.146] |
| molecular | matched_proposals_no_witness | +0.011 | [-0.054, +0.078] |

Intervals average observed seeds before patient resampling; they do not estimate new-seed variability and are unadjusted descriptive intervals. Gains versus raw policy must be separated from calibration gains and from the additional language-agent contribution.

| Panel | Round | Raw proposal F1 | Calibrated proposal F1 | Own-agent proposal F1 | Rules / conjunctions by seed |
|---|---:|---:|---:|---:|---|
| full | 1 | 0.56323 | 0.56793 | 0.56846 | 2/0, 3/0, 1/0 |
| full | 2 | 0.57907 | 0.58485 | 0.58475 | 3/0, 3/0, 2/0 |
| full | 3 | 0.58813 | 0.59438 | 0.59409 | 3/1, 7/0, 2/0 |
| full | 4 | 0.59418 | 0.59895 | 0.59831 | 5/1, 10/0, 4/0 |
| full | 5 | 0.59770 | 0.60233 | 0.60200 | 6/1, 11/1, 6/0 |
| molecular | 1 | 0.53803 | 0.54189 | 0.54214 | 2/0, 0/0, 1/1 |
| molecular | 2 | 0.55354 | 0.55899 | 0.55957 | 3/0, 0/0, 3/1 |
| molecular | 3 | 0.56260 | 0.57181 | 0.57188 | 4/0, 2/0, 4/2 |
| molecular | 4 | 0.57198 | 0.57727 | 0.57716 | 6/0, 5/0, 6/2 |
| molecular | 5 | 0.57429 | 0.58165 | 0.58178 | 5/0, 8/0, 9/2 |

| Panel | Method | Logical model calls | Logical response USD | Enumerated programs | Proposal seconds |
|---|---|---:|---:|---:|---:|
| full | raw_policy | 0 | 0.00000 | 0 | 0.0 |
| full | calibrated_policy | 0 | 0.00000 | 0 | 0.0 |
| full | greedy_conditional_memory | 0 | 0.00000 | 76350 | 227.2 |
| full | random_conditional_memory | 0 | 0.00000 | 76348 | 225.3 |
| full | own_error_program_agent | 15 | 0.02429 | 46125 | 193.7 |
| full | shuffled_evidence_program_agent | 15 | 0.02255 | 46096 | 213.3 |
| full | matched_proposals_no_witness | 0 | 0.00000 | 0 | 0.2 |
| molecular | raw_policy | 0 | 0.00000 | 0 | 0.0 |
| molecular | calibrated_policy | 0 | 0.00000 | 0 | 0.0 |
| molecular | greedy_conditional_memory | 0 | 0.00000 | 76354 | 214.1 |
| molecular | random_conditional_memory | 0 | 0.00000 | 76374 | 214.0 |
| molecular | own_error_program_agent | 15 | 0.02775 | 46116 | 167.9 |
| molecular | shuffled_evidence_program_agent | 15 | 0.02504 | 46111 | 162.3 |
| molecular | matched_proposals_no_witness | 0 | 0.00000 | 0 | 0.1 |

## 4. Executed memory carryover and edit-transfer diagnosis

This registered replay uses proposal cases only, after early development scores were observed. It changes no training decision, fits no model and makes no new API call. For each round, all compared memories use the same current policy and calibration.

| Audited run | Accepted edits with positive proposal transfer | Negative transfer | Zero transfer |
|---|---:|---:|---:|
| full-seed42 | 4 | 4 | 0 |
| full-seed137 | 7 | 4 | 0 |
| full-seed2026 | 5 | 3 | 0 |
| molecular-seed42 | 4 | 3 | 0 |
| molecular-seed137 | 5 | 3 | 0 |
| molecular-seed2026 | 6 | 3 | 0 |

| Audited run | Round | Prior-memory effect (F1 pp) | New-edit effect (F1 pp) |
|---|---:|---:|---:|
| full-seed42 | 1 | +0.0000 | +0.0203 |
| full-seed42 | 2 | -0.0182 | -0.0296 |
| full-seed42 | 3 | -0.1099 | +0.0249 |
| full-seed42 | 4 | -0.0077 | -0.0201 |
| full-seed42 | 5 | -0.0421 | +0.0185 |
| full-seed137 | 1 | +0.0000 | +0.1175 |
| full-seed137 | 2 | +0.0462 | +0.0000 |
| full-seed137 | 3 | -0.0277 | +0.0176 |
| full-seed137 | 4 | -0.0640 | -0.0109 |
| full-seed137 | 5 | -0.0371 | -0.0089 |
| full-seed2026 | 1 | +0.0000 | +0.0236 |
| full-seed2026 | 2 | -0.0151 | -0.0131 |
| full-seed2026 | 3 | -0.0258 | +0.0342 |
| full-seed2026 | 4 | -0.0263 | -0.0633 |
| full-seed2026 | 5 | -0.0314 | +0.0030 |
| molecular-seed42 | 1 | +0.0000 | +0.0574 |
| molecular-seed42 | 2 | +0.1709 | -0.0036 |
| molecular-seed42 | 3 | +0.0263 | -0.0153 |
| molecular-seed42 | 4 | +0.0202 | -0.0056 |
| molecular-seed42 | 5 | -0.0099 | +0.0101 |
| molecular-seed137 | 1 | +0.0000 | +0.0000 |
| molecular-seed137 | 2 | +0.0000 | +0.0000 |
| molecular-seed137 | 3 | +0.0000 | +0.0037 |
| molecular-seed137 | 4 | +0.0209 | +0.0476 |
| molecular-seed137 | 5 | +0.0458 | +0.0282 |
| molecular-seed2026 | 1 | +0.0000 | +0.0203 |
| molecular-seed2026 | 2 | +0.0002 | +0.0059 |
| molecular-seed2026 | 3 | -0.0184 | +0.0252 |
| molecular-seed2026 | 4 | -0.0485 | -0.0661 |
| molecular-seed2026 | 5 | -0.0428 | +0.0088 |

A positive fresh-witness edit can have a negative effect on proposal patients. Old rules can also change value after the policy/calibration changes. These findings motivate compatibility revalidation, but do not constitute an executed improved agent or an independently learned counterfactual trajectory.

## Artifacts / 交付

- [Registered protocol](protocol.json)
- [Actual pre-training probes](results/runtime_probe.json)
- [Audit-gated aggregate results](results/summary.json)
- [Registered memory diagnosis](diagnostic_addendum.json) and [actual replay effects](results/memory_diagnostic.json)
- [Historical round-selection metadata correction](../paper/round_selection_metadata_audit.json)

A rolling-export dictionary can show later best-round choices in older nested `round.best` fields. Immutable per-round receipts and per-arm `best_round` values are independently verified; corrected historical selections are linked above. Scores, rules and final model choices are unchanged. Restricted records, predictions and fitted weights stay local.
