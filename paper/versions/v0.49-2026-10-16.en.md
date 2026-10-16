# Literal-schema prescription experiment: completed negative results

The complete 1,082-admission RxRSIAgent runs finished. The broader method comparison was **interrupted** after a controlled training probe identified format-example anchoring. SafeRx/SkeMex/FLAME results are not claimed here. The corrected experiment is in [upgrade_v50](../upgrade_v50/README.md).

| Completed method | Drug F1 | Core4 F1 | Core5 F1 |
|---|---:|---:|---:|
| rxrsi_base | 7.34% | 3.53% | 1.97% |
| rxrsi_selected | 7.27% | 3.33% | 1.88% |

One conditional fact-scope update passed development but failed on test: drug F1 7.34→7.27%, Core4 F1 3.53→3.33%. It adds 3 correctly predicted drugs and 138 extras. Patient-cluster 95% drug-F1 difference interval: [-0.592,+0.439] pp. Acceptance is not generalization.

The frozen supervised top-8 initializer plus common order tool reaches drug/Core4 F1 17.57/10.58%. RxRSIAgent does not beat it. Targets outside the fixed candidate catalogue remain in recall.

## Controlled training probe

The same 48 training cases, unchanged candidate contents and batch layout:

| Format / 格式示例 | Drug F1 | A1 selected | A23 selected |
|---|---:|---:|---:|
| Original A1/A2 | 3.57% | 36 | 5 |
| A23/A24 example | 3.39% | 0 | 46 |
| Descriptive schema | 7.57% | 8 | 3 |

This confirms an interface shortcut in this adapter. Descriptive-schema repair is researcher engineering, not RSI, and is applied to all common local controls. The small-sample F1 interval includes zero; test gains are not implied. See `results/schema_probe.json` and `schema_probe_protocol.json`.

No patient records or generated clinical text are published. New paid API expenditure: USD0. The test is historically exposed and exploratory.
