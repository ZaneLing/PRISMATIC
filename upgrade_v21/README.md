# Recorded-availability-controlled prescription study

The v0.20 audit found that treatment start times do not reliably identify when an order was authored. This increment rebuilds targets from complete source tables and audits both provider and pharmacy clocks.

- [Cohort protocol](protocol.json), [frozen method protocol](evaluation_protocol.json)
- [Cohort manifest](results/data_manifest.json), [independent reconstruction audit](results/independent_cohort_audit.json)
- [English report](RESULTS.en.md), [中文报告](RESULTS.zh.md)

The registered suite runs three seeds and five cumulative training checkpoints, strong equal-data controls, prior-order reuse and conditional object freezes. It reuses the explicitly supervised v0.7 method family; it does not claim a novel optimizer or faithful GAMENet/SafeDrug reproduction. Test patients are disjoint from the older v0.6/v0.7/v0.9 tests.

## Local execution

1. `build_temporal_cohort.py` re-reads the complete restricted hospital tables.
2. `audit_cohort.py` independently validates saved source joins and case serialization.
3. `run_comparison.py` locks the method protocol, trains and freezes choices before within-seed test scoring.
4. `summarize.py` independently recounts every saved prediction and emits bilingual reports, paired patient intervals and trajectories.

All patient records, features, predictions and fitted models stay under the restricted dataset directory. Only code and aggregate outputs are committed. This is a retrospectively selected coherent-time, nonempty-target task; released tables do not provide complete field-version histories. Raw-name agreement is not clinical safety or equivalence to published ATC/RxNorm benchmarks.
