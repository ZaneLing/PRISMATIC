# Cumulative experiment spending audit

Snapshot: 2026-10-16T12:25:42.440004+00:00. [中文](TOTAL_COST.zh.md) · [Machine-readable audit](total_spend_audit.json) · [Recount code](audit_total_spend.py)

## Located provider-reported cost: approximately USD 89.53

The located successful-response records contain **USD 89.52684587–89.53179153**. The tiny interval reflects ambiguity over copied versus separately executed identical legacy records; it does not bound unrecorded charges. This is not a reconciled OpenRouter invoice, account balance or all-time project expenditure.

- Main append-only response ledger: **171,219 events, USD 87.79773723**.
- Legacy public experiments: USD 1.72910863 after exact-record deduplication, or USD 1.73405430 if all overlapping records represent separate executions.
- Cache reconciliation: 169,877 files; **0 successful cache replies absent from the ledger**. Cached rereads are not charged again in this audit.
- This audit makes **zero new inference/API requests**.

## Main ledger by returned model

| Returned model | Successful events | Input tokens | Output tokens | Reported USD |
|---|---:|---:|---:|---:|
| deepseek/deepseek-v4.1-flash | 166,028 | 308,511,214 | 23,282,810 | 65.384815 |
| google/gemini-3.8-flash | 5,123 | 7,694,568 | 2,067,895 | 13.525532 |
| anthropic/claude-opus-4.8 | 68 | 1,455,103 | 64,475 | 8.887390 |

This breakdown covers the shared ledger only. Earlier public experiments also used OpenAI models and are listed below; they are included in the overall total.

## Legacy stores (not individually additive without overlap handling)

| Canonical source | Received records without error flag | Recorded USD |
|---|---:|---:|
| `upgrade_v2/results/openrouter_rxqa_pilot_predictions.json` | 300 | 0.162941 |
| `upgrade_v2/results/openrouter_rxsafe_harness_pilot_predictions.json` | 360 | 0.796368 |
| `upgrade_v2/results/openrouter_rxsafe_pilot_predictions.json` | 180 | 0.135024 |
| `upgrade_v3/results/openrouter_rxqa_full_predictions.json` | 300 | 0.011396 |
| `upgrade_v3/results/openrouter_rxsafe_full_harness_predictions.json` | 4,000 | 0.479707 |
| `upgrade_v3/results/openrouter_rxsafe_full_predictions.json` | 2,000 | 0.148618 |

There are 86 identical overlapping legacy records and 6 records with no price/token/model metadata. They lack provider generation IDs, so copied results cannot be distinguished conclusively from identical independent calls. Sibling-folder mirrors are excluded.

The main ledger has 169,877 distinct request signatures and 1,342 additional events with repeated signatures. All are retained: the client appends only after a new successful response, whereas cache hits return without appending. There are 0 byte-identical duplicate ledger lines. Deduplicating by prompt hash would incorrectly remove possible paid repeated executions. Per-role costs are in the JSON.

## Unknown or excluded expenditure

- 16 logged transport-failure attempts can have unknown charges; discarded or overwritten legacy responses cannot be reconstructed.
- The main client defaulted absent usage cost to zero; its 1 zero-price record cannot be verified as free from this schema alone.
- Local CPU/MPS training has recorded runtime for some studies, but no electricity/hardware dollar meter. See [compute accounting](COMPUTE_ACCOUNTING.en.md). Unrecorded original 2025 experiments are not included.
- Codex/chat usage, subscription charges, taxes, funding fees, credits and refunds are outside this ledger.
- USD 22.370971562 for the trace-learning study and USD 3.19195587 for recent failure repairs are **already included** in the shared ledger. Do not add them again. Method-level logical costs include reused responses and cannot be summed as new spending.

Rerun `python paper/audit_total_spend.py` followed by `python paper/report_total_spend.py` after experiments finish. Report the snapshot and source hashes with every update.

<!-- UPDATER_REPAIR_COST -->

## 2026-10-20 updater repair increment

Provider-reported proposer receipts: USD 0.085203, within the USD 10 authorization. This increment is additional to the earlier approximately USD 89.53 located receipts. Local Qwen/Llama compute is unpriced. Aggregate-only requests are audited in `upgrade_v51/results/cost.json`; no patient records were sent.
