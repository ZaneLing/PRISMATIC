# v0.24 — External eICU hospital-split data audit

## What was executed

Scan all 200,859 stays,7,301,853 medication records and 39,132,531 lab records. The proposed decision is ICU admission plus 6h, with new orders in the following 6h identified by order time. Adults with complete window follow-up and medication documentation somewhere in the stay yield 142,485 retained stays after cross-partition patient filtering. No model is fitted and no prediction score is generated.

Hospitals are assigned by a fixed hash to train/proposal/guard/test. Cross-partition patients retain stays only in their highest-priority partition (test first);1,457 other stays are dropped. Patient and hospital overlap are both zero. Zero-target stays are retained rather than treated as model failures.

## Fixed hospital partitions

| Split | Stays | Patients | Hospitals | New-order rows | Zero-target stays |
|---|---:|---:|---:|---:|---:|
| train | 108772 | 81555 | 128 | 232413 | 48362 |
| proposal | 12000 | 10000 | 13 | 26535 | 5051 |
| guard | 13525 | 10896 | 17 | 26125 | 6562 |
| test | 8188 | 6353 | 16 | 17430 | 3842 |

## Drug identity and reachability

Filtering to nonempty names would lose coded orders:6,283 test-window rows have no name, but 6,064 retain valid HICL;219 have neither. HICL is a native code identity, without an established equivalence to RxNorm or MIMIC labels. Training contains 1,306 distinct HICL codes,177 associated with multiple raw names.

| Split | Target rows | Valid HICL | Missing name, valid HICL | Neither name nor valid HICL |
|---|---:|---:|---:|---:|
| train | 232413 | 215446 | 75544 | 5046 |
| proposal | 26535 | 26011 | 12821 | 238 |
| guard | 26125 | 25371 | 8441 | 338 |
| test | 17430 | 16985 | 6064 | 219 |

## Development vocabulary coverage / 开发词表覆盖

| Train vocabulary size | Train coverage (%) | Proposal coverage (%) | Guard coverage (%) |
|---|---:|---:|---:|
| 64 | 64.78 | 61.91 | 65.41 |
| 128 | 80.68 | 78.84 | 80.01 |
| 256 | 91.45 | 89.41 | 90.18 |
| 512 | 97.84 | 96.69 | 97.52 |

Vocabulary ranking uses training-stay code frequency; coverage counts unique stay/code pairs. Only train/development capacity is measured, without test-capacity tuning. A final missing-identity policy, output schema and matched training budgets remain to be frozen.

## Time audit and limits

- Of 7,768,438 finite measurements drawn by the decision,238,680 were revised later and must be excluded from early inputs;7,529,758 meet both clocks.
- 154,701 medication rows start within the target window but were ordered outside it. These clocks are not interchangeable.
- Final cancellation flags do not filter targets because cancellation time is absent. The target is recorded order creation, not administration or an optimal prescription.
- Medication storage times and full field histories are unavailable; prospective availability is not established. Requiring medication documentation somewhere in the stay is retrospective selection.
- Dosage strings and separate frequency fields define a different proposed joint-order task from MIMIC dose/unit tuples. Results must remain in a separate panel.

Patient data, hospital mapping and membership remain local; only aggregates and hashes are published. Sources: [medication](https://eicu.mit.edu/eicutables/medication/), [lab](https://eicu.mit.edu/eicutables/lab/), [patient](https://eicu.mit.edu/eicutables/patient/).
