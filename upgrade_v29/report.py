"""Maintained bilingual report separating implemented changes and audited scores."""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main():
    runs=[]
    for p in sorted((HERE/'results').glob('*-seed*.json')):
        z=json.loads(p.read_text())
        if 'lock' in z:runs.append(z)
    summary=json.loads((HERE/'results/summary.json').read_text()) if (HERE/'results/summary.json').exists() else {'status':'pending_audit','panels':{}}
    for lang in ['en','zh']:
        text=('''# v0.29 — Conditional program memory with isolated fresh witnesses

## 1. Question and actual mechanism

v0.27 showed tiny memory gains and no established advantage over greedy edits. This registered intervention separates ordinary per-drug calibration from language-agent rule synthesis and isolates every witness patient from all policy fits and candidate statistics. It uses the same retrospective MIMIC-IV ATC-L4 task, with full and molecular spaces kept separate. It does not generate doses or establish prospective clinical correctness.

Of the 7,115 training patients, each seed assigns 5,692 to policy fitting and 1,423 permanently to witness verification by a label-independent hash. Five rounds grow the fit cohort and expose a fresh disjoint witness batch of 285/285/285/284/284 patients. Witness labels cannot fit any coefficient or candidate statistic at any round. Fixed v0.27 vocabularies predate this partition. A witness is reused for up to four sequential edits within its one round; this is adaptive training validation, not independent confirmation.

The shared calibration control learns class-specific thresholds from cross-fitted fitting-patient predictions. The language agent receives only aggregate, supported feature/drug error contexts and synthesizes one- or two-predicate ADD/DELETE programs. Actual induction effects and fresh witnesses verify them. Greedy search enumerates both positive and negative predicate combinations; random and shuffled-evidence agents remain visible. Shuffling changes numeric support/gain assignment, while error-based focus-drug and feature selection stay fixed. No-witness uses the same own-agent proposals, not an independently learned counterfactual trajectory.

**Evolved artifact:** executable conditional rule memory. Calibration and coefficient refits are ordinary supervised updates; language-model weights and tool code stay fixed. All original base/fold models, proposals, rejected edits and raw round states are saved locally. No v0.29 test inference is performed.

## 2. Actual execution status

''' if lang=='en' else '''# v0.29：条件程序记忆与隔离的新witness

## 1. 问题与真实机制

v0.27的记忆收益很小，尚未证明优于贪心编辑。本次登记干预将普通逐药物校准与语言agent规则生成分开，并把每位witness患者永久排除在策略拟合和候选统计之外。使用相同历史MIMIC-IV ATC-L4任务，完整与分子空间分别报告；不生成剂量，不证明入院时点的临床正确性。

7,115位训练患者按与标签无关的哈希划分：5,692位拟合策略，1,423位永久用于witness验证。五轮逐步增加拟合患者，每轮只使用一批新的witness，分别285／285／285／284／284人。任何轮次的模型系数和候选统计都不能使用witness标签；固定v0.27词表早于本划分。每位witness只在所属轮内被最多四项编辑顺序复用，仍属于自适应训练验证，不是独立确认。

共同校准对照从拟合患者的交叉拟合预测中学习逐类别阈值。语言agent只接收有足够支持的聚合特征／药物错误上下文，生成一到两个条件组成的新增或删除程序；再用真实归纳收益和新witness核验。贪心对照穷举包含肯定与否定条件的组合，随机和打乱证据方法同时保留。打乱仅改变数值支持／收益的对应关系，错误驱动的药类及特征筛选仍固定。取消witness方法使用相同agent提议，不冒充独立反事实学习轨迹。

**实际进化对象：可执行条件规则记忆。** 校准和系数重新拟合属于普通监督更新；语言模型权重、工具代码保持固定。原始基础／折模型、提议、拒绝和全部原始轮次均本地保存。本版不运行测试集推断。

## 2. 真实运行状态

''')
        text+='| Panel | Seed | Completed rounds /5 | Own-agent rules | Status |\n|---|---:|---:|---:|---|\n'
        for z in runs:
            rows=z['rounds'];n=rows[-1]['arms']['own_error_program_agent']['memory_size'] if rows else 0
            text+=f"| {z['lock']['panel']} | {z['lock']['seed']} | {len(rows)} | {n} | {z['status']} |\n"
        text+=('\nSynthetic execution probes cover strict patient roles, conjunction semantics, target-field rejection, supported program effects, accept/reject gates and calibration changes. These probes are not clinical performance scores.\n' if lang=='en' else '\n合成执行探针已覆盖患者角色隔离、组合条件语义、目标字段拒绝、实际支持度、接纳／拒绝与校准变化；它们不是临床性能分数。\n')
        if summary['panels']:
            text+=('\n## 3. Independently audited guard comparison\n\nSame 1,231 visits/467 patients, report-only guard. Each included seed has independent raw-source reconstruction and fresh reproduction of all selected base/fold fits. Unfinished/unaudited cells remain pending.\n\n' if lang=='en' else '\n## 3. 独立核验后的guard比较\n\n相同1,231次就诊／467人，仅报告guard。每个纳入种子均完成原始数据重建及所选基础／全部折模型的独立重新拟合；未完成或未审计的单元保持待完成。\n\n')
            text+='| Panel | Method | Audited seeds | Patient F1 ± SD | Patient Jaccard ± SD |\n|---|---|---:|---:|---:|\n'
            for panel,p in summary['panels'].items():
                for arm,z in p['methods'].items():
                    def fmt(k):
                        q=z[k];return f"{q['mean']:.5f}"+(f" ± {q['seed_sd']:.5f}" if q['seed_sd'] is not None else ' (one seed)')
                    text+=f"| {panel} | {arm} | {len(p['seeds'])} | {fmt('patient_f1')} | {fmt('patient_jaccard')} |\n"
            text+='\n| Panel | Own agent minus comparator | F1 difference (pp) | Patient interval (pp) |\n|---|---|---:|---:|\n'
            for panel,p in summary['panels'].items():
                for arm,z in p['own_agent_minus_control'].items():
                    q=z['patient_f1'];lo,hi=q['patient_ci95'];text+=f"| {panel} | {arm} | {100*q['difference']:+.3f} | [{100*lo:+.3f}, {100*hi:+.3f}] |\n"
            text+=('\nIntervals average observed seeds before patient resampling; they do not estimate new-seed variability and are unadjusted descriptive intervals. Gains versus raw policy must be separated from calibration gains and from the additional language-agent contribution.\n' if lang=='en' else '\n区间先平均已有种子再按患者重采样，不估计新种子的变化，属于未作多重比较校正的描述性区间。相对原策略的提升必须分解为普通校准收益与语言agent额外贡献。\n')
            text+='\n| Panel | Round | Raw proposal F1 | Calibrated proposal F1 | Own-agent proposal F1 | Rules / conjunctions by seed |\n|---|---:|---:|---:|---:|---|\n'
            for panel,p in summary['panels'].items():
                for r in range(5):
                    curve=p['proposal_curves'];own=curve['own_error_program_agent'][r];mean=lambda a:sum(a)/len(a)
                    values=[mean(curve[k][r]['proposal_f1']) for k in ['raw_policy','calibrated_policy','own_error_program_agent']]
                    text+=f"| {panel} | {r+1} | "+' | '.join(f'{v:.5f}' for v in values)+' | '+', '.join(f'{a}/{b}' for a,b in zip(own['memory_size'],own['retained_conjunctions']))+' |\n'
            text+='\n| Panel | Method | Logical model calls | Logical response USD | Enumerated programs | Proposal seconds |\n|---|---|---:|---:|---:|---:|\n'
            for panel,p in summary['panels'].items():
                for arm,z in p['proposal_costs'].items():text+=f"| {panel} | {arm} | {z['logical_model_calls']} | {z['logical_response_cost_usd']:.5f} | {z['enumerated_programs']} | {z['proposal_seconds']:.1f} |\n"
        if (HERE/'results/memory_diagnostic.json').exists():
            diagnostic=json.loads((HERE/'results/memory_diagnostic.json').read_text())
            text+=('\n## 4. Executed memory carryover and edit-transfer diagnosis\n\nThis registered replay uses proposal cases only, after early development scores were observed. It changes no training decision, fits no model and makes no new API call. For each round, all compared memories use the same current policy and calibration.\n\n' if lang=='en' else '\n## 4. 已执行的旧记忆与新编辑诊断\n\n本登记回放在早期开发成绩已观察后进行，只用proposal病例；不改训练决定、不拟合新模型、不新增API调用。每轮不同记忆使用同一个当前策略与校准。\n\n')
            text+='| Audited run | Accepted edits with positive proposal transfer | Negative transfer | Zero transfer |\n|---|---:|---:|---:|\n'
            for name,z in diagnostic['runs'].items():text+=f"| {name} | {z['accepted_positive_transfer']} | {z['accepted_negative_transfer']} | {z['accepted_zero_transfer']} |\n"
            text+='\n| Audited run | Round | Prior-memory effect (F1 pp) | New-edit effect (F1 pp) |\n|---|---:|---:|---:|\n'
            for name,z in diagnostic['runs'].items():
                for row in z['rounds']:text+=f"| {name} | {row['round']} | {100*row['carryover_memory_effect']:+.4f} | {100*row['current_edits_effect']:+.4f} |\n"
            text+=('\nA positive fresh-witness edit can have a negative effect on proposal patients. Old rules can also change value after the policy/calibration changes. These findings motivate compatibility revalidation, but do not constitute an executed improved agent or an independently learned counterfactual trajectory.\n' if lang=='en' else '\n新witness上有益的编辑仍可能损害proposal表现；基础策略／校准改变后，旧规则的作用也会变化。这为重新核验规则兼容性提供依据，但不是已经执行的新改进agent，也不是独立学习的反事实轨迹。\n')
        text+='\n## Artifacts / 交付\n\n- [Registered protocol](protocol.json)\n- [Actual pre-training probes](results/runtime_probe.json)\n- [Audit-gated aggregate results](results/summary.json)\n- [Registered memory diagnosis](diagnostic_addendum.json) and [actual replay effects](results/memory_diagnostic.json)\n- [Historical round-selection metadata correction](../paper/round_selection_metadata_audit.json)\n'
        text+=('\nA rolling-export dictionary can show later best-round choices in older nested `round.best` fields. Immutable per-round receipts and per-arm `best_round` values are independently verified; corrected historical selections are linked above. Scores, rules and final model choices are unchanged. Restricted records, predictions and fitted weights stay local.\n' if lang=='en' else '\n滚动导出的共享字典会使旧轮次嵌套`round.best`显示较晚选择。不可变逐轮回执与各方法`best_round`已独立核对，历史选择修正在上方链接；分数、规则和最终模型选择没有变化。受限病例、预测与权重保持本地。\n')
        (HERE/f'RESULTS.{lang}.md').write_text(text)
if __name__=='__main__':main()
