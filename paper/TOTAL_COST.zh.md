# 历次实验累计费用审计

快照：2026-10-16T12:25:42.440004+00:00。[English](TOTAL_COST.en.md) · [可审计 JSON](total_spend_audit.json) · [重算代码](audit_total_spend.py)

## 已找到的响应费用：约 89.53 美元

现存成功响应记录合计 **USD 89.52684587–89.53179153**。很窄的区间来自早期重复记录究竟是拷贝还是再次调用的歧义，**不代表未知费用的上下界**。这不是已对账的 OpenRouter 账单、账户余额或包含所有历史成本的项目总支出。

- 主追加账本：**171,219 次成功响应，USD 87.79773723**。
- 早期公开实验：逐条完全相同记录去重后 USD 1.72910863；若重复记录均为单独执行则为 USD 1.73405430。
- 缓存核对：169,877 个文件，**0 个成功响应未出现在主账本**。缓存复用不再累计费用。
- 本次审计新增模型/API 调用 **0 次**。

## 主账本按实际返回模型分解

| 模型 | 成功响应数 | 输入 token | 输出 token | 已报告美元 |
|---|---:|---:|---:|---:|
| deepseek/deepseek-v4.1-flash | 166,028 | 308,511,214 | 23,282,810 | 65.384815 |
| google/gemini-3.8-flash | 5,123 | 7,694,568 | 2,067,895 | 13.525532 |
| anthropic/claude-opus-4.8 | 68 | 1,455,103 | 64,475 | 8.887390 |

上表只分解共享主账本。早期还调用了 OpenAI 模型，其费用列于下表并已包含在总额内。

## 早期记录（存在重叠，不可直接逐表相加）

| 标准来源文件 | 无 error 标记的响应记录 | 记录费用 USD |
|---|---:|---:|
| `upgrade_v2/results/openrouter_rxqa_pilot_predictions.json` | 300 | 0.162941 |
| `upgrade_v2/results/openrouter_rxsafe_harness_pilot_predictions.json` | 360 | 0.796368 |
| `upgrade_v2/results/openrouter_rxsafe_pilot_predictions.json` | 180 | 0.135024 |
| `upgrade_v3/results/openrouter_rxqa_full_predictions.json` | 300 | 0.011396 |
| `upgrade_v3/results/openrouter_rxsafe_full_harness_predictions.json` | 4,000 | 0.479707 |
| `upgrade_v3/results/openrouter_rxsafe_full_predictions.json` | 2,000 | 0.148618 |

早期有 86 条完全一致的跨文件重叠记录，另有 6 条没有价格/token/模型元数据。未保留 provider generation ID，不能确证重叠部分是拷贝还是两次确定性调用。仓库外的镜像文件不重复计算。

主账本有 169,877 个不同请求签名，另有 1,342 次重复签名响应事件。这些仍计费：客户端仅在收到新的成功响应后追加账本，读取缓存不会追加。完全相同的账本行有 0 条。不能按 prompt hash 去重，否则会漏掉重复请求真实产生的费用。按运行角色的明细保存在 JSON。

## 尚未计入或无法确认的费用

- 16 次已记录传输失败可能有未返回的服务端计费；早期被覆盖或未保存的响应无法恢复。
- 主客户端会把未提供的 cost 默认为零；1 条零价格记录无法仅凭该格式证明免费。
- 本地 CPU/MPS 训练只有部分耗时记录，没有硬件/电费计价；见[算力说明](COMPUTE_ACCOUNTING.zh.md)。原 2025 年未记录的实验不在本次范围。
- Codex/聊天费用、订阅、税费、充值手续费、赠金和退款不在该账本内。
- 之前报告的 22.370971562 美元和最近修复的 3.19195587 美元**已经包含在共享账本中**，不要再加。各方法的“逻辑成本”包含复用响应，也不能累加为真实新支出。

更新方式：实验结束后依次运行 `python paper/audit_total_spend.py` 和 `python paper/report_total_spend.py`，保留快照时间和来源哈希。

<!-- UPDATER_REPAIR_COST -->

## 2026-10-20 updater repair increment

本轮新增提案 API 账单 USD 0.085203，在授权 USD 10 内；与此前已定位约 USD 89.53 的账单分开计量。本地 Qwen/Llama 计算时间未计价。费用证据为 `upgrade_v51/results/cost.json`；提案请求只发送汇总统计，没有患者记录。
