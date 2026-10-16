# RxRSIAgent: trace-root reflection, scoped interventions, and independent evaluation

Updated 16 October 2026. This living report supersedes the previous current summary; prior evidence is archived. The paper method is **RxRSIAgent**, not a list of version names.

## 1. Actual results and outstanding targets

- Current frozen actor: **491/988 (49.70%) RxSafe; 196/300 (65.33%) RxQA**.
- Independent MedPIC exact-set score: **274/467 (58.67%)**. Guideline-following:193/284; counterfactual:81/183; both members correct:3/35 strict pairs.
- **The target of beating the strongest completed named-agent controls on both benchmarks is unmet.**
- **No positive evolution is established: no procedural, retrieval or vocabulary update is retained. Identical states reuse predictions; the flat trajectory is not five independent replications.**

## 2. What supervised calibration actually means

The previous 556/988 result includes ordinary logistic regression trained on 625 labeled cases. It learns weights for drug identities, drug/UNII–question-word interactions, and an LLM draft indicator. When all options are short names seen in training and the score gap is at least 0.2, it may override the LLM. It was applied on 527 RxSafe cases and applied on zero RxQA items. This is a statistical option scorer, not reflection, root-cause tracing or tool evolution. A name-only diagnostic scored 564/988, exposing a shortcut concern.

GT feedback can legitimately supervise an agent-update experiment. The distinction is **what is updated and what is validated**: ordinary option-weight fitting is kept separate from persistent process/tool-configuration changes. Even the latter does not become successful RSI merely because code exists or memory grows. We require an actual accepted change and independent improvement. The current actor has no fitted option ranker or raw training-answer retrieval; pretrained drug knowledge still exists.

## 3. Named-method main table

| Method / 方法 | RxSafe 988 | RxQA 300 | Output cap / 输出上限 |
|---|---:|---:|---:|
| GRASP | 495/988 (50.10%) | 185/300 (61.67%) | 4608 |
| MedAgents | 462/988 (46.76%) | 200/300 (66.67%) | 4608 |
| MDAgents | 475/988 (48.08%) | 197/300 (65.67%) | 4608 |
| Supervised source-agent control / 普通监督校准对照 | 556/988 (56.28%) | 199/300 (66.33%) | 4608 |
| **RxRSIAgent** | **491/988 (49.70%)** | **196/300 (65.33%)** | 4608 |
| MedAgents, higher allowance / 高额度 | 468/988 (47.37%) | 208/300 (69.33%) | 24000 |
| MDAgents, higher allowance / 高额度 | 478/988 (48.38%) | 199/300 (66.33%) | 24000 |

Same served DeepSeek identifier and identical question sets. Author workflows are pinned local adaptations, not their papers' copied scores. RxRSIAgent uses 3×1536 output tokens. Shared output allowance does **not** equal input cost, call count or training supervision. The source-agent calibration control uses its earlier fixed source workflow; it is a separate method/control, not a clean one-factor ablation of the new actor. Higher-allowance MedAgents remains 208/300. No SafeRx-Agent score is invented; medication-set methods cannot populate QA accuracy columns.

## 4. Why earlier skill updates all failed

The earlier eight updates never passed the proposal set; no guard rejection occurred. Two produced no schema-valid cards. The other proposals caused more regressions than fixes (for example 9 corrections versus 16 regressions). The code audit identified missing retrieved spans/intermediate checks in reflection, unconditional skill injection, nearest-success examples without scope validation, and missing replay of rejected interventions.

Further real experiments found: long-context ID/role confusion; a broad age-or-pregnancy trigger activating on 115/120 MedQA questions and reducing 103 correct to 97; a missed gestational-timing phrase in the context detector; old root IDs being invalidated solely because they came from an earlier round; and treating a legitimate null/no-edit response as a schema error, forcing an unsupported repair. These defects have explicit fixes and retained negative experiments. They are not all failures of clinical knowledge or merely an overly strict gate.

## 5. Current inference and learning mechanism

1. Extract quoted facts, medication roles and explicit routes.
2. Resolve product variants and retrieve indication/dose/safety windows with balanced per-product allocation. Record exact source offsets and unresolved metadata.
3. Assess every option. Verify quotations, bounded arithmetic and explicitly sourced age/eGFR/CrCl comparisons. Unit consistency, all rule qualifiers and overall clinical applicability remain unverified.
4. Decide with the original input and check results; no numeric answer override.
5. On training feedback, record GT/prediction discrepancy, earliest suspected failure stage, source-grounded root hypothesis, minimal repair and counterexample requirement. A model's hypothesis is not clinical adjudication.
6. Accumulate past eligible roots, recent rejected edits and the two highest positive-net failed probes. Use compact typed role pools and short IDs. Do not forget an earlier root when new cases arrive.
7. Propose one scoped procedure or one retrieval-parameter change; data-bound context-vocabulary patches can repair detector misses. The patch must match a failure and a success; this does not prove every term's meaning. Explicit no-edit decisions are preserved.
8. Training probe: at least 2 net corrections and no extra invalid answers. Proposal RxSafe 190/MedQA120: neither loses and pooled count improves. Guard RxSafe 197/MedQA120: neither loses. Freeze all states before evaluation.

Only procedures, retrieval configuration and condition vocabulary can change. Backbone weights and executable tools remain fixed during learning. Tool repairs between experiments are **researcher changes**, not autonomous agent gains. The final proposal model is **anthropic/claude-opus-4.8**; actor and initial reflector remainDeepSeek. This is externally assisted agent-state learning with additional offline compute, not autonomous same-model recursion. Earlier controls used a strict positive guard gain; the non-regression guard was declared before tests.

## 6. Completed updater experiments

| Experiment / 实验 | Attempts / 尝试 | Schema / 角色或格式 | No edit / 无证据更新 | Probe rejected / 探针拒绝 | Proposal / 候选集拒绝 | Guard / 守门拒绝 | Accepted / 保留 |
|---|---:|---:|---:|---:|---:|---:|---:|
| v37 | 8 | 5 | 0 | 3 | 0 | 0 | 0 |
| v38 | 8 | 3 | 0 | 4 | 1 | 0 | 0 |
| v39 | 16 | 4 | 0 | 12 | 0 | 0 | 0 |
| v40 | 16 | 12 | 0 | 4 | 0 | 0 | 0 |
| v41 | 16 | 3 | 0 | 12 | 1 | 0 | 0 |
| v42 | 16 | 9 | 0 | 7 | 0 | 0 | 0 |
| v43 | 16 | 3 | 13 | 0 | 0 | 0 | 0 |
| v44 | 16 | 2 | 14 | 0 | 0 | 0 | 0 |

These are 112 proposal attempts across eight four-round development experiments, all reusing the same 400-case training cohort. They are not 3,200 unique cases or independent random-seed runs. All rejected/declined candidates remain in the records. v37 adds full traces; v38 explicit role repair; v39 narrow interventions; v40 condition vocabulary; v41 compact context; v42 external proposer; v43 legitimate abstention; v44 cumulative root and promising-failure replay.

## 7. Round-by-round independent validation

| Round / 轮次 | Cases / 累计病例 | Cards / 技能 | Retrieval edits / 检索项 | Terms / 条件词 | Proposal S/M | Guard S/M | MedPIC |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 | 0 | 99/190; 103/120 | 104/197; 102/120 | 274/467 |
| 1 | 100 | 0 | 0 | 0 | 99/190; 103/120 | 104/197; 102/120 | 274/467 |
| 2 | 200 | 0 | 0 | 0 | 99/190; 103/120 | 104/197; 102/120 | 274/467 |
| 3 | 300 | 0 | 0 | 0 | 99/190; 103/120 | 104/197; 102/120 | 274/467 |
| 4 | 400 | 0 | 0 | 0 | 99/190; 103/120 | 104/197; 102/120 | 274/467 |

**No positive evolution is established: no procedural, retrieval or vocabulary update is retained. Identical states reuse predictions; the flat trajectory is not five independent replications.** New training comprises 200 existing RxSafe train cases and 200 non-overlapping MedQA train cases, mixed 50/50 per round. Repeated development exposure is disclosed. Main RxSafe/RxQA sets have historical exposure and are exploratory. MedPIC uses the pinned author release 467, including 108 multiple-answer questions. All stages freeze before independent inference; no best-test checkpoint selection occurs. One publicly viewed schema example remains in the predeclared denominator.

## 8. Drug-prior and patient-condition diagnostics

| Condition / 条件 | Exact-set / 完全正确 | Both pair members / 成对全对 |
|---|---:|---:|
| Original / 原始 | 24/70 | 3/35 |
| Permutation / 选项置换 | 26/70 | 4/35 |
| No vignette / 去掉患者背景 | 24/70 | 0/35 |

The 35 pairs share identical option strings and all 35 change the correct answer set when patient information changes. Option-remapping prediction agreement is 48/70. No-vignette inputs retain the question/options, which can still contain clinical clues. Removing the vignette leaves 24/70 exact answers unchanged, and option permutation changes 22/70 mapped predictions. Thus shortcut robustness is not demonstrated. These controls assess context and position sensitivity; they cannot exclude all parametric drug priors or establish clinical quality.

## 9. Audits, costs and limitations

- Recounted 1895 distinct evaluation rows and 31401 exact source spans; receipts and numeric checks were revalidated. A declared post-freeze parser repair normalized list-valued search focus for two incomplete cases; the other 986 saved predictions were hash-verified unchanged. Ten synthetic verifier/routing tests pass; these are software checks, not clinical validation.
- Root ledger:131 records,114 with verified supporting quotes. Reference-status judgments:{"ambiguous": 73, "supported": 11, "inconsistent": 20, "insufficient_evidence": 27}. These model-generated categories do not prove GT errors.
- Enhanced source-request outcomes:{"http_404": 340, "retrieved": 300}. An intended 600-request cap overshot during initial concurrent fetching; cached responses and actual counts are retained, not hidden. Missing labels and query-limit fallbacks remain limitations.
- Shared new successful-response ledger increment: **USD 22.370972**, including all updater variants and final evaluation. Logical cached inference cost differs from newly billed responses; this is not an invoice.
- Source-span validity and narrow threshold checks do not establish correct complete prescriptions, full DDI handling, renal dosing, dose units, formulation strength or monitoring. Clinical annotations and real EHR execution remain unfinished.

## 10. Protocol correction and artifacts

**Correction:** original RxSafeBench already uses three-option MCQ (paper SectionII-C). Earlier local prose calling it free generation was wrong. Our local deduplication, ordering, grouped split and evaluation subset still differ, so published scores cannot be copied into the same-protocol main table. Historical hash-bound files remain archived with this correction.

- Current code/profile: `rxrsiagent/selected_agent.py`, `rxrsiagent/selected_profile.json`.
- Actor/checks: `upgrade_v40/agent40.py`; evidence tool: `upgrade_v37/evidence37.py`.
- Final learner and compact context: `upgrade_v44/learn.py`, `proposal_context.py`.
- Final states/gates: `upgrade_v44/results/learning.json`; independent trajectory and shortcut results alongside it.
- Freeze and audit: `upgrade_v44/test_freeze.json`, `upgrade_v44/results/audit.json`.
- Public per-case answer letters: `upgrade_v44/results/public_predictions.jsonl` (1,895 rows, no patient/source prose); its manifest independently recounts the totals.
- Current English ACL source: `paper/latex/v0.3/prismatic_v03_en.tex`; numbers are generated from audited artifacts. The paper does not rename earlier variants as different proposed methods.
- Raw benchmark data, downloaded label bodies, provider receipts, restricted records and credentials remain outside Git.

Sources: [RxSafeBench paper](https://arxiv.org/html/2511.04328v1), [MedPIC paper](https://arxiv.org/abs/2608.03028), [MedPIC author data](https://huggingface.co/datasets/TIM0927/MedPIC-Bench), [openFDA fields](https://open.fda.gov/apis/drug/label/searchable-fields/).

## 11. Failure-directed cases and MIMIC-IV

Four failure-directed candidates were executed: product scope, decision obligations, whole-sentence evidence and narrow scope routing. Specific training errors were repaired, but every candidate failed development acceptance; the main table and current runtime retain the frozen actor. Scoped routing changes269→273/400 training answers, but99→98/190 RxSafe and103→102/120 MedQA proposal answers. No independent evolutionary gain is established.

The three public benchmarks are option-answering tasks, not complete-prescription coverage. Earlier MIMIC-IV work completed a time-controlled new-order task on1,082 test admissions. A new local recount gives the earlier supervised agent15.85%/24.16%/19.14% drug precision/recall/F1, versus17.56%/23.53%/20.10% for the ensemble. These are not current LLM-agent scores. The full final ATC-L4 comparison remains unfinished.

[Full English case/task/MIMIC report](TASKS_CASES_AND_MIMIC.en.md) · [中文](TASKS_CASES_AND_MIMIC.zh.md). New development predictions, source audits and local MIMIC recounts are in`upgrade_v45/results/` and`upgrade_v47/results/`. Incremental successful-response ledger cost is approximatelyUSD3.192.
