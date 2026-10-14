# Public benchmark coverage and exact evaluation scope

## RxQA: the entire public OpenFDA component

The official release contains **300 OpenFDA questions**, all of which are used for transfer. They are not a sampled subset of the publicly released component. The BNF-derived questions are not publicly released because of licensing restrictions and are not evaluated here. [Official release and scope](https://github.com/Google-Health/rxqa).

A fresh independent audit verifies the pinned CSV hash, 300 unique question IDs, the complete transfer membership, original option order and every answer label. It also recounts all four matched v17 methods from saved per-question predictions:

| Method | Correct / all public questions | Accuracy |
|---|---:|---:|
| cot | 193/300 | 64.33% |
| author_grasp | 189/300 | 63.00% |
| fixed_grounded | 188/300 | 62.67% |
| evolving_grounded | 183/300 | 61.00% |

These are existing results, independently recounted here. Skill evolution does not improve transfer in this comparison. The historical v3 direct prompt scores186/300; it is a different prompt/budget snapshot and is not substituted for the matched CoT row.

## RxSafeBench: raw release, deduplication and evolution split

The pinned two source files contain **2,443 records**, consistent with the official release description. Deduplication by task type, exact dialogue and correct drug yields **2,000 derived three-option cases**. Historical direct/reconsideration/light-review runs cover all 2,000 cases. This conversion is different from the original medication-generation evaluation; its scores cannot be compared numerically with the official leaderboard. [Official benchmark](https://github.com/CAS-SIAT-XinHai/RxSafeBench).

| Historical fixed method | Correct / unique cases | Accuracy | Fixes / regressions vs direct |
|---|---:|---:|---:|
| direct | 924/2000 | 46.20% | reference |
| repeat | 878/2000 | 43.90% | 72 / 118 |
| harness | 952/2000 | 47.60% | 338 / 310 |

Later adaptive experiments partition these same 2,000 cases into625 training,190 proposal,197 guard and988 test cases, with no question/scenario-group overlap. Those methods are compared on the **same988 test cases**; reporting all2,000 as their held-out test would include adaptation data. The historical full-set table and the later frozen-test table therefore remain separate.

## Metadata correction and audit limits

The archived v3 full-harness report retained a stale “30+30” sample description. Actual source identities and all saved predictions independently verify **2,000 cases per method**. The archived report is preserved; this document and its audit record correct the description. The English manuscript now names RxQA as the complete public OpenFDA component. No scores or original predictions are changed.

This audit verifies coverage, conversion and saved-answer counting. It does not establish clinical safety, official benchmark equivalence or a new method improvement.

[Coverage audit and hashes](public_benchmark_coverage.json) · [Current public method comparison](../upgrade_v17/RESULTS.en.md)
