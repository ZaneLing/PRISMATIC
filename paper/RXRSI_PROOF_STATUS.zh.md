# 当前处方RSI证据

**完整命题仍未得到支持。** 本轮已经跑完实验。三种病例顺序分别保留5、4、4条规则，全部是删除，没有保留带实证反例的规则。首个预设顺序下，Qwen 药物F1从 6.61% 变为 6.65%；Llama 从 4.58% 变为 4.64%。F1提高或多余订单减少，均不能替代三类错误同时可靠下降的证据。

## 做了什么

[Full results / 完整结果](../upgrade_v53/RESULTS.zh.md) · [Research / 调研](../upgrade_v53/RESEARCH.zh.md) · [Review / 评审](../upgrade_v53/REVIEW_PROTOCOL.zh.md)

| Backbone / method | Drug F1 % | Native4 F1 % | Missed / patient ↓ | Extra / patient ↓ | Joint discrepancy / patient ↓ |
|---|---:|---:|---:|---:|---:|
| qwen / Frozen LLM agent | 6.61 | 1.49 | 1.516 | 6.980 | 7.223 |
| qwen / Fixed contract fallback (not RSI) | 6.60 | 1.49 | 1.516 | 6.992 | 7.234 |
| qwen / RxRSIAgent / order53 | 6.65 | 1.44 | 1.523 | 6.707 | 6.969 |
| qwen / RxRSIAgent / order153 | 6.63 | 1.43 | 1.523 | 6.727 | 6.980 |
| qwen / RxRSIAgent / order253 | 6.63 | 1.43 | 1.523 | 6.727 | 6.980 |
| qwen / Frozen supervised draft | 14.14 | 2.98 | 1.598 | 1.059 | 2.289 |
| qwen / Raw feedback correction replay | 5.94 | 1.31 | 1.555 | 6.734 | 7.086 |
| qwen / Learned actions without conditions | 6.23 | 1.21 | 1.562 | 6.082 | 6.371 |
| qwen / Shuffled reflection feedback | 6.60 | 1.33 | 1.527 | 6.652 | 6.969 |
| llama / Frozen LLM agent | 4.58 | 0.73 | 1.605 | 7.188 | 7.387 |
| llama / Fixed contract fallback (not RSI) | 6.72 | 1.30 | 1.488 | 7.625 | 7.684 |
| llama / RxRSIAgent / order53 | 4.64 | 0.75 | 1.605 | 7.066 | 7.270 |
| llama / RxRSIAgent / order153 | 4.63 | 0.74 | 1.605 | 7.090 | 7.293 |
| llama / RxRSIAgent / order253 | 4.63 | 0.75 | 1.605 | 7.082 | 7.285 |
| llama / Frozen supervised draft | 14.14 | 2.98 | 1.598 | 1.059 | 2.289 |
| llama / Raw feedback correction replay | 4.27 | 0.54 | 1.625 | 6.965 | 7.254 |
| llama / Learned actions without conditions | 4.21 | 0.69 | 1.637 | 6.535 | 6.789 |
| llama / Shuffled reflection feedback | 4.56 | 0.64 | 1.609 | 7.059 | 7.289 |
