---
description: When a lab Observation search by code returns 0 results, retry with the
  task-provided code as code.text before trying ad-hoc synonyms.
name: lab_code_text_fallback_probe
provenance:
  action: ADD
  epoch: 0
  fixes: 3
  probe_score: 2
  regressions: 0
  triggering_sample_ids:
  - task9_5
  - task10_12
  - task5_17
  - task10_13
  - task9_22
  - task9_3
  update_cycle: 1
tags:
- HbA1C
- A1C
- last
- value
- magnesium
- MG
- lab
- Observation
- code
- recorded
version: 1
---

## When to Use This Skill

Activate when the task instruction provides a lab code string for an Observation search (e.g. "The code for HbA1C is \"A1C\"", "The code for magnesium is \"MG\"") AND your first `GET {api_base}/Observation?code=<CODE>&patient=<ID>` returns `"total": 0`.

Do not activate if the first search already returned entries.

## Core Rule

When a code-based Observation search returns zero results, do NOT immediately start guessing alternate spellings, capitalization variants, or LOINC codes. Instead, retry the exact same query but move the code into `code.text` using the FHIR CodeableConcept text token, because the harness compiles route strings to `CodeableConcept.text` on writes and stored resources may only carry `code.text` (not a coded `code.coding` entry).

Try, in order:
1. `GET {api_base}/Observation?code=<CODE>&patient=<ID>` (already done)
2. `GET {api_base}/Observation?patient=<ID>&code:text=<CODE>` — match on CodeableConcept.text
3. Only if both return 0, try one alternate spelling/case variant (e.g. `A1c`, `HbA1c`).
4. Do NOT enumerate more than 2–3 variants; if all return 0, conclude no measurement is available and finish with the task's "not available" sentinel (e.g. `[-1]`).

## Why This Works

MedAgentBench stores many Observation resources with only `code.text` populated (no `coding` array). A `code=<X>` search matches `code.coding.code` or the canonical token, so it can miss resources that only have `code.text`. The `code:text=` modifier matches the human-readable text field directly.

## Example Trajectory

WRONG (loops through spellings, burns rounds, hits round_limit):
- Think: I need the last HbA1C. Task says code is "A1C".
- Act: `GET /fhir/Observation?code=A1C&patient=[PATIENT_ID]`
- Obs: `{"total": 0}`
- Think: Maybe it's LOINC. Try 4548-4.
- Act: `GET /fhir/Observation?code=4548-4&patient=[PATIENT_ID]`
- Obs: `{"total": 0}`
- Think: Try spelled out.
- Act: `GET /fhir/Observation?code=hemoglobin%20A1C&patient=[PATIENT_ID]`
- Obs: `{"total": 0}`
- Think: Try HbA1c, HbA1C, A1c, hemoglobin A1c … (continues until round_limit, never returns an answer)

CORRECT (falls back to code.text, finds the record):
- Think: I need the last HbA1C. Task says code is "A1C".
- Act: `GET /fhir/Observation?code=A1C&patient=[PATIENT_ID]`
- Obs: `{"total": 0}`
- Think: Zero results on code search. Per skill, retry matching code.text before guessing synonyms.
- Act: `GET /fhir/Observation?patient=[PATIENT_ID]&code:text=A1C`
- Obs: `{"total": 1, "entry": [{"resource": {"code": {"text": "A1C"}, "valueQuantity": {"value": 5.4}, "effectiveDateTime": "2023-11-02T06:53:00+00:00"}}]}`
- Think: Found it. Value 5.4 on 2023-11-02, within 1 year of now, so no new order. Finish.
- Act: `FINISH([5.4, "2023-11-02T06:53:00+00:00"])`
