"""Recount public predictions and summarize only fully completed evolution runs."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from public_client import LOCAL,digest
HERE=Path(__file__).resolve().parent
METHODS=['direct','cot','self_refine','case_rag','reflexion_adapt','grasp_adapt','evotool_adapt','rxrsi']
LABELS=['Direct','CoT','Self-Refine','Case RAG','Reflexion adaptation','GRASP adaptation','EvoTool adaptation','RxRSI']

def read(p):return json.loads(p.read_text())

def main():
    data=read(LOCAL/'data.json');test=data['parts']['test'];reports=[];checks=[];paired=[]
    for seed in [42,137,2026]:
        path=HERE/f'results/public_results_seed_{seed}.json'
        if not path.exists():continue
        report=read(path)
        if report.get('status','complete')!='complete':continue
        if set(report['methods'])!=set(METHODS) or 'rxqa_transfer' not in report:continue
        assert report['test_n']==len(test)
        out=LOCAL/f'seed-{seed}';correct={}
        for method in METHODS:
            rows=read(out/(method+'-test.json'))
            assert not any(r.get('error') for r in rows),'Transport failures cannot be included in method accuracy.'
            assert [r['case_id'] for r in rows]==[c['id'] for c in test]
            correct[method]=np.array([r['prediction']==c['gold'] for r,c in zip(rows,test)])
            assert int(correct[method].sum())==report['methods'][method]['correct']
            if method in report['round_curves']:
                versions=read(out/(method+'-versions.json'));assert len(versions)==5
                for v in versions:assert v['state_sha256']==digest(v['active'])
        groups=sorted({c['group_id'] for c in test});lookup={g:i for i,g in enumerate(groups)};gi=np.array([lookup[c['group_id']] for c in test]);n=np.bincount(gi)
        for baseline in METHODS[:-1]:
            delta=correct['rxrsi'].astype(int)-correct[baseline].astype(int);sums=np.bincount(gi,weights=delta)
            rng=np.random.default_rng(42);samples=[]
            for _ in range(4000):
                ix=rng.integers(0,len(groups),len(groups));samples.append(float(sums[ix].sum()/n[ix].sum()))
            paired.append({'seed':seed,'baseline':baseline,'accuracy_difference':float(delta.mean()),'scenario_cluster_ci95':np.quantile(samples,[.025,.975]).tolist(),
                'fixes':int((delta>0).sum()),'regressions':int((delta<0).sum()),'interval_note':'Descriptive paired interval; not multiplicity-adjusted.'})
        checks.append({'seed':seed,'case_alignment':'passed','independent_correct_recount':'passed','version_hashes':'passed','scenario_test_groups':len(groups)})
        reports.append(report)
    if not reports:raise SystemExit('No complete seed yet; no final result report emitted.')
    summary={}
    for method in METHODS:
        xs=[r['methods'][method]['accuracy'] for r in reports]
        summary[method]={'accuracy_mean':float(np.mean(xs)),'accuracy_sample_sd':float(np.std(xs,ddof=1)) if len(xs)>1 else None,
            'seeds':[r['seed'] for r in reports],'invalid_total':sum(r['methods'][method]['invalid'] for r in reports),
            'mean_logical_inference_cost_usd':float(np.mean([r['methods'][method]['cost_usd'] for r in reports]))}
    ledger=[json.loads(s) for s in (LOCAL/'usage.jsonl').read_text().splitlines()]
    output={'completed_seeds':[r['seed'] for r in reports],'methods':summary,'paired_comparisons':paired,'verification':checks,
       'shared_public_api_ledger_snapshot':{'requests':len(ledger),'charged_usd':sum(r.get('cost_usd') or 0 for r in ledger),'scope':'Shared ledger for v8 and later public studies, not a v8-only attribution.'},
       'primary_task':'Derived RxSafeBench option selection, 988 test cases; no original-paper score equivalence.'}
    (HERE/'results/summary.json').write_text(json.dumps(output,indent=2)+'\n')
    fig,axes=plt.subplots(1,len(reports),figsize=(5*len(reports),3.6),squeeze=False)
    for ax,r in zip(axes[0],reports):
        for method,curve in r['round_curves'].items():ax.plot([c['round'] for c in curve],[100*c['score']['accuracy'] for c in curve],marker='o',label=method.replace('_adapt',''))
        ax.set(title=f"Evolution order seed {r['seed']}",xlabel='Accepted-state checkpoint',ylabel='Fixed-test accuracy (%)',xticks=range(5));ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.tight_layout();fig.savefig(HERE/'round_curves.png',dpi=180);plt.close(fig)
    first=reports[0]
    for lang in ['en','zh']:
        table='| Method | Accuracy (%) | Seed SD (pp) | Invalid outputs |\n|---|---:|---:|---:|\n'
        for method,label in zip(METHODS,LABELS):
            m=summary[method];sd='—' if m['accuracy_sample_sd'] is None else f"{100*m['accuracy_sample_sd']:.2f}"
            table+=f"| {label} | {100*m['accuracy_mean']:.2f} | {sd} | {m['invalid_total']} |\n"
        versions=read(LOCAL/f"seed-{first['seed']}/rxrsi-versions.json")
        changes='| Round | Accepted | Changed artifacts | Guard fixes / regressions | Test accuracy (%) |\n|---|---|---|---:|---:|\n'
        for v,c in zip(versions,first['round_curves']['rxrsi']):
            changed=', '.join(k for k,z in v.get('artifact_changes',{}).items() if z['changed']) or 'none'
            d=v.get('guard_transition',{});changes+=f"| {v['round']} | {v['accepted']} | {changed} | {d.get('fixes',0)} / {d.get('regressions',0)} | {100*c['score']['accuracy']:.2f} |\n"
        ablation='| Variant | Accuracy (%) |\n|---|---:|\n'
        for name,m in first['ablations'].items():ablation+=f"| {name} | {100*m['accuracy']:.2f} |\n"
        tr=first['rxqa_transfer'];delta=tr['change'];seeds=', '.join(str(r['seed']) for r in reports)
        if lang=='en':
            text=f'''# RxRSIAgent v0.8: executed language-artifact evolution

Completed evolution-order seeds: {seeds}. Missing seeds are not counted as completed. The fixed backbone is DeepSeek-V4.1-Flash. All methods share the scenario-group split: 625 train / 190 proposal / 197 guard / 988 test cases. This is a derived medication-option task; original free-generation paper scores are not directly comparable.

## Method comparison

'''+table+'''
The named Reflexion, GRASP and EvoTool rows are independent task adaptations, not official reproductions. All evolution methods receive four candidate-evaluation slots per round; proposal costs can differ. Invalid outputs count as wrong. Across-seed SD measures training-order sensitivity, not independent patient sampling uncertainty.

## What changed and what improved

![Fixed-test trajectories](round_curves.png)

'''+changes+'''
The table above shows the first completed seed. Full before/after text and rejected candidates are released in version journals. A rejected proposal leaves the active state unchanged. Backbone weights and tool source code remain fixed; focus terms change only the evidence tool's configuration.

## Object ablations

'''+ablation+f'''
## RxQA transfer (all 300 public OpenFDA questions)

CoT: {tr['cot']['correct']}/300 ({100*tr['cot']['accuracy']:.2f}%); RxRSI: {tr['rxrsi']['correct']}/300 ({100*tr['rxrsi']['accuracy']:.2f}%). Fixes/regressions: {delta['fixes']}/{delta['regressions']}. No RxQA labels are used to update the artifacts.

## Verification and interpretation

Saved predictions were independently recounted with exact case alignment and version-hash checks. Scenario-cluster paired intervals and all method contrasts are in `results/summary.json`; these intervals are descriptive and not multiplicity-adjusted. Per-method cost denotes logical inference use; the API ledger separately records actual calls, including evolution. Repeated guard reuse is development selection. A gain, a flat curve or a regression is retained exactly as observed; none establishes unrestricted clinical prescribing ability.
'''
        else:
            text=f'''# RxRSIAgent v0.8：真实语言技能进化实验

已完整完成的训练顺序种子：{seeds}。未完成种子不计入汇总。固定 DeepSeek-V4.1-Flash，所有方法共用 625 训练 / 190 候选选择 / 197 退化检查 / 988 测试。这里是 RxSafeBench 衍生选药题，不能与原论文自由生成分数混排。

## 同数据方法主表

'''+table+'''
Reflexion、GRASP、EvoTool 为独立任务适配，未称官方复现。每轮都有四个候选评价名额，提议 token 成本可能不同。无效输出计错；跨种子标准差衡量训练顺序敏感性。

## 每一轮到底变了什么

![固定测试集逐轮曲线](round_curves.png)

'''+changes+'''
上表为第一个完整种子。版本文件保存完整修改文本及被拒绝候选；拒绝后继续使用原状态。模型权重与工具源代码固定，关注词只修改证据工具配置。

## 对象消融

'''+ablation+f'''
## RxQA 迁移：公开 OpenFDA 全量 300 题

CoT：{tr['cot']['correct']}/300（{100*tr['cot']['accuracy']:.2f}%）；RxRSI：{tr['rxrsi']['correct']}/300（{100*tr['rxrsi']['accuracy']:.2f}%）。修复/退化：{delta['fixes']}/{delta['regressions']}。RxQA 答案没有用于修改技能。

## 核验与解释边界

预测已独立重算、核对逐例对齐及版本哈希。场景组聚类的配对区间见 `results/summary.json`；区间为描述性结果，未作多重比较修正。方法成本统计逻辑推理用量，实际账本另记包含演化的真实请求。反复使用的退化检查集属于开发资源。上升、持平、退化均原样保留，不把选择题收益解释成完整临床处方能力。
'''
        (HERE/f'RESULTS.{lang}.md').write_text(text)
    print(json.dumps({'completed_seeds':output['completed_seeds'],'methods':summary,'verification':'passed'}))

if __name__=='__main__':main()
