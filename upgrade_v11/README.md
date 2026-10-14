# v0.11 — grounded prescription evidence tools

[English executed results](RESULTS.en.md) · [中文实测结果](RESULTS.zh.md)

**Status: partial.** CoT, balanced/safety reviews and the four-round router are complete. The indication test and Gemini development requests are incomplete after HTTP 402; incomplete rows have no accuracy. The client now fails fast on account errors and the scorer rejects transport failures. A received malformed answer remains a model error.

Motivation from completed/development experiments: broad language reflections can regress correct decisions; narrowly memorized trigger rules barely cover new cases. The next increment adds retrieved drug-label evidence and compares a fixed evidence tool with feedback-selected tool configurations under equal evidence access.

`prepare_labels.py` queries only public candidate drug names from RxSafeBench. It sends no patient text or reference answers. It caches the response hash, label identifiers, effective date, exact query, matched names and failures. Missing labels remain missing. The source is [openFDA drug labeling](https://open.fda.gov/apis/drug/label/), which distributes company-submitted label records; its content is not uniformly FDA-verified. Labels are research evidence, not a clinical decision authority.

The completed first-stage development pilot motivates the executed two-call evidence-review study. `run_router_evolution.py` generates counterfactual training feedback, learns route parameters, freezes choices, then scores test. `summarize.py` independently verifies and reports only completed rows. The [v0.12 gate ablation](../upgrade_v12/README.md) reuses complete traces with three training orders.
