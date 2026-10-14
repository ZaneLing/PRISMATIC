---
description: URL-encode spaces in FHIR Patient name search params before concluding
  'not found'.
name: fhir_patient_name_search_url_encoding
provenance:
  action: ADD
  epoch: 0
  fixes: 1
  probe_score: 1
  regressions: 0
  triggering_sample_ids:
  - task1_20
  - task10_24
  - task9_9
  - task5_7
  - task4_26
  - task10_15
  - task9_20
  - task1_10
  - task1_11
  - task10_16
  update_cycle: 0
tags:
- MRN
- patient
- name
- DOB
- Patient not found
- birthdate
version: 1
---

## When to Use This Skill
Use when the task asks you to find a patient by full name (e.g. "patient with name Christopher Cruz") and optionally a DOB, and to return the MRN or "Patient not found". The trigger is the presence of a multi-word patient name in the instruction.

## Procedure
FHIR search parameters with spaces must be percent-encoded in the URL. A raw space in `name=Christopher Cruz` is not a valid query value and the server may silently return an empty Bundle even when the patient exists.

1. Split the requested name into given and family components.
2. Build the Patient search with each component URL-encoded (space -> `%20`). Prefer encoding both the given and family parts separately: `name=Christopher%20Cruz` or, more robustly, `given=Christopher&family=Cruz`.
3. Always include the DOB as `birthdate=YYYY-MM-DD` when the task supplies one.
4. Only after receiving `"total": 0` from a properly encoded query may you conclude the patient does not exist.
5. If the Bundle has `total >= 1`, read `entry[0].resource.identifier` (or `id`) to extract the MRN.

## Example Trajectory

### Wrong
Task: "What's the MRN of the patient with name Christopher Cruz and DOB of 1940-08-28? If the patient does not exist, the answer should be 'Patient not found'"

Think: I'll search Patient by name and birthdate.
Act: `GET http://127.0.0.1:18080/fhir/Patient?name=Christopher Cruz&birthdate=1940-08-28`
Obs: `{"resourceType": "Bundle", "type": "searchset", "total": 0, ...}`
Think: Zero results, so the patient must not exist.
Act: `FINISH(["Patient not found"])`  <-- WRONG: raw space broke the query.

### Correct
Task: same as above.

Think: The name contains a space, so I must URL-encode it before querying.
Act: `GET http://127.0.0.1:18080/fhir/Patient?name=Christopher%20Cruz&birthdate=1940-08-28`
Obs: `{"resourceType": "Bundle", "type": "searchset", "total": 1, "entry": [{"resource": {"resourceType": "Patient", "id": "...", "identifier": [{"value": "<MRN>"}]}}]}`
Think: One match found; extract the MRN from the identifier.
Act: `FINISH(["<MRN>"])`

## Failure Mode This Prevents
Prematurely returning "Patient not found" because a raw space in the `name` parameter caused the FHIR server to drop the search and return an empty Bundle.
