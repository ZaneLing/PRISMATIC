# PRISMATIC manuscript and execution index

**Active draft: v0.4-dev (2026-10-14), English only.** The existing [English LaTeX source](latex/v0.3/prismatic_v03_en.tex) is updated in place. Its directory name preserves the editor path; the draft version appears inside the manuscript. The template is the original AAMAS class from the supplied ZIP, with provenance recorded [here](latex/v0.3/template_provenance.json). The updated source compiled successfully in the Codex editor.

## 下一步完整计划 / Completion plan

**[完整 Markdown 计划：实验、比较方法、实施步骤、验收和交付台账](COMPLETION_PLAN.md)**

[Full English plan](COMPLETION_PLAN.en.md) · [Compilation verification](latex/v0.3/compile_check.json)

The plan covers a common-protocol method comparison, reviewed-case growth, mechanism ablations, two-reviewer clinical evaluation, full public benchmarks, and real FHIR tool-state evaluation. Planned experiments are not completed results.

This increment completes P00 (English AAMAS template) and P01a (label observability audit). The next stage is P01b/P02: verify information availability, audit mapping by route, define complete orders and unknown-label scoring, and freeze the confirmatory patient split. See the [execution report](../upgrade_v4/README.md).

## Where is the main table?

- **Table 2 in the [active English paper](latex/v0.3/prismatic_v03_en.tex)** compares methods on MIMIC. Prevalence, case retrieval and direct SGD have pilot results; GAMENet, SafeDrug, SafeRx-Agent and full harness remain unmeasured under the common protocol.
- **Dataset:** restricted MIMIC-IV v3.1 + MIMIC-IV-ED v2.2; 201,750 ED-to-hospital admissions, 107,097 patients; patient-disjoint splits; six-hour all-route prescription targets in ATC-L4. The pilot uses 40,000/4,000/4,000 admissions, top-80 training classes and five predictions per admission.
- **Observability:** 45.652% of raw six-hour orders map to ATC-L4. Of the pilot's 4,000 test admissions, 1,144 have no recorded raw order in the window and 152 have orders but no mapped label. These are different missing-target conditions; neither establishes a clinical need for no medication. See the [audit](../upgrade_v4/results/label_observability_audit.json).
- **Public secondary tasks:** RxSafeBench deduplicated 2,000 questions and RxQA OpenFDA 300 questions. Their multiple-choice results are separate from the prescribing main table.
- **Clinical evaluation:** two reviewers are available; the [review protocol](../upgrade_v3/CLINICAL_REVIEW_PROTOCOL.md) and a local 200-case manifest exist. Complete candidate orders and independent ratings are pending.

## Versions

| Version | Record | Evidence |
| --- | --- | --- |
| v0.4-dev | [Active English source](latex/v0.3/prismatic_v03_en.tex), [plan](COMPLETION_PLAN.md), [change log](CHANGELOG.md) | Original ZIP template; label observability audit; expanded completion protocol |
| v0.3 | [Frozen Git snapshot](https://github.com/ZaneLing/PRISMATIC/tree/289bf4c0fc90df12c3f6e851c32ac63f257cc281/paper), [experiment records](../upgrade_v3/README.md) | Three MIMIC method pilot rows and full public secondary runs |
| v0.2 | [English archive](versions/v0.2-2026-10-14.en.md), [Chinese archive](versions/v0.2-2026-10-14.zh.md) | 60-question lightweight harness pilot |
| v0.1 | [English archive](versions/v0.1-2026-10-14.en.md), [Chinese archive](versions/v0.1-2026-10-14.zh.md) | Initial case-growth and model experiments |

The old Chinese LaTeX is retained as an archive and is no longer maintained as an active manuscript.

## Update contract

1. Update the active English source in place, compile it, and append completed evidence, protocol changes and outstanding work to the plan and change log. Preserve historical versions through Git.
2. Main-table scores require the same data, decision-time inputs, patient split, drug space and scorer. Never copy another paper's original score into this table.
3. Trace every numeric result to a versioned aggregate output and run manifest. Keep restricted case-level data and credentials outside the public repository.
4. Fill clinical appropriateness, DDI, renal adjustment and saline purpose/dose/rate endpoints only after generating evaluable orders and obtaining the required adjudication. Historical order overlap does not establish these outcomes.
