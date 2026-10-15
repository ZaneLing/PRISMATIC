# RxRSIAgent

One prescription-agent identity, with a pinned evaluated configuration and explicit implementation boundaries.

- [中文方法与临床问题映射](../paper/RXRSI_DESIGN.zh.md) / [English method and risk map](../paper/RXRSI_DESIGN.en.md)
- [中文结果](../paper/CURRENT_RESULTS.zh.md) / [English results](../paper/CURRENT_RESULTS.en.md)
- [English ACL manuscript](../paper/latex/v0.3/prismatic_v03_en.tex)

## What is executable here?

`RxRSIAgent` loads and verifies the selected skill file, passes it to an injected actor with evidence and task context, checks option outputs, and reviews draft-order structure. `LabelIndex` retrieves exact spans from a supplied frozen openFDA corpus using source drug-name aliases in both questions and options. No API credentials, provider calls, clinical writes, or automatic dosing changes are performed by this package.

```python
from rxrsiagent import RxRSIAgent, LabelIndex

# Supply your local corpus and an actor that accepts the context dictionary.
labels = LabelIndex("/path/to/frozen/labels.json")
agent = RxRSIAgent(actor=my_actor, label_index=labels)
result = agent.run(question, options)
```

The selected skill is loaded from the repository path in [evaluated_profile.json](evaluated_profile.json). The caller must include `skill_memory`, evidence and policy in the actual actor prompt. Without an actor, `run()` returns `needs_actor`. Supplying an arbitrary actor does not reproduce the published protocol. Exact scored inference and learning remain in [the grounded-skill experiment](../upgrade_v17/README.md); the new retrieval and review components have not received an end-to-end answer score.

For order drafts, provide `orders` as a list of objects with `ingredient_id`, `indication`, numeric `dose`, `dose_unit`, `route`, `frequency`, and `duration`. Ingredient IDs must already be normalized by the caller. Patient allergy IDs must be a list; missing history remains unknown. The IV and adjunct checks require evidence/purpose fields, but do not validate the medical correctness of supplied evidence. Empty orders require resolution. `structurally_complete` never means clinically safe; all unresolved clinical domains remain `not_assessed`.

The eighteen-domain [registry](clinical_skills.json) declares required facts, procedures, external tools, sources and memory boundaries. Most named clinical tools are integration requirements, not implemented clinical engines. `admit_memory()` validates proposal fields and a declared training split; it does not independently establish provenance or promote a skill. The evaluated updater is the credited GRASP author core, not a new optimizer implemented by this package.

## Verification and real observations

```bash
python -m unittest rxrsiagent.test_contracts -v
python -m rxrsiagent.audit_public_snapshot
```

The audit command expects the original local public caches; it makes no network calls. It rechecks saved answer correctness, binds the selected profile to the existing validation record, selects two contrasting public cases using a declared rule, and independently compares every returned quote with the original source paragraph and offset.

| Artifact | Result | Scope |
|---|---|---|
| [Contract checks](results/contract_checks.json) | 12 tests passed | Synthetic software behavior, not clinical validation |
| [Retrieval coverage](results/retrieval_coverage.json) | 1 → 214 of 300 questions with excerpts | Same frozen corpus; no actor calls |
| Dosage excerpt coverage | 0 → 193 of 300 | Not evidence of dose correctness |
| Exact source-span recount | 1,666 / 1,666 | Provenance, not relevance or applicability |
| [Case studies](results/case_studies.json) | One corrected choice, one frequency regression | Saved public predictions, selected post hoc |

The audit uses test questions only for retrospective diagnosis. It does not change the frozen scored configuration or learn memory from their labels. Since retrieval was repaired after observing benchmark behavior, future scores on these same questions must be described as exploratory and confirmed on an untouched or independently scoped set.

## Current scientific claim

RxRSIAgent's retained checkpoint is development-selected. Its saved scores are **501/988** on derived RxSafeBench and **183/300** on public RxQA. They do not yet beat the GRASP control. The new retriever repairs a measured tool-coverage failure; the new clinical interfaces expose unresolved checks. Neither result establishes medical-agent superiority or autonomous safe prescribing.

## Clinical endpoint design and evolution audit

- [Clinical evaluation protocol](../paper/CLINICAL_EVALUATION.en.md), [机器可读协议](clinical_evaluation_protocol.json), and [blank rating template](clinical_review_template.json). No clinician results have been collected.
- [Audited skill evolution](../paper/EVOLUTION.en.md):625 unique training traces,16 initial proposals, one revision, three accepted edits; all saved round outcomes independently recounted.
- `python -m rxrsiagent.audit_evolution` checks the local public caches and unchanged credited GRASP core without actor calls.
- `python -m unittest rxrsiagent.test_clinical_metrics -v` runs seven synthetic aggregation checks. They are separate from the twelve structural contract tests.
- `python -m rxrsiagent.clinical_metrics local_adjudicated_ratings.json local_summary.json` aggregates clinical labels only after they have been supplied; it does not generate clinical judgments.
