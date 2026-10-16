# RxRSIAgent: completed evidence, calibration and matched-output experiments

Updated 16 October 2026. Versioned evidence: v35 main experiment and v36 independent follow-up. Method name remains **RxRSIAgent**. [English ACL source](../paper/latex/v0.3/prismatic_v03_en.tex).

## 1. Findings

- Selected RxRSIAgent: **556/988 (56.28%) RxSafeBench;199/300 (66.33%) RxQA**.
- Relative to the prior retained agent501/988 and183/300: **+5.57 and+5.33 percentage points**. These are historical descriptive changes, not a causal matched-budget ablation.
- RxSafe exceeds matched-output GRASP495/988 by6.17pp, paired scenario-bootstrap95% interval[2.84,9.63]. It exceeds earlier GRASP502/988 descriptively by5.47pp.
- RxQA remains below matched-output MedAgents200/300 by0.33pp and higher-allowance MedAgents208/300 by3.00pp. The latter paired interval is[-8.33,+2.33]pp. **The two-benchmark superiority target is not achieved.**
- Gains come from ordinary supervised calibration, not proven autonomous skill evolution. Strong identity-only controls expose a shortcut risk.

## 2. Main table: other methods on the same questions

Same served model `deepseek/deepseek-v4.1-flash`. Each row permits4608 generated output tokens/case. Author adapters preserve their workflow within an80-call ceiling; RxRSIAgent uses3×1536 and GRASP one call. **Equal output allowance does not equal input cost, training supervision or number of calls.** MedAgents/MDAgents are task-adapted author workflows; GRASP uses the pinned author core and previously selected skill. These are executed local results, not imported paper scores.

| Method | RxSafeBench derived test | RxQA OpenFDA | Mean calls S/Q | Invalid S/Q |
|---|---:|---:|---:|---:|
| GRASP | 495/988 (50.10%) | 185/300 (61.67%) | 1.00 / 1.00 | 0 / 0 |
| MedAgents | 462/988 (46.76%) | 200/300 (66.67%) | 18.87 / 18.43 | 81 / 16 |
| MDAgents | 475/988 (48.08%) | 197/300 (65.67%) | 4.31 / 4.63 | 18 / 9 |
| **RxRSIAgent** | 556/988 (56.28%) | 199/300 (66.33%) | 3.00 / 3.00 | 0 / 0 |

Higher-allowance results remain visible:

| Method | Total output allowance | RxSafe988 | RxQA300 |
|---|---:|---:|---:|
| MedAgents |24000|468 (47.37%)|208 (69.33%)|
| MDAgents |24000|478 (48.38%)|199 (66.33%)|
| GRASP earlier run |512|502 (50.81%)|189 (63.00%)|

MedAgents' matched-output failures:78/14 budget exhaustion and3/2 invalid finals (RxSafe/RxQA). MDAgents:8/7 exhaustion and10/2 invalid finals. Invalids are retained in denominators. SafeRx-Agent is unexecuted; GAMENet/SafeDrug medication-set scores do not belong in QA accuracy columns. No global SOTA claim is supported.

## 3. Datasets and selection

RxSafeBench:2443 source rows become2000 deduplicated local option tasks;625 train,190 proposal,197 guard,988 evaluation. This is a derived three-option task, not the original free-generation metric. RxQA:all300 public OpenFDA questions; no licensed BNF subset. Main benchmarks have historical exposure and remain exploratory.

New independent development uses the public MedQA training mirror (revision `153e61cdd129eb79d3c27f82cdf3bc5e018c11b0`, source train10178). An input-only medication/treatment keyword plus one option longer than6 words gives784 eligible cases; hash order selects120 proposal and120 guard. Exact overlap with earlier local benchmark texts is excluded. These are general medical exam questions, including some references to unavailable images, not a curated dose dataset. The mirror and parquet hash are pinned in `upgrade_v36/protocol.json`; raw data is not uploaded.

## 4. What changed in the agent

1. Call1 extracts patient facts with input quotations, drug entities, explicit route and question intent.
2. Label tool rejects unrelated fixed-combination products, handles generic/salt/brand identity, exposes UNII and available routes, and excludes explicit route conflicts. It returns balanced indication/dose/safety windows with source IDs and offsets.
3. Call2 assesses each option, proposes citations and source-bound arithmetic.
4. Deterministic tools check exact quotations and bounded arithmetic. They do not validate clinical applicability, units, renal dosing or complete DDIs.
5. Call3 chooses a final option with remaining uncertainty.
6. A frozen supervised logistic calibrator may override short, previously observed medication names when its probability gap is≥0.2. After an override, the old explanation is explicitly separated and is not presented as justification for the new choice.

Current entry: `rxrsiagent/selected_agent.py`; profile: `rxrsiagent/selected_profile.json`. Historical `core.py` and `evaluated_profile.json` preserve their old audits and are not the current main-table entry.

## 5. Controlled components and attribution

| Configuration | RxSafe988 correct | RxQA300 correct |
|---|---:|---:|
| No evidence / 无证据 | 487/988 | 194/300 |
| Old lookup / 原名称检索 | 488/988 | 189/300 |
| Verified source / 来源核验 | 472/988 | 199/300 |
| Selected full agent / 选定完整方法 | 556/988 | 199/300 |

Verified retrieval alone **regresses** on RxSafe test, despite improving proposal94→103 and guard98→102 against the no-evidence control. RxQA source availability rises from1/300 under old name lookup to267/300. Availability is not relevance or correctness. The selected calibrator fixes118 source-agent test errors and regresses34, adding8.50pp [6.08,10.93]. It applies527 times on RxSafe and0 on RxQA.

The numerical module uses draft, normalized medication-name indicators and medication/UNII×focus words. It uses ordinary logistic regression; C grid0.1/1/10 and margin grid0/.05/.1/.2/.3. Proposal selects C10,margin0.2:110/190; guard116/197 versus102. Model hash freezes before test. There are no answer-position or case-ID features.

### Post-selection diagnostic controls

Fixed C10 and margin0.2; none replaces the selected main model using test performance.

| Features | Proposal | Guard | RxSafe test |
|---|---:|---:|---:|
| identity_only | 116/190 | 120/197 | 564/988 |
| identity_and_draft | 112/190 | 121/197 | 553/988 |
| context_only | 112/190 | 116/197 | 574/988 |
| context_and_draft | 106/190 | 115/197 | 533/988 |

Identity-only scoring reaches564/988 and context interactions without a draft574/988, above the selected full model556. This weakens a claim that the full architecture is necessary or that all gain reflects clinical reasoning. New medication combinations and independently constructed tasks are required for confirmation.

## 6. What evolves as cases increase

Two four-round language-memory attempts require applicability, exclusion conditions, supporting failures and successful counterexamples. Every proposed update is rejected. No text card is retained. The numeric state is learned by ordinary supervised optimization; tools, prompts and backbone weights do not evolve during learning.

| Cumulative cases | Numeric features/weights | Proposal | Guard | Retained text cards run1/run2 |
|---:|---:|---:|---:|---:|
| 156 | 4,848 | 102/190 | 101/197 | 0 / 0 |
| 312 | 9,250 | 108/190 | 107/197 | 0 / 0 |
| 468 | 13,546 | 113/190 | 112/197 | 0 / 0 |
| 625 | 17,672 | 110/190 | 116/197 | 0 / 0 |

These are **post hoc fixed-hyperparameter prefix diagnostics**: C and margin were selected using all625 training cases and development feedback. They are not a prospective onlineRSI study. Proposal accuracy is nonmonotonic. Guard growth alone does not prove independent transfer.

## 7. Continued independent experiments, including failures

| Candidate | Proposal120 | Fixes/regressions vs static | Decision |
|---|---:|---:|---|
| Static source agent |99|reference|control|
| Expanded dose/population sections |99|4/4|rejected|
| Independent draft + contradiction review |99|7/7|rejected|
| Retrieval of3 training examples from9936 cases |99|5/5|rejected|

All three candidates retain3×1536 call allowance. The last uses extra external training data, so is not equal-data. None strictly improves proposal; **guard and RxQA are not run for these candidates**. The240-case cohort was prepared, but only its120 proposal cases were needed. Earlier active second retrieval also fails103→100/190. Failure gates prevent test-driven cherry-picking; they do not guarantee that the retained configuration generalizes.

## 8. Cases and clinical boundary

Deterministically choose the first lexical calibration fix and regression (post hoc public examples):

- `0445a1cf61c5e4ac`:risperidone→sertraline, matching the reference. The old rationale supports risperidone and cannot justify the overridden answer. This is a reference correction, not established clinical improvement.
- `0d0cc811ec14bfd3`:griseofulvin→ketoconazole, creating an error. The source rationale also overgeneralizes from one shampoo product label. Both calibration and applicability remain imperfect.

Eight synthetic software tests pass;24735 original and1556 follow-up source spans are checked. No clinician ratings are fabricated. Fourteen clinician-oriented endpoints, including treatment-goal coverage, major-error cases, joint clinically correct orders and unnecessary medication, remain awaiting the two reviewers. QA accuracy is not prescription execution or clinical safety.

## 9. Audit, cost and reproduction

- Main audit: `upgrade_v35/results/audit.json`; test freeze: `upgrade_v35/test_freeze.json`.
- Follow-up: `upgrade_v36/results/audit.json`; calibration diagnostics: `upgrade_v35/results/calibration_diagnostics.json`.
- Main successful-response ledger increment:USD16.260916; follow-up:USD0.892790; total:USD17.153706. This is the local response ledger, not a provider invoice. Logical full-inference costs include cached responses and are reported separately.
- 1655 receipt references differ from the latest exact-request cache because concurrent identical calls can yield different raw responses; per-case raw receipts are authoritative. This count includes repeated references. No claim of identical planner samples in v35; v36 adds cross-process request locks.
- Source requests are cached with statuses, including missing sources and HTTP errors. No missing evidence is converted to “safe.”
- Raw benchmark traces, downloaded labels, credentials and trained pickle remain local. Code, aggregates and hashes are tracked.

Reproduction uses Python3.9 with numpy/scipy/scikit-learn/pandas/pyarrow and the existing public client. After restoring the local input/cache manifests, run the stage CLIs in the README; audits run without new API calls. Do not rerun `prepare.py` over an existing experiment directory because it starts a new ledger/split record.

## 10. Remaining research target

The two-benchmark win and convincing autonomous RSI are **not complete**. Priority:build independent label-grounded dosing/applicability tasks, fix product-strength/release-form matching, validate clinical rules, and compare calibration against ordinary supervised baselines on unseen medication combinations. Choose subsequent configurations on new development data; reserve a new final test before further optimization. Real order execution and blinded clinical endpoints are separate required evidence.

Primary sources: [openFDA](https://open.fda.gov/apis/drug/label/), [MedQA author repository](https://github.com/jind11/MedQA), [RxQA official release](https://github.com/Google-Health/rxqa). Historical runs and rejected candidates remain versioned; only the selected configuration appears as RxRSIAgent in the main paper.
