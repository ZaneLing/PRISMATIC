# Compute accounting for the common medication-method study

## 1. What is matched

Within each ATC-L4 panel, methods use the same patient partitions and label space. Author neural methods each receive 50 full epochs over 18,429 training visits, or 921,450 visit exposures. Their batch sizes, optimizer steps, parameter counts and devices differ. The 50-epoch budget therefore supports a matched exposure comparison; FLOPs and training duration are reported separately where recorded.

Each neural run evaluates six global thresholds at each of 50 epochs: 300 epoch/threshold candidates on the same proposal set. This is a shared selection budget among the author neural methods.

The v27 rule study shares each round's supervised fits across six arms. v29 shares them across seven arms, with 5,692 policy-fit patients and 1,423 permanently separate witness patients. v30 reuses those exact v29 fits for 14 new memory trajectories. Shared fitting is counted once in the execution ledger. Reproducing any arm in isolation still requires its source policy fits.

## 2. Completed and independently audited author models

12/15 registered runs are complete and audited in this snapshot. Each row matches all 50 saved epoch records to the original execution log. Fit seconds exclude proposal/guard prediction, checkpoint writing and audit reruns.

| Panel | Method | Seed | Device | Parameters | Steps | Visit exposures | Fit minutes |
|---|---|---:|---|---:|---:|---:|---:|
| full | ARMR | 42 | mps | 12,141,073 | 29,750 | 921,450 | 51.39 |
| full | ARMR | 137 | mps | 12,141,073 | 29,750 | 921,450 | 53.14 |
| full | ARMR | 2026 | mps | 12,141,073 | 29,750 | 921,450 | 183.58 |
| full | GAMENet | 42 | cpu | 1,295,952 | 921,450 | 921,450 | 69.76 |
| full | GAMENet | 137 | cpu | 1,295,952 | 921,450 | 921,450 | 75.84 |
| full | GAMENet | 2026 | cpu | 1,295,952 | 921,450 | 921,450 | 83.87 |
| molecular | GAMENet | 42 | cpu | 1,282,588 | 921,450 | 921,450 | 65.20 |
| molecular | GAMENet | 137 | cpu | 1,282,588 | 921,450 | 921,450 | 45.97 |
| molecular | GAMENet | 2026 | cpu | 1,282,588 | 921,450 | 921,450 | 44.12 |
| molecular | SafeDrug | 42 | cpu | 1,379,598 | 921,450 | 921,450 | 67.86 |
| molecular | SafeDrug | 137 | cpu | 1,379,598 | 921,450 | 921,450 | 72.12 |
| molecular | SafeDrug | 2026 | cpu | 1,379,598 | 921,450 | 921,450 | 81.21 |

### Corresponding development results

| Panel / method | Audited seeds | Guard patient F1 ± seed SD | Guard patient Jaccard ± seed SD |
|---|---|---:|---:|
| full/ARMR | 42, 137, 2026 | 0.60864 ± 0.00132 | 0.45327 ± 0.00113 |
| full/GAMENet | 42, 137, 2026 | 0.52708 ± 0.00664 | 0.37087 ± 0.00643 |
| molecular/GAMENet | 42, 137, 2026 | 0.50735 ± 0.00350 | 0.35384 ± 0.00324 |
| molecular/SafeDrug | 42, 137, 2026 | 0.53689 ± 0.00244 | 0.38432 ± 0.00223 |

All scores above are on the same 1,231 guard visits / 467 patients, after proposal-only checkpoint selection. An unfinished seed is not filled with zero. This table does not replace the gated final test comparison.

## 3. Actual shared supervised fitting

| Study | Panel | Seed | Fit events / unique labels | Input-row participations | Fit minutes | Final fit patients / visits | Shared arms |
|---|---|---:|---:|---:|---:|---:|---:|
| v27 | full | 42 | 30/30 | 277,995 | 6.68 | 7,115/18,429 | 6 |
| v27 | full | 137 | 30/30 | 277,255 | 6.63 | 7,115/18,429 | 6 |
| v27 | full | 2026 | 30/30 | 275,445 | 6.41 | 7,115/18,429 | 6 |
| v29 | full | 42 | 30/30 | 220,615 | 5.03 | 5,692/14,728 | 7 |
| v29 | full | 137 | 30/30 | 220,720 | 5.08 | 5,692/14,665 | 7 |
| v29 | full | 2026 | 30/30 | 220,475 | 5.07 | 5,692/14,643 | 7 |
| v27 | molecular | 42 | 30/30 | 277,995 | 5.27 | 7,115/18,429 | 6 |
| v27 | molecular | 137 | 30/30 | 277,255 | 5.26 | 7,115/18,429 | 6 |
| v27 | molecular | 2026 | 30/30 | 275,445 | 5.08 | 7,115/18,429 | 6 |
| v29 | molecular | 42 | 30/30 | 220,615 | 4.06 | 5,692/14,728 | 7 |
| v29 | molecular | 137 | 30/30 | 220,720 | 4.03 | 5,692/14,665 | 7 |
| v29 | molecular | 2026 | 30/30 | 220,475 | 4.08 | 5,692/14,643 | 7 |

Each five-round source run has three regularization candidates and three cross-fit models per round. The recorded fit label denotes a full one-vs-rest model collection; constant-target classes can bypass optimization. Input-row participations sum rows provided to these fits, and do not measure internal solver iterations or epoch exposures. Any repeated fit event is retained in the total. Runtime rule search, calibration, generation, prediction and audits are outside these fit timers.

| Reuse study | Panel | Seed | Frozen fit source | Additional policy fits | Shared arms |
|---|---|---:|---|---:|---:|
| v30 | full | 42 | v29/full/42 | 0 | 14 |
| v30 | molecular | 42 | v29/molecular/42 | 0 | 14 |

Zero additional policy fits refers to exact reuse. Memory induction and verification still consume computation and logical model calls.

## 4. Proposal calls for the audited runs

| Study | Panel | Seed | Arm | Logical calls | Known logical response USD | Unpriced calls |
|---|---|---:|---|---:|---:|---:|
| v27 | full | 42 | own_error_rule_agent | 5 | 0.00232 | 0 |
| v27 | full | 42 | shuffled_evidence_rule_agent | 5 | 0.00194 | 0 |
| v27 | full | 137 | own_error_rule_agent | 5 | 0.00218 | 0 |
| v27 | full | 137 | shuffled_evidence_rule_agent | 5 | 0.00207 | 0 |
| v27 | full | 2026 | own_error_rule_agent | 5 | 0.00265 | 0 |
| v27 | full | 2026 | shuffled_evidence_rule_agent | 5 | 0.00272 | 0 |
| v29 | full | 42 | own_error_program_agent | 5 | 0.00983 | 0 |
| v29 | full | 42 | shuffled_evidence_program_agent | 5 | 0.00890 | 0 |
| v29 | full | 137 | own_error_program_agent | 5 | 0.00300 | 0 |
| v29 | full | 137 | shuffled_evidence_program_agent | 5 | 0.00399 | 0 |
| v29 | full | 2026 | own_error_program_agent | 5 | 0.01146 | 0 |
| v29 | full | 2026 | shuffled_evidence_program_agent | 5 | 0.00965 | 0 |
| v27 | molecular | 42 | own_error_rule_agent | 5 | 0.00210 | 0 |
| v27 | molecular | 42 | shuffled_evidence_rule_agent | 5 | 0.00198 | 0 |
| v27 | molecular | 137 | own_error_rule_agent | 5 | 0.00200 | 0 |
| v27 | molecular | 137 | shuffled_evidence_rule_agent | 5 | 0.00155 | 0 |
| v27 | molecular | 2026 | own_error_rule_agent | 5 | 0.00141 | 0 |
| v27 | molecular | 2026 | shuffled_evidence_rule_agent | 5 | 0.00229 | 0 |
| v29 | molecular | 42 | own_error_program_agent | 5 | 0.00846 | 0 |
| v29 | molecular | 42 | shuffled_evidence_program_agent | 5 | 0.00757 | 0 |
| v29 | molecular | 137 | own_error_program_agent | 5 | 0.00924 | 0 |
| v29 | molecular | 137 | shuffled_evidence_program_agent | 5 | 0.00839 | 0 |
| v29 | molecular | 2026 | own_error_program_agent | 5 | 0.01005 | 0 |
| v29 | molecular | 2026 | shuffled_evidence_program_agent | 5 | 0.00908 | 0 |
| v30 | full | 42 | own_C0P0 | 5 | 0.00782 | 0 |
| v30 | full | 42 | own_C0P1 | 5 | 0.00623 | 0 |
| v30 | full | 42 | own_C1P0 | 5 | 0.00623 | 0 |
| v30 | full | 42 | own_C1P1 | 5 | 0.00623 | 0 |
| v30 | full | 42 | shuffled_C0P0 | 5 | 0.00616 | 0 |
| v30 | full | 42 | shuffled_C0P1 | 5 | 0.00589 | 0 |
| v30 | full | 42 | shuffled_C1P0 | 5 | 0.00589 | 0 |
| v30 | full | 42 | shuffled_C1P1 | 5 | 0.00589 | 0 |
| v30 | molecular | 42 | own_C0P0 | 5 | 0.00934 | 0 |
| v30 | molecular | 42 | own_C0P1 | 5 | 0.00934 | 0 |
| v30 | molecular | 42 | own_C1P0 | 5 | 0.00877 | 0 |
| v30 | molecular | 42 | own_C1P1 | 5 | 0.00881 | 0 |
| v30 | molecular | 42 | shuffled_C0P0 | 5 | 0.00831 | 0 |
| v30 | molecular | 42 | shuffled_C0P1 | 5 | 0.00836 | 0 |
| v30 | molecular | 42 | shuffled_C1P0 | 5 | 0.00827 | 0 |
| v30 | molecular | 42 | shuffled_C1P1 | 5 | 0.00827 | 0 |

These are method-level logical requests and the prices associated with their saved successful responses. Identical responses can be reused across conditions; this table must not be summed as fresh account spend. Failed attempts, account-wide usage and time waiting for credit are not covered. The physical request ledger remains the source for billed experiment requests.

## 5. Conventional-method timing scope

| Panel | Method | Recorded block seconds | Configurations × thresholds | Shared feature seconds |
|---|---|---:|---:|---:|
| full | prevalence | not measured | 1 × 6 = 6 | 3.062 |
| full | last_visit | not measured | 1 × 6 = 6 | 3.062 |
| full | cosine_knn | 2.574 | 3 × 6 = 18 | 3.062 |
| full | structured_logistic | 92.086 | 3 × 6 = 18 | 3.062 |
| molecular | prevalence | not measured | 1 × 6 = 6 | 3.283 |
| molecular | last_visit | not measured | 1 × 6 = 6 | 3.283 |
| molecular | cosine_knn | 3.893 | 3 × 6 = 18 | 3.283 |
| molecular | structured_logistic | 87.223 | 3 × 6 = 18 | 3.283 |

Cosine retrieval and logistic timing blocks include proposal search and guard prediction, so they have a broader scope than the neural fit timers. Historical prevalence/last-visit values of zero are unmeasured sentinels. Feature construction is shared once per panel. No FLOP, energy, isolated latency or peak-memory measurement is inferred from these records.

## 6. Interpretation and coverage

The runs use CPU and Apple MPS concurrently. Summed method timers are resource-activity measurements under contention, not one continuous elapsed wall clock or an isolated speed leaderboard. This analysis creates no fits, model requests or test predictions. It reconstructs saved receipts and binds the source hashes; it is not an independent compute profiler. Exact budgets are matched within each registered intervention, while heterogeneous method comparisons disclose their distinct search and fitting costs.

[Machine-readable receipts and source hashes](compute_accounting.json) · [Common method study](../upgrade_v27/RESULTS.en.md) · [Common test extension](../upgrade_v30/COMMON_TEST.en.md)
