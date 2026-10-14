# Prior-case exposure and frozen test-subset analysis

## 1. Actual independent membership audit

Before current common-test inference, independently reconstructing **11 experiment families / 38 roles** identifies **69,839 prior or conservatively reserved patients**. Among the890 current test patients, **572** occur in this union; the frozen complementary subset retains **318 patients / 801 visits**. All visits of retained patients remain. The retained/prior intersection is zero.

The original all-patient main table remains unchanged. Exclusion uses identity/history only, never outcomes or predictions. The full and molecular panels use exactly the same patient subset. Every eligible repeated-visit patient in the source panel is already allocated (8,905/8,905); relabeling another existing split would not create new data.

| Recorded family | Patients overlapping the890 current test patients | Membership evidence |
|---|---:|---|
| v2_6h | 367 | Original deterministic sampler reconstructed; public per-role admission/patient counts match. No original membership hash was recorded. |
| v2_24h | 371 | Original deterministic sampler reconstructed; public per-role admission/patient counts match. No original membership hash was recorded. |
| v2_legacy_support | 138 | Original deterministic sampler; historical membership only, no legacy endpoint recomputed. |
| v3 | 323 | Original deterministic sampler; recorded role counts match. |
| v4_v5_v6 | 323 | Source cohort hash and original admission membership hashes match; v5/v6 use the same deterministic selection. |
| v7 | 178 | All original role membership hashes and patient counts match. |
| prepared_review | 36 | Read saved manifest; conservatively exclude despite no completed clinician ratings. |
| v9 | 20 | Exact saved local parameter-case patient membership; all listed roles excluded. |
| v15 | 20 | Exact saved local parameter-case patient membership; all listed roles excluded. |
| v21_v22_v23 | 50 | Stored source IDs reconstruct all original case membership hashes. |
| current_v27_v29_v30 | 0 | Current fitting/development membership included; reserved unexecuted test handled separately. |

Rows overlap and must not be added. Early deterministic samples have source/code hashes and matching counts but lack original membership digests; later samples match saved membership hashes or exact stored identities. Prepared reviewer cases are excluded conservatively even though clinician ratings were never obtained. This is bookkeeping, not a requirement for clinician review of GT metrics.

## 2. Scope and pending comparison

This registry covers the named PRISMATIC MIMIC-IV history. It does not establish absence from foundation-model pretraining, undocumented experiments or external use. Population-level source audits are distinct from model-exposure records. The subset is a registered prior-record-excluded sensitivity analysis, not proof of globally untouched confirmation or a new external dataset. Composition differences between retained and excluded patients cannot be interpreted as a causal effect of exposure.

**Performance results remain pending.** After both common-test audits pass, the evaluator regrades their exact immutable predictions on the retained and excluded groups, reporting every selected method with seed variation and descriptive patient-cluster intervals. No new fitting, API call or checkpoint selection occurs.

[Registered protocol](prior_case_exclusion_protocol.json) · [Registry aggregates](exposure_registry.json) · [Independent membership audit](exposure_registry_audit.json)
