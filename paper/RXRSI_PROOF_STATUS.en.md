# RxRSIAgent evidence status

## Compatible runtime, regated learning and current decision

Complete JSON with a mixture of known and unknown IDs previously lost the entire output. The compatible runtime retains only verified IDs, logs unknown IDs, accepts complete fenced JSON, and never completes a truncated structure. It restores nonempty outputs for8 Qwen audit patients and13 Llama patients. **All development gates were rerun using this same decoder before audit metrics**, rather than attributing an output-parser change to learned improvement. No new LLM inference was needed.

| Method | Drug F1 % | Native4 F1 % | Missed/patient | Extra/patient | Joint errors/patient |
|---|---:|---:|---:|---:|---:|
| Fixed Qwen, compatible runtime | 7.38 | 1.64 | 1.152 | 7.184 | 7.035 |
| RxRSIAgent, compatible runtime + gated memory | 7.20 | 1.60 | 1.176 | 6.773 | 6.723 |
| Reflection-label shuffle, true development gates | 7.32 | 1.49 | 1.172 | 6.746 | 6.707 |
| Static all repairs, compatible runtime | 7.48 | 1.12 | 1.227 | 5.148 | 5.512 |
| Fixed Llama, compatible runtime (128) | 3.17 | 0.37 | 1.156 | 9.352 | 8.305 |
| Llama + transferred memory, compatible runtime (128) | 3.24 | 0.38 | 1.156 | 9.102 | 8.172 |

The compatible learner also loses6 correct drug targets; the omission-rate difference95% interval is [0.0078, 0.0430] per patient. 6 patients worsen on at least one primary component. A lower summed error count must not conceal these trade-offs. The reflection-label-shuffle control permutes **only reflection labels**; proposal and guard references remain correct, so it does not eliminate development supervision. After decoder repair it also retains3 rules. This weakens attribution to patient-specific reflection learning.

**The strong hypothesis is not established.** We observed automatic conditional rule selection, but no accepted explicit exception, no recovery of a previously missed correct drug, and no jointly improving three-endpoint trajectory. The current catalogue reaches only54.21% of target drugs and11.30% of complete target order tuples. No bounded selector can recover a target absent from its action space. The next scientific target is order-level applicability and joint-field construction with independently verified evidence, followed by a new patient lock; this audit is now exposed and must not be reused as unseen confirmation.

The learned memory is **not promoted**. `serve.py` uses the compatible initial actor by default; `--experimental-memory` reproduces the failed memory for research. This rollback does not retrospectively change the frozen result table or count as a positive evolution result.
