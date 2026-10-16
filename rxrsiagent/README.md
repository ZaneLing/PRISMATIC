# RxRSIAgent — current frozen inference entry

Use [selected_agent.py](selected_agent.py) and [selected_profile.json](selected_profile.json). Current results:491/988 RxSafe,196/300 RxQA,274/467 MedPIC. The selected procedural state is empty: no update passed the declared gates. This is not evidence of successful RSI or best-method performance.

```python
from rxrsiagent.selected_agent import SelectedRxRSIAgent

agent = SelectedRxRSIAgent()
result = agent.solve({
    "id": "public-example",
    "dialogue": "...",
    "options": ["...", "..."],
    "multiple": False,
})
# prediction is a sorted list of option letters, or None for invalid output.
```

Requires the existing public source caches and configured OpenRouter client. `solve` invokes the provider unless requests are cached. No calibration pickle or numerical answer override is used by this entry. The current runtime normalizes malformed search-focus types; its declared post-freeze repair completed two missing cases and preserved986 previous files byte-for-byte.

- [English results](../upgrade_v44/RESULTS.en.md) · [中文结果](../upgrade_v44/RESULTS.zh.md).
- [Freeze](../upgrade_v44/test_freeze.json) · [runtime amendment](../upgrade_v44/runtime_amendment.json) · [audit](../upgrade_v44/results/audit.json).
- Ordinary supervised calibration remains separately available as `upgrade_v35/supervised_control.py` with its archived profile. Its556/988 score is not procedural evolution.

## Historical interfaces

The package-level `RxRSIAgent` import from `core.py`, `evaluated_profile.json` and older contracts preserve earlier experiments. They are not the current paper's entry. No old audit is relabeled as validating the new runtime.

The clinical registry and annotation protocol remain available. Many clinical functions are incomplete; two reviewers have not yet supplied ratings. Exact quotes, arithmetic and narrow threshold checks do not establish clinical prescribing safety.
