# Independent development continuation: three candidates rejected

This experiment continues after the main source/calibration run. It did not stop at an observed small gain:three further mechanisms were actually executed. All failed the declared strict-improvement gate on independent development.

| Candidate | Correct/120 | Fixes/regressions vs static | New guard/test |
|---|---:|---:|---|
| Static source workflow |99|reference|not needed|
| Full source sections |99|4/4|not run|
| Independent draft and contradiction review |99|7/7|not run|
| Three retrieved training examples |99|5/5|not run|

Each candidate uses3×1536 output allowance. The training-memory variant uses9936 external train examples, so is not equal-data. The memory archive has no exact normalized text overlap with the prepared development questions or prior main benchmarks. Earlier independent MedQA200 questions also have zero exact overlap with the full downloaded training split; the initial optional filename in the example-memory loader did not point to that artifact, but the separate full-source exclusion audit confirms zero membership impact.

## Data and selection

`prepare.py` pins the public MedQA training mirror, source revision, parquet hash and120+120 question membership. The input-only medication/treatment rule produces784 eligible examples. Only proposal120 is used:all three candidates tie the baseline, so the untouched guard120 and RxQA are not run. This is general medical-exam development and includes some questions referencing unavailable images. No RxQA per-item mistakes or answers select these candidates.

`experiment.py`:static vs expanded source context. `contrast.py`:researcher-authored reflection on the first8 independent proposal errors. `experience.py`:TF-IDF retrieval of3 non-evaluation training cases, with explicit applicability and non-authority instructions. Prompt/tool changes are engineering interventions, not autonomous code evolution. Requests share a cross-process lock for identical prompts.

`audit.py` checks1556 source spans, final answers, executable checks and rejection gates. [audit.json](results/audit.json) retains complete metrics. Successful-response ledger increment:USD0.892790. No candidate is promoted to the main table. [Full bilingual results](../upgrade_v35/README.md).

Do not rerun `prepare.py` in the existing directory:it would replace the split/protocol/ledger-start record. For a new experiment, create a new run directory and protocol. Runners require the pinned local public data and source caches; raw data is not in Git.
