# -*- coding: utf-8 -*-
"""Render the actual scope of training and proposal budgets in both languages."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    z = json.loads((HERE / 'compute_accounting.json').read_text())
    assert z['script_sha256'] == sha(HERE / 'build_compute_accounting.py')
    assert all(sha(ROOT / name) == digest for name, digest in z['source_sha256'].items())
    for lang in ['en', 'zh']:
        en = lang == 'en'
        lines = [('# Compute accounting for the common medication-method study' if en else '# 共同处方方法实验：实际计算预算账本'), '',
                 ('## 1. What is matched' if en else '## 1. 哪些条件已经对齐'), '',
                 ('Within each ATC-L4 panel, methods use the same patient partitions and label space. Author neural methods each receive 50 full epochs over 18,429 training visits, or 921,450 visit exposures. Their batch sizes, optimizer steps, parameter counts and devices differ. The 50-epoch budget therefore supports a matched exposure comparison; FLOPs and training duration are reported separately where recorded.' if en else
                  '每个 ATC-L4 分组内使用相同患者划分与药物空间。作者神经方法均训练 50 整轮，每轮 18,429 次就诊，合计 921,450 次就诊曝光。各方法的批量、优化步数、参数数量和设备不同；50 轮对应相同病例曝光，具体步数与已记录耗时另列。'), '',
                 ('Each neural run evaluates six global thresholds at each of 50 epochs: 300 epoch/threshold candidates on the same proposal set. This is a shared selection budget among the author neural methods.' if en else
                  '每组神经方法在每个训练轮次上评价 6 个全局阈值，共 300 个轮次／阈值候选，均由同一 proposal 集选择。作者神经方法之间使用相同选择预算。'), '',
                 ('The v27 rule study shares each round\'s supervised fits across six arms. v29 shares them across seven arms, with 5,692 policy-fit patients and 1,423 permanently separate witness patients. v30 reuses those exact v29 fits for 14 new memory trajectories. Shared fitting is counted once in the execution ledger. Reproducing any arm in isolation still requires its source policy fits.' if en else
                  'v27 六种规则方法共享每轮监督拟合。v29 七种方法也共享拟合，其中 5,692 人用于策略训练，1,423 人永久独立作为 witness。v30 的 14 种记忆轨迹原样复用 v29 模型。执行账本对共享拟合只计一次；单独复现实验中的某一种方法时，仍需完成其基础策略拟合。'), '',
                 ('## 2. Completed and independently audited author models' if en else '## 2. 已完成并独立核验的作者模型'), '',
                 f"{len(z['author_runs'])}/15 " + ('registered runs are complete and audited in this snapshot. Each row matches all 50 saved epoch records to the original execution log. Fit seconds exclude proposal/guard prediction, checkpoint writing and audit reruns.' if en else
                  '组已登记运行在此快照中完成并通过核验。逐组将 50 条训练轮次记录与原执行日志对齐。拟合秒数不包含 proposal／guard 预测、检查点写入和核验重跑。'), '',
                 '| Panel | Method | Seed | Device | Parameters | Steps | Visit exposures | Fit minutes |',
                 '|---|---|---:|---|---:|---:|---:|---:|']
        for r in z['author_runs']:
            lines.append(f"| {r['panel']} | {r['method']} | {r['seed']} | {r['device']} | {r['parameters']:,} | {r['optimizer_steps']:,} | {r['visit_exposures']:,} | {r['summed_training_seconds']/60:.2f} |")
        lines += ['', ('### Corresponding development results' if en else '### 对应的开发集结果'), '',
                  '| Panel / method | Audited seeds | Guard patient F1 ± seed SD | Guard patient Jaccard ± seed SD |', '|---|---|---:|---:|']
        for name, r in z['author_method_summary'].items():
            values = []
            for key in ['guard_patient_f1', 'guard_patient_jaccard']:
                q = r[key]; values.append(f"{q['mean']:.5f}" + (f" ± {q['seed_sd']:.5f}" if q['seed_sd'] is not None else ' (one seed)'))
            lines.append(f"| {name} | {', '.join(map(str,r['seeds']))} | " + ' | '.join(values) + ' |')
        lines += ['', ('All scores above are on the same 1,231 guard visits / 467 patients, after proposal-only checkpoint selection. An unfinished seed is not filled with zero. This table does not replace the gated final test comparison.' if en else
                       '以上均来自同一 1,231 次 guard 就诊／467 位患者，检查点只由 proposal 选择。未完成种子不补零；这些开发结果不会替代等待全部方法完成后的统一测试主表。'), '',
                  ('## 3. Actual shared supervised fitting' if en else '## 3. 共享监督拟合的实际开销'), '',
                  '| Study | Panel | Seed | Fit events / unique labels | Input-row participations | Fit minutes | Final fit patients / visits | Shared arms |',
                  '|---|---|---:|---:|---:|---:|---:|---:|']
        for r in z['shared_policy_runs']:
            lines.append(f"| v{r['version']} | {r['panel']} | {r['seed']} | {r['fit_events']}/{r['unique_fit_labels']} | {r['fit_input_rows_summed']:,} | {r['summed_fit_seconds']/60:.2f} | {r['final_policy_fit_patients']:,}/{r['final_policy_fit_visits']:,} | {len(r['methods_sharing_fits'])} |")
        lines += ['', ('Each five-round source run has three regularization candidates and three cross-fit models per round. The recorded fit label denotes a full one-vs-rest model collection; constant-target classes can bypass optimization. Input-row participations sum rows provided to these fits, and do not measure internal solver iterations or epoch exposures. Any repeated fit event is retained in the total. Runtime rule search, calibration, generation, prediction and audits are outside these fit timers.' if en else
                       '每个五轮源实验，每轮拟合 3 个正则化候选和 3 个交叉拟合模型。每项拟合记录表示一整套逐类分类器；目标恒定的类别可能无需优化。输入行参与次数统计传入这些拟合的数据行数，不代表求解器内部迭代数或 epoch 曝光。重复拟合事件如有发生仍计入总数。规则搜索、校准、生成、预测和审计不在这些拟合计时之内。'), '',
                  '| Reuse study | Panel | Seed | Frozen fit source | Additional policy fits | Shared arms |', '|---|---|---:|---|---:|---:|']
        for r in z['reused_policy_runs']:
            lines.append(f"| v30 | {r['panel']} | {r['seed']} | {r['source_fit_run']} | 0 | {len(r['methods_sharing_fits'])} |")
        lines += ['', ('Zero additional policy fits refers to exact reuse. Memory induction and verification still consume computation and logical model calls.' if en else
                       '新增策略拟合为零表示原样复用；记忆归纳与验证仍消耗计算和逻辑模型调用。'), '',
                  ('## 4. Proposal calls for the audited runs' if en else '## 4. 已核验运行的提议调用'), '',
                  '| Study | Panel | Seed | Arm | Logical calls | Known logical response USD | Unpriced calls |', '|---|---|---:|---|---:|---:|---:|']
        for r in z['shared_policy_runs'] + z['reused_policy_runs']:
            for name, c in r['logical_proposals_by_arm'].items():
                if not c['logical_calls']: continue
                lines.append(f"| v{r['version']} | {r['panel']} | {r['seed']} | {name} | {c['logical_calls']} | {c['known_logical_response_usd']:.5f} | {c['unpriced_logical_calls']} |")
        lines += ['', ('These are method-level logical requests and the prices associated with their saved successful responses. Identical responses can be reused across conditions; this table must not be summed as fresh account spend. Failed attempts, account-wide usage and time waiting for credit are not covered. The physical request ledger remains the source for billed experiment requests.' if en else
                       '此处统计方法层面的逻辑请求，以及保存的成功响应对应价格。相同响应可能跨组合复用，不能把表中价格相加当作新增账户扣款。失败尝试、账户级用量和等待充值时间不在此表覆盖范围内；实际计费请求仍以物理请求账本为准。'), '',
                  ('## 5. Conventional-method timing scope' if en else '## 5. 传统方法计时范围'), '',
                  '| Panel | Method | Recorded block seconds | Configurations × thresholds | Shared feature seconds |', '|---|---|---:|---:|---:|']
        for r in z['conventional_controls']:
            timing = f"{r['recorded_seconds']:.3f}" if r['timing_measured'] else 'not measured'
            lines.append(f"| {r['panel']} | {r['method']} | {timing} | {r['configuration_candidates']} × 6 = {r['proposal_configuration_threshold_candidates']} | {r['shared_feature_seconds']:.3f} |")
        lines += ['', ('Cosine retrieval and logistic timing blocks include proposal search and guard prediction, so they have a broader scope than the neural fit timers. Historical prevalence/last-visit values of zero are unmeasured sentinels. Feature construction is shared once per panel. No FLOP, energy, isolated latency or peak-memory measurement is inferred from these records.' if en else
                       '余弦检索和逻辑回归计时包含 proposal 搜索及 guard 预测，范围宽于神经模型的纯拟合计时。历史频率／上次就诊方法保存的零值表示未计时。特征构建按每个药物分组共享一次。现有记录不支持推算 FLOPs、能耗、独占设备延迟或峰值内存。'), '',
                  ('## 6. Interpretation and coverage' if en else '## 6. 如何解释这些数字'), '',
                  ('The runs use CPU and Apple MPS concurrently. Summed method timers are resource-activity measurements under contention, not one continuous elapsed wall clock or an isolated speed leaderboard. This analysis creates no fits, model requests or test predictions. It reconstructs saved receipts and binds the source hashes; it is not an independent compute profiler. Exact budgets are matched within each registered intervention, while heterogeneous method comparisons disclose their distinct search and fitting costs.' if en else
                       'CPU 与 Apple MPS 上有多个任务并行运行。各方法计时之和反映共享硬件下的活动时间，不是连续经过的墙钟时间，也不能作为独占设备速度排名。本次核算没有新增拟合、模型请求或测试预测；它重建已有回执并绑定源哈希，不是独立计算性能剖析。每个已登记干预内部按其协议匹配预算，异构方法之间分别披露搜索与拟合开销。'), '',
                  '[Machine-readable receipts and source hashes](compute_accounting.json) · [Common method study](../upgrade_v27/RESULTS.' + lang + '.md) · [Common test extension](../upgrade_v30/COMMON_TEST.' + lang + '.md)', '']
        (HERE / f'COMPUTE_ACCOUNTING.{lang}.md').write_text('\n'.join(lines))


if __name__ == '__main__':
    main()
