# v0.15 — Explicit candidate inclusion and exclusion

**Status: complete, with independently recounted test scores and a disclosed training-feedback receipt gap.**

The v0.9 guard set reveals over-selection: the target averages 3.635 reachable drugs, whereas adapted outputs often include 14.57–18.71 of 20 candidates. This intervention changes the supervised response from positive IDs to exactly 20 binary inclusion decisions. It explicitly trains refusals for each negative candidate.

The model, three feedback blocks, 400 sampled cases/100 steps per round, uniform versus error-prioritized feedback, guard selection and 500 test memberships match v0.9. Both arms restart from the original backbone. Equal steps and output caps do not mean identical training target-token counts. The representation change must beat both the ID-format study and direct-tool controls before it supports a benefit claim.

All data/weights remain local. `protocol.json` records that v0.9 test results did not exist when this design was frozen. Three parser contracts verify exact length, explicit negatives and cache identity. Completed results are in [English](RESULTS.en.md) and [中文](RESULTS.zh.md).

## Execution update — 14 October 2026

The preceding v0.9 test completed and passed independent recount. The queued binary-intervention process has now started. `results/*_rounds.json` records progress; no unfinished test score is reported.

## Completed — 15 October 2026

Priority binary updates score 0.29192/0.19329 drug/order F1 versus uniform 0.24094/0.15072 and direct top-8 tools 0.31169/0.20739. Both arms select round 2; the final priority candidate collapses to all-zero masks and is rejected. All scores are independently recounted. The learning audit verifies weights, sampling, labels, actual adapters and training steps, but 10/3,600 individual feedback generations cannot be recovered exactly from duplicate-input caches. This limitation is retained in the report; scores are not altered.
