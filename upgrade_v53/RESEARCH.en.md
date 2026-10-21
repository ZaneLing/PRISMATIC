# Research update: from memory growth to defensible prescription improvement

**Research question.** Can feedback produce executable, clinically meaningful conditional skills that retain reductions in omissions, extra drugs and joint-order errors on new patients, different case orders and backbones?

## Primary sources and design consequences

| Source | What it studies | Consequence for our experiment |
|---|---|---|
| [GuideSkill, July2026](https://arxiv.org/html/2607.26160) | Guideline-derived executable diagnostic criteria, refined using labeled cases; diagnostic support rather than prescription generation | Make conditions inspectable and distinguish guideline engineering from learned updates. Its diagnostic scores cannot populate our prescription table. |
| [SkillLearnBench, April2026](https://arxiv.org/html/2604.20087) | Skill quality, execution and outcomes across reusable tasks; contrasts external and self feedback | Record which program actually executes and what errors change, instead of reporting library size alone. |
| [ContinualSkillBench, v3 October15,2026](https://arxiv.org/html/2608.03874v3) | Sequential task learning; explicit skill libraries versus retained context/feedback | Add a feedback-memory replay comparator. Our deterministic replay is a task-specific control, not a reproduction of their contextual agent. |
| [WHO prescribing teaching framework,2001](https://iris.who.int/handle/10665/67010) | Patient problem, treatment objective, individual suitability, writing orders, instructions and follow-up | Separate event forecasting from appropriate treatment. Require explicit goals and mark unavailable context. |
| [Medication Appropriateness Index original study,1992](https://doi.org/10.1016/0895-4356(92)90144-C) | Structured expert assessment of medication appropriateness | Prepare independent blinded review. Our adapted dimensions are not a validated MAI score. |

### Label-backed executable checks

Three small fixed tools screen renal and related conditions using current typed measurements: [metformin](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=4e4c4ba9-65c6-4273-8f6b-2423ab521dad), [enoxaparin](https://dailymed.nlm.nih.gov/dailymed/lookup.cfm?setid=d8afb29f-cbed-43bc-809f-09b30fca28f5), and [eplerenone](https://dailymed.nlm.nih.gov/dailymed/fda/fdaDrugXsl.cfm?setid=bcd7595f-700f-48ba-bf83-05a995ce0731&type=display). Source sections and URLs are returned with each check. Missing, stale, mismatched-unit and unavailable-at-cutoff facts remain unknown. Treatment initiation is not inferred from absent prior records. These tools do not calculate doses, infer active diagnoses, resolve all drug identities or certify safety. Synthetic boundary tests validate implementation, not clinical effectiveness.

## Updated architecture

1. Freeze the observable hour6 context and the recorded hours6–12 target contract.
2. Run a fixed local actor using training-only ranking and retrieval.
3. Compare development outputs with references component by component; aggregate repeated errors.
4. Induce target-drug-specific add/remove/replace programs with diagnostic-path conditions, optional prior-record status and harmful-case exceptions.
5. Require reflection support and proposal improvement; use a separate guard that rejects aggregate regression and any individual increase in omissions. Keep rejected-program memory.
6. Freeze every round. Execute on untouched patients with both actors and all prespecified case orders; compare feedback replay, frozen supervised tools and scope ablation.
7. Produce source-backed preflight findings and a blinded human review package. A statistical association is not automatically a clinical indication or a reason to stop therapy.

The learner is a fixed symbolic program inducer with labeled feedback. It changes external memory; it neither retrains LLM weights nor autonomously invents clinical algorithms. This is a bounded component of the RSI hypothesis, not proof of full recursive self-improvement.

## Development finding and amendment

The192 reflection patients support only2 identical complete native4 tuples in at least3 patients. All training-qualified original proposals are removals. A pre-outcome amendment therefore adds recurrent joint templates from the previous40000 training stays, counted by distinct patients, while retaining the same support and validation gates. Only templates already encountered in reflection feedback may become proposals. The initial feedback-only template bank remains an ablation. This amendment was frozen after audit generation began but before audit outcomes were read. The expanded template bank is shared with its replay control; no new backbone fitting is performed.

## What would constitute success

Report all final case-order/backbone combinations with paired patient uncertainty; require simultaneous improvement in the three error endpoints, retention in multiple-system patients, real counterexample-bearing skills and completed appropriateness review. Also report errors on shared-drug joint fields: deleting an incorrect extra tuple is not the same as correcting a dose. No test checkpoint selection or favorable-stream selection is allowed.

The remaining discovery target is whether treatment intent and disease-specific evidence enable *productive* repairs rather than generic deletion. The present sparse event-prediction labels cannot alone establish clinically appropriate full prescriptions or causal prescribing mechanisms.

### Execution-level root trace

For the14 additional field-repair candidates,896 proposal-case checks yield787 unmet conditions,97 cases with the target drug absent from the draft, and12 actual tuple changes. All12 changes leave every primary reference-error count unchanged: execution occurred without correction. This is a measured failure of this bounded language, not proof that clinical field repair is impossible.
