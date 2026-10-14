# v0.25 — Native-code eICU methods, held-out hospitals and feedback controls

## Question and cohort

Evaluate prescription methods and feedback mechanisms on the external eICU dataset. Keep the v0.24 hospital partitions and cross-partition patient exclusions: no hospital or patient crosses partitions. Models train within eICU and test on unseen hospitals; this is not zero-shot transfer of a MIMIC model.

The decision is ICU admission plus six hours, predicting newly documented orders in the next six hours. Labels are native HICL codes, without claiming RxNorm, ATC or ingredient equivalence. Exclude an entire stay if any target lacks a valid HICL code; retain zero-target stays. From 142,485 parent-cohort stays, 8,003 fail target-identity completeness, leaving 134,482 before fixed hash sampling. This retrospective label/documentation selection does not represent all clinical stays.

| Split | Stays | Patients | Hospitals | Zero-target stays | Complete / all joint targets |
|---|---:|---:|---:|---:|---:|
| train | 40,000 | 35,249 | 124 | 19,105 | 52,637 / 70,277 |
| proposal | 2,000 | 1,914 | 13 | 820 | 3,105 / 4,523 |
| guard | 2,000 | 1,912 | 17 | 1,001 | 2,564 / 3,398 |
| test | 8,005 | 6,227 | 16 | 3,842 | 11,853 / 15,594 |

## Inputs, order protocol and methods

Inputs contain age decade/gender, the latest 24 early medication records and 32 distinct finite lab-name/unit measurements. Lab draw and revision timestamps must precede the decision. Hospital/patient IDs, future orders, cancellation/discharge status and untimed diagnoses are excluded. Medication storage times and full field histories are absent, so actual prospective availability is not proven.

The complete order tuple is HICL, route, dosage string and frequency string. Normalize case/whitespace only, without inferring dose units. Missing values remain null. Drug recall includes out-of-vocabulary GT; joint-order metrics score complete observed labels with coverage reported separately.

Three seeds run five rounds of 8k/16k/24k/32k/40k stays. Vocabulary (512 codes) and word/character/numerical maps freeze on the initial 8k. The three feedback arms have identical cases, order and exactly 60 epochs per classifier. Compare uniform learning, priorities from the prior accepted policy's own errors, and the exact same weights shuffled among the new cases. Tools fit only currently seen orders. Proposal selects thresholds; a separate guard promotes states. Rejected versions retain the previous policy/tool bundle. Every seed and static selection freezes before test-feature inference.

Changing artifacts are policy parameters, persistent feedback weights and order-tool parameters. No LLM/API is used; this is supervised artifact evolution. Static controls include prevalence, prior-order reuse, 30-neighbor retrieval, word models, word/character ensembles and full-data uniform learning. Extra ensemble fit/search budgets are disclosed; matched-arm contrasts isolate priority assignment. Component ablations do not retune other components.

## Completed development trajectory replay

All 45 policy/tool states are reexecuted, with independent checks of proposal thresholds, guard metrics and acceptance decisions. Raw and accepted curves are separate; these cases participate in development selection and are not a held-out test result.

[Development curves and every feedback control](DEVELOPMENT_CURVES.en.md)

## Execution status

All three seeds and static-control choices are frozen. The original queue is executing the unified 8,005-stay held-out hospital test and independent audit. The final method table waits for completion of all results and checks; the development curves above do not replace it.

## Reproducibility and scope

`protocol.json`, `results/cohort_manifest.json`, `results/cohort_audit.json` and round journals record the protocol, membership counts and transitions. Restricted cases, predictions and weights remain local. Agreement with recorded GT does not establish clinical safety. This native-code/field protocol cannot be ranked directly against published ATC scores.
