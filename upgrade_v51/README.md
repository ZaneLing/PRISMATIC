# RxRSIAgent: executable failure-driven repair pilot

This study repairs four implementation failures of the prior frozen updater. It is an exploratory pilot, not a replacement full-benchmark score or proof of clinical safety.

## What changes

1. **Action space:** the updater can choose a 48-drug classifier candidate list or a training-case retrieval expansion beyond the fixed 128-name vocabulary; choose source-route filtering, distinct-drug evidence, all-observed fact checking, temporal reconciliation, or access to the already frozen classifier draft. Generated procedural text accompanies a typed executable operator.
2. **No-op rejection:** an applicable rule must change the actual candidate set, evidence spans, fact checking, or temporal-review prompt. It must then change at least one training output before development evaluation. A changed prompt alone does not establish benefit.
3. **Validation:** numeric observations in counterexamples are separate from operative instructions. `unless` scopes execute as exclusions; case-ID references are rejected. This is a syntactic/protocol validator, not a complete clinical appropriateness checker.
4. **Reflection:** every seen training case contributes to cumulative stage-error counts and overlapping observable-context groups. Six distinct stage-stratified examples support the summary. All acceptance/rejection records remain in the next reflection prompt; accepted skills persist across rounds.

The backbone and the joint dose/route/frequency templates remain frozen. The agent selects and configures researcher-implemented tools; it does not invent tool code. No per-drug supervised output calibrator is added. The classifier, retrieval records and order templates are nevertheless supervised resources from 40,000 training admissions, shared across states. We distinguish bounded agent skill/configuration learning from weight training and from fully autonomous code evolution.

## Context groups and disease categories

Current inputs contain demographics, prior orders and timestamp-available blood tests. They do not contain verified decision-time diagnoses. The optional `disease_memory.py` contract accepts explicitly documented pre-decision problem categories with availability times, permits multiple categories, and excludes future, untimed, and merely suspected entries. It does not map ICD codes or infer diagnoses. On this cohort, routing therefore uses observed renal, glucose/electrolyte, hematology, liver and blood-gas laboratory groups; one case can belong to several. These labels describe available measurements, not diagnoses or confirmed organ dysfunction. A prior drug is not converted into a disease label; discharge ICD codes are not used as runtime inputs. Disease-specific efficacy remains untested until contemporaneous diagnoses are available.

## Causal-contract correction

An interrupted first attempt is preserved under the restricted `attempt1` directory, with aggregate outcomes in `results/attempt1`. Before any audit inference, we found that the reflector repeatedly attributed excluded candidates to insufficient fact checking. The amended learner enforces root/operator compatibility and prioritizes candidate omission before downstream selection. Unchecked-fact counts are process observations, not prescription-error counts. All inputs were already visible to the LLM. The ranked-draft tool exposes an existing frozen predictor; it is not a newly trained calibrator. Training agreement must improve before spending development evaluations. This is documented iterative development, not a claim of an untouched preregistered experiment.

## Protocol

- 72 further training admissions: three rounds of 24, source positions 288–359.
- 24 proposal and 32 guard admissions, disjoint patients from training and audit.
- 48 fixed audit admissions, frozen before inference; historically exposed benchmark, not a pristine confirmatory test.
- Candidate reachability was diagnostically counted before learning. No audit actor score selects a state.
- At most two LLM-proposed skills per round; one schema-repair attempt each.
- Retain only strict proposal average(drug F1, Core4 F1) improvement with neither guard endpoint decreasing.
- After learning: evaluate each unique retained state, a fixed manual repair bundle, and initial/final cross-model transfer to Llama-3.2-3B.
- All actors use three calls with 128/128/96 output-token caps; wider catalogues increase input tokens. Equal output allowance is not equal input cost.
- Existing full 1,082-admission scores remain unchanged.

## Data and privacy

All patient rows, generated skills and raw model traces stay under:

`/Users/bytedance/Desktop/MedTreeBench/dataset/restricted/prismatic-v51`

Only aggregate metrics, structural state descriptions and artifact hashes are published. The stronger proposer uses OpenRouter with a strict USD 10 cumulative cap and a USD 0.25 reservation per request. Only anonymous aggregate counts and typed configuration metadata are transmitted; no patient rows, drug names or clinical values are sent. Actual receipt cost is in results/cost.json. Local inference has no API charge; local hardware time is not priced.

## Reproduce locally

Run from the repository root with the existing environments:

```bash
/Users/bytedance/Desktop/PRISMATIC/upgrade_v2/.venv/bin/python upgrade_v51/prepare.py
/Users/bytedance/Desktop/PRISMATIC/upgrade_v2/.venv-llm/bin/python -m unittest discover -s upgrade_v51 -p 'test_*.py' -v
/Users/bytedance/Desktop/PRISMATIC/upgrade_v2/.venv-llm/bin/python upgrade_v51/learn.py
/Users/bytedance/Desktop/PRISMATIC/upgrade_v2/.venv-llm/bin/python upgrade_v51/cloud_learn.py
/Users/bytedance/Desktop/PRISMATIC/upgrade_v2/.venv-llm/bin/python upgrade_v51/cloud_evaluate.py
/Users/bytedance/Desktop/PRISMATIC/upgrade_v2/.venv-llm/bin/python upgrade_v51/decoder_replay.py
/Users/bytedance/Desktop/PRISMATIC/upgrade_v2/.venv-llm/bin/python upgrade_v51/mechanism_audit.py
/Users/bytedance/Desktop/PRISMATIC/upgrade_v2/.venv-llm/bin/python upgrade_v51/final_case_studies.py
/Users/bytedance/Desktop/PRISMATIC/upgrade_v2/.venv/bin/python upgrade_v51/make_figures.py
/Users/bytedance/Desktop/PRISMATIC/upgrade_v2/.venv-llm/bin/python upgrade_v51/report.py
```

Execution caches include complete case content and implementation hashes. MLX greedy generation can depend on batching; keep the same chunks and preserve receipts. Cumulative error counts describe errors when each case was encountered, not repeated rescoring under the final state.

The local-proposer trajectory is retained in `results/trajectory.json`; the stronger aggregate-proposer trajectory and controls are in `results/cloud/`. They reuse the same 72 training admissions. Generated skill text remains restricted. For the current case report, run `case_studies` with `common.PRIVATE` set to its `cloud` subdirectory before importing the module.

The stronger proposer receives aggregates while the local proposer also receives private representative traces. Model identity and feedback granularity therefore change together; this is a workflow comparison, not an isolated model ablation. The static ranked-draft-only control and no-LLM top-eight tool control distinguish predictive-tool access from learned conditional use.

Candidate variants retain the existing list-local alphabetical identifier scheme: expansion can also renumber old candidates and change evidence tie-breaking. These are whole-workflow interventions; a score difference does not isolate recall from ordering effects or establish absence of drug-name/position shortcuts.

Schema amendment: root/operator compatibility is checked on typed fields; prose may compare different failure stages without rejection. A response containing exactly one wrapped proposal is normalized without rewriting its contents. An interrupted cloud audit and all original schema failures are preserved privately. The corrected third-round proposal is actually evaluated. Frozen local proposals are replayed with `RXRSI_REFLECTION_REPLAY` solely to verify implementation parity, not as extra learning data. See `schema_amendment.json`.

## Complete-array output compatibility

Final inspection found five complete identifier arrays incorrectly treated as empty predictions. `order_decoder.decode` and `run_with_compatible_output` accept only complete JSON arrays of known catalogue identifiers, without completing truncated text or selecting new drugs. The explicit runtime adapter applies to any supported method. `decoder_replay.py` applies this same repair to all frozen states and controls without new model calls. Original gates and original scores remain preserved; compatible scores are a separate post hoc engineering result, not added RSI learning. Restoring these predictions lowers final Qwen F1 from 16.96% to 16.10% because they contain no new GT hits. Future learning must use one decoder consistently from training through audit.
