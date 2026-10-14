# v0.12 — controlled gate and routing audit

[English results](RESULTS.en.md) · [中文结果](RESULTS.zh.md)

This completed three-seed experiment replays actual complete public model outputs. It makes no network requests. `run_gate_audit.py` fits/fixes every version before scoring cached test predictions. `summarize.py` independently recounts cases and round transitions, computes paired scenario-cluster intervals and produces bilingual reports.

```bash
python upgrade_v12/run_gate_audit.py
python upgrade_v12/summarize.py
```

Inputs are the locally cached v0.11 counterfactual evidence reviews. The published artifacts contain only aggregate results, protocol and parameter fingerprints. This increment is an exploratory development extension on a previously observed test, not independent confirmation.
