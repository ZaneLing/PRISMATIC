"""Render the independently recounted development trajectories and their limits."""
import json
from pathlib import Path
import numpy as np
from data_contract import sha

HERE = Path(__file__).resolve().parent
LABELS = {'uniform': ('普通更新', 'Uniform updates'),
          'error_prioritized': ('自身错误优先', 'Own-error priorities'),
          'permuted_priority': ('打乱错误权重', 'Shuffled priorities')}
METRICS = ['drug_micro_f1', 'core_order_micro_f1']


def main():
    path = HERE / 'results/development_curves.json'
    d = json.loads(path.read_text())
    assert d['status'] == 'passed' and d['development_states_reexecuted'] == 45
    assert d['script_sha256'] == sha(HERE / 'recount_development.py')
    assert all(sha(HERE / n) == value for n, value in d['source_sha256'].items())
    import matplotlib
    matplotlib.use('Agg')
    matplotlib.rcParams['svg.hashsalt'] = 'rxrsi-v25-development'
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 2, figsize=(10.2, 6.7), sharex=True, sharey='col')
    for row, kind in enumerate(['raw', 'accepted']):
        for col, metric in enumerate(METRICS):
            ax = axes[row, col]
            for arm, labels in LABELS.items():
                scores = d['aggregate'][kind][arm]
                mean = np.array([s[metric]['mean'] for s in scores])
                sd = np.array([s[metric]['seed_sd'] for s in scores])
                line = ax.plot([8, 16, 24, 32, 40], mean, marker='o', ms=4, label=labels[1])[0]
                ax.fill_between([8, 16, 24, 32, 40], mean-sd, mean+sd, color=line.get_color(), alpha=.13)
            ax.set_title(('Raw checkpoints' if kind == 'raw' else 'Guard-accepted states') +
                         (' — drug F1' if col == 0 else ' — joint-order F1'), fontsize=10)
            ax.grid(alpha=.2)
            ax.set_xticks([8, 16, 24, 32, 40])
            ax.set_ylabel('Micro-F1')
            if row == 1:
                ax.set_xlabel('Cumulative training stays encountered (thousands)')
    axes[0, 0].legend(fontsize=8)
    fig.suptitle('eICU development guard: 2,000 stays, 17 hospitals; three-seed mean ± SD', fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, .96])
    fig.savefig(HERE / 'development_round_curves.png', dpi=180)
    svg=HERE / 'development_round_curves.svg'
    fig.savefig(svg, metadata={'Date': None})
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
    plt.close(fig)
    for lang, col in [('zh', 0), ('en', 1)]:
        en = lang == 'en'
        text = ['# ' + ('eICU: audited development learning curves' if en else 'eICU：独立复算的开发集学习曲线'), '',
                ('## Scope' if en else '## 数据与解释范围'), '',
                ('This retrospective analysis reexecutes 45 already completed checkpoints: three seeds × three feedback arms × five rounds. It opens only the development bundle. The guard contains 2,000 stays, 1,912 patients and 17 hospitals, including 1,001 stays with no target medication. The separate 8,005-stay test remains behind the original complete-selection gate.' if en else
                 '本项事后分析重新执行已完成的 45 个状态：三个种子 × 三种反馈方法 × 五轮。只打开开发数据包。guard 含 2,000 次住院、1,912 位患者、17 家医院，其中 1,001 次住院没有目标药物。另有 8,005 次住院的测试集，仍遵循原全部版本选择冻结后的开放规则。'), '',
                ('The original parameter hashes, 60-epoch records, seen-only tool memberships, seven proposal thresholds and all guard accept/reject decisions are checked. Saved policies and tools are reexecuted; set metrics are counted without calling the training scorer. This is not an independent refit of the optimizer or tool implementation. The final registered audit separately checks feedback weights and test predictions.' if en else
                 '逐项核对原始参数哈希、60 轮训练记录、工具的已见病例成员、七个 proposal 阈值及全部 guard 接纳／拒绝决定。重新运行保存的策略和工具，使用独立集合计数复算指标。这里没有独立重新训练优化器，也没有重写订单工具；反馈权重和测试预测仍由原登记的最终审计核验。'), '',
                ('## Case-growth curves' if en else '## 病例增长曲线'), '',
                '![Raw and guard-accepted development curves](development_round_curves.png)', '',
                ('Shading is sample standard deviation over three seeds, not a confidence interval. The horizontal axis counts cases encountered; a rejected update retains an earlier policy/tool bundle. Accepted curves are evaluated on the same guard that selects them and cannot establish generalization.' if en else
                 '阴影是三个种子的样本标准差，不是置信区间。横轴表示已遇到的病例数；拒绝更新时，实际使用的策略和工具仍来自较早轮次。接纳曲线在负责选择它们的同一 guard 上评价，不能证明泛化。')]
        for kind in ['raw', 'accepted']:
            text += ['', '### ' + (('Raw checkpoints' if kind == 'raw' else 'Guard-accepted states') if en else
                                   ('每轮原始状态' if kind == 'raw' else 'guard 接纳状态')), '',
                     ('| Round | Stays encountered | Uniform drug / order | Own-error drug / order | Shuffled drug / order |' if en else '| 轮次 | 累计住院病例 | 普通更新：药物／订单 | 自身错误优先：药物／订单 | 打乱权重：药物／订单 |'),
                     '|---|---:|---:|---:|---:|']
            for r in range(5):
                cells = []
                for arm in LABELS:
                    scores = d['aggregate'][kind][arm][r]
                    cells.append(' / '.join(f"{scores[k]['mean']:.5f} ± {scores[k]['seed_sd']:.5f}" for k in METRICS))
                text.append(f'| {r} | {8000*(r+1):,} | ' + ' | '.join(cells) + ' |')
        text += ['', ('## Final-round paired differences' if en else '## 末轮配对差异'), '',
                 ('| State | Own-error minus | Drug F1 Δ | Joint-order F1 Δ |' if en else '| 状态 | 自身错误优先减去 | 药物 F1 差值 | 完整订单 F1 差值 |'), '|---|---|---:|---:|']
        for kind, controls in d['final_own_error_minus_control'].items():
            for arm, values in controls.items():
                state_label=kind if en else {'raw':'原始末轮','accepted':'最终接纳'}[kind]
                text.append(f"| {state_label} | {LABELS[arm][col]} | {values['mean'][METRICS[0]]:+.5f} | {values['mean'][METRICS[1]]:+.5f} |")
        raw_delta=d['final_own_error_minus_control']['raw']['uniform']['mean']
        accepted_delta=d['final_own_error_minus_control']['accepted']['uniform']['mean']
        text += ['', (f"**Observed finding:** raw final own-error-minus-uniform drug/order F1 is {raw_delta[METRICS[0]]:+.5f}/{raw_delta[METRICS[1]]:+.5f}; for guard-accepted states it is {accepted_delta[METRICS[0]]:+.5f}/{accepted_delta[METRICS[1]]:+.5f}. Case-growth gains alone do not establish a benefit from assigning priorities to the model's own errors. A small positive order difference must be considered alongside the drug difference and guard selection." if en else
                      f"**实际发现：** 末轮原始状态中，自身错误优先减普通更新的药物／订单 F1 为 {raw_delta[METRICS[0]]:+.5f}/{raw_delta[METRICS[1]]:+.5f}；guard 接纳状态中为 {accepted_delta[METRICS[0]]:+.5f}/{accepted_delta[METRICS[1]]:+.5f}。病例增长的收益不能单独证明自身错误分配机制有效。订单上的小幅正差，需要结合药物差值及 guard 选择效应一起判断。")]
        text += ['', ('Differences pair the same seed, cases, round budget and outcome protocol, then average three seed differences. All individual seed values remain in the JSON. These are descriptive development comparisons without significance claims.' if en else
                      '差值在相同种子、病例、轮次预算和输出协议下配对，再平均三个种子的差值。JSON 保留逐种子结果。这是描述性开发集比较，不作显著性声明。'), '',
                 ('## Raw regressions and final selection' if en else '## 原始退化与末轮保留状态'), '',
                 ('| Method | Raw drug declines / 12 | Raw order declines / 12 | Accepted rounds, seeds 42 / 137 / 2026 |' if en else '| 方法 | 药物指标退化次数／12 | 订单指标退化次数／12 | 最终保留轮次：种子 42／137／2026 |'),
                 '|---|---:|---:|---|']
        for arm, labels in LABELS.items():
            n = d['raw_regressions_among_12_transitions'][arm]
            rounds = ' / '.join(str(d['states'][str(s)][arm][4]['active_round']) for s in d['seeds'])
            text.append(f'| {labels[col]} | {n[METRICS[0]]} | {n[METRICS[1]]} | {rounds} |')
        text += ['', ('## Final accepted-state output behavior' if en else '## 最终接纳状态的输出行为'), '',
                 ('| Method | Drug precision | Drug recall | Empty % | Mean predicted codes |' if en else '| 方法 | 药物精确率 | 药物召回率 | 空输出率（%） | 平均预测药物编码数 |'), '|---|---:|---:|---:|---:|']
        for arm, labels in LABELS.items():
            z = d['aggregate']['accepted'][arm][-1]
            text.append(f"| {labels[col]} | {z['drug_precision']['mean']:.5f} | {z['drug_recall']['mean']:.5f} | {100*z['empty_fraction']['mean']:.2f} | {z['mean_predicted_drugs']['mean']:.3f} |")
        text += ['', ('## What this does and does not show' if en else '## 结论边界'), '',
                 ('Read improvement over the initial 8k state separately from the benefit of own-error feedback over uniform or shuffled training. The guard promotion rule creates selection effects, and individual raw rounds can regress. No language model or API is used in this study. These native HICL/route/dosage/frequency results measure agreement with documented orders, not clinical safety or ATC benchmark superiority. Static controls and the held-out hospital test will be reported only after their registered execution and audits finish.' if en else
                  '相对初始 8k 状态的改善，与自身错误反馈相对普通／打乱训练的收益，是两个不同问题。guard 接纳规则存在选择效应，原始模型也可能逐轮退化。本研究不使用语言模型或 API。原生 HICL／途径／剂量字符串／频率字符串结果衡量与记录订单的一致性，不能证明临床安全或超过 ATC 基准。静态对照和留出医院测试在原登记执行及审计完成后报告。'), '',
                 ('[Source-bound replay results](results/development_curves.json) · [Full study](RESULTS.en.md)' if en else '[源文件与完整复算结果](results/development_curves.json) · [完整研究说明](RESULTS.zh.md)'), '']
        (HERE / f'DEVELOPMENT_CURVES.{lang}.md').write_text('\n'.join(text))


if __name__ == '__main__':
    main()
