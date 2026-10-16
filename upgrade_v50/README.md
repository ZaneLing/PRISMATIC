# RxRSIAgent: corrected local prescription experiment

The previous literal-example interface is diagnosed in `../upgrade_v49/results/schema_probe.json`. On the same 48 training cases, changing only example identifiers shifts selection of A23 from 5 to 46 cases. **All common local actors now receive descriptive schemas with no example action identifiers. This common engineering repair is not credited as RSI.**

## Executed task

At admission +6 hours, predict the complete set of recorded new/change orders in hours 6–12. The coherent-time, nonempty-target cohort requires complete 12-hour follow-up, provider and pharmacy entry timestamps in the target window, and verification by its end; ambiguous admissions are excluded. It does not represent all admissions, and released field-version histories are incomplete. The [source reconstruction audit](../upgrade_v21/results/independent_cohort_audit.json) applies to the unchanged source cases. The 1,082-admission, 1,024-patient evaluation cohort, 24-candidate catalogue and 128-name vocabulary are unchanged. A shared supervised tool trained on 40,000 admissions supplies joint drug/route/dose/unit/frequency templates. Targets outside the catalogue remain in recall. This is catalogue-constrained order forecasting, not unrestricted prescribing or the whole hospital-stay regimen.

## Learning and comparison

- Six rounds process 144 different training admissions (source positions 144:288), after 144 earlier admissions informed development. Proposal/guard subsets reuse 48/64 cases.
- The local reflector sees actual training inputs, reference discrepancies, intermediate decisions, checks and label evidence, plus rejected-edit outcomes. It may decline to edit. Best-scoring replay cases are explicitly not assumed completely correct.
- Candidate updates contain an observable condition, procedure, counterexample and selected/all-observed fact scope. Up to two simple observable conditions may be conjoined. Numeric dose rules and copied reference-dependent actions are rejected. Natural-language counterexamples are not formally certified clinical exclusions.
- Retention requires a strictly higher proposal drug/Core4 composite, with neither guard endpoint lower. All states freeze before corrected-interface test inference. Previous literal-interface test scores have already been observed, so the benchmark is exploratory rather than pristine.
- Current primary controls: Direct self-refinement, a limited independent SafeRx-Agent specialty/supportive/critic adaptation, and the pinned SkeMex author memory core with a common actor. They share Qwen3-4B, cases, catalogue, label resource and 128+128+96 maximum output tokens. Actual input use, offline computation and validation supervision differ.
- FLAME separately transfers the actual released trained list policy, including all 224 merged adapter layers, with a fixed supervised top-8 initializer. Its full classifier and collaborative embeddings are not reproduced. Source scores remain separate in `published_reference_scores.json`.
- Transfer freezes the learned state on Llama-3.2-3B, without model-specific selection. Component and catalogue-permutation diagnostics use a fixed 128-case subset with controlled fresh batch layouts.

## Run

```bash
../upgrade_v2/.venv/bin/python upgrade_v50/prepare.py
../upgrade_v2/.venv-llm/bin/python upgrade_v50/learn.py
../upgrade_v2/.venv-llm/bin/python upgrade_v50/run_suite.py
```

Local model files and pinned author resources from the preceding setup must exist. The runtime is MLX on Apple Silicon. `run_suite.py` waits for the private frozen state before testing and stops explicitly on stage failure. All row-level cases, model-generated reflection text, skill stores and executable learned-state text stay in the restricted local directory. Public state files expose hashes, observable condition categories and module counts, not automatically copied clinical traces.

**Incremental paid model API expenditure remains USD 0 of the USD 10 cap.** Patient inference, reflection and semantic embeddings are local. Downloaded public checkpoints do not invoke paid inference. Local compute is not monetized. No patient data are sent to OpenRouter.

Source pins: SkeMex `a640474590e384669dd71b657c441264beef73d2`; FLAME `642500e5a48e64c1a888ceb0e8d450ea285776ae`; FLAME weights `2dbdc8d5c31ab320e57b9e6b1a07683301b44dfc`.
