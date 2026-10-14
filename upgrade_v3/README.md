# PRISMATIC v0.3 experiments / v0.3 实验说明

The [Chinese](../paper/latex/v0.3/prismatic_v03_zh.tex) and [English](../paper/latex/v0.3/prismatic_v03_en.tex) manuscripts are standalone LaTeX files and have both compiled successfully in the Codex desktop editor. Table 2 is the method-level MIMIC prescription table. Rows with `--` have no same-protocol score. Do not copy published GAMENet, SafeDrug or SafeRx-Agent scores into it.

中英文论文均为独立 LaTeX 源文件，已编译成功。表 2 的行是处方方法；`--` 表示尚无同协议分数，不应填入其他论文的原始数值。

## Private MIMIC task / 受限 MIMIC 任务

- Dataset: MIMIC-IV v3.1 + MIMIC-IV-ED v2.2 under `/Users/bytedance/Desktop/MedTreeBench/dataset/restricted`.
- Decision: admission during ED stay. Features: chief complaint, acuity, vitals, admission metadata, pre-admission medication reconciliation. Targets: prescriptions starting in the next six hours, all routes, ATC-L4 (five-character codes).
- Source cohort: **all 201,750** ED-to-hospital admissions satisfying the decision-time criterion, 107,097 patients. Admissions with no subsequent oral drug or mappable ATC order remain included. The older v0.2 cohort selected on a future oral order; v0.3 removes that condition.
- Split: patient-disjoint deterministic BLAKE2b salt `patient-split-2026`, 80/10/10, before admission sampling.
- Public mapping: SafeDrug official `data/input/RXCUI2atc4.csv`, commit `88ce5c377dcdc2aa01aaa88f5478dfa4373ba49a`, SHA-256 `162fefc5cc374ac545501dec0d3738cb7a362e1e08b46b64d1a779eaeda7888e`. Only unambiguous NDC mappings; GSN and drug-name fallback learned on training patients at ≥10 observations and ≥98% purity.
- Coverage: 816,348/1,788,195 historical six-hour orders = **45.652%**. Missing mapping is a key constraint. All 253 observed ATC-L4 labels stay local in the cohort; the current model output space is the 80 most common training classes.
- Pilot budget: 40,000/4,000/4,000 admissions; identical validation and test patients, fields and five predictions per case. Training compute differs by method, so only case and output budgets are controlled in the pilot.
- Outputs: [admission cohort audit](results/admission_cohort_audit.json), [mapping audit](results/atc4_mapping_audit.json), [method results and paired patient bootstrap](results/atc4_method_pilot.json). These score historical order overlap, not clinical correctness.

To reproduce locally, install `upgrade_v2/requirements.txt`, clone the pinned public SafeDrug commit and run:

```bash
python upgrade_v2/build_cohort.py --include-unlabeled --hours 6 --output /path/to/restricted/prismatic-v3/admission_cohort_6h.parquet
python upgrade_v3/build_atc4_cohort.py --base /path/to/restricted/prismatic-v3/admission_cohort_6h.parquet --public-map /path/to/SafeDrug/data/input/RXCUI2atc4.csv
python upgrade_v3/run_atc4_methods.py
python upgrade_v3/prepare_clinical_review.py
```

The patient-level cohort and [200-case review manifest audit](results/review_sample_audit.json) are written only under `restricted/prismatic-v3`. The manifest has 25 cases in each of eight supportive-order strata and includes only common held-out test patients. The [bilingual review protocol](CLINICAL_REVIEW_PROTOCOL.md) defines blinded independent ratings, adjudication, denominators and missing-data handling. It is **not** a completed clinical evaluation.

## Public secondary tasks / 公开次级任务

Only pinned public benchmark questions went to OpenRouter, with `zdr=true`, `data_collection=deny` and temperature 0. Restricted MIMIC records were never sent. Public source commits: RxSafeBench `a25f9a1f173cf034b678c60f051901e86fbbbbb2`, RxQA `203979bf928c1fe9e45aa89e2ed76c3d2a63b503`.

| Task and method | Correct / N | Accuracy | Cost, USD |
| --- | ---: | ---: | ---: |
| RxSafeBench 2,000, DeepSeek direct | 924/2,000 | 46.2% | 0.1486 |
| RxSafeBench 2,000, normal second call | 878/2,000 | 43.9% | 0.2764 total |
| RxSafeBench 2,000, quote-gated light harness | 952/2,000 | 47.6% | 0.5006 total |
| RxQA OpenFDA 300, DeepSeek direct | 186/300 | 62.0% | 0.0114 |

The RxSafeBench light harness minus direct difference is +1.4 percentage points, paired 95% bootstrap CI −1.1 to +3.85 points; it fixed 338 first-answer errors and harmed 310 first-answer correct cases. Quote presence is not a clinical evidence check. Full reports and public-case predictions: [RxSafeBench direct](results/openrouter_rxsafe_full.json), [paired second-call arms](results/openrouter_rxsafe_full_harness.json), [RxQA](results/openrouter_rxqa_full.json). This is distinct from the complete EHR prescription harness.

## Method reproduction and tool status / 方法复现与工具状态

The public [GAMENet](https://github.com/sjy1203/GAMENet), [SafeDrug](https://github.com/ycq091044/SafeDrug) and [DREAM](https://github.com/novzyg/DREAM) implementations were inspected. Their original diagnosis/procedure/history inputs are not the same as the admission-time snapshot; SafeDrug additionally needs a molecular representation in the target medication space. Any common-input run requires a documented independent adaptation and a usable DDI/molecule mapping. No numeric result is yet available on our MIMIC split for GAMENet, SafeDrug, SafeRx-Agent or the complete prescription harness. These rows are therefore blank.

MedAgentBench's official setup requires a live Docker FHIR server and an external reference-solution file. Neither Docker nor its socket nor that file was available on this host, so no real tool-state test was run; see [feasibility audit](results/medagentbench_feasibility.json). A text-only simulation would not count.

## Next release gates / 下一版门槛

1. Improve RxNorm/ATC coverage on the newly unconditioned ED admission cohort; report missingness by route/class.
2. Run temporally valid independent GAMENet/SafeDrug/SafeRx-Agent adaptations on identical patients, labels and scorer, with pinned versions and compute budgets.
3. Produce complete ingredient/dose/route/frequency and saline purpose/volume/rate outputs, then run direct, retrieval and full-harness arms with matched model and call budgets.
4. Assemble local review cards only from timestamp-verified pre-decision evidence. Obtain two independent blinded scores, adjudicate disagreements and release aggregate error rates with patient-level paired intervals.
5. Bring up a real MedAgentBench FHIR server and run state-changing tasks; report task completion and state verification separately from multiple-choice accuracy.
