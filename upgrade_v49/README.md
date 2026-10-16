# RxRSIAgent: local full-window prescription experiment

This directory executes a **new prescription-task adaptation**. The frozen public-QA agent is preserved in `rxrsiagent/`; its published DeepSeek scores are not relabeled as MIMIC scores.

## Task and output contract

At admission +6 hours, predict the whole set of new/change orders recorded during hours 6–12. This is not the whole hospital-stay regimen. Inputs are the existing timestamp-audited demographics, prior orders and blood laboratories. Current discharge diagnoses, future tests and targets are hidden from inference.

A frozen, supervised 40,000-admission candidate tool proposes 24 drug/order templates from the original 128-name vocabulary. All actors receive the same alphabetized catalogue; gold outside it remains in all recall denominators. Selecting multiple catalogue IDs compiles joint drug, route, dose, unit and frequency values. This is **catalogue-constrained structured order prediction**, not unconstrained clinical prescribing. Unknown frequency, indication, duration, infusion purpose and rate are not invented.

## Execution

Run from the repository root, with the local Python environments already installed:

```bash
../upgrade_v2/.venv/bin/python upgrade_v49/prepare.py
../upgrade_v2/.venv-llm/bin/python upgrade_v49/experiment.py --stage learn
../upgrade_v2/.venv/bin/python upgrade_v49/prepare_more_training.py
../upgrade_v2/.venv-llm/bin/python upgrade_v49/learn_scope.py
../upgrade_v2/.venv-llm/bin/python upgrade_v49/run_final_suite.py --model qwen
../upgrade_v2/.venv-llm/bin/python upgrade_v49/skemex_adapter.py
../upgrade_v2/.venv-llm/bin/python upgrade_v49/run_final_suite.py --model llama
../upgrade_v2/.venv-llm/bin/python upgrade_v49/trajectory_eval.py
../upgrade_v2/.venv/bin/python upgrade_v49/prepare_flame_seed.py
../upgrade_v2/.venv-llm/bin/python upgrade_v49/convert_flame.py
../upgrade_v2/.venv-llm/bin/python upgrade_v49/flame_adapter.py
../upgrade_v2/.venv-llm/bin/python upgrade_v49/evidence_ablation.py
../upgrade_v2/.venv/bin/python upgrade_v49/audit_results.py
```

Model files and restricted source data must already be present. `convert_flame.py` requires every released list-model shard and adapter. A missing dependency must fail explicitly; do not replace it with an untrained prompt.

## Inference and adaptation

1. Select observed fact IDs; each resolves to exact source text.
2. Retrieve up to two complete sentences from offline product labels, preserving source ID, section and route metadata. Exact product-name coverage is reported. Retrieval does not establish patient applicability.
3. Assess candidate orders and compile the final selected IDs into structured fields. Invalid IDs cannot discard valid selections; malformed output has no hidden prevalence fallback.
4. Observe 24 new training cases per round, for three rounds. Up to 12 discrepant cases per round are shown to the local reflector. It proposes one procedural rule with an explicit observable condition and counterexample.
5. Evaluate the candidate on 48 proposal and 64 guard cases. Retain only if the proposal composite improves and neither guard drug F1 nor guard Core4 F1 decreases.
6. Freeze every retained state before testing. Transfer the frozen memory to Llama 3.2 3B without tuning it on that model.

The first trajectory updates procedural memory. After it retains no rules, an instrumented extension adds 72 different training cases and a model-selectable, bounded verifier scope (`selected` versus `all_observed`). The reflector sees mechanically derived complete-trace profiles with drug identities and literal target prescriptions withheld. Its researcher-designed interface is not autonomous tool invention. See `scope_protocol.json`. LLM weights, vocabulary, candidate ranker, order templates and executable evidence code remain fixed within each trajectory. Researcher protocol repairs are separate from accepted state changes. Memory growth without held-out improvement is not successful RSI.

## Comparator identity

| Row | What is actually executed | Boundary |
|---|---|---|
| Direct self-refinement | Same local model, catalogue, label tool and three calls | Local control |
| SafeRx-Agent task adaptation | Independent grouped specialty/supportive proposal, critic and final adjudication | No author package; the source ICD/MEDI routing and ATC safety matrices are unavailable in this time-controlled task; not a full reproduction |
| SkeMex memory-core adaptation | Pinned author encoder, store, utility update, governance and retrieval; common local prescription actor; all 144 training cases | Local MiniLM semantic embeddings with full-text chunk pooling, fixed task category, no web/ReAct tool loop; not the complete author benchmark |
| FLAME released list-policy transfer | Actual released SFT model + GRPO LoRA merged, then 4-bit quantized; author add/remove prompts | Full FLAME classifier and collaborative embeddings are not reproduced; separate backbone/training/initializer, so report separately |

The three-call local controls permit 128+128+96 output tokens per case. Actual token use, memory-training compute and tool inputs are not automatically equal. The FLAME component has extra initializer information and is not an equal-information comparison.

## Integrity, costs and interpretation

- Incremental external API cap: **USD 10**. These local experiments issue **zero external patient requests and zero paid model requests**. Downloads are public model artifacts; local compute is not monetized.
- Every row-level case, target, model completion, error trace, skill store and prediction stays under the local restricted `prismatic-v49` directory. Only aggregates, source pins and code enter GitHub.
- The 1,082-case test was previously used by supervised studies. New-method results are exploratory; it is not a pristine untouched benchmark.
- GT prescriptions record actions. They do not expose complete clinical reasoning, establish the uniquely correct regimen, or turn every extra into an unsafe medication.
- Core5 scores include only complete observed tuples, with the reference-field coverage reported alongside them. No saline-presence F1 is used.
- DDI, allergy, renal-dose and clinical appropriateness claims require supporting patient information and a validated checker. This experiment does not establish them.
- Source pins: SkeMex `a640474590e384669dd71b657c441264beef73d2`; FLAME code `642500e5a48e64c1a888ceb0e8d450ea285776ae`; FLAME weights `2dbdc8d5c31ab320e57b9e6b1a07683301b44dfc`; Llama weights `7f0dc925e0d0afb0322d96f9255cfddf2ba5636e`.

## Confirmed development finding

The initial output protocol produced valid final JSON but zero parseable intermediate assessments and zero verified fact cases on 48 proposal examples. Its drug/Core4 F1 was 9.59%/4.26%. Fact IDs, concise intermediate schemas and conversational state reuse repair the engineering contract. Whether they improve prescription agreement is measured separately; syntactic repair must not be presented as a clinical gain.

A training-only observability audit finds 1,722 of 40,000 admissions in 144 groups with identical visible contexts but differing target drug sets. Missing observations and treatment variation can therefore contribute to disagreement. This does not prove that all errors are unavoidable or identify a neural mechanism.
