# Clinical appropriateness and skill review

Predicting recorded future orders and assessing clinically appropriate treatment are separate endpoints. A recorded order may depend on information arriving after the decision cutoff. Reference disagreement alone is not a clinical error.

The research rubric is informed by the [WHO prescribing teaching framework](https://iris.who.int/handle/10665/67010) and the [original Medication Appropriateness Index](https://doi.org/10.1016/0895-4356(92)90144-C). It is an adaptation, not a validated MAI total score.

## Independent blinded review

- Two reviewers receive the same32 patients, hash-sampled within one-system and multiple-system strata (16 each), without outcome-based selection.
- Phase1: identify treatment goals, necessary new/changed actions and missing information from the hour6 context before inspecting candidate plans.
- Phase2: rate independently randomized anonymous plans from the fixed agent, the first prespecified RxRSIAgent stream, the supervised tool and recorded future orders. Identical sets are deduplicated. The source key is withheld.
- Rate indication, effectiveness, dose, route, frequency, duration, drug–drug and drug–disease interactions, organ-function adjustment, duplication, monitoring and administration feasibility. Use appropriate/marginal/inappropriate/unknown/not_applicable, with severity and evidence.
- Record omitted necessary actions and unsupported actions separately. Report assessable denominators and unknown rates; unknown is never a pass.
- Preserve both initial ratings. Jointly review major/critical disagreements; retain unresolved disagreements. Report raw agreement and weighted kappa when applicable, separately from consensus.

## Skill audit

Review every unique rule for clinical linkage between its diagnosis predicate and the affected medication, forecasting-versus-treatment meaning, empirical counterexamples, missing exclusions, and source support. An empty exception clause is not evidence that exceptions are unnecessary. Do not infer clinical validity from benchmark improvement.

Restricted files are in `prismatic-v53/review/`: `reviewer_A.json`, `reviewer_B.json`, `skills_to_review.json`. Complete null fields without changing identifiers. Keep `BLINDING_KEY_DO_NOT_SHARE.json` away from reviewers. No annotations have been supplied; clinical appropriateness remains unassessed. Fixed label checks are partial screening only.
