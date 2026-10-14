# v0.31: why the first new adapter returned empty prescriptions

## Directly observed failure

The first seed42 permuted-uniform update completes 100 optimizer steps. All 100 proposal admissions under both ranked and permuted presentation produce the same valid all-zero mask: **200/200 empty prescriptions, drug/order micro-F1=0**. Removing the empty reasoning wrapper does not change any decision. This is a semantic prediction failure, not failed JSON parsing. The promotion rule rejects this adapter and retains the base model.

The actual 400 training sequences contain **1604/8000 positive decisions (20.05%)**; 122/400 have no reachable target drug. The 69-token completion includes only 20 binary decisions; the remaining tokens encode syntax and the template. Constant decisions can therefore coexist with a low overall language-model loss. These observations motivate, but alone do not prove, an imbalance explanation.

## Frozen-checkpoint probability diagnosis

Before further inference, the diagnostic fixed the first 32 training examples and first 32 proposal cases in both views, comparing the frozen base and failed adapter. At each of 20 decision positions it measures P(1 | token is 0 or 1). **Zero-prefix** scoring supplies zeros at earlier decision positions without looking at labels. **GT-prefix** scoring supplies earlier ground-truth decisions and is an oracle diagnostic, not deployable accuracy. No threshold is selected, no model is refit, and no guard/test prediction is generated.

| State | Cases/view | Prefix | Conditional BCE ↓ | AUROC ↑ | Mean P(1), positive / negative | P(1) ≥ 0.5 (%) |
|---|---|---|---:|---:|---:|---:|
| frozen_base | train_permuted | GT | 0.8595 | 0.7259 | 0.2732 / 0.1305 | 13.12 |
| frozen_base | train_permuted | zero | 1.4946 | 0.5749 | 0.1319 / 0.0838 | 8.59 |
| frozen_base | proposal_ranked | GT | 1.0704 | 0.7154 | 0.4177 / 0.1841 | 22.97 |
| frozen_base | proposal_ranked | zero | 1.8241 | 0.6724 | 0.1832 / 0.0833 | 10.16 |
| frozen_base | proposal_permuted | GT | 1.1614 | 0.6844 | 0.3583 / 0.1636 | 19.69 |
| frozen_base | proposal_permuted | zero | 2.3327 | 0.5555 | 0.1614 / 0.0791 | 9.84 |
| permuted_uniform_seed42_round1 | train_permuted | GT | 0.2883 | 0.8284 | 0.2842 / 0.1300 | 0.62 |
| permuted_uniform_seed42_round1 | train_permuted | zero | 0.4258 | 0.5854 | 0.0828 / 0.0566 | 0.00 |
| permuted_uniform_seed42_round1 | proposal_ranked | GT | 0.4470 | 0.7424 | 0.3229 / 0.1987 | 3.44 |
| permuted_uniform_seed42_round1 | proposal_ranked | zero | 0.6380 | 0.6855 | 0.1096 / 0.0566 | 0.00 |
| permuted_uniform_seed42_round1 | proposal_permuted | GT | 0.4492 | 0.7385 | 0.2973 / 0.1810 | 2.34 |
| permuted_uniform_seed42_round1 | proposal_permuted | zero | 0.7465 | 0.5503 | 0.0832 / 0.0580 | 0.00 |

![Frozen-checkpoint probability diagnosis](collapse_probability.png)

**Observed pattern:** the updated model's permuted-view AUROC is 0.7385 with GT prefixes and 0.5503 with zero prefixes. Under zero prefixes, mean P(1) is 0.0832 for positive slots and 0.0580 for negative slots; none reaches0.5. Ranked-view zero-prefix AUROC is 0.6855, so display-order sensitivity also remains. This supports testing prefix exposure and calibration separately; it does not identify a unique cause.

## Interpretation and next intervention

Compare conditional discrimination and probability calibration separately from greedy generation. Low probability for every positive decision can yield empty generation even when rankings retain signal. Near-chance AUROC would instead indicate little useful conditional discrimination in this diagnostic. Neither outcome proves human-like prescribing or a distinct RSI benefit.

The next repair should explicitly supervise drug decisions, separate syntax tokens from decision loss, and test probability calibration against unmodified greedy decoding. It must keep no-feedback, uniform-update and shuffled-feedback controls at the same update budget. Register any such intervention before fitting, retain the failed checkpoint, select settings on development data, and freeze them before evaluating generalization. This diagnostic does not retrospectively replace the original v31 outputs.

## Evidence and limits

The independent recount reconstructs source targets and recomputes all saved-probability metrics with a separate implementation. Neural forward passes were not independently rerun. The sample is small, deterministic and selected by file order after an observed failure; this is a mechanism diagnostic, not a new test result.

[Registered diagnostic](collapse_diagnostic_protocol.json) · [Aggregate results](results/collapse_diagnostic.json) · [Independent recount](results/collapse_diagnostic_audit.json)

[Registered controlled decision-supervision repair](../upgrade_v32/README.en.md)
