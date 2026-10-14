# v0.17 — Grounded skill evolution

This controlled extension combines the frozen openFDA evidence tool with the unmodified, pinned GRASP skill optimizer. It compares one-call grounded inference with and without skill updates, and the completed author-core control without evidence. Only skill files evolve. Evidence retrieval, label snapshot and backbone weights stay fixed. The optimizer is credited to GRASP; this is a task/harness integration, not a new optimizer.

625 training questions are exposed in four batches; the same 387 development questions select the skill state before 988-question testing. The already observed test makes this a development extension. RxQA provides a separate 300-question transfer check, including explicit missing drug-label matches. No restricted records are uploaded. `run_grounded_skills.py` saves protocol, skill hashes and actual results; pending runs are not evidence of improvement.
