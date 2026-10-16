# RxRSIAgent: current measured configuration

**Current:** [selected_agent.py](selected_agent.py), [selected_profile.json](selected_profile.json), [English results](../upgrade_v35/RESULTS.en.md), [中文结果](../upgrade_v35/RESULTS.zh.md).

Three calls ×1536 output tokens: observable facts → drug-label identity/route/section retrieval → option assessment → executable quote/arithmetic checks → final decision → eligible supervised calibration. Measured scores: **556/988 RxSafeBench;199/300 RxQA**. RxQA remains below higher-budget MedAgents208/300. The calibrator is ordinary supervised learning; no language-memory update is accepted in the current two four-round experiments.

```python
from rxrsiagent.selected_agent import SelectedRxRSIAgent

# Requires the trusted local model artifact, matching the selected profile hash,
# the original source caches, and configured public OpenRouter client.
agent = SelectedRxRSIAgent()
result = agent.solve({"id": "public-example", "dialogue": "...", "options": ["...", "..."]})
```

`solve` invokes the external model provider. Use public benchmark cases under the recorded data policy. `finalize(case, saved_trace)` is the no-network calibration path. After calibration changes a choice, `final_explanation` is null and the prior explanation is separately labeled. The binary is not uploaded; train/rebuild with [calibrate.py](../upgrade_v35/calibrate.py), and verify its hash before loading.

The selected entry reproduces every saved final prediction on988+300 cases without new API calls: [entrypoint_check.json](../upgrade_v35/results/entrypoint_check.json). Sources, code and selection are pinned in the [test freeze](../upgrade_v35/test_freeze.json). Source quotes/arithmetic checks are not clinical safety validation; strength, formulation, renal adjustment and full DDI verification remain incomplete.

## Preserved interfaces and historical evidence

`core.py`, the package-level `RxRSIAgent` interface, `evaluated_profile.json` and existing contract audits preserve the earlier one-call checkpoint. They are **not the current paper's inference entry**. Their documentation is archived in [v0.34 source](../paper/versions/v0.34_source/rxrsiagent_README.md). No old audit is relabeled as evidence for the new agent.

The18-domain [clinical registry](clinical_skills.json), [clinical evaluation protocol](clinical_evaluation_protocol.json) and [blank annotation template](clinical_review_template.json) remain available. Most declared clinical tools require further implementation/validation. Two reviewers are available; annotations have not been received.
