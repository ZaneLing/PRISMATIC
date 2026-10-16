"""Render the bilingual cumulative receipt audit without inventing invoice data."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
d = json.loads((HERE/'total_spend_audit.json').read_text())
ledger = d['main_ledger']; old = d['legacy']; lo, hi = d['located_successful_reported_usd_range']
rows = '\n'.join(f"| {m} | {v['responses']:,} | {v['input_tokens']:,} | {v['output_tokens']:,} | {v['usd']:.6f} |" for m,v in ledger['by_model'].items())
early = '\n'.join(f"| `{v['path']}` | {v['successful_records']:,} | {v['recorded_usd']:.6f} |" for v in old['files'])
en = f'''# Cumulative experiment spending audit

Snapshot: {d['snapshot_utc']}. [中文](TOTAL_COST.zh.md) · [Machine-readable audit](total_spend_audit.json) · [Recount code](audit_total_spend.py)

## Located provider-reported cost: approximately USD {(lo+hi)/2:.2f}

The located successful-response records contain **USD {lo:.8f}–{hi:.8f}**. The tiny interval reflects ambiguity over copied versus separately executed identical legacy records; it does not bound unrecorded charges. This is not a reconciled OpenRouter invoice, account balance or all-time project expenditure.

- Main append-only response ledger: **{ledger['successful_response_events']:,} events, USD {ledger['reported_usd']:.8f}**.
- Legacy public experiments: USD {old['deduplicated_recorded_usd']:.8f} after exact-record deduplication, or USD {old['all_records_usd']:.8f} if all overlapping records represent separate executions.
- Cache reconciliation: {d['cache_reconciliation']['files']:,} files; **{d['cache_reconciliation']['successful_orphan_records']} successful cache replies absent from the ledger**. Cached rereads are not charged again in this audit.
- This audit makes **zero new inference/API requests**.

## Main ledger by returned model

| Returned model | Successful events | Input tokens | Output tokens | Reported USD |
|---|---:|---:|---:|---:|
{rows}

This breakdown covers the shared ledger only. Earlier public experiments also used OpenAI models and are listed below; they are included in the overall total.

## Legacy stores (not individually additive without overlap handling)

| Canonical source | Received records without error flag | Recorded USD |
|---|---:|---:|
{early}

There are {old['ambiguous_repeat_records']} identical overlapping legacy records and {old['missing_cost_records']} records with no price/token/model metadata. They lack provider generation IDs, so copied results cannot be distinguished conclusively from identical independent calls. Sibling-folder mirrors are excluded.

The main ledger has {ledger['distinct_request_signatures']:,} distinct request signatures and {ledger['repeated_signature_events']:,} additional events with repeated signatures. All are retained: the client appends only after a new successful response, whereas cache hits return without appending. There are {ledger['exact_duplicate_ledger_lines']} byte-identical duplicate ledger lines. Deduplicating by prompt hash would incorrectly remove possible paid repeated executions. Per-role costs are in the JSON.

## Unknown or excluded expenditure

- {d['transport_failure_attempts']} logged transport-failure attempts can have unknown charges; discarded or overwritten legacy responses cannot be reconstructed.
- The main client defaulted absent usage cost to zero; its {ledger['zero_cost_records']} zero-price record cannot be verified as free from this schema alone.
- Local CPU/MPS training has recorded runtime for some studies, but no electricity/hardware dollar meter. See [compute accounting](COMPUTE_ACCOUNTING.en.md). Unrecorded original 2025 experiments are not included.
- Codex/chat usage, subscription charges, taxes, funding fees, credits and refunds are outside this ledger.
- USD 22.370971562 for the trace-learning study and USD 3.19195587 for recent failure repairs are **already included** in the shared ledger. Do not add them again. Method-level logical costs include reused responses and cannot be summed as new spending.

Rerun `python paper/audit_total_spend.py` followed by `python paper/report_total_spend.py` after experiments finish. Report the snapshot and source hashes with every update.
'''
zh = f'''# 历次实验累计费用审计

快照：{d['snapshot_utc']}。[English](TOTAL_COST.en.md) · [可审计 JSON](total_spend_audit.json) · [重算代码](audit_total_spend.py)

## 已找到的响应费用：约 {(lo+hi)/2:.2f} 美元

现存成功响应记录合计 **USD {lo:.8f}–{hi:.8f}**。很窄的区间来自早期重复记录究竟是拷贝还是再次调用的歧义，**不代表未知费用的上下界**。这不是已对账的 OpenRouter 账单、账户余额或包含所有历史成本的项目总支出。

- 主追加账本：**{ledger['successful_response_events']:,} 次成功响应，USD {ledger['reported_usd']:.8f}**。
- 早期公开实验：逐条完全相同记录去重后 USD {old['deduplicated_recorded_usd']:.8f}；若重复记录均为单独执行则为 USD {old['all_records_usd']:.8f}。
- 缓存核对：{d['cache_reconciliation']['files']:,} 个文件，**{d['cache_reconciliation']['successful_orphan_records']} 个成功响应未出现在主账本**。缓存复用不再累计费用。
- 本次审计新增模型/API 调用 **0 次**。

## 主账本按实际返回模型分解

| 模型 | 成功响应数 | 输入 token | 输出 token | 已报告美元 |
|---|---:|---:|---:|---:|
{rows}

上表只分解共享主账本。早期还调用了 OpenAI 模型，其费用列于下表并已包含在总额内。

## 早期记录（存在重叠，不可直接逐表相加）

| 标准来源文件 | 无 error 标记的响应记录 | 记录费用 USD |
|---|---:|---:|
{early}

早期有 {old['ambiguous_repeat_records']} 条完全一致的跨文件重叠记录，另有 {old['missing_cost_records']} 条没有价格/token/模型元数据。未保留 provider generation ID，不能确证重叠部分是拷贝还是两次确定性调用。仓库外的镜像文件不重复计算。

主账本有 {ledger['distinct_request_signatures']:,} 个不同请求签名，另有 {ledger['repeated_signature_events']:,} 次重复签名响应事件。这些仍计费：客户端仅在收到新的成功响应后追加账本，读取缓存不会追加。完全相同的账本行有 {ledger['exact_duplicate_ledger_lines']} 条。不能按 prompt hash 去重，否则会漏掉重复请求真实产生的费用。按运行角色的明细保存在 JSON。

## 尚未计入或无法确认的费用

- {d['transport_failure_attempts']} 次已记录传输失败可能有未返回的服务端计费；早期被覆盖或未保存的响应无法恢复。
- 主客户端会把未提供的 cost 默认为零；{ledger['zero_cost_records']} 条零价格记录无法仅凭该格式证明免费。
- 本地 CPU/MPS 训练只有部分耗时记录，没有硬件/电费计价；见[算力说明](COMPUTE_ACCOUNTING.zh.md)。原 2025 年未记录的实验不在本次范围。
- Codex/聊天费用、订阅、税费、充值手续费、赠金和退款不在该账本内。
- 之前报告的 22.370971562 美元和最近修复的 3.19195587 美元**已经包含在共享账本中**，不要再加。各方法的“逻辑成本”包含复用响应，也不能累加为真实新支出。

更新方式：实验结束后依次运行 `python paper/audit_total_spend.py` 和 `python paper/report_total_spend.py`，保留快照时间和来源哈希。
'''
(HERE/'TOTAL_COST.en.md').write_text(en)
(HERE/'TOTAL_COST.zh.md').write_text(zh)
