# v0.15 — Explicit candidate inclusion and exclusion

**Status: design/data prepared before v0.9 test scoring; training pending the current local GPU job.**

The v0.9 guard set reveals over-selection: the target averages 3.635 reachable drugs, whereas adapted outputs often include 14.57–18.71 of 20 candidates. This intervention changes the supervised response from positive IDs to exactly 20 binary inclusion decisions. It explicitly trains refusals for each negative candidate.

The model, three feedback blocks, 400 sampled cases/100 steps per round, uniform versus error-prioritized feedback, guard selection and 500 test memberships match v0.9. Both arms restart from the original backbone. Equal steps and output caps do not mean identical training target-token counts. The representation change must beat both the ID-format study and direct-tool controls before it supports a benefit claim.

All data/weights remain local. `protocol.json` records that v0.9 test results did not exist when this design was frozen. Three parser contracts verify exact length, explicit negatives and cache identity. No result is filled before generation-based evaluation.
