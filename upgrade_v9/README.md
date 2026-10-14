# RxRSIAgent v0.9 — local parameter evolution

**Status: running.** This experiment actually updates Qwen3-4B adapter weights locally; no restricted record is uploaded.

## Matched comparison

| Item | Uniform SFT | Error-prioritized SFT |
|---|---|---|
| Backbone | Qwen3-4B-Instruct-2507, 4-bit MLX | Same |
| Candidate/order tools | Frozen initial-8k policy, 20 candidates | Same |
| Feedback | Three new blocks of 600 admissions | Same |
| Optimization | 400 sampled examples, 100 steps per round | Same |
| Sampling | Uniform over observed cases | Weight 1 + 3 × reachable-action error |
| Selection | Best checkpoint on 200-case guard | Same |
| Final evaluation | 500 new admissions, 494 patients | Same |

The 100-case loss-validation set and guard are patient-disjoint from training and test. New test patients exclude v0.6/v0.7 tests. Feedback blocks exclude the initial candidate-policy training patients and are patient-disjoint across rounds. Complete training sequences are checked before optimization; target completions are not truncated.

Only the last eight model layers receive LoRA adapters. Optimizers reset each round in both arms. Both arms continue training their latest checkpoint, while inference selection retains the best guard checkpoint. Error weights for an older case retain its original pre-update error. The LLM selects listed order IDs; the fixed compiler expands the fields. This does not learn novel doses outside the catalogue.

```bash
python prepare_local.py  # research Python environment
python run_parameter_evolution.py  # local MLX environment
```

`results/*_rounds.json` stores actual adapter hashes, sample membership hashes, guard metrics and training time. `results/parameter_results.json` will contain generated test predictions' aggregate scores, not training-loss proxies. All checkpoints and patient-level predictions stay in the restricted directory.

## Development-stage parser repair

The first adapted model emitted a leading empty `<think></think>` envelope before otherwise valid JSON. The original strict parser marked all 200 guard responses invalid. `selection_parser.py` now removes only this empty envelope for every arm/checkpoint and preserves both strict and normalized validity. Raw model outputs and trained weights are unchanged. Nonempty reasoning and malformed JSON remain invalid. A second fix rebinds cached identical-prompt outputs to the current case and catalogue; the alignment assertion exposed the issue before test scoring. Four regression tests pass. The original strict-parser journal remains archived.

The separate `run_tool_control.py --freeze-only` chooses a frozen-candidate top-k control on guard data. Its test evaluation waits until both LLM arms have frozen their selections. This measures whether LLM training improves over using the same tools directly.
