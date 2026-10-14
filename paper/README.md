# PRISMATIC / RxRSIAgent manuscript and execution index

**Active English draft: v0.6 (14 October 2026).** The [existing English LaTeX source](latex/v0.3/prismatic_v03_en.tex) is edited in place, retaining the original AAMAS template from the supplied ZIP. Its path is unchanged for the open editor. See [template provenance](latex/v0.3/template_provenance.json) and [compilation check](latex/v0.3/compile_check.json).

## Start here

- [中文：RxRSIAgent 流程、进化设计、后续实验](../upgrade_v6/DESIGN.zh.md) / [English design](../upgrade_v6/DESIGN.en.md)
- [中文真实结果](../upgrade_v6/RESULTS.zh.md) / [English results](../upgrade_v6/RESULTS.en.md)
- [完整持续更新计划](COMPLETION_PLAN.md) / [Versioned English plan](COMPLETION_PLAN.en.md)
- [Executable code and evidence map](../upgrade_v6/README.md)

## Where are the main tables?

- **Table 1:** literature datasets, task definitions and experiment types.
- **Table 2:** directly cited, author-reported GAMENet, SafeDrug, SafeRx-Agent and RxEval results, grouped by protocol. Reimplementation is not required. Our matched-protocol rows remain to be measured.
- **Table 3:** executed local raw-order comparison on the same 4,000 development-test admissions. Methods include retrieval, the initial 8k policy, accumulated 40k policies and the selected RxRSIAgent variant.
- **Tables 4–5:** case-growth experiment and actual local LLM planning pilot.

The current task uses MIMIC-IV/ED 40k/4k/4k patient-disjoint admissions and six-hour prescription targets. Its 128 raw-name vocabulary is frozen from the first 8k training cases; names, route, dose, unit and observed frequency are scored. It is distinct from older ATC-L4 pilots. Unknown clinical attributes remain unscored.

GT-based training and evaluation **do not require clinician review**. Two-reviewer assessment remains optional for additional clinical questions absent from GT. Existing clinical-review preparation is preserved as a supplementary resource.

## Latest evidence

Drug F1 improves from 0.35841 to 0.40668 with 8k → 40k training cases. Selected core-order F1 is 0.28003. Same-40k ordinary training matches the selected variant; error-prioritized replay does not add a demonstrated benefit. Validation also selects direct learned-policy output over the tested LLM planners. The system updates policy parameters, case memory and joint templates, while LLM weights remain frozen.

## Versions

| Version | Record | Evidence |
| --- | --- | --- |
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
