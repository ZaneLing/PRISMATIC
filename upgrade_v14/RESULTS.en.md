# v0.14 — Executed FHIR state integration

## Environment

The official MedAgentBench image is pinned to digest `sha256:3fb83d7ed71c5476f9eb6212bd440a909ef7505922bbc757dc488a8fc0701966`. We checksum-verified and extracted its unmodified Java application, configuration and public database. HAPI FHIR 7.6.0 serves FHIR R4 (4.0.1), bound to loopback only. Native Amazon Corretto 21.0.12.12.1 replaces the original Linux/amd64 runtime on this macOS ARM machine; equivalence beyond the performed integration probes is not assumed.

## Actual executed checks

| Check | Result |
|---|---|
| Create a synthetic probe Patient, then read it back | Pass |
| Create MedicationRequest linked to that Patient, then read it back | Pass |
| Update the request and verify both status and version change | Pass |
| Reject an invalid transaction with no partially created Patient | Pass |
| Delete only probe resources and recover original resource counts | Pass |

| Resource | Before | After cleanup |
|---|---:|---:|
| Patient | 695 | 695 |
| MedicationRequest | 21,991 | 21,991 |
| Observation | 563,426 | 563,426 |
| ServiceRequest | 0 | 0 |

No model calls or restricted MIMIC records are involved. These are genuine state operations, not simulated success messages. Probe resources have no clinical administration intent. Detailed aggregate evidence is in `results/fhir_state_probe.json`.

## Benchmark semantics and next evaluation

The [official implementation](https://github.com/stanfordmlgroup/MedAgentBench/blob/99260117137b09f04837a8c18d18a1107efa55ae/src/server/tasks/medagentbench/__init__.py) parses POST payloads and records acceptance in the trajectory; it does not actually issue the HTTP POST. Its reference grader inspects action history. This is the released benchmark convention. We will report this trace criterion and real persisted-state validation separately; the five checks above are not a substitute for a model success rate.

The pinned GRASP benchmark adapter provides 96 development / 80 validation / 64 in-distribution test / 60 held-out-task-type test cases. Case IDs do not overlap across these splits. The original configuration allows eight action rounds. Dataset and grader fingerprints are recorded in `results/task_manifest.json`. A model-based development pilot is now complete; full benchmark evaluation remains pending.

## Completed model pilot: 16 development tasks

Both methods used DeepSeek-V4.1-Flash, at most eight action calls and 512 output tokens per call. Two cases per development task type were selected before running. Both performed real writes, with separate original trace and persisted-state scoring.

| Method | Trace success | State-checked success | Invalid action | Model calls | Created/readback-verified resources |
|---|---:|---:|---:|---:|---:|
| Direct tools | 10/16 | 10/16 | 1 | 36 | 6/6 |
| Fixed workflow + preflight/readback | 8/16 | 8/16 | 3 | 38 | 5/5 |

The fixed harness did not improve this pilot. Errors include empty patient searches, incorrect handling of observation dates and answers with extra prose outside the required action grammar. This does not test an evolved policy. The original reference grader was rerun independently; resource counts and cleanup journals were checked after the pilot. These are development results, not the 64-case ID or 60-case held-out-task-type test.
