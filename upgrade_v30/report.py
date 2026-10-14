"""Bilingual mechanism and actual results, with explicit pending cells."""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main():
    runs=[]
    for path in sorted((HERE/'results').glob('*-seed*.json')):
        z=json.loads(path.read_text())
        if 'lock' in z:runs.append(z)
    summary=json.loads((HERE/'results/summary.json').read_text()) if (HERE/'results/summary.json').exists() else {'panels':{}}
    for lang in ['en','zh']:
        text=('''# v0.30 — Revalidate old memory and confirm the whole update

## 1. Executed design

The v0.29 replay found both stale-memory effects and negative transfer of individually accepted edits. This registered intervention reuses the exact independently audited v0.29 policies/calibration and changes the memory-maintenance trajectory. It fits no new predictor and performs no test inference.

Each fresh witness batch is divided by patient into edit group **A** and confirmation group **B**. **C** revalidates the old memory on cross-fitted fitting patients and A before proposing new rules. **P** confirms the entire edited memory on B. Failed gates reset the correction memory; the current calibrated prescribing policy still produces its medication set. Resetting memory does not force an empty prescription.

Greedy enumeration, own-error language synthesis and shuffled numeric evidence each run all four C/P combinations. Raw and calibrated policies add two controls, for **14 arms × five rounds × three seeds × two medication spaces**. All C/P conditions edit on A and compute identical shadow checks; only the gate's effect on retained state changes. C0P0 therefore differs from the preceding v0.29 full-batch verifier. Identical prompts across gate variants reuse the same exact response; divergent memories generate new prompts.

The language agent evolves executable rule memory. C/P policies and tools are fixed engineering choices, and coefficient/threshold updates are inherited ordinary supervised learning. No autonomous tool-code or language-weight improvement is claimed. These are reused development patients; B is disjoint from A within a round, not a new external confirmation cohort.

''' if lang=='en' else '''# v0.30：重新核验旧记忆，独立确认整套更新

## 1. 已执行设计

v0.29回放发现旧记忆失效和已接纳编辑的负迁移。本登记干预复用v0.29已经独立核验的原策略／校准，真正重新运行记忆维护轨迹；不重新拟合基础预测器，不运行测试集。

每轮新witness按患者分为编辑组 **A** 和确认组 **B**。**C** 在提议规则前，用拟合患者的交叉拟合预测及A重新核验旧记忆；**P** 用B确认整套编辑后的记忆。验证失败时清空的是纠错记忆，当前校准后的处方策略仍输出药物集合，不会因此强制输出空处方。

贪心穷举、自身错误驱动语言生成、打乱数值证据三种方法各运行C/P四种组合，再加原策略和校准策略，共 **14种方法状态×五轮×三个种子×两种药物空间**。所有C/P组合只在A上编辑，计算相同的影子检查，仅改变验证结果是否影响保留状态。因此C0P0与上版使用整批witness编辑的设置不同。不同验证组合如果提示完全相同，会共享同一条真实模型响应；记忆分化后会生成新提示。

语言agent实际进化的是可执行规则记忆。C/P验证策略及工具由研究者固定；系数和阈值更新沿用普通监督学习，不称为自主工具代码／语言权重进化。患者来自已使用的开发数据；B在当前轮内与A隔离，不是新的外部确认队列。

''')
        text+='''```mermaid
flowchart TD
  F[Current audited policy and calibration] --> C
  M[Previous retained rule memory] --> C[Optional C: verify compatibility on cross-fit outputs and A]
  C --> E[Own / greedy / shuffled program proposal]
  E --> A[Up to four sequential edit checks on A]
  A --> P[Optional P: whole-memory confirmation on separate B]
  P --> R[Retain supported memory or reset corrections]
  R --> O[Current calibrated policy plus retained rules]
  R --> M
```

'''
        text+=('## 2. Actual execution status\n\n' if lang=='en' else '## 2. 真实运行状态\n\n')
        status=HERE.parent/'paper/execution_status.json'
        if status.exists() and json.loads(status.read_text())['api']['status']=='waiting_for_credit':text+=('**API interruption:** unfinished model calls await credit after a new HTTP402; completed states and audits are preserved.\n\n' if lang=='en' else '**API中断：** 新HTTP402后，未完成模型调用等待补充额度；已完成状态和独立核验保留。\n\n')
        text+='| Panel | Seed | Completed rounds /5 | Status |\n|---|---:|---:|---|\n'
        indexed={(z['lock']['panel'],z['lock']['seed']):z for z in runs}
        for panel in ['full','molecular']:
            for seed in [42,137,2026]:
                z=indexed.get((panel,seed),{'rounds':[],'status':'no_completed_round'})
                text+=f"| {panel} | {seed} | {len(z['rounds'])} | {z['status']} |\n"
        text+=('\nNine synthetic checks passed before the first run, including a correction that helps A but harms B, stale-memory resets, low-support rejection and patient isolation. These are execution checks, not clinical scores.\n' if lang=='en' else '\n首轮前通过九项合成检查，包括A上改善而B上有害的编辑、旧记忆清除、低支持度拒绝和患者隔离；这些是执行检查，不是临床分数。\n')
        if not summary['panels']:text+=('\n**Guard scores pending independent audit.**\n' if lang=='en' else '\n**guard成绩等待独立核验后发布。**\n')
        for endpoint in ['selected','final']:
            if not summary['panels']:break
            text+=f'\n## {3 if endpoint=="selected" else 4}. '+('Proposal-selected guard' if endpoint=='selected' else 'Raw round5 guard')+'\n\n'
            text+='| Panel | Arm | Audited seeds | Patient F1 ± SD | Patient Jaccard ± SD |\n|---|---|---:|---:|---:|\n'
            for panel,p in summary['panels'].items():
                for arm,z in p['endpoints'][endpoint]['methods'].items():
                    def fmt(k):
                        v=z[k];return f"{v['mean']:.5f}"+(f" ± {v['seed_sd']:.5f}" if v['seed_sd'] is not None else ' (one seed)')
                    text+=f"| {panel} | {arm} | {len(p['seeds'])} | {fmt('patient_f1')} | {fmt('patient_jaccard')} |\n"
            text+='\n| Panel | Registered contrast | F1 difference (pp) | Patient interval (pp) |\n|---|---|---:|---:|\n'
            for panel,p in summary['panels'].items():
                for name,z in p['endpoints'][endpoint]['contrasts'].items():
                    v=z['patient_f1'];lo,hi=v['patient_ci95'];text+=f"| {panel} | {name} | {100*v['difference']:+.3f} | [{100*lo:+.3f}, {100*hi:+.3f}] |\n"
        if summary['panels']:
            text+='\n## 5. Raw proposal rounds and actual gate actions\n\n| Panel | Round | Calibration F1 | Own C0P0 F1 | Own C1P1 F1 | Greedy C1P1 F1 | Own C1P1 rules by seed |\n|---|---:|---:|---:|---:|---:|---|\n'
            for panel,p in summary['panels'].items():
                for r in range(5):
                    curve=p['proposal_curves'];avg=lambda arm:sum(curve[arm][r]['proposal_f1'])/len(p['seeds']);text+=f'| {panel} | {r+1} | '+' | '.join(f'{avg(arm):.5f}' for arm in ['calibrated_policy','own_C0P0','own_C1P1','greedy_C1P1'])+' | '+str(curve['own_C1P1'][r]['memory_size'])+' |\n'
            text+='\n| Panel | Arm | C resets | P resets | Accepted edits before P | Logical model calls | Logical response USD |\n|---|---|---:|---:|---:|---:|---:|\n'
            for panel,p in summary['panels'].items():
                for arm,z in p['costs'].items():text+=f"| {panel} | {arm} | {z['compatibility_resets']} | {z['confirmation_resets']} | {z['accepted_edits_before_confirmation']} | {z['logical_model_calls']} | {z['logical_response_usd']:.5f} |\n"
            for panel,p in summary['panels'].items():
                text+=f"\n{panel}: {p['unique_request_count']} unique request hashes, USD {p['unique_response_usd']:.5f} in corresponding responses.\n\n"
        text+=('\nAll scores use the same 1,231 guard visits/467 patients. Intervals average observed seeds before patient resampling and are descriptive without multiplicity correction. Positive results on reused development cases do not establish final-test superiority. Exact shared responses reduce irrelevant generation noise; response costs are not fresh physical-spend estimates. Independent audit reconstructs source probabilities, patient roles, induction effects, every gate and final outputs; it does not rerun the full greedy candidate ranking.\n' if lang=='en' else '\n全部分数使用相同1,231次guard就诊／467人。区间先平均已有种子再按患者重采样，未作多重比较校正。已使用开发病例上的改善不等于最终测试领先。共享完全相同的响应减少无关生成噪声；响应成本不是本次新增实际扣款。独立核验重建源概率、患者角色、归纳效应、全部验证与最终输出，不重新穷举整个贪心候选排名。\n')
        text+='\n## Artifacts / 交付\n\n- [Registered protocol](protocol.json)\n- [Pre-execution checks](results/runtime_probe.json)\n- [Audit-gated summary](results/summary.json)\n- [Preceding diagnosis](../upgrade_v29/results/memory_diagnostic.json)\n'
        (HERE/f'RESULTS.{lang}.md').write_text(text)
if __name__=='__main__':main()
