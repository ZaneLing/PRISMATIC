# PRISMATIC / RxRSIAgent manuscript and execution index

<!-- RXRSI_CURRENT_EXECUTION_START -->
## Live execution snapshot

The common medication-method study has **8/15** completed 50-epoch author runs (459/750 saved epochs) and **6/6** completed five-round rule runs. The final common test remains gated by the registered selections and audits. These counts describe a saved snapshot; running outputs continue to update.

[中文当前结果](CURRENT_RESULTS.zh.md) · [English current results](CURRENT_RESULTS.en.md) · [Cross-method development comparison](../upgrade_v27/DEVELOPMENT_METHODS.en.md) · [Final common-test table and gate](../upgrade_v30/COMMON_TEST.en.md)
<!-- RXRSI_CURRENT_EXECUTION_END -->


**Target: ACL 2027.** The [current method tables and execution status](CURRENT_RESULTS.en.md) distinguish completed audited results from running work. The [active English LaTeX source](latex/v0.3/prismatic_v03_en.tex) is updated in place using the official ACL review style. See [template provenance](latex/v0.3/acl_template_provenance.json) and [compile check](latex/v0.3/compile_check.json). The earlier AAMAS template is preserved in Git history.

## Start here

- [中文系统流程与进化对象](RXRSI_DESIGN.zh.md) / [English design](RXRSI_DESIGN.en.md)
- [中文当前主表](CURRENT_RESULTS.zh.md) / [Current English method tables](CURRENT_RESULTS.en.md)
- [持续更新计划](COMPLETION_PLAN.md) / [English plan](COMPLETION_PLAN.en.md)
- [历史病例与冻结子集核验](EXPOSURE.zh.md) / [Exposure audit and frozen subset](EXPOSURE.en.md)
- [共同测试主表入口](../upgrade_v30/COMMON_TEST.zh.md) / [Frozen common-test comparison](../upgrade_v30/COMMON_TEST.en.md)
- [v0.7 evidence and reproduction](../upgrade_v7/README.md), [v0.8 language evolution](../upgrade_v8/README.md), [v0.9 parameter evolution](../upgrade_v9/README.md)

[Current consolidated results](CURRENT_RESULTS.en.md) / [中文总览](CURRENT_RESULTS.zh.md)

## Where are the main tables?

The manuscript now gives the common medication-method experiment its own **Study A: Common Medication-Set Comparison** section, following the agent definition. Figure/table numbering can change as results arrive; use these stable study names and report links.

| Reader question | Maintained result entry | Manuscript location |
|---|---|---|
| How do GAMENet, SafeDrug, ARMR, conventional methods and our agent compare on identical cases? | [中文跨方法开发表](../upgrade_v27/DEVELOPMENT_METHODS.zh.md) / [English development comparison](../upgrade_v27/DEVELOPMENT_METHODS.en.md); [final-test table and gate](../upgrade_v30/COMMON_TEST.en.md) | Study A; development and final test remain distinct |
| Which datasets and experiments do published papers use? | [Recent-method source audit](LATEST_METHODS.en.md) | Related Work: published task registry and author-reported scores |
| Does more experience improve complete recorded orders? | [Recorded-availability results](../upgrade_v21/RESULTS.en.md), [matched feedback controls](../upgrade_v23/RESULTS.en.md), [eICU external study](../upgrade_v25/RESULTS.en.md) | Study B; each cohort and drug space is separate |
| Do learned language skills generalize? | [Public component/round comparison](../upgrade_v17/RESULTS.en.md), [second-backbone transfer](../upgrade_v18/RESULTS.en.md) | Study C |
| What changed in model weights, and is it robust to candidate order? | [Parameter rounds](../upgrade_v31/RESULTS.en.md), [controlled decision repair](../upgrade_v32/RESULTS.en.md) | Study D |
| Do real tools execute the intended state changes? | [FHIR skill results](../upgrade_v19/RESULTS.en.md), [repair factorial](../upgrade_v28/RESULTS.en.md) | Study E |
| What was the actual fitting and proposal budget? | [中文计算账本](COMPUTE_ACCOUNTING.zh.md) / [English compute receipts](COMPUTE_ACCOUNTING.en.md) | Study A computation paragraph and linked full receipts |

The agent-state section includes a study map linking each task to its output and evolving object. The original 4,000-admission and later 1,082-admission order tasks retain their original protocols and results. Original-paper scores remain source-specific citations.

## Additional completed comparisons

[Public method table, English](../upgrade_v8/RESULTS.en.md) / [中文](../upgrade_v8/RESULTS.zh.md): Direct 46.15%, CoT 47.27%, Self-Refine 47.57%, case RAG 49.09%, three-seed RxRSI 47.27%. The [unmodified GRASP core](../upgrade_v10/RESULTS.en.md) reaches 50.81% on the same 988 questions; scoped RxRSI remains flat. The [evidence-tool increment](../upgrade_v11/RESULTS.en.md) reaches 48.99% with the validation-selected fixed review. [Three-seed learned routing](../upgrade_v12/RESULTS.en.md) reaches 48.68%/48.79%; it changes parameters but has no stable advantage over the fixed tool.

## Evidence to read together

The [cross-method development comparison](../upgrade_v27/DEVELOPMENT_METHODS.en.md) includes every available completed conventional, author-core and rule-memory method, with matched-patient intervals. The rule agent improves over some older neural architectures; strong greedy and ordinary-learning controls constrain an RSI-specific claim. The final common test remains conditional on every registered selection and audit completing. The [current execution entry](CURRENT_RESULTS.en.md) is the source for changing completion counts.

### Earlier structured-order finding retained from v0.7

v0.7 selected-state mean drug/order F1 is **0.39920 / 0.27865**; the stronger equal-data word/character ensemble reaches **0.40209 / 0.28110**. Three-seed accepted-state curves improve with accumulated cases, but ordinary learning remains a strong explanation. Conditional order tools help; expanding case memory is not consistently beneficial. This motivates the ongoing language-artifact and parameter studies.

GT-based evaluation does not require clinician review. Missing attributes remain unknown. Legacy structured-order inputs retain admission-proxy timing limitations; the recorded-availability rebuild and retrospective ATC-L4 cohort have separately declared input rules. None is interchangeable with an unavailable official RxEval protocol. The saline-presence endpoint is removed from current scoring and tables.

## Versions

| Version | Record | Evidence |
| --- | --- | --- |
| v0.32 | [Controlled decision repair](../upgrade_v32/RESULTS.en.md) | Four same-data/100-step prefix/loss arms; fixed and calibrated scoring, independent recount and guard prerequisites |
| v0.31 | [Parameter intervention](../upgrade_v31/RESULTS.en.md) | Four arms, three seeds, three rounds; position randomization with original ranks retained; training running |
| v0.30 | [Memory gates](../upgrade_v30/RESULTS.en.md) | Fourteen arms isolate old-memory compatibility and separate whole-update confirmation; audited completed seeds reported |
| v0.29 | [Program synthesis](../upgrade_v29/RESULTS.en.md) | All six five-round runs independently audited; permanent witness separation, ordinary calibration, greedy/random/shuffled controls |
| v0.28 | [FHIR factorial](../upgrade_v28/RESULTS.en.md) | Twenty-three of24 cells audited; fixed engineering repairs distinguished from learned frozen skills |
| v0.27 | [Author-method compatibility](../upgrade_v27/RESULTS.en.md) | Common patient splits and ATC-L4 spaces; genuine author-model training and gated test evaluator |
| v0.26 | [Position diagnostic](../upgrade_v26/README.en.md) | 200 existing development cases,3 fixed states,4 rank-preserving display conditions; complete and audited |
| v0.25 | [External method experiment](../upgrade_v25/RESULTS.en.md) | Native-code cohort audited; 8,005 test stays; three seeds running, no test score |
| v0.24 | [External eICU audit](../upgrade_v24/RESULTS.en.md) | 142,485 stays; hospital/patient-disjoint partition and HICL/time coverage audited; no model scores |
| v0.23 | [Matched feedback results](../upgrade_v23/RESULTS.en.md) | Three seeds/five rounds audited; uniform learning is stronger than error priorities |
| v0.22 | [Numerical-state development pilot](../upgrade_v22/RESULTS.en.md) | Guard point gain passes the declared rule; intervals include zero; no test scoring |
| v0.21 | [Recorded-availability method table](../upgrade_v21/RESULTS.en.md) | Three seeds,14 method/ablation rows, independent recounts and patient intervals complete |
| v0.20 | [Order-entry audit](../upgrade_v20/RESULTS.en.md) | 1.788M target rows, actual provider/pharmacy clocks, explicit identity conflicts |
| v0.19 | [Real-order skill results](../upgrade_v19/RESULTS.en.md) | Completed real-FHIR learning, ID and held-out-type comparisons; reference-shape correction and negative skill transfer retained |
| v0.18 | [Frozen-transfer results](../upgrade_v18/RESULTS.en.md) | All four Gemini methods complete; grounded skills regress versus fixed grounding |
| v0.17 | [Grounded skill results](../upgrade_v17/RESULTS.en.md) | Four matched components, all frozen rounds, transfer and paired intervals |
| v0.16 | [Budget repair results](../upgrade_v16/RESULTS.en.md) | Completed 190-question Gemini development repair; 2,048-token follow-up complete; four-method backbone transfer complete in v0.18 |
| v0.15 | [Binary parameter results](../upgrade_v15/RESULTS.en.md) | Complete: priority0.29192/0.19329; below top-8; raw collapse and10 feedback receipt gaps disclosed |
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
