# v0.13 — Outcome-aware revision verifier

[English executed results](RESULTS.en.md) · [中文结果](RESULTS.zh.md)

Complete: three seeds, four rounds, uniform and pre-update-error-prioritized feedback, same two-call budget, ordinary supervised and fixed-tool controls. No new API calls.

```bash
python -m unittest discover -s upgrade_v13 -p 'test_*.py'
python upgrade_v13/run_outcome_evolution.py
python upgrade_v13/summarize.py
```

Uses the complete public v0.11 trace cache. Private working-cache paths are not published. Protocol and all configuration choices are saved before this increment scores test outputs. The test was used in prior increments, so these are exploratory development results.
