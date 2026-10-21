# Conditional executable prescription memory: new-patient eICU study

This study tests the narrower, falsifiable part of the RxRSIAgent hypothesis: whether feedback can induce useful **conditional programs** over frozen tools. The learner is deterministic symbolic induction. It does not optimize backbone weights, generate new executable tool implementations, or establish recursive improvement of the learning algorithm itself.

## Execution

Run from the repository root. Preparation requires the credentialed local eICU files and frozen v25 training assets. Local actor inference requires MLX and the existing Qwen/Llama checkpoints. All case-level files stay in `dataset/restricted/prismatic-v52`; no patient records are sent to an external model.

1. `prepare.py`: lock the protocol; exclude all previously used v25 patients; sample one ICU stay per patient; build diagnosis-aware training retrieval and common joint-order catalogues.
2. `audit_contract.py`: verify patient isolation, input timestamps, source files and retrieval exclusion.
3. `actor.py --splits reflection proposal guard`: collect fixed Qwen predictions on development patients.
4. `learn.py --seed 52`, `learn.py --seed 152`, `learn.py --seed 52 --shuffle`: induce conditional procedural memories under two case orders and a shuffled-feedback control. `learn.py --backbone tool` is a diagnostic executable-tool control.
5. `freeze.py`: record state and implementation hashes before audit inference.
6. `actor.py --splits audit`, then `actor.py --model llama --splits audit`: run frozen actors on new patients.
7. `evaluate.py`: evaluate all frozen states, static controls, scope removal, transfer, endpoint intervals and restricted case studies.
8. `report.py`: generate bilingual results, figures and the in-place English manuscript section.

Run boundary tests with `python -m unittest discover -s upgrade_v52 -p 'test_*.py'`.

### Declared amendments and usable runtime

`learn_refined.py` separately tests componentwise counterexamples and persistent rejection memory, with each change ablated. Its state hashes were recorded before audit metrics, after audit actor generation began. `evaluate_refined.py` reports it without replacing the original study.

`runtime_decoder.py` preserves verified identifiers in complete JSON containing other unknown IDs and accepts a complete fenced JSON wrapper. Unknown IDs remain logged; truncated structures are never completed. `decoder_development.py` replays all development outputs and reruns gates consistently; `evaluate_decoder.py` applies the same decoder on audit and transfer. These engineering changes are separated from learned improvements.

For the usable compatible local interface, run `serve.py --model qwen --splits audit` with the MLX interpreter. It writes final orders and source receipts to the restricted `runtime/` directory. Because the learned memory increases audit omissions, it is **not enabled by default**. `--experimental-memory` reproduces it explicitly for research; `--model llama --experimental-memory` applies the same frozen Qwen memory. The runtime uses the existing generation cache and preserves every original study file. This is a research interface, not clinical deployment.

## What changes during learning?

Each retained card contains an observable `when` predicate, an optional executable `unless` predicate, an operator, a root hypothesis, the round/case count, support counts and empirically harmful exception counts. A root hypothesis is an error-associated repair proposal, not an established medical cause.

Four fixed tools support candidate recovery, unsupported-selection pruning, joint-field revision and prior-order reconciliation. Feedback chooses their scopes and exception clauses. Every actor starts with the same catalogue, diagnosis-aware retrieval counts and supervised predictive draft; acquiring access to these resources is not counted as learning. Hash-derived order IDs remain stable across arms. All new target drugs remain in the scoring denominator.

Acceptance requires strict reduction of summed reference discrepancies and nonincrease in each of missed drugs, extra drugs and complete joint-order errors on seen training, proposal and guard cases. At most three proposal-ranked candidates reach the guard per round. Repeated use of small gates can still overfit; the new-patient audit is not used to select a checkpoint.

## Task and endpoints

- ICU hour6 context → recorded orders entered in hours6–12, not a lifetime prescription list or discharge regimen.
- eICU HICL identity, route, dosage string and frequency string. Native4 is different from MIMIC Core4 and does not include all clinically required prescribing fields.
- Multi-system stratum: at least two clinical diagnosis categories recorded by hour6. This is not a validated phenotype of chronic multimorbidity.
- Reference-relative omissions, extras and complete-joint symmetric difference per patient are primary. Drug and joint F1, field coverage, empty/invalid output and nonzero-target strata are reported together.
- Historical orders can be renewed unchanged. `reconcile_prior` is therefore a falsifiable heuristic, not a clinical rule.

The [official diagnosis source contract](https://github.com/MIT-LCP/eicu-code/blob/main/website/content/eicutables/diagnosis.md) defines diagnosis entry offsets and warns that resolved/ruled-out status is unavailable. Discharge activity and diagnosis priority are excluded. Medication storage-time and full revision history remain unavailable.

## Limits

Fresh patients exclude all v25 members. Audit hospitals were previously development hospitals for different patients; they are not globally unseen institutions. No held-out clinical appropriateness scores, unrestricted drug generation, confirmed causal discoveries, or superiority over original medical-agent papers follow from this experiment. Development rejection and new-patient regressions are reportable outcomes, not reasons to silently relax the protocol.
