# v0.11 — Drug-label evidence and feedback-selected routing

## Data, tools and budget

The same public RxSafeBench scenario-group split has 625/190/197/988 train/proposal/guard/test questions. DeepSeek-V4.1-Flash receives at most 512 output tokens per call. Each review receives the same initial CoT answer and retrieved label excerpts for all options. The fixed balanced review was selected on proposal data. This is a method comparison within one backbone and one derived task.

The openFDA label snapshot matched 623 of 699 public candidate names; test-option coverage is 92.98%. Retrieval returns up to two exact contiguous excerpts per option with label IDs and source fields. Labels are company-submitted records and are not uniformly FDA-verified. Missing evidence is explicitly retained. No restricted patient data is sent to a service.

## Completed test results

| Method | Correct / 988 | Accuracy (%) | Model calls | Fixes / regressions vs CoT |
|---|---:|---:|---:|---:|
| cot | 467 | 47.27 | 1 | 0 / 0 |
| balanced | 484 | 48.99 | 2 | 119 / 102 |
| safety | 487 | 49.29 | 2 | 108 / 88 |
| RxRSI evidence router, seed 42 | 467 | 47.27 | 1 | 0 / 0 |
| indication review | Incomplete | — | 2 intended | — |

The router learns coefficients for evidence-action benefit over CoT from 156/312/468/625 observed training cases. A 190-case proposal set selects from regularization/threshold candidates; a separate 197-case guard checks net repairs. All four updates were rejected, so the active router remains CoT. The fixed evidence tool improves the point estimate, but this does not demonstrate an evolving-agent advantage. Paired scenario-cluster intervals are released in `results/summary.json` and are descriptive, without multiple-comparison correction.

## Incomplete evaluations and repair

The indication review received 835/988 answers; 153 requests failed with HTTP 402 after account credits were exhausted. Its accuracy is unreported. The Gemini development pilot received zero of its 380 planned answers, so it has no model score. Earlier incomplete numeric summaries are retained only in explicitly invalidated archives. The client now stops on authentication/credit errors and the scorer rejects any result with transport errors. A genuinely received malformed answer still counts wrong.

## Next controlled increment

[v0.12](../upgrade_v12/RESULTS.en.md) compares two gates across three seeds using only complete cached action traces. It makes zero new requests and distinguishes routing-parameter updates from backbone or executable-tool updates.
