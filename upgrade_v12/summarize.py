"""Independently recount cached decisions and report gate/object evidence."""
import json, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'upgrade_v11'))
from evidence_tool import LOCAL
from public_client import LOCAL as DATA_LOCAL


def read(p):
    return json.loads(p.read_text())


def main():
    test = read(DATA_LOCAL / 'data.json')['parts']['test']
    actions = read(LOCAL / 'test-review-actions.json')
    predictions = read(LOCAL / 'gate-audit-v12-predictions.json')
    result = read(HERE / 'results/gate_audit.json')
    journal = read(HERE / 'results/frozen_decisions.json')['decisions']
    groups = sorted({c['group_id'] for c in test})
    lookup = {g: i for i, g in enumerate(groups)}
    gi = np.array([lookup[c['group_id']] for c in test])
    counts = np.bincount(gi)

    def recount(rows):
        assert len(rows) == len(test)
        assert not any(r.get('error') for r in rows)
        assert [r['case_id'] for r in rows] == [c['id'] for c in test]
        return np.array([r['prediction'] == c['gold'] for r, c in zip(rows, test)], dtype=int)

    def paired(a, b):
        delta = a - b
        totals = np.bincount(gi, weights=delta)
        rng = np.random.default_rng(42)
        draws = []
        for _ in range(4000):
            ix = rng.integers(0, len(groups), len(groups))
            draws.append(totals[ix].sum() / counts[ix].sum())
        return {'difference': float(delta.mean()), 'scenario_cluster_ci95': np.quantile(draws, [.025, .975]).tolist(),
                'fixes': int((delta > 0).sum()), 'regressions': int((delta < 0).sum())}

    fixed = {a: recount(actions[a]) for a in ['cot', 'balanced', 'safety']}
    for a, correct in fixed.items():
        assert int(correct.sum()) == result['methods'][a]['correct']
    contrasts = {}
    for name, curves in predictions.items():
        previous = fixed['cot']
        for rows, entry in zip(curves, result['runs'][name]['curve']):
            correct = recount(rows)
            assert int(correct.sum()) == entry['score']['correct']
            assert int(((correct - previous) > 0).sum()) == entry['fixes']
            assert int(((correct - previous) < 0).sum()) == entry['regressions']
            previous = correct
        contrasts[name] = {base: paired(previous, fixed[base]) for base in ['cot', 'balanced']}
    summary = {'status': 'complete', 'test_cases': len(test), 'test_scenario_groups': len(groups),
               'verification': 'Independent prediction/case alignment, correct counts and round transitions passed.',
               'new_network_calls': 0, 'interval_note': 'Descriptive paired intervals, no multiple-comparison adjustment; development extension.',
               'fixed_controls': {a: {'correct': int(v.sum()), 'accuracy': float(v.mean())} for a, v in fixed.items()},
               'gate_summaries': {}, 'paired_comparisons': contrasts}
    for gate in ['independent_guard', 'joint_validation']:
        runs = [result['runs'][f'{gate}_seed_{s}'] for s in [42, 137, 2026]]
        xs = [r['final']['accuracy'] for r in runs]
        summary['gate_summaries'][gate] = {'accuracy_mean': float(np.mean(xs)), 'accuracy_sample_sd': float(np.std(xs, ddof=1)),
            'mean_calls': float(np.mean([r['curve'][-1]['mean_calls'] for r in runs])),
            'mean_logical_test_cost_usd': float(np.mean([r['final']['cost_usd'] for r in runs]))}
    (HERE / 'results/summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.6), sharey=True)
    for ax, seed in zip(axes, [42, 137, 2026]):
        for gate, label in [('independent_guard', 'Independent guard'), ('joint_validation', 'Pooled validation')]:
            curve = result['runs'][f'{gate}_seed_{seed}']['curve']
            ax.plot(range(5), [100 * c['score']['accuracy'] for c in curve], marker='o', label=label)
        ax.axhline(100 * fixed['balanced'].mean(), color='gray', linestyle='--', label='Selected fixed tool')
        ax.set(title=f'Training-order seed {seed}', xlabel='Round (active version)', xticks=range(5))
        ax.grid(alpha=.2)
    axes[0].set_ylabel('Fixed-test accuracy (%)')
    axes[-1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(HERE / 'round_curves.png', dpi=180)
    plt.close(fig)
    methods = '| Method | Accuracy (%) | Seed SD (pp) | Mean model calls |\n|---|---:|---:|---:|\n'
    for a, label, calls in [('cot', 'Frozen CoT', 1), ('balanced', 'Validation-selected fixed evidence review', 2), ('safety', 'Fixed safety evidence review', 2)]:
        methods += f'| {label} | {100 * fixed[a].mean():.2f} | — | {calls} |\n'
    for gate, m in summary['gate_summaries'].items():
        methods += f"| Evolving router: {gate.replace('_', ' ')} | {100*m['accuracy_mean']:.2f} | {100*m['accuracy_sample_sd']:.2f} | {m['mean_calls']:.3f} |\n"
    rounds = '| Gate / seed | Round | Seen cases | Promoted | Active training cases | Correct / 988 | Fixes / regressions vs previous |\n|---|---:|---:|---|---:|---:|---:|\n'
    for name, entries in journal.items():
        curve = result['runs'][name]['curve']
        for entry, c in zip(entries, curve[1:]):
            rounds += f"| {name} | {entry['round']} | {entry['training_seen']} | {entry['accepted']} | {entry['active_training_n']} | {c['score']['correct']} | {c['fixes']} / {c['regressions']} |\n"
    for lang in ['en', 'zh']:
        if lang == 'en':
            text = '''# v0.12 — Does a different update gate make RSI work?

## Abstract

We replay complete, previously executed public model traces to isolate the update gate and action set. Three training orders and four rounds produce genuine changes to routing parameters, but neither gate improves over the validation-selected fixed tool on average. Some accepted updates regress on test. This is an exploratory development extension, not an untouched confirmation study.

## Data and controlled protocol

RxSafeBench-derived option selection: 625 train / 190 proposal / 197 guard / 988 test; scenario groups are disjoint. DeepSeek-V4.1-Flash, 512 output tokens per call. Actions share an identical CoT draft: retain it, review balanced label evidence, or review safety label evidence. Runtime requires one or two model calls. The indication action is excluded because 153 requests were not answered after HTTP 402; its observed score was not used for exclusion. Both gates receive the same remaining actions and 387 development labels.

Each round exposes 156/312/468/625 training cases. A fixed hashing representation encodes the question, options and initial answer. Ridge routing weights learn the observed improvement of each evidence action over CoT. The 3 regularizers × 3 thresholds are chosen using either proposal selection plus an independent guard, or all 387 validation cases jointly. The latter reduces validation fragmentation but has no separate regression check. Every round choice was frozen before this script scored test outputs; the test had already been observed in prior increments.

## Same-task comparison

''' + methods + '''
The selected fixed review is balanced, chosen without test labels. The safety row is a prespecified fixed control, not a test-selected winner. SD measures order sensitivity across three seeds. All rows use complete received responses; malformed received answers count wrong. No new model requests were made for this replay. Counterfactual action generation during development has a higher cost than the one/two-call runtime, and is not free training feedback.

## What actually evolves

Only the routing coefficients, intercepts and decision threshold change. The LLM weights, label corpus, retrieval code and feature transform stay fixed. The version journal records parameter hashes, training counts, candidates, guard fixes and regressions. This is learned tool routing; it is not tool-source-code evolution or medical knowledge discovery.

![Round trajectories](round_curves.png)

''' + rounds + '''
## Interpretation and next experiment

Seed 2026 pooled selection moves from 480 to 476 correct after an accepted update: validation improvement does not guarantee test improvement. In seed 42, pooled selection matches the fixed tool at 484 correct while averaging 1.538 calls, but the other seeds do not establish a stable accuracy advantage. Independent recount and scenario-cluster paired intervals are in `results/summary.json`. The small train set and weak text-based routing signal remain plausible limitations. The next increment should add an outcome verifier with matched supervised and non-evolving controls, then confirm a frozen design on an untouched dataset or split. Reusing this test cannot establish confirmatory superiority.
'''
        else:
            text = '''# v0.12：更换更新门控后，RSI 是否有效？

## 摘要

用已真实执行且完整收到回答的公开模型轨迹，隔离比较更新门控与动作空间。三个训练顺序、四轮更新确实改变了路由参数，但两个门控的平均准确率都没有超过开发集选出的固定工具。某些被接受更新在测试集退化。本版是探索性开发延伸，不是新的独立确认实验。

## 数据与控制协议

RxSafeBench 衍生选药题：625 训练 / 190 候选选择 / 197 退化检查 / 988 测试，场景组不交叉。固定 DeepSeek-V4.1-Flash，每次最多 512 输出 token。三个动作共用同一个 CoT 初稿：保留初稿、结合均衡说明书证据复核、结合安全证据复核。推理需一至两次模型调用。适应证动作有 153 个请求因 HTTP 402 未收到回答，因此排除；没有根据其已观察分数决定排除。两个门控均使用相同剩余动作及相同 387 个开发标签。

四轮依次暴露 156/312/468/625 个训练病例。固定文本哈希特征编码问题、候选药物和初稿，Ridge 参数学习各证据动作相对 CoT 的正确性变化。3 个正则系数 × 3 个阈值，分别通过“190 题选择 + 197 题独立检查”或“合并 387 题选择”决定。合并方案减少开发数据碎片化，但没有独立退化检查。此脚本先冻结全部选择再计算测试分数；此前版本已观察过该测试集，因此不称为全新确认。

## 同任务方法主表

''' + methods + '''
固定工具为开发集选出的 balanced。safety 是预设固定对照，不按测试分数选赢家。SD 表示三种训练顺序的敏感性。表内只含完整返回的回答，收到但格式错误的回答计错。此次重放没有新增模型请求；开发阶段为同一病例生成多个动作的反事实回答有额外成本，不能视为免费反馈。

## 究竟进化了什么

变化对象只有工具路由的系数、截距和阈值；模型权重、说明书库、检索代码、特征变换固定。版本文件保存参数哈希、已见病例数、候选及检查集修复/退化。这证明路由参数更新，不等同于工具源代码进化或发现新医学知识。

![逐轮轨迹](round_curves.png)

''' + rounds + '''
## 解释与下一步

seed 2026 的合并选择方案在接受更新后，从 480 题正确降至 476 题，说明开发集改善不保证测试改善。seed 42 在平均 1.538 次调用下达到 484 题，与固定工具相同，但其他种子未确立稳定准确率优势。独立重算与场景聚类配对区间见 `results/summary.json`。训练量较小、仅文本路由信号较弱仍是可能原因。下一版应加入结果核验器，并配套同数据普通监督与固定策略对照；最终需在未使用的数据或切分上确认冻结设计，不能反复使用本测试集来证明最终领先。
'''
        (HERE / f'RESULTS.{lang}.md').write_text(text)
    print(json.dumps(summary['gate_summaries']))


if __name__ == '__main__':
    main()
