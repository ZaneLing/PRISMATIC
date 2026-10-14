# v0.31 — Parameter evolution with randomized candidate positions

## 1. Motivation and implemented comparison

The prior v0.26 diagnostic found near-universal display-prefix selection in the trained adapters. This local experiment keeps original retrieval ranks, candidate identities and order fields visible while randomizing display positions during supervision. It separates a representation repair from error-specific learning using four arms: ranked uniform, permuted uniform, permuted own-error priority and permuted shuffled-error priority.

Each of three seeds receives three600-case patient blocks in a declared order. Every round samples400 accumulated admissions without replacement and performs100 QLoRA steps, batch4, updating the last eight layers of the same Qwen3-4B backbone. A model predicts each new block before those outputs generate sampling priorities. Earlier priorities retain their original pre-update errors; the study does not rescore every earlier case. Fixed candidate tools and recorded order templates do not evolve.

Checkpoint selection uses100 proposal admissions under ranked and permuted views, including base as an option. Training continues from each latest raw adapter. Only after all four arms freeze three rounds does a seed evaluate all raw checkpoints on the200-case report-only guard under ranked, permuted and reversed views. The500 old test admissions are excluded; these are exploratory development results on the legacy admission-proxy task, with incomplete entry-time provenance and no novel dose generation.

## 2. Execution and data integrity

- Completed optimizer runs / 已完成训练回执：**0/36**
- Updates with completed proposal evaluation / 已完成proposal评价的更新：**0/36**
- Unique local model responses saved / 已保存本地唯一模型响应：**800**
- Audited complete seeds / 已完整核验种子：**0/3**

The data audit checks33,300 transformed views with zero patient-role overlap, unchanged candidate sets/GT and no target truncation. The longest complete sequence has1005 tokens against a1,536-token limit; each target has69 tokens. Eleven synthetic execution checks cover target transport, prompt blindness, shuffled-weight identity and loss masking. These are integrity checks, not performance gains.

Before any generation/fitting, a synthetic probe confirmed that the installed trainer included one trailing padded target per sequence. All four arms use the same strict completion-only loss excluding that position, via a wrapper that leaves the installed library unchanged. This does not identify the cause of the historical collapse; the new ranked-uniform control shares the correction.

## 3. Independently recounted proposal results

Proposal scores select checkpoints and are not test results.

| Seed | Arm | Raw round | Ranked drug/order F1 | Permuted drug/order F1 | Accepted round so far |
|---:|---|---:|---:|---:|---:|
| 42 | base | 0 | 0.16846/0.10223 | 0.14129/0.09434 | 0 |

Only completed, independently audited states contribute to guard comparisons. For each completed update, audits check source receipts, sampled examples, finite changed adapter tensors and 100-step logs. The floating-point optimizer trajectory is not independently refit.

## Artifacts / 交付

- [Frozen protocol](protocol.json)
- [Actual data audit](results/data_audit.json)
- [Synthetic runtime checks](results/runtime_probe.json)
- [Execution progress](results/progress.json)
- [Earlier position diagnosis](../upgrade_v26/RESULTS.en.md)
