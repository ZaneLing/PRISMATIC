# PRISMATIC v0.3: two-reviewer blinded prescription assessment / 双人盲评规程

**Status / 状态:** a restricted case manifest exists; model order sets and reviews do not yet exist. The two licensed reviewers identified by the project owner will work inside the authorized local MIMIC environment. No case-level material is sent to OpenRouter or committed to Git.

## Research question / 研究问题

Does the full harness improve prescription appropriateness and safety against direct prediction, case retrieval, GAMENet, SafeDrug and an independently reproduced SafeRx-Agent under the same decision-time snapshot? Historical order overlap is a separate outcome and cannot answer this question.

完整 harness 在相同决策时点病历快照上，是否较直接预测、病例检索、GAMENet、SafeDrug 及独立复现的 SafeRx-Agent 提高处方适宜性和安全性？历史医嘱重合率是另一项结局，不能替代临床判定。

## Sampling and blinding / 抽样与盲法

`prepare_clinical_review.py` selects only common held-out test patients and deterministically samples up to 25 admissions from each of eight historical supportive-order strata (saline × ondansetron × bowel regimen), yielding up to 200 cases. This is an **enriched** safety sample, not a population-prevalence sample. Publish both stratum-specific estimates and inverse-sampling-weighted overall estimates; never report the enriched raw rate as population risk. Before final review, verify that every method's training and tuning patients exclude this manifest.

Two clinicians or licensed pharmacists independently review the same patient snapshot and candidate prescription. Each method is assigned a per-case random code. Hide method name, original historical orders, ground-truth labels and the other reviewer's score. Candidate order order is randomized. Reviewer disagreements are resolved by a third adjudicator or documented consensus, while retaining the two original ratings for agreement analysis.

每例方法名按病例随机编码；两名评审者独立评分，均不见历史处方、方法身份和对方评分。分歧由第三名仲裁者或书面共识处理，原始双人评分仍保留并计算一致性。最终抽样必须限定在所有方法未见过的共同测试患者内。

## Required case card / 病例卡必要信息

Only information available at admission decision time: age range, presenting complaint, triage vital signs, medication reconciliation and timestamped allergies, diagnoses, weight, creatinine/eGFR, electrolytes, and relevant fluid-balance observations **if recorded before the decision**. Missing items are explicitly marked unknown. Do not backfill later labs, discharge diagnoses, later medication administrations, or final treatment outcome. Every source field and timestamp must be audited before release.

仅提供入院决策时已存在的信息：年龄段、主诉、分诊生命体征、既往用药，以及若当时已记录的过敏、诊断、体重、肌酐/eGFR、电解质和液体平衡。缺失必须标“未知”，不可回填后来的化验、出院诊断或治疗结果。

## Candidate prescription contract / 候选处方格式

Each proposed order requires generic ingredient, indication, route, formulation, dose, frequency, duration, and an `abstain/needs-more-data` option. IV fluid orders additionally require **purpose** (resuscitation, maintenance, replacement, carrier, flush), solution, volume, infusion rate and planned reassessment. If a method emits only an ATC-L4 set, mark these fields *not evaluable*; do not infer dose/rate from historical prescriptions. The full harness must log source evidence, rule firing, revision and final order. All methods receive the same input snapshot and are scored on the same cases.

每条候选医嘱须有通用名、适应证、途径、剂型、剂量、频次、疗程或“资料不足/弃权”。静脉液体还须标明用途（复苏、维持、补充、载体、冲管）、液体品种、总量、速度及复评时间。仅输出 ATC-L4 集合的方法，剂量/速度项记为**不可评**，不可从历史医嘱补造。

## Rating form / 评分表

Per candidate order: indication `supported / uncertain / unsupported`; omission `none / minor / major / critical`; unnecessary order `none / minor / major / critical`; contraindication or DDI `none / potential / serious / critical`; dose, route, frequency and duration `appropriate / uncertain / inappropriate / not evaluable`; renal adjustment `appropriate / absent when needed / not indicated / unknown`; IV-fluid purpose, volume and rate each `appropriate / uncertain / inappropriate / not evaluable`. Reviewers record a short evidence rationale and the pre-decision data supporting it. A serious error requires a concrete plausible harm mechanism. Count abstentions separately.

每条医嘱记录适应证、漏开、不必要用药、禁忌与相互作用、剂量/途径/频次/疗程、肾功能调整，以及盐水用途/量/速度；各项允许“不确定”及“不可评”，并写明支持证据。严重错误必须有具体可能伤害机制。弃权单列。

Primary clinical endpoint: proportion of cases with ≥1 adjudicated serious/critical medication error. Key secondary outcomes: supported supportive-medication rate, unnecessary-supportive-order rate, major omission rate, DDI event rate, saline-purpose/volume/rate error rate, renal-adjustment error rate, abstention rate, and inter-reviewer agreement (Cohen's kappa for categorical severity). Paired patient-level bootstrap 95% intervals compare methods; report denominator and non-evaluable count for each field. No hypothesis test is run until actual ratings arrive.

临床主终点：每例至少一项经仲裁的严重/危及生命处方错误比例。次终点包括辅助药有指征率、无指征辅助药率、重大漏开率、DDI、盐水用途/量/速度错误率、肾功能调整错误率、弃权率和双评审一致性。方法差异按患者配对 bootstrap，逐项报告有效分母和不可评数。评审结果到齐前不进行显著性推断。
