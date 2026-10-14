# v0.22 — Numerical-state representation pilot

## Question and predeclared design

Does a more faithful representation of already-available numerical state improve selection? The v0.21 text policy tokenizes lab numbers and prior doses as words. This pilot adds standardized numerical values with explicit observed flags, prior-drug/route presence and demographics. Input vocabulary and robust numerical scales are fitted only on the initial8k training contexts. Units stay distinct; no clinical threshold or future information is added.

Two feature views (typed alone or word+typed), three regularizers and seven thresholds compete on the2,000-case proposal split. One candidate then faces the same2,000-case guard as the preselected word/character control. Both use40k training cases, seed42,128 labels, at most20 outputs, and the unchanged v0.21 full-data conditional order tool. The comparator keeps its original proposal-selected tool setting. **No v0.21 test score is computed by this pilot.**

## Actual development results

| Method | Guard drug F1 | Guard core-order F1 | Mean drugs | Empty (%) |
|---|---:|---:|---:|---:|
| Selected typed-state intervention | 0.22456 | 0.13656 | 5.20 | 2.30 |
| Existing word/character control | 0.21942 | 0.13458 | 4.51 | 5.40 |

Selected view / 选中表示：`word_plus_typed_state`; alpha=`1e-05`; threshold=`0.1`.

Drug/order differences / 药物与订单F1差值：+0.00514, +0.00198; patient-cluster95% intervals / 患者聚类区间：[-0.00057, +0.01079], [-0.00237, +0.00652].

Declared guard rule passed / 是否通过预设检查：**True**.

## Interpretation

Predictions were independently recounted; learned parameters are finite. This changes the selection representation and parameters, not language-model weights, executable tools or clinical knowledge. It is an engineering/development intervention, not recursive self-improvement or a held-out test win. The guard has been used in preceding development and this pilot has one seed. Even a positive result needs a registered round-wise, equal-data, multi-seed comparison and fresh confirmation. All patient data, features, numerical statistics, weights and predictions remain local.
