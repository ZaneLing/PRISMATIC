# v0.19 — Reliable order execution and real-tool skill learning

## Executed engineering evidence

An actual loopback FHIR probe submitted the same synthetic medication order in two structural forms.

| Payload | HTTP create | Readback | Dosage fields preserved |
|---|---:|---:|---|
| Literal benchmark route string | 201 | 200 | No |
| Route converted to CodeableConcept text | 201 | 200 | Yes |

FHIR R4 defines the route as CodeableConcept. The compiler preserves the original route text without inventing terminology codes. Duration-like units found in a legacy rate field are preserved and flagged; this does not validate their clinical meaning. [FHIR R4 dosage definition](https://hl7.org/fhir/R4/dosage-definitions.html#Dosage.route).

A second executed probe intentionally triggers field loss, detects it, deletes only the newly created resource, and returns repair feedback within the original action budget. All resource counts return to their initial values. These are synthetic engineering probes with zero language-model calls, not agent success scores.

## Full task experiment queued

The declared comparison uses 96 development, 80 validation, 64 ID test and 60 held-out-task-type test tasks. The fixed compiled harness adds typed serialization, field readback and format-error feedback within eight calls. The evolving arm uses the unchanged, credited GRASP core to edit persistent skills; compiler code and backbone weights stay fixed. A literal direct-tool control is included. Four 24-case feedback batches, four proposal slots, 12-case balanced training probes, actor cap 512 and proposer cap 3,072 are recorded before testing.

Episodes execute serially to avoid shared-state interference; exact previously executed code/case/skill episodes can replay from cache. Task GT fields never enter actor prompts. Patient IDs in training feedback are redacted. Released task splits overlap in patients and are not patient-disjoint.

The full agent experiment is queued after the Gemini and intermediate-skill evaluations. No unfinished agent result is claimed. See `protocol.json` and the actual probe records in `results/`.

## Task-schema repair before learning

The first launch stopped before any episode because only task1 has a literal `sol`. Other task types use reference functions against FHIR state. The adapter now preserves absent literal answers as null and uses the unchanged reference grader; it does not fabricate answers. All300 released task records load, all ten grader functions exist, and five execution/label-isolation contracts pass. The queue now requires the Gemini comparison to be complete, not merely an exited process. See `results/task_schema_audit.json`.
