# External eICU feasibility audit

[English results](RESULTS.en.md) / [中文结果](RESULTS.zh.md)

The registered hospital split and complete-source audit are executed. This directory reports data feasibility and development vocabulary coverage; it contains no model prediction scores.

- `protocol.json`: fixed time, cohort and hospital/patient partition rules.
- `audit_source.py`: full-source counts, time/missingness checks, private cohort membership and source-checksum verification.
- `audit_native_codes.py`: HICL/name availability and train-only vocabulary ranking with development coverage.
- `report.py`: bilingual reports from aggregate JSON.

All raw tables, hospital assignments and membership files remain in the authorized restricted directory. A distinct training/evaluation protocol must be frozen before model experiments. Native HICL labels and eICU order fields are not asserted to match MIMIC or RxNorm protocols.
