# PRISMATIC v4 executed development protocol

Protocol `v4-development-20261014-r1` is frozen for these runs; it is not prospective registration or final confirmation. See [machine configuration](protocol.json), [order schema](order_schema.json), and [detailed Chinese protocol](PROTOCOL.md).

## Timing and population

The decision point is admission during the ED stay. The primary admission-proxy view contains chief complaint, acuity and home medication charted by admission. Triage has no per-row timestamp and medrecon lacks storetime, so their entry availability is not fully verifiable. The executed sensitivities use home medications only and no patient text; neither proves absence of leakage.

New laboratory extraction requires the same admission ID, a numeric result in the previous 24 hours, and both charttime and storetime no later than admission. Retain the latest per analyte; exclude missing admission links instead of guessing across encounters. These labs are not added post hoc to the frozen method comparison.

Retain all 201,750 eligible admissions and the original patient-disjoint hash split. The deterministic 40k/4k/4k sample is unchanged. Results are developmental because this test has been inspected; a separate confirmatory split remains outstanding.

## Mapping and unknown targets

Normalize raw and dictionary NDCs to unambiguous 11-digit forms. Reject ambiguous mappings. Train GSN/name fallbacks on exactly the sampled 40,000 training admissions, with support at least 10 and purity at least 98%. Smaller growth checkpoints must rebuild fallbacks or use a fixed external dictionary.

Retain raw/mapped counts and mapping provenance. Preserve unmapped names, formulation, concentration and route with unknown normalized ingredient IDs. ATC-L4 is not an ingredient or formulation identifier. Report no recorded order, unmapped-only orders and mapped-label cases separately.

The main engineering measure is all-case observed-label overlap, with a separate mapped-label-only sensitivity. Empty labels are not clinical negatives, and the conditional sensitivity is selected on future label availability. Neither unmatched predictions nor unrecorded orders determine clinical error. Saline name proxies remain separate from ATC targets; never infer fluid purpose from a name.

## Complete order contract

Each order records drug name, ingredient ID, formulation, concentration, ATC class, dose/value/unit, route, frequency, duration, indication, patient evidence and uncertainty. Fluids also require purpose, volume, rate and reassessment. Unknowns are explicit nulls with uncertainty; no default clinical values are inserted. Preserve textual/range source doses rather than falsely converting them to scalars.

Evidence references identify this patient's E1/E2/E3 fields; retrieved training cases are not patient evidence. Reference existence does not establish clinical entailment. Check missing fields, invalid numerics, duplicate ingredients, invented references and incomplete fluid information. Preserve the original draft and at most one revision.

Output status is abstained, needs_information or needs_clinical_review. No status authorizes administration. Missing ingredient-level DDI/renal knowledge always remains unknown. Report raw complete-schema validity separately from normalization that fills nulls. Clinical dose, fluid-purpose/rate and renal correctness await independent reviewers.

Normalization revision r2 retains wrongly formatted/granular ATC strings in uncertainty and sets the normalized field to null, without guessing by truncation. Preserve original r1 failures and distinguish normalized parseability from raw model validity.

## Methods and budgets

All 4,000 development admissions: prevalence, 30-neighbor retrieval, TF-IDF/SGD with seeds 17/42/73; top-80 training ATC-L4 classes and five outputs per case. Recall retains all mapped targets. Cases and task are shared, not training compute.

The independent GAMENet adaptation retains the author's graph and readout code but substitutes two text-token channels for diagnosis/procedure codes and uses a single visit. Thus longitudinal dynamic-memory reading is absent. Use three seeds, five epochs and validation-only checkpoint selection. Check batched forward equivalence against author code. A real TWOSIDES research graph has disclosed coverage; the input, training objective/schedule and all-pair graph differ from the original paper. This is not faithful reproduction.

The nested 50-case comparison holds local Qwen3-4B weights and temperature fixed across direct, ordinary repeat, training-case RAG and bounded harness. Repeat shares direct's first response; harness shares RAG's first response. Each call has a 192-token output cap; repeat and harness each use two calls. Retrieval increases input tokens, so total token/cost budgets are not identical. Report actual usage. Invalid outputs count as empty predictions in all-case denominators.

A separate ten-case order probe allows at most two orders and 640 output tokens per call. Compare one draft against one retrieval-informed revision; this is a structural probe, not a matched-call causal experiment.

## Interpretation and reproducibility

The class-level TWOSIDES graph is not a clinical rule base and an absent edge does not establish safety. Bundled SafeDrug molecules use ATC-L3, not the required ATC-L4. SafeRx-Agent requires compatible diagnosis/procedure, routing and knowledge inputs. Unavailable comparable results remain blank.

Publish code and aggregate metrics. Keep case-level inputs, predictions, weights and review cards local under the restricted directory. New methods or protocol revisions get new run IDs; negative results are retained. See [actual results](RESULTS.en.md) for execution records and reproduction commands.
