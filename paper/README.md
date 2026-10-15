# RxRSIAgent: current manuscript and evidence index

Target: ACL 2027. Updated 15 October 2026.

The [English ACL manuscript](latex/v0.3/prismatic_v03_en.tex) is maintained at its existing editor path. It uses one development-selected **RxRSIAgent** configuration. Historical prototypes and version inventories are retained below and in Git, not inside the current paper.

## Start here

- [中文当前结果与主表](CURRENT_RESULTS.zh.md) / [Current English results](CURRENT_RESULTS.en.md).
- [中文架构与临床问题映射](RXRSI_DESIGN.zh.md) / [English architecture and risk map](RXRSI_DESIGN.en.md).
- [Executable RxRSIAgent components](../rxrsiagent/README.md) / [selected configuration](../rxrsiagent/evaluated_profile.json).
- [Evidence manifest](latex/v0.3/manuscript_evidence.json), [compile check](latex/v0.3/compile_check.json), [ACL template provenance](latex/v0.3/acl_template_provenance.json).
- [Earlier study archive, English](RESULTS_ARCHIVE_2026-10-15.en.md) / [历史实验归档](RESULTS_ARCHIVE_2026-10-15.zh.md).

- [Clinical assessment protocol](CLINICAL_EVALUATION.en.md) / [医生视角评估](CLINICAL_EVALUATION.zh.md).
- [Audited evolution mechanism and rounds](EVOLUTION.en.md) / [机制与逐轮证据](EVOLUTION.zh.md).

## Where is each part of the paper?

| Reader question | Location | Evidence boundary |
|---|---|---|
| What is the complete agent workflow? | Figure1, RxRSIAgent | Measured QA core is solid; new clinical review interfaces are dashed |
| Which datasets and tasks are evaluated? | Table1, Experimental Setup | Public option tasks and separate eICU order-tool study |
| How does RxRSIAgent compare with other paper methods? | **Table2, Main agent comparison** | MedAgents, MDAgents, SafeRx-Agent, GRASP and **RxRSIAgent**; missing runs explicitly marked |
| What do evidence and skills contribute? | Table3, Component ablations | Same backbone, questions and inference cap |
| What changes as cases accumulate? | Table4, Experience trajectory | Five checkpoints, artifact words/operations and Figure2 curves; no monotonic improvement claim |
| Does an order tool help? | Table5, Order-tool component evidence | eICU fixed-policy intervention; not a full-agent score |
| Where are real examples? | Table6, Case Studies | Public case104 correction and case10 frequency regression |
| What did the new retrieval repair accomplish? | Table7, Retrieval failure and repair | Coverage1→214/300, dosage0→193/300; no new answer accuracy |
| Which clinical risks are implemented or unresolved? | Method, Clinical Review Scope appendix; bilingual design notes | Eighteen interfaces, structural checks, pending clinical engines |
| What would clinicians measure beyond F1? | Table8, Clinician-Oriented Evaluation Protocol | Fourteen proposed endpoints, three primary; annotations pending |
| Which modules actually evolve? | Table9, Module-level attribution | Learned skill updates versus fixed modules and separate component repairs |

## Current interpretation

The selected agent scores501/988 and183/300 and does not beat the measured GRASP control. The newly repaired retriever improves source availability, and twelve software tests exercise the new interfaces. Missing medical-agent comparisons, product applicability and clinical rule validation remain required work. The paper does not call all prescribing risks solved.

Existing long-running queues remain paused. This writing/implementation increment only audited public caches and synthetic fixtures, without new provider calls. Required follow-up experiments are listed in the [current results](CURRENT_RESULTS.en.md#5-auxiliary-evidence-and-remaining-experiments).

## Versions

| Version | Record | Evidence |
| --- | --- | --- |
| v0.32 | [Controlled decision repair](../upgrade_v32/RESULTS.en.md) | Four same-data/100-step prefix/loss arms; fixed and calibrated scoring, independent recount and guard prerequisites |
| v0.31 | [Parameter intervention](../upgrade_v31/RESULTS.en.md) | Four arms, three seeds, three rounds; position randomization with original ranks retained; partial; paused |
| v0.30 | [Memory gates](../upgrade_v30/RESULTS.en.md) | Fourteen arms isolate old-memory compatibility and separate whole-update confirmation; audited completed seeds reported |
| v0.29 | [Program synthesis](../upgrade_v29/RESULTS.en.md) | All six five-round runs independently audited; permanent witness separation, ordinary calibration, greedy/random/shuffled controls |
| v0.28 | [FHIR factorial](../upgrade_v28/RESULTS.en.md) | Twenty-three of24 cells audited; fixed engineering repairs distinguished from learned frozen skills |
| v0.27 | [Author-method compatibility](../upgrade_v27/RESULTS.en.md) | Common patient splits and ATC-L4 spaces; genuine author-model training and gated test evaluator |
| v0.26 | [Position diagnostic](../upgrade_v26/README.en.md) | 200 existing development cases,3 fixed states,4 rank-preserving display conditions; complete and audited |
| v0.25 | [External method experiment](../upgrade_v25/RESULTS.en.md), [development curves](../upgrade_v25/DEVELOPMENT_CURVES.en.md) | Completed 8,005-stay / 16-hospital test, 13 methods/components, three seeds; raw/accepted curves and independent interval recount |
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
