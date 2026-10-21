# RxRSIAgent — order-specific memory and clinical applicability audit

Entry points: [研究更新](RESEARCH.zh.md), [research update](RESEARCH.en.md), [中文结果](RESULTS.zh.md), [English results](RESULTS.en.md), [clinical review protocol](REVIEW_PROTOCOL.en.md).

## Reproduction

All clinical data must remain in the authorized local restricted directory. `common53.py` defines paths. Analysis uses the existing Python environment with NumPy, pandas, scikit-learn, joblib and DuckDB; local actor inference uses the existing MLX environment and pinned local models. There are no cloud inference requests.

```bash
# Run from the repository root with the appropriate local Python environment.
python upgrade_v53/prepare.py
python upgrade_v53/learn.py
python upgrade_v53/learn_library.py
python upgrade_v53/diagnose_development.py
python upgrade_v53/actor.py --model qwen --splits audit
python upgrade_v53/actor.py --model llama --splits audit
python upgrade_v53/evaluate.py
python upgrade_v53/review.py
python upgrade_v53/plot.py
python upgrade_v53/report.py
python -m unittest discover -s upgrade_v53 -p 'test_*.py'
python upgrade_v53/verify.py
```

The initial and training-template amendment states were frozen before reading fresh audit outcomes. The amendment was made after audit generation started. Preserve the saved freeze manifests; rerunning learning after outcomes are known is a reproduction, not a new unseen experiment. No audit-dependent checkpoint selection is implemented.

`runtime.run_case` takes a case without reference labels, initial orders and an optional experimental state. It returns orders, actual skill-execution traces and partial label-preflight findings. The default state is empty; research programs do not constitute clinical prescriptions. New learned rules and clinical cases stay restricted; public exports contain aggregate outcomes and hashes only.

The main clinical caveats are sparse future-order targets, incomplete patient context, unvalidated diagnosis-to-drug scope, exact-string joint fields, reused development cohorts and two small local backbones. Independent review is prepared but not completed.
