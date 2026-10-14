# v0.26 — Development diagnostic of candidate-position dependence

## Design

After v0.15 exposes prefix selection and collapsed checkpoints, freeze a diagnostic on its existing200-case/197-patient guard. No training or test case is evaluated. Keep the base model and both previously selected round2 adapters fixed. Compare fresh original prompts with ranked, deterministically permuted and reversed candidates. The latter three conditions explicitly retain each candidate's original retrieval rank, all drug/order fields and the same patient context; masks are interpreted in displayed order. Thus the reordering contrast does not silently remove the tool's rank information. The extra rank-prompt effect is measured separately against original prompts.

This is a post-test-motivated development sensitivity study, not untouched confirmation. It performs no checkpoint, prompt or model promotion. All generations stay local; duplicate inputs generate once and each case has an immutable output receipt.

## Fixed-method results

| Frozen method | Display condition | Drug F1 | Order F1 | Empty (%) | Invalid | Nontrivial display-prefix (%) |
|---|---|---:|---:|---:|---:|---:|
| base | original | 0.19211 | 0.12091 | 3.0 | 0 | 1.0 |
| base | ranked_explicit | 0.21480 | 0.13843 | 3.0 | 0 | 4.1 |
| base | permuted_rank_explicit | 0.19417 | 0.12603 | 1.0 | 0 | 1.5 |
| base | reversed_rank_explicit | 0.10402 | 0.06915 | 5.5 | 0 | 0.5 |
| uniform_sft_round2 | original | 0.27561 | 0.19212 | 10.5 | 0 | 99.4 |
| uniform_sft_round2 | ranked_explicit | 0.22125 | 0.14351 | 10.0 | 0 | 99.4 |
| uniform_sft_round2 | permuted_rank_explicit | 0.10492 | 0.07377 | 9.0 | 0 | 100.0 |
| uniform_sft_round2 | reversed_rank_explicit | 0.03301 | 0.02120 | 28.5 | 0 | 100.0 |
| error_prioritized_sft_round2 | original | 0.32043 | 0.22181 | 3.5 | 0 | 99.4 |
| error_prioritized_sft_round2 | ranked_explicit | 0.27471 | 0.19207 | 4.5 | 0 | 100.0 |
| error_prioritized_sft_round2 | permuted_rank_explicit | 0.17441 | 0.12645 | 1.0 | 0 | 100.0 |
| error_prioritized_sft_round2 | reversed_rank_explicit | 0.21980 | 0.15146 | 0.0 | 0 | 100.0 |

Direct original-rank controls (drug/order F1): direct_original_rank_top8 0.32027/0.22434, direct_original_rank_top20 0.27382/0.19522.

## Reordering contrasts / 重排比较

| Frozen method | Contrast | Drug/order Δ | Medication-set agreement (%) | Mean Jaccard |
|---|---|---:|---:|---:|
| base | ranked_explicit__minus__original | +0.02269/+0.01751 | 18.5 | 0.537 |
| base | permuted_rank_explicit__minus__ranked_explicit | -0.02062/-0.01240 | 0.0 | 0.198 |
| base | reversed_rank_explicit__minus__ranked_explicit | -0.11078/-0.06927 | 0.5 | 0.090 |
| uniform_sft_round2 | ranked_explicit__minus__original | -0.05436/-0.04861 | 42.5 | 0.671 |
| uniform_sft_round2 | permuted_rank_explicit__minus__ranked_explicit | -0.11633/-0.06974 | 1.0 | 0.091 |
| uniform_sft_round2 | reversed_rank_explicit__minus__ranked_explicit | -0.18824/-0.12231 | 3.0 | 0.030 |
| error_prioritized_sft_round2 | ranked_explicit__minus__original | -0.04573/-0.02974 | 21.5 | 0.522 |
| error_prioritized_sft_round2 | permuted_rank_explicit__minus__ranked_explicit | -0.10030/-0.06562 | 11.0 | 0.238 |
| error_prioritized_sft_round2 | reversed_rank_explicit__minus__ranked_explicit | -0.05491/-0.04061 | 26.5 | 0.355 |

## What this says about evolution

With original ranks explicitly retained, permuting display order lowers priority-model drug F1 from0.27471 to0.17441 (difference−0.10030; patient-cluster interval[−0.13508,−0.06646]). The uniform adapter drops0.22125→0.10492. Both adapters select a display prefix in100% of nontrivial valid permuted masks, whereas the frozen base does so in1.5%. The original-prompt priority score0.32043 is almost equal to the fixed top8 control0.32027; this is not evidence of superior clinical selection. All2,400 case/state/condition outputs parse successfully, so malformed JSON is not the explanation.

The next intervention should test drug-specific decisions under randomized display positions, with explicit preserved rank and equal token/step budgets. It must compare ordinary, own-error and shuffled-feedback updates plus a fixed rank control, then report per-round raw and accepted states. This diagnostic supports that repair direction; it neither identifies the complete cause nor licenses choosing a winner on this already-used guard.

All predictions, candidate-set/GT equality and case-bound receipt hashes pass independent checks. Complete paired patient-cluster intervals are in `results/summary.json`. Order sensitivity does not by itself establish clinical reasoning or explain training collapse causally. No improvement or best-method claim follows from this diagnostic.
