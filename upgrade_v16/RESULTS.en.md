# v0.16 — Repairing a reasoning-token budget failure

## Completed development experiment

The model is Gemini-3.8-Flash. All rows use the same 190 RxSafeBench proposal questions and unchanged answer prompt. Reasoning tokens count against the completion budget. Genuine truncated responses count wrong; HTTP failures are never scored.

| Setting | CoT correct | CoT invalid | Evidence correct | Evidence invalid |
|---|---:|---:|---:|---:|
| Default reasoning, 512 tokens (v0.11) | 72/190 | 69 | 62/190 | 85 |
| Low reasoning, 1,024 tokens | 100/190 | 16 | 94/190 | 13 |
| Low reasoning, 2,048 tokens | **105/190** | **2** | **100/190** | **1** |

The repair increases CoT accuracy from 37.89% to 52.63%; safety evidence rises from 32.63% to 49.47%. Evidence still trails CoT on this development set. This is not test-set improvement or an RSI result. The low-reasoning choice and larger cap are changed together, so their effects are not independently identified.

A 30-question pilot compared low reasoning at caps 512 and 1,024 (19/30 with 5 invalid versus 20/30 with 3 invalid), selecting by invalid count, then accuracy, then smaller cap. All 30 pilot questions are contraindication cases: selection is not stratified. Original results remain preserved.

## Completed follow-up and frozen setting

The separately declared 2,048-token follow-up is complete: CoT 55.26% and evidence 52.63%. Two responses per method have a length finish reason; one truncated evidence response still contains a valid parsed answer. The 2,048-token/low-reasoning setting is frozen using development results, before any Gemini test scoring. Original settings remain available; none of these are test-set results.

Source: [OpenRouter reasoning-token documentation](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens).
