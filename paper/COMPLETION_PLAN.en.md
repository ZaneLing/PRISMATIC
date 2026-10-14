# PRISMATIC manuscript completion and execution plan

## Current execution: P5 / v0.12 complete (2026-10-14)

[English results](../upgrade_v12/RESULTS.en.md) · [中文结果](../upgrade_v12/RESULTS.zh.md) · [English paper](latex/v0.3/prismatic_v03_en.tex)

- **v0.11 executed:** fixed balanced review 484/988 (48.99%), safety review 487/988 (49.29%). The original four-action router rejects all updates and stays at 467/988. Indication has 153 missing replies; Gemini has 380 missing development replies. These are unscored. [Results](../upgrade_v11/RESULTS.en.md).
- **v0.12 executed:** three seeds, identical complete actions and 387 development labels. Separate-guard / pooled selection average 48.68±0.61% / 48.79±0.54%, versus 48.99% for the development-selected fixed tool. Routing parameters change; every round's repairs, regressions and calls are recorded.
- **Validity repair:** HTTP 402 interrupted 713 GRASP-adaptation test requests for v0.8 seed 137 and round-four selection for seed 2026. The latter is rolled back to round three. Seed 42 and v0.10 remain complete. Incomplete runs are excluded from summaries; transport failures cannot be scored as model errors.
- **v0.9 running:** the uniform arm completed three training rounds; error-prioritized updates continue locally. All choices freeze before reporting the new 500-case test. Development metrics are not test results.

### Ordered continuation

1. Finish local parameter arms and the direct-tool control; independently recount fresh-patient tests, per-case repairs/regressions and parameter trajectories.
2. Improve outcome verification and action-selection signal using complete public traces, with fixed-tool and equal-data ordinary-supervision controls.
3. After API access is restored, resume incomplete seeds, indication review and the second model using the same protocol and caches.
4. Freeze a viable design before untouched confirmation and RxQA transfer. Repeated exploratory tests do not establish confirmatory superiority.
5. Complete real FHIR stateful execution, ingredient-level medication coverage and temporal sensitivity. Current evidence does not establish research maturity or overall superiority.

---

## Active execution: P4 / ACL 2027 / v0.7–v0.9 (14 October 2026)

This section supersedes historical plans below. The user has no official RxEval/SafeRx test package; proceed with runnable data. The existing English editor path is retained with the official ACL review style. Markdown remains bilingual and versioned.

| Increment | Experiment | Status / evidence |
|---|---|---|
| v0.7 | 40k/2k/2k/4k patient-disjoint data; three seeds; five checkpoints; 12 method/ablation rows | Complete: [results](../upgrade_v7/RESULTS.en.md), independent recount, patient-cluster intervals, fixes/regressions and artifact hashes |
| v0.8 | Fixed-LLM public scenario-group split; language skills, memory, tool configuration; direct/CoT/Self-Refine/RAG and Reflexion/GRASP/EvoTool task adaptations | Running: [protocol](../upgrade_v8/README.md); four rounds, artifact ablations and 300-question RxQA transfer; remaining seeds/backbone transfer pending |
| v0.9 | Local QLoRA, uniform versus feedback-prioritized updates, equal optimization steps | Running: [protocol](../upgrade_v9/README.md); actual adapter hashes, frozen tools and new test patients; await generation scores |

v0.7 full-system mean drug/order F1 is 0.39920/0.27865 versus 0.40209/0.28110 for the word/character control. This is not a win. The saline-presence endpoint is removed; common prescription metrics cover all items.

### Added execution record: first v0.8 seed / v0.10 / v0.11

- v0.8 seed 42 completes eight methods, four rounds, ablations and all RxQA questions; two other seeds continue. [Results](../upgrade_v8/RESULTS.en.md). All RxRSI updates in this seed are rejected; the curve is flat.
- v0.10 executes the unmodified author GRASP core: 50.81% on the same 988 questions versus CoT 47.27%; scoped RxRSI does not improve. [Comparison and reflection](../upgrade_v10/RESULTS.en.md).
- v0.9 fixes empty-reasoning-envelope parsing and identical-prompt cache case binding on development, retaining the original failures and unchanged weights; both three-round parameter arms continue.
- v0.11 retrieves name-matched label records for 623 of 699 public drug options, covering about 93% of test option occurrences. Evidence utility is first evaluated only on development data.

### Iteration and maturity gates

1. Complete v0.8/v0.9; audit changed objects, rejected proposals, fixes/regressions, cost and ablations; update the paper with actual results.
2. Use training/validation errors to design subsequent versions, prioritizing inapplicable generic skills, memory interference and candidate-tool coverage. Preserve unsuccessful versions; test answers never propose edits.
3. Match backbone, data and comparable budgets against ordinary same-data learning and recent mechanisms. Distinguish task adaptations from official reproductions.
4. Establish multiple-seed stability, new-patient confirmation, transfer and retention. New choices informed by development findings require unused confirmation data.
5. Maturity requires reproducible gains attributable to identified objects, full evolution/regression traces, real tool or full-order ability, explicit timing/label limits, independently checked statistics and a compilable manuscript. Continue iterations if these are not met; do not claim SOTA prematurely.

Each completed increment updates the English manuscript, bilingual reports, execution manifest and GitHub. Optional clinician review of attributes absent from GT does not block automatic experiments.

---

## Active execution version: P3 / RxRSIAgent v0.6 (14 October 2026)

**This section and the [RxRSIAgent design](../upgrade_v6/DESIGN.en.md) supersede conflicting requirements in the historical P1/P2 plan retained below.**

Outperforming published methods is the paper objective, not a runtime instruction. Existing prescription GT supports automatic training, typed error feedback and evaluation without clinician review. Human assessment is optional for attributes absent from GT. Published scores may be cited directly with their dataset, protocol, metric and source table; reproducing all baselines is not required. Our own matched-protocol measurements are required before claiming superiority.

The current paper's **Table 2** contains protocol-separated reported literature scores. **Table 3** contains executed 4,000-case raw-order comparisons. Earlier ATC scores are a different task.

### Completed v0.6 increment

| Work | Executed evidence |
| --- | --- |
| Prescription workflow | Patient state → prescription tools → selected planner/policy → structured order compiler |
| GT evaluation | Drug-set F1, exact drug/route/dose/unit tuple F1, observed-field accuracy, saline occurrence |
| Accumulated cases | 8k/16k/32k/40k; fixed-test drug F1 0.35841 → 0.40668 |
| Error replay | 32k pre-update training feedback records; strengths 0/0.25/1; validation selects zero extra weighting |
| Order templates | Global versus similar-case comparison; selected core-order F1 0.28003; same-40k ordinary training matches it |
| Actual local LLM | 20 validation + 20 test; catalogue/experience/policy drug F1 0.27350/0.32000/0.42997; policy selected on validation |
| Literature registry | GAMENet, SafeDrug, SafeRx, RxEval, MedAgentSim, MedAgentBench and GRASP protocols/results |
| Verification | Seven contract tests; independent recomputation; disjoint patient splits; 2,000 patient-cluster bootstrap replicates |

[Results](../upgrade_v6/RESULTS.en.md) · [Code and evidence map](../upgrade_v6/README.md)

### Ordered remaining experiments

1. **RxEval:** verify formal release and access, retain the 1,547-question medication/dose/route option task, execute direct/RxRSI, cite published baselines; report macro F1, exact match and budgets.
2. **SafeRx ATC-L4:** align IV/III membership, inputs, labels and scoring, then run our method only. Label approximate membership as an adaptation rather than a strict head-to-head result.
3. **Richer order task:** timepoint trajectories, verified allergy/renal facts, ingredient normalization and broader order coverage including saline.
4. **Mechanism benefit:** equal-data ordinary training, episode retrieval, typed error replay and skill editing; training-only proposals and separate passing/failing regression probes.
5. **Parameter evolution:** same-backbone memory/SFT/combined/GT-preference experiments. LLM-weight updates must be executed before they are claimed.
6. **Confirmation:** freeze configurations, evaluate independent patients and multiple seeds, and report paired intervals.

LLM weights remain frozen in v0.6. Skill editing, LLM fine-tuning and matched external-benchmark superiority are unfinished. Existing RxSafeBench/RxQA results remain secondary evidence; real FHIR evaluation remains a tool-capability supplement.

---

## Historical P1/P2 plan (retained for provenance)

Version P1, 14 October 2026. [Chinese plan and execution ledger](COMPLETION_PLAN.md). The active manuscript is English only and uses the original AAMAS template from the supplied ZIP. Planned experiments and acceptance criteria are not achieved results.

## 1. Deliverables and claims

Deliver an English AAMAS manuscript with reproducible evidence for two questions: does the complete prescription harness improve prescribing quality, and does accumulating reviewed cases improve decisions about supportive medication and fluid orders?

Required outputs are a common-protocol method comparison, case-growth curves, mechanism ablations, two-reviewer clinical evaluation, full public secondary benchmarks, real FHIR tool-state evaluation, source code, configurations, aggregate results, run manifests and a change log. Update the open English source in place, compile after edits, preserve history in Git and synchronize completed increments to GitHub.

| Claim | Required evidence | Interpretation if unsupported |
| --- | --- | --- |
| H1: improved prescription quality | E01 common-protocol comparison and E04 clinical error/indication ratings | Report null or adverse effects; multiple-choice accuracy is not a substitute |
| H2: useful learning from reviewed cases | E02 growth with fixed test patients and static/raw/reviewed memory controls | Historical overlap alone supports behavior prediction, not clinical reasoning |
| H3: mechanism beyond extra computation | E03 matched-budget controls, ordinary repeat calls and ablations | Attribute gains to computation if they disappear under controls |
| H4: reliable tool and state management | E06 actual FHIR actions and final-state scoring | No performance claim without the environment and scorer |

## 2. Existing evidence

- MIMIC-IV v3.1 plus MIMIC-IV-ED v2.2: 201,750 ED-to-hospital admissions and 107,097 patients, without selection on future oral orders.
- ATC-L4 mapping covers 45.652% of 1,788,195 six-hour all-route orders. Unmapped orders cannot be treated as absent; class labels do not establish saline purpose, volume or rate.
- The 40k/4k/4k pilot uses the same patients and exactly five predictions from 80 training classes. Prevalence/retrieval/direct SGD micro-F1@5 is .28362/.32752/.38640. These are developmental historical-overlap results.
- Current predictors actually use chief complaint, acuity and home-medication text. Stored vital signs are not model inputs. Timestamp availability remains incompletely verified.
- RxSafeBench deduplicated 2,000 questions: DeepSeek direct/repeat/light review accuracy is 46.2/43.9/47.6%. The light-review paired gain interval crosses zero. RxQA OpenFDA 300: direct accuracy is 62.0%.
- Two clinical reviewers are available, with a local 200-case manifest and rating protocol; complete orders and independent ratings remain pending.
- MedAgentBench has no real tool-state result: Docker FHIR and the external reference scorer are not ready.

## 3. Freeze data and evaluation before expanding the main table

### P01: label observability, input timing and patient splits

Separate admissions with no recorded raw order in six hours, orders with no mapped class, and at least one mapped class. Report counts for all splits and the existing pilot. Partially mapped admissions may still have missing labels. Audit mapping by route and supportive-medication category, including saline, carriers and flushes; combine very small aggregate groups.

The current name/GSN fallback mapper uses the entire training-patient pool, beyond the predictor's 40,000 admissions. Disclose this resource. Growth experiments must use a fixed external dictionary or rebuild the mapper using only cases available at each checkpoint.

Record observation time, availability time and source for every proposed input. Require both charttime and storetime where available. Distinguish prescription starttime from order-authoring time. Missing timestamps cannot be silently treated as verified admission-time evidence. Prespecify an input policy and sensitivity excluding fields with unverifiable availability.

Existing test results have been inspected and are developmental. Lock a confirmatory patient pool that has not informed tuning, retrieval, mapping or error feedback, with a membership hash. If the pool has already influenced choices, disclose that limitation instead of calling it unseen.

Acceptance requires zero patient overlap, compliance with the chosen timestamp policy, explicit unverifiable fields and label unknowns, and reviewed stratified mapping errors. No arbitrary coverage percentage establishes clinical safety.

### P02: medication space and complete orders

Use ATC-L4 for historical-set comparison. Retain RxNorm or locally normalized ingredient, formulation, concentration, route, dose, frequency and duration for full orders. Prefer pinned public/licensed dictionaries, traceable exact matches and training-only fallbacks. Review ambiguous matches or retain uncertainty. ATC class membership does not establish interchangeability.

Supportive orders require indication, evidence references and uncertainty. Fluid orders additionally require purpose (resuscitation, maintenance, replacement, carrier, flush or unknown), volume, rate and reassessment. Allow abstention when essential information is missing. Check interactions at ingredient/order level before projecting results to classes. Pin the DDI/renal/contraindication resource, license, conditions and coverage; unknown coverage is not a safe result.

Deliver the order JSON schema, mapping version, training vocabulary, molecule/DDI coverage and shared scorer. Keep top-five as a historical compatibility metric; formal evaluation permits variable order counts and abstention, with thresholds selected only on validation data.

## 4. Methods to compare

| Method | Implementation requirement | Destination |
| --- | --- | --- |
| Prevalence and LR/SGD | Common split and medication space | Main table foundations |
| Case retrieval | Training-only cases, fixed K and context budget | Main table |
| Direct local LLM | Fixed locally authorized base model, structured orders | Main table |
| Ordinary second answer | Same model and call limit, no special memory/checker | Main table or ablation |
| Original PRISMATIC | Verify original DSWA, DFPC and agent roles; document missing components | Historical method and ablations |
| GAMENet | Preserve medication graph memory/history; document admission-input adaptation | Main table after protocol compliance |
| SafeDrug | Preserve molecular representation and DDI mechanism; start from official archived reproduction | Main table after valid ATC-L4 mapping/retraining |
| SafeRx-Agent | Verify official executable implementation; otherwise independently reproduce the paper and list deviations | Main table after validation |
| Full PRISMATIC | Structured state, supportive candidates, experience retrieval, independent checks, bounded revision, abstention, traces | Core main-table row |
| HealthFlow/EMR experience strategies | Adapt experience organization/retrieval on the common base model; their original tasks differ | Growth/mechanism table |
| Additional DREAM-supported methods | Verify method, dataset, code and license; select at most one or two strong additions | Supplementary robustness |

Do not give retrospective discharge codes only to GAMENet/SafeDrug. Do not rename complaint tokens as diagnosis codes and claim faithful reproduction. A common admission-state encoder is an explicitly tested adaptation. If original assumptions cannot be preserved, run a separate retrospective-visit panel in which every participating method gets the same inputs. Never fill missing DDI/molecule inputs with zero graphs while claiming the complete original method. Never import published scores into the common-protocol table.

Primary sources checked on 14 October 2026: [GAMENet](https://github.com/sjy1203/GAMENet), [SafeDrug](https://github.com/ycq091044/SafeDrug), [SafeRx-Agent](https://arxiv.org/abs/2605.29146), [DREAM](https://github.com/novzyg/DREAM), [HealthFlow](https://github.com/yhzhu99/HealthFlow), [EMR](https://arxiv.org/abs/2609.15161). DREAM is a framework; HealthFlow is an EHR-analysis workflow and EMR concerns clinical-reasoning experience. Their original scores are not prescribing comparators.

## 5. Experiment specifications

### E01: method-level prescribing comparison

Use the frozen MIMIC admission snapshot and identical patient lists, medication space, evidence and scorer. Debug on the existing 40k/4k/4k development protocol, then run formal training and the locked confirmatory set. Begin with SGD, retrieval and direct local LLM; add verified GAMENet/SafeDrug, original PRISMATIC, SafeRx-Agent and full harness. Small schema/timing/scoring checks precede larger runs.

Select the local base model after a 50-case throughput/format check and pin model ID, weight revision, quantization and hardware. LLM comparisons share model, input/output token caps, tool-step limits and ordinary repeat controls. Report actual tokens, calls, latency and memory. Traditional networks share data, a fixed tuning-trial budget and early stopping; report compute without claiming exact GPU-time equivalence to LLMs. Use at least three training seeds, preferably five if feasible; repeat a fixed LLM subset to assess nondeterminism.

Report Jaccard, micro/macro F1, PR-AUC, P/R@5 and predicted counts, alongside mapping/unknown coverage. Clinical outcomes come from E04. DDI reporting includes evaluable pairs, resource coverage and severity; empty recommendations do not establish safety without omission rates. Table 2A covers historical sets; Table 2B covers complete-order clinical quality. Dose/rate outcomes are N/A for class-only methods. Every cell links to a run and aggregate result.

### E02: accumulating cases and experience

First study experience-memory updates with frozen base weights. Keep memory learning, policy revisions and parameter training distinct. A weight-learning claim requires a separate SFT/preference-training experiment.

Use 0, 250, 1k, 4k, 16k and 40k cases, then the full training pool if supported. Predict each training-stream case before obtaining feedback and updating memory; never write test feedback into memory. Keep test patients, retrieval K, context tokens and inference budget fixed. Use at least three fixed stream orders and keep repeated admissions within one split. Cross-patient shifted MIMIC dates do not establish a real calendar deployment.

Controls: frozen model; fixed static RAG; growing raw-case RAG; success-only memory; success/failure memory; reviewed experience; updates without rollback gating. Add random or irrelevant token-matched memory as research controls. Plot historical-case and clinically reviewed-case growth separately; 40,000 unreviewed orders are not 40,000 expert rationales.

Measure supportive indication precision, major omissions, unnecessary drugs, saline purpose/volume/rate, renal adjustment, serious errors and abstention; historical AP/F1 is separate. Report intervals, final differences, learning-curve area, regressions and memory cost. Do not impose monotonic improvement. Freeze promotion/rollback criteria on validation data and retain accepted/rejected versions.

### E03: mechanism and compute ablations

Remove supportive-treatment proposals, retrieval, indication evidence, independent pharmacology checks, revision limits, experience quality gates and failure memory. Ablate original DSWA and DFPC individually. Include ordinary repeated answers and a single agent with the same tool/call budget. Count retrieval and checking costs.

Screen on a fixed development subset, then prespecify key confirmatory ablations. Report both precision and omissions, serious errors and per-case cost; avoid optimizing only one direction.

### E04: two-reviewer clinical evaluation

Calibrate on 20–30 training/development cases, then freeze rules. Reviewers are blinded to method identity and each other's ratings; experiment operators know the method codes. Preserve independent scores and record consensus or third-party adjudication.

The existing 200 cases in eight strata are exploratory. Weight by original stratum prevalence and cluster repeated admissions by patient. Estimate confirmatory sample size from pilot event rates, paired correlation and target effects; do not assume 200 is sufficient. Use a new locked patient set or disclose prior exploration.

Cards contain only eligible decision-time evidence, including history, allergies, vitals, medication reconciliation, weight, renal function, electrolytes and fluid-relevant information. Mark missing evidence unknown. Rate indications, omissions, unnecessary medication, DDI, renal adjustment and saline purpose/volume/rate. Keep unknown and unevaluable distinct; class-only outputs cannot be scored for dose. The clinical primary endpoint is at least one serious/life-threatening error per case. Report agreement, evaluable denominators, disagreements, adjudication, weighted rates and patient-paired intervals. Do not invent results before reviewers submit ratings.

### E05: full public secondary benchmarks

Use pinned [RxSafeBench](https://github.com/CAS-SIAT-XinHai/RxSafeBench) deduplicated 2,000 questions, retaining existing direct/repeat/light-review results; add two fixed OpenRouter models and a substantive knowledge-checking arm. Complete direct/repeat/knowledge-check arms on all 300 public OpenFDA [RxQA](https://github.com/Google-Health/rxqa) questions; do not imply access to the unpublished BNF component.

Rotate answer options with correct remapping, report cue-bearing questions separately, and disclose development reuse. A quoted passage does not establish applicability or medical correctness. Report accuracy, valid output, fixed/harmed answers, failures, latency, total cost and paired intervals. Count API failures in the primary denominator; fix retries beforehand. Estimate full-run costs from a small batch, set request/token/spend limits and support resumption. Verify current model IDs and prices at execution time. Public questions may use OpenRouter; restricted MIMIC stays in the authorized local environment.

### E06: real MedAgentBench tools and state

Install the [official environment](https://github.com/stanfordmlgroup/MedAgentBench), Docker FHIR, task controller and reference scorer; pin code and image digests. Run ten smoke tasks for query, order creation, readback and reset, then the official 300 tasks with direct tool agent, budget-matched planner and harness.

Reset or isolate each initial state and retain calls, errors, retries and final resources. Report official completion, schema validity, duplicate orders, wrong-patient writes, final-state verification, latency and cost. Write retries require idempotency. A textual completion claim is not state verification. If infrastructure/scoring remains unavailable, record that limitation rather than simulated success rates.

### E07: robustness and generalization

Evaluate missing renal function/weight/allergies, contradictory evidence, near-duplicate retrieval, wrong/stale/irrelevant experience, long records and knowledge-service failure. Stratify by condition, route, renal evidence and supportive category. Report rare-event counts and intervals. External-center validation requires authorized independent data under the same protocol; MIMIC-III/IV source overlap means they are not automatically independent centers.

## 6. Statistics, reproducibility and paper structure

Prespecify H1 serious clinical errors and H2 supportive indication/omission outcomes; mark other analyses exploratory or adjust multiplicity. Resample MIMIC by patient and public tasks by paired question. Report effect sizes and 95% intervals, including negative findings.

Each run records code commit, data/split/mapping hashes, task and actual inputs, label/knowledge coverage, method revision, base model/quantization, prompt/schema, seed, budgets, hardware, start/end times, retry/failure policy, local case traces and aggregate paths. Generate tables from results. Publish code and aggregates; keep credentials, restricted case data and derived training weights private.

Paper order: abstract, introduction/claims, related work, task/data, harness/experience update, setup, method results, growth, ablations, clinical evaluation, public/tool evaluation, limitations/ethics, reproducibility. Abstract and conclusions contain completed evidence only.

Tables: 1 data and observability; 2A historical methods and 2B clinical orders; 3 ablations/budgets; 4 public full benchmarks; 5 FHIR. Figures: harness/state/experience flow, growth curves, clinical error/abstention/cost. Base-model variation belongs in explicit groups or the appendix and does not replace method comparisons.

## 7. Execution gates and current delivery

| Stage | Acceptance/output | Status |
| --- | --- | --- |
| P00 | Original template, active English source, provenance, compiler success | Complete this increment |
| P01a | Separate absent raw orders and unmapped-only orders; matching pilot denominator | Complete this increment |
| P01b/P02 | Timing/mapping protocol, order schema, knowledge coverage, confirmatory split | Development timing/mapping/order protocol executed; confirmation and clinical coverage pending |
| E01 foundations | Common-protocol direct/retrieval/GAMENet/SafeDrug with documented adaptations | Direct/retrieval/three-seed GAMENet adaptation executed; SafeDrug resources pending |
| E01 harness | Full orders, checks/revision/abstention, original PRISMATIC/SafeRx controls | Bounded 50-case harness and ten-case order probe executed; clinical completion pending |
| E02/E03 | Fixed-test/budget growth and key ablations; no test-memory updates | Pending harness |
| E04 | Complete orders, independent ratings, adjudication and clinical aggregate | Reviewers available; outputs/ratings pending |
| E05 | Full specified method arms and option sensitivity | Partially complete |
| E06 | Reproducible actual FHIR execution and scoring | Infrastructure dependency outstanding |
| E07/final | Robustness, consistent figures/tables, references and compiled English manuscript | Pending main experiments |

This increment's [audit report](../upgrade_v4/README.md) and JSON files provide actual outcomes. In the 4,000-case pilot, 1,144 admissions have no recorded raw six-hour order, 152 have orders but no mapped class, and 2,704 have mapped labels. The full cohort has 58,982/8,004/134,764 respectively. Unparseable prescription starttimes occur in 497 admissions (2,364 rows), with window membership unknown.

The input-time audit finds zero missing decision times, included home-medication charttime violations, duplicate admissions or cross-split patients. However, triage has no timestamp and medrecon lacks storetime; availability is therefore not fully verified. Laboratory charttime/storetime checks remain necessary before adding labs. The English paper reports these limitations, retains previous F1 values as developmental evidence, and compiles successfully. Detailed run IDs and updates are appended to the Chinese ledger and [change log](CHANGELOG.md); English content is maintained alongside them.

### Executed batch r1 / order normalization r2 (14 October 2026)

See [actual English results](../upgrade_v4/RESULTS.en.md) and the [executed protocol](../upgrade_v4/PROTOCOL.en.md). The new train-40k mapper and route audit are complete; dual-timestamp laboratory extraction excludes 2,127 late-stored records. The development unknown-label and complete-order contracts are implemented. Fully verified input availability and a new confirmatory split remain unresolved.

Three-seed 4,000-case SGD and GAMENet text/single-visit adaptation reach mean F1 .3864 and .3436. A fixed-backbone, identical-50-case direct/repeat/retrieval/bounded-harness comparison yields .2445/.2445/.2871/.2082; the harness does not improve F1 and abstains excessively. Ten-case order generation has 4/10 raw schema validity per arm; explicit-unknown ATC normalization yields 9/10 parseability without implying model correctness. Seven contract tests pass.

The author-linked DDI source is now available, but SafeDrug's compatible ATC-L4 molecular mapping and SafeRx's compatible input/knowledge adapter remain missing. Table 2 in the active English paper distinguishes the 4,000-case and same-50-case panels. Next engineering repairs concern order encoding/truncation and over-abstention on validation data; clinical knowledge, reviewers, case growth and confirmation remain required. Original negative results are preserved.

### v0.5 executed: empty-output repair, ranking and experience updates (2026-10-14)

Delivered [v0.5 executed results](../upgrade_v5/RESULTS.en.md) and the [architecture diagram](../upgrade_v5/ARCHITECTURE.md).

- **E01 engineering repair:** trace all 50 cases; all 25 empty arrays are valid and 20 erase nonempty proposals. Separate historical predictions from clinical unknowns; preserve valid code members and recover invalid revisions.
- **E01 measurements:** free review F1=0.31130, empty rate=0%, versus v4 0.20820 / 50%. Validation-gated harness F1=0.41015; not a clinically complete order result.
- **E02/E03 conditional memory:** freeze an 8,000-case base, replay 250/1,000/4,000/16,000/32,000 episodes with 30 neighbors and validation-selected updates. Base/final F1=0.34727/0.35281, non-monotonic. Vocabulary/mapping fixed from the common 40k training cohort; not end-to-end low-data learning.
- **Strong baseline and negative ablations:** static ensemble three-seed mean 0.39176; 10% memory fusion 0.39022 is worse than seed-42 static 0.39185. Validation also rejects LLM candidate edits. All failures are retained.
- **Verification:** eight contract tests; independent recalculation of LLM and 4k aggregates; embedded class unchanged; active English source updated in place and checked with the built-in compiler.
- **Outstanding:** clinician-rated experience, supportive/fluid full orders, ingredient-level knowledge, compatible SafeDrug/SafeRx implementations, independent patient confirmation and live FHIR. No claim of surpassing these original methods.
