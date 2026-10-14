# RxRSIAgent v0.8 — language-artifact evolution

**Status: running.** Completed rows and version journals are saved incrementally under `results/`; the presence of a partial file does not imply completion.

## Question

Does feedback-driven editing of persistent skills, memory and evidence-tool configuration improve a fixed LLM beyond direct prompting, CoT, Self-Refine, case retrieval and independently implemented Reflexion/GRASP/EvoTool task adaptations?

The official methods are inspiration for named mechanism adaptations. This implementation does not reproduce their original task environments, prompts, full algorithms or published scores.

## Frozen protocol

- Backbone: `deepseek/deepseek-v4.1-flash`, temperature 0, OpenRouter with zero-retention routing.
- Verified public fictional RxSafeBench scenarios; 625 train / 190 proposal / 197 guard / 988 test after scenario-group splitting. No restricted MIMIC text is sent to an API.
- Four feedback rounds; four candidate-evaluation slots for each evolving method. Proposal-token usage is retained because it can differ.
- Select on proposal validation; accept only when guard fixes exceed regressions. Test labels are excluded from proposals and acceptance.
- State: skills (up to six), training-case IDs, evidence-focus terms, three prompt modules. The evidence tool emits exact dialogue excerpts; its executable code and the backbone weights stay fixed.
- Final test, fixed-test checkpoint curves, object ablations, and all 300 RxQA OpenFDA questions for transfer. This RxSafeBench task is a derived option-selection task, distinct from the original free-generation score.

## Run

```bash
python prepare_public.py
python run_evolution.py --seed 42
python run_evolution.py --seed 137
python run_evolution.py --seed 2026
```

Set `OPENROUTER_API_KEY` locally. Requests are resumable by a content hash. Private working caches contain only public benchmark requests/responses. Reported per-method inference costs represent logical request usage, including reused cached answers; the usage ledger records actual charged calls separately. A default $15 cumulative ledger cap is checked before uncached requests and retries; already in-flight calls may finish above the cap. A declared subsequent funded study can set `RXRSI_PUBLIC_COST_CAP_USD`; this engineering cap does not change previously recorded method costs.

Full before/after artifacts, candidate scores, guard fixes/regressions and rejected proposals are retained. A changed artifact alone does not prove improvement. Repeated guard use is development selection.
