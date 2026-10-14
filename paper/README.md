# PRISMATIC / RxRSIAgent manuscript and execution index

**Target: ACL 2027. v0.9 local parameter tests and v0.17 grounded skill/round evaluations are complete and independently recounted. v0.15 binary supervision and v0.18 Gemini artifact transfer are running; the v0.21 temporal method suite and v0.22 development pilot are complete, the v0.23 matched-feedback study is running, and full FHIR skill learning is queued after Gemini.** The [active English LaTeX source](latex/v0.3/prismatic_v03_en.tex) is updated in place and compiles with the official ACL review style. See [template provenance](latex/v0.3/acl_template_provenance.json) and [compile check](latex/v0.3/compile_check.json). The earlier AAMAS template is preserved in Git history.

## Start here

- [中文系统流程与进化对象](RXRSI_DESIGN.zh.md) / [English design](RXRSI_DESIGN.en.md)
- [中文当前主表](CURRENT_RESULTS.zh.md) / [Current English method tables](CURRENT_RESULTS.en.md)
- [持续更新计划](COMPLETION_PLAN.md) / [English plan](COMPLETION_PLAN.en.md)
- [v0.7 evidence and reproduction](../upgrade_v7/README.md), [v0.8 language evolution](../upgrade_v8/README.md), [v0.9 parameter evolution](../upgrade_v9/README.md)

[Current consolidated results](CURRENT_RESULTS.en.md) / [中文总览](CURRENT_RESULTS.zh.md)

## Where are the main tables?

- **Table 1:** published datasets, task definitions and experiments.
- **Table 2:** original reported GAMENet, SafeDrug, SafeRx and RxEval scores, grouped by source protocol. These are citations, not our reruns.
- **Table 3:** actual same-4,000-admission method comparison; 12 rows, three seeds, drug and joint-order F1.
- **Table 4:** frozen-checkpoint case-growth trajectory.
- The recorded-availability table covers1,082 new test admissions; its protocol differs from Table3. Public language-agent and local QLoRA tables use their respective fixed cohorts. Incomplete experiments are explicitly marked.

## Additional completed comparisons

[Public method table, English](../upgrade_v8/RESULTS.en.md) / [中文](../upgrade_v8/RESULTS.zh.md): Direct 46.15%, CoT 47.27%, Self-Refine 47.57%, case RAG 49.09%, three-seed RxRSI 47.27%. The [unmodified GRASP core](../upgrade_v10/RESULTS.en.md) reaches 50.81% on the same 988 questions; scoped RxRSI remains flat. The [evidence-tool increment](../upgrade_v11/RESULTS.en.md) reaches 48.99% with the validation-selected fixed review. [Three-seed learned routing](../upgrade_v12/RESULTS.en.md) reaches 48.68%/48.79%; it changes parameters but has no stable advantage over the fixed tool.

## Current conclusion

v0.7 selected-state mean drug/order F1 is **0.39920 / 0.27865**; the stronger equal-data word/character ensemble reaches **0.40209 / 0.28110**. Three-seed accepted-state curves improve with accumulated cases, but ordinary learning remains a strong explanation. Conditional order tools help; expanding case memory is not consistently beneficial. This motivates the ongoing language-artifact and parameter studies.

GT-based evaluation does not require clinician review. Missing attributes remain unknown. Current MIMIC inputs retain admission-proxy timing limitations; the task is not interchangeable with the original ATC-L4 or RxEval protocols. The saline-presence endpoint is removed from current scoring and tables.

## Versions

| Version | Record | Evidence |
| --- | --- | --- |
| v0.23 | [Matched feedback protocol](../upgrade_v23/README.en.md) | Three seeds/five rounds; equal-epoch uniform, own-error and shuffled-weight controls running |
| v0.22 | [Numerical-state development pilot](../upgrade_v22/RESULTS.en.md) | Guard point gain passes the declared rule; intervals include zero; no test scoring |
| v0.21 | [Recorded-availability method table](../upgrade_v21/RESULTS.en.md) | Three seeds,14 method/ablation rows, independent recounts and patient intervals complete |
| v0.20 | [Order-entry audit](../upgrade_v20/RESULTS.en.md) | 1.788M target rows, actual provider/pharmacy clocks, explicit identity conflicts |
| v0.19 | [Real-order compiler probes](../upgrade_v19/RESULTS.en.md) | Actual field preservation and rollback; full FHIR learning queued |
| v0.18 | [Backbone-transfer protocol](../upgrade_v18/protocol.json) | Gemini four-method frozen-artifact comparison running |
| v0.17 | [Grounded skill results](../upgrade_v17/RESULTS.en.md) | Four matched components, all frozen rounds, transfer and paired intervals |
| v0.16 | [Budget repair results](../upgrade_v16/RESULTS.en.md) | Completed 190-question Gemini development repair; 2,048-token follow-up complete; four-method backbone transfer queued |
| v0.15 | [Pre-test intervention](../upgrade_v15/README.md) | Binary candidate output protocol frozen before v0.9 test scoring; local training running |
| v0.14 | [Real FHIR results](../upgrade_v14/RESULTS.en.md) | Five integration probes and matched 16-task model pilot |
| v0.13 | [Executed outcome-verifier results](../upgrade_v13/RESULTS.en.md) | Three seeds, same two-call budget, uniform/error-prioritized updates and full-data supervision |
| v0.12 | [Executed gate/round results](../upgrade_v12/RESULTS.en.md) | Three-seed cached replay, evolving routing parameters, regressions and fixed-tool control |
| v0.11 | [Completed executed results](../upgrade_v11/RESULTS.en.md) | All indication/Gemini requests recovered under the original protocol |
| v0.10 | [Executed results](../upgrade_v10/RESULTS.en.md) | Unmodified author GRASP core, scoped-skill failure and paired analysis |
| v0.9 | [Completed results](../upgrade_v9/RESULTS.en.md) | 500-case all-checkpoint QLoRA evaluation and direct tool controls |
| v0.8 | [Results / three seeds complete](../upgrade_v8/RESULTS.en.md) | Public language-artifact evolution, named task adaptations, transfer |
| v0.7 | [Executed results](../upgrade_v7/RESULTS.en.md) | Three seeds, new 4k test, artifact ablations, stronger equal-data controls |
| v0.6 | [Results](../upgrade_v6/RESULTS.en.md), [design](../upgrade_v6/DESIGN.en.md) | Raw orders, GT automatic feedback, policy evolution, reported baselines and negative replay/planner ablations |
| v0.5 | [Results](../upgrade_v5/RESULTS.en.md), [frozen paper](https://github.com/ZaneLing/PRISMATIC/tree/1f488edbbf6a8c22423bcbb0a5cf6585c5a81bb2/paper) | Empty-output repair, stronger ranking and residual memory |
| v0.4 | [Results](../upgrade_v4/RESULTS.en.md) | Time/mapping audits, adapted methods and original harness failures |
| v0.3 | [Frozen paper](https://github.com/ZaneLing/PRISMATIC/tree/289bf4c0fc90df12c3f6e851c32ac63f257cc281/paper) | Initial common-cohort comparison and full public secondary runs |
| v0.2 | [English archive](versions/v0.2-2026-10-14.en.md), [中文](versions/v0.2-2026-10-14.zh.md) | Paired 60-question harness pilot |
| v0.1 | [English archive](versions/v0.1-2026-10-14.en.md), [中文](versions/v0.1-2026-10-14.zh.md) | Initial model and case-growth experiments |

The Chinese LaTeX is an archive; only the English paper is maintained.

## Update contract

1. Update the active English source in place, compile, update both Markdown languages, and synchronize GitHub. Preserve previous versions and failures.
2. Cite published baselines directly with source tables and protocol identifiers. Claim a numerical win only after measuring our method under the corresponding protocol.
3. Link executed values to aggregate outputs and manifests. Keep restricted records, traces, checkpoints and credentials outside GitHub.
4. Evaluate observed GT automatically. Use optional rules or human assessment for additional attributes, with their coverage stated.
