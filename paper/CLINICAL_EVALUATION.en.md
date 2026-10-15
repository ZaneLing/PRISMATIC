# Clinician-oriented evaluation of RxRSIAgent prescriptions

Updated 2026-10-15. **Status: protocol and aggregation software implemented; clinician annotations unavailable.** These endpoints complement reference F1 and QA accuracy. Software tests are not clinical measurements.

[中文](CLINICAL_EVALUATION.zh.md) · [Manuscript](latex/v0.3/prismatic_v03_en.tex) · [Machine-readable protocol](../rxrsiagent/clinical_evaluation_protocol.json) · [Blank annotation template](../rxrsiagent/clinical_review_template.json)

## Motivation and primary endpoints

Reference overlap does not establish that patient needs are addressed, orders are executable, unnecessary treatment is avoided, or monitoring and escalation are appropriate. Multiple regimens may be acceptable. We draw on structured medication review and the Medication Appropriateness Index, without claiming our rubric is a validated MAI variant. [NICE NG5](https://www.nice.org.uk/guidance/ng5/chapter/Recommendations), [Hanlon et al.,1992](https://pubmed.ncbi.nlm.nih.gov/1474400/)

| Primary endpoint | Operational definition | Required companion |
|---|---|---|
| **Treatment-goal coverage** ↑ | Satisfied predeclared clinical requirements / applicable requirements; critical needs reported separately | Assessment coverage and unresolved requirements |
| **Major-error case rate** ↓ | Cases with at least one adjudicated serious/potentially life-threatening error / cases with determined major-error status | Unknown status, action coverage and error categories |
| **Joint clinically correct order rate** ↑ | Generated orders with every applicable clinical field correct / assessed generated orders | Goal coverage, order counts and field-level errors |

Patient requirements and acceptable alternatives are established before reviewers see anonymized outputs. Correct withholding or escalation can satisfy a predeclared requirement. Product-specific order checks are instantiated from predefined rules after the output inventory is fixed. Rules cannot change after comparing methods.

## Secondary endpoints

1. **Unnecessary-medication rate:** unjustified or inappropriate duplicate orders / assessed generated orders; report medications per case.
2. **Required-field completeness:** present applicable fields / required fields, separate from clinical correctness of ingredient, dose, unit, route, frequency and duration.
3. **Constraint handling:** sensitivity, precision, missed hazards and false alerts against adjudicated actionable risks; stratify allergy, DDI, renal/hepatic adjustment and population restrictions.
4. **Adjunct and infusion adequacy:** justified purpose and correct applicable compatibility, diluent, volume, concentration and rate. No saline-presence F1 endpoint.
5. **Monitoring coverage:** required observations, follow-up times and action criteria addressed.
6. **Applicable-evidence support:** clinically material claims supported by the cited source for the relevant product, population and time; excerpt availability is separate.
7. **Appropriate disposition:** prescribe, renew, withhold, request information or escalate; pair with action and unknown rates.
8. **Medication reconciliation:** correct continue/start/change/stop handling, including relevant OTC products.
9. **Patient feasibility:** administration ability, access, preferences and treatment goals.
10. **Clinician edit burden:** number/type of corrections and time to an acceptable draft, with medians and dispersion.
11. **Operational resources:** calls, tokens, monetary cost, latency and invalid/absent outputs under matched budgets.

Proposed severity categories are0: no identified error within assessed scope;1: minor documentation/clarity issue;2: clinically relevant correction without expected serious harm;3: potential serious harm;4: potential life-threatening harm. Unknown is separate from0. These are potential prescribing errors, not observed patient outcomes.

## Denominators and analysis

Report applicable/rated/passed/failed/unknown counts and assessment coverage with every score. Patient/case macro estimates are primary, with opportunity-level aggregates alongside them and patient clustering for repeated visits. Missing assessments are neither failures nor successes; additionally report confirmed-success lower bounds over all applicable requirements. Non-applicable items are excluded, and zero denominators produce NA. Empty outputs cannot earn perfect order quality, and unknown interaction/rule coverage cannot become safety clearance.

Use paired cases, patient bootstrap intervals, binary agreement and severity-weighted kappa. Confirmatory tests of the three primary endpoints require preregistered multiplicity handling; secondary analyses remain exploratory. Avoid a single weighted quality score that hides trade-offs.

## Dataset and case boundaries

The planned complete-order review uses **MIMIC-IV3.1** contexts reconstructed from recorded information availability at a declared decision time. Target orders and later facts are excluded from actor inputs. The roster is not yet sampled: check patients against historical exposure and freeze membership before scoring; any reused cases remain exploratory. Existing [availability records](../upgrade_v20/RESULTS.en.md) and the [exposure audit](EXPOSURE.en.md) support reconstruction.

This task is separate from the RxSafeBench/RxQA option-selection main table. QA labels do not supply full-order clinical judgments. Any later eICU external-hospital review needs its own context and annotation-coverage protocol; its scores are not pooled with MIMIC or QA.

## Two-reviewer protocol

Two qualified reviewers with authorized local data access are already available; their annotations are pending.

- Twenty calibration cases are excluded from final evaluation.
- Target100 randomly sampled eligible patients and a separate50-case input-defined risk challenge cohort. Record exclusions and unassessable cases before judging outputs; do not remove model failures. Report cohorts separately. These are planning targets, not a statistical power claim.
- Compare RxRSIAgent, a frozen skill/tool control and two runnable external agents chosen on development data. Four configurations yield150×4×2=1,200 independent ratings.
- Hide method/checkpoint names, normalize output presentation and randomize/counterbalance order. Review independently before discussion; retain original ratings and unresolved disagreements.
- Keep clinical selection data separate from final evaluation. Test ratings never become training feedback. Restricted records, predictions and identity mappings remain local; publish templates, code, aggregates and hashes only.

## Implemented aggregation

[clinical_metrics.py](../rxrsiagent/clinical_metrics.py) aggregates adjudicated requirement ratings, major-error labels and unnecessary-order labels. It verifies case/order inventories and rejects the blank template until its status is adjudicated. It does not infer clinical labels. [Seven synthetic tests](../rxrsiagent/results/clinical_metric_checks.json) cover omissions, missing reviews, empty orders, unknown critical items, inventory mismatches, non-applicability and incomplete annotation status.

The current utility does not compute hazard matching, edit times, kappa or confidence intervals; these require actual annotations and subsequent analysis.

```bash
python -m rxrsiagent.clinical_metrics local_adjudicated_ratings.json local_summary.json
```

## Evolution evaluation

Apply the same frozen endpoint definitions to every checkpoint. Record proposal cases, changed objects, sources, acceptance decisions and regressions. Isolate modules by replacing one state at a time while holding others fixed, and compare fixed memory, ordinary feedback and shuffled feedback under equal experience and budgets. Clinical development feedback may guide selection; final clinical ratings may not. Current completed learning trajectories concern language skills; researcher tool repairs are not autonomous tool evolution.
