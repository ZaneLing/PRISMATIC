# Failure-directed product-scope study

Read [中文 results](RESULTS.zh.md) or [English results](RESULTS.en.md). These are development candidates, not promoted main-table results or autonomous RSI.

## Reproduce with the existing local public caches

```bash
python upgrade_v45/run.py --mode freeze
python upgrade_v45/run.py --mode train
python upgrade_v45/run.py --mode proposal
python upgrade_v45/run.py --mode guard
python upgrade_v46/run.py --mode freeze
python upgrade_v46/run.py --mode train
python upgrade_v46/run.py --mode proposal
python upgrade_v46/run.py --mode guard
python upgrade_v47/run.py --mode freeze
python upgrade_v47/run.py --mode development
python upgrade_v45/case_audit.py
python upgrade_v45/audit.py
python upgrade_v47/audit.py
python upgrade_v47/check_runtime.py
python upgrade_v45/recount_mimic.py
python upgrade_v45/report.py
python paper/render_acl.py
```

The MIMIC recount requires authorized local restricted artifacts from the earlier study. It makes no provider requests. Raw patient data, provider receipts and full label bodies are not committed. Model inference only receives public questions. Source availability is capped at800 cached queries; newly unavailable requests remain unknown. Exact replay requires retained source caches; a fresh live download is not guaranteed to recover identical labels or query scheduling. Reused development scores do not constitute new independent validation.

See `protocol.json`, `results/audit.json`, `results/source_manifest.json`, and `results/mimic_recount.json`. The existing main entry remains frozen under `rxrsiagent/selected_agent.py`.
