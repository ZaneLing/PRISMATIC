# v0.10 — stronger published-method implementation control

This increment responds to the limitation of v0.8's simplified method adaptations. It executes the **unmodified GRASP author core**, pinned to commit `9d7d125a3e9b46ed591692475eb07aff4ae67d34`, through a medication-option `Task` adapter. It retains the author's failure classification, diagnosis, ADD/MODIFY/REMOVE proposals, balanced probes, hard regression gate, bounded skill repository and skill selection/injection.

This is the official core applied to a new task, **not an official MedAgentBench/FHIR-AgentBench benchmark rerun**. The adapter and runtime configuration are public. Development has the same 625 training and 387 validation/guard labels as v0.8; the original core allocates them differently. It processes four batches in one training pass, uses four proposals per update and a 40-case balanced probe. Actor cap is 512 tokens; the author's longer structured skill proposal format gets 3,072 tokens at temperature 0.7. Costs must be compared separately.

```bash
python run_grasp_core.py --seed 42
```

The source assertion verifies the pinned core has no edits. All test evaluation occurs after the best-validation skill library is frozen. Results are incomplete until both RxSafeBench (988) and RxQA (300) evaluations exist. Further RxRSI changes will be driven by training/development evidence, with their own version and confirmation results.


## Scoped RxRSI iteration and actual results

`run_scoped_rsi.py` learns explicit applicability phrases with each skill and injects at most two matching cards. Unmatched cases retain exactly the base prompt. Candidate rules are proposed from eight failed and four successful training traces, then evaluated on proposal/guard data. Four rounds completed without an accepted card because coverage was too narrow. Three applicability contracts pass.

[English results](RESULTS.en.md) · [中文结果](RESULTS.zh.md). The completed author-core control improves the common test, while our scoped variant remains flat; v0.11 continues with grounded evidence tools.
