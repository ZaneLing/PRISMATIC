# PRISMATIC manuscript and execution index

**Active draft: v0.4-dev (2026-10-14), English only.** The existing [English LaTeX source](latex/v0.3/prismatic_v03_en.tex) is updated in place. Its directory name preserves the editor path; the draft version appears inside the manuscript. The template is the original AAMAS class from the supplied ZIP, with provenance recorded [here](latex/v0.3/template_provenance.json). The updated source compiled successfully in the Codex editor.

**Latest executed batch: v0.4 r1. [真实实验结果（中文）](../upgrade_v4/RESULTS.zh.md) / [English results](../upgrade_v4/RESULTS.en.md).** Table 2 now has a 4,000-case panel (including three-seed GAMENet text adaptation) and a separate identical-50-case panel containing direct, ordinary repeat, retrieval and bounded harness. The bounded harness did not improve observed F1. SafeDrug, SafeRx-Agent and the clinically complete harness remain unscored.

## 下一步完整计划 / Completion plan

**[完整 Markdown 计划：实验、比较方法、实施步骤、验收和交付台账](COMPLETION_PLAN.md)**

[Full English plan](COMPLETION_PLAN.en.md) · [Compilation verification](latex/v0.3/compile_check.json)

The plan covers a common-protocol method comparison, reviewed-case growth, mechanism ablations, two-reviewer clinical evaluation, full public benchmarks, and real FHIR tool-state evaluation. Planned experiments are not completed results.

The latest increment executes timestamp and route-mapping audits, freezes the development input/unknown-label/order protocol, and runs method comparisons and an order probe. A new confirmatory split, compatible SafeDrug/SafeRx resources and clinical ratings remain outstanding. See the [execution report](../upgrade_v4/RESULTS.en.md).

## Where is the main table?

- **Table 2 in the [active English paper](latex/v0.3/prismatic_v03_en.tex)** compares methods on MIMIC. Panel A contains prevalence, retrieval, SGD and GAMENet text adaptation on 4,000 admissions. Panel B uses the identical nested 50 cases for those methods and four fixed-backbone LLM approaches including bounded PRISMATIC. Never compare scores across the two sample sizes as if they were the same test.
- **Dataset:** restricted MIMIC-IV v3.1 + MIMIC-IV-ED v2.2; 201,750 ED-to-hospital admissions, 107,097 patients; patient-disjoint splits; six-hour all-route prescription targets in ATC-L4. The pilot uses 40,000/4,000/4,000 admissions, top-80 training classes and five predictions per admission.
- **Observability:** the revised train-40k-only mapper covers 45.535% of raw six-hour orders (v0.3: 45.652%). Of the pilot's 4,000 admissions, 1,144 have no recorded raw order and 152 have unmapped-only orders. These are distinct unknown-target conditions. See the [mapping audit](../upgrade_v4/results/mapping_protocol_audit.json).
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
