# v0.26 — Candidate position with retrieval rank retained

**Status: registered and running; no complete result yet.**

The completed binary parameter study exhibits catalogue-prefix selection. This diagnostic uses only its existing200-case/197-patient development guard and freezes the base model plus both selected round2 adapters. It does not retrain or select a winner.

| Condition | Candidate display | Original retrieval rank |
|---|---|---|
| original | Original prompt/order | Implicit in list order |
| ranked_explicit | Same order with rank annotation | Explicit on every candidate |
| permuted_rank_explicit | Deterministic case-specific permutation | Retained explicitly |
| reversed_rank_explicit | Reverse order | Retained explicitly |

Drug/order content and patient context are identical across conditions. O IDs and target masks are consistently remapped. Fresh original generations distinguish the added-rank prompt effect; explicit-rank comparisons change display positions while preserving the original ranking signal. This is a post-test-motivated development diagnostic, not an untouched confirmation test or an improvement claim.

Three frozen states × four conditions ×200 cases give2,400 logical evaluations. The local runner generates each distinct prompt once and saves immutable per-case receipts. All raw text and patient data remain in the restricted directory. Independent recount will report drug/order F1, empty/invalid rates, nontrivial prefix masks, medication-set agreement/Jaccard and descriptive patient-cluster intervals. No model/prompt promotion follows from this diagnostic. See `protocol.json` and `results/data_audit.json`.
