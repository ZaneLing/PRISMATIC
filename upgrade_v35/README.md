# Completed source-checking and experience-calibration experiment

[English results](RESULTS.en.md) / [中文结果](RESULTS.zh.md). Primary audit:[results/audit.json](results/audit.json). Current agent:[selected entry](../rxrsiagent/selected_agent.py).

## Executed stages

1. `workflow.py` + `evidence.py`:three-call controlled source workflow, explicit product/route identity, section-balanced retrieval, quotation and bounded arithmetic checks.
2. `run.py --arm {no_evidence,old_evidence,verified_evidence} --split {proposal,guard,test,rxqa}`:saved public inference.
3. `learn.py`, `learn_bound.py`:two four-round scoped-memory trajectories; all candidates rejected. `learn_bound.py` had a report-path correction before test; development history retains the original summary and hashes.
4. `run_active.py`:active second retrieval, rejected on proposal.
5. `calibrate.py --stage develop`:ordinary supervised logistic calibration, trained on625 examples; select on190 proposal, gate on197 guard. `test_freeze.json` records state/code before test.
6. `calibrate.py --stage test` and `--stage rxqa`:apply frozen numeric state to saved source-agent outputs.
7. `run_author_budget.py --method {medagents,mdagents} --split {test,rxqa}` and `run_grasp_budget.py`:same4608 total output allowance, with unequal calls and inputs explicitly reported.
8. `audit.py`:independent answer recount, source offsets, executed checks, learning gates and paired intervals. No network calls.
9. `calibration_diagnostics.py`:post-selection fixed-hyperparameter ablations; not new test-selected main models.
10. `write_report.py` and `../paper/render_acl.py`:aggregate-only bilingual reporting and in-place English manuscript rendering.

## Reproduction conditions

Use the established Python3.9 environment with numpy,scipy,scikit-learn,pandas and the public client in `upgrade_v8`. The original public dataset/cache is under local `rxrsi-v8`; source snapshots are under `rxrsi-v11`; this run's traces are under `rxrsi-v35`. Raw data, labels, credentials and the trained pickle are intentionally excluded from Git. Exact original scores require the saved response receipts because a served model at temperature0 can still return different responses.

The repository's protocol files bind the original experiment. For a genuinely new run, use a new run directory/protocol and explicit cost envelope; do not overwrite frozen original artifacts. Start with `python upgrade_v35/test_tools.py` and read the recorded data/source hashes. Audits assume local artifacts are restored. Inference commands may incur provider cost; report/audit commands do not.

The selected model is ordinary supervised calibration. It does not establish autonomous RSI or clinical prescribing safety. Expanded context, contradiction review and external training-memory continuation are fully reported under [upgrade_v36](../upgrade_v36/README.md).
