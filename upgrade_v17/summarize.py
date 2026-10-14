"""Independent factorial/round audit; no checkpoint selected using test labels."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parent
LOCAL=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/rxrsi-v8'
FOLDER=LOCAL/'grounded-grasp-v17-seed-42'

def read(p):return json.loads(p.read_text())

def interval(delta,cases):
    groups=[c.get('group_id',c['id']) for c in cases];names=sorted(set(groups));lookup={g:i for i,g in enumerate(names)}
    ix=np.array([lookup[g] for g in groups]);totals=np.bincount(ix,weights=delta);counts=np.bincount(ix)
    rng=np.random.default_rng(42);draws=[]
    for _ in range(4000):
        b=rng.integers(0,len(names),len(names));draws.append(totals[b].sum()/counts[b].sum())
    return {'difference':float(delta.mean()),'ci95':np.quantile(draws,[.025,.975]).tolist(),'groups':len(names)}

def main():
    main=read(HERE/'results/method_results.json');assert main['status']=='complete'
    frozen=read(HERE/'results/frozen_skills.json')['skills_sha256']
    for name,source in [('round_2','.history/label_indication_and_caution_parsing_v1.md'),('round_3','.history/label_indication_and_caution_parsing_v2.md'),('round_4','label_indication_and_caution_parsing.md')]:
        path=HERE/'artifacts'/name/'label_indication_and_caution_parsing.md'
        assert hashlib.sha256(path.read_bytes()).hexdigest()==frozen[source]
    data=read(LOCAL/'data.json');summary={'status':'complete_main_comparison','datasets':{},'round_status':'pending',
        'interval_note':'Exploratory paired scenario-cluster intervals for RxSafeBench, item bootstrap for RxQA; 4000 draws, no multiplicity adjustment.'}
    methods={'cot':'CoT','author_grasp':'Author GRASP core','fixed_grounded':'Fixed grounded harness','evolving_grounded':'Grounded skill evolution'}
    all_correct={};tables={}
    for dataset,cases in [('rxsafebench',data['parts']['test']),('rxqa',data['transfer'])]:
        correct={};metrics={}
        for method in methods:
            p=FOLDER/'round_evaluation'/(method+'-'+dataset+'.json') if method in ['cot','author_grasp'] else FOLDER/(method+'-'+dataset+'.json')
            rows=read(p);assert [r['case_id'] for r in rows]==[c['id'] for c in cases]
            a=np.array([r['prediction']==c['gold'] for r,c in zip(rows,cases)],dtype=int)
            assert all(bool(r['correct'])==bool(v) for r,v in zip(rows,a));correct[method]=a
            metrics[method]={'correct':int(a.sum()),'n':len(a),'accuracy':float(a.mean()),'invalid':sum(r['prediction'] is None for r in rows)}
            if method in main['methods']:assert metrics[method]['correct']==main['methods'][method][dataset]['correct']
        contrasts={}
        for left,right in [('evolving_grounded','fixed_grounded'),('evolving_grounded','author_grasp'),('author_grasp','cot'),('fixed_grounded','cot')]:
            d=correct[left]-correct[right];contrasts[left+'__minus__'+right]={**interval(d,cases),'fixes':int((d>0).sum()),'regressions':int((d<0).sum())}
        interaction=correct['evolving_grounded']-correct['fixed_grounded']-correct['author_grasp']+correct['cot']
        summary['datasets'][dataset]={'methods':metrics,'paired':contrasts,'factorial_interaction':interval(interaction,cases),'independent_recount':'passed'};all_correct[dataset]=correct
        table='| Method | Correct | Accuracy (%) | Calls / case |\n|---|---:|---:|---:|\n'
        for k,label in methods.items():table+=f"| {label} | {metrics[k]['correct']}/{len(cases)} | {100*metrics[k]['accuracy']:.2f} | 1 |\n"
        tables[dataset]=table
    updates=read(FOLDER/'epoch_0/skill_updates.json')
    summary['updates']=[{'round':x['update_cycle']+1,'new_cases':x['batch_size'],'applied':[{'action':a['action'],'name':a['name']} for a in x['applied']]} for x in updates]
    round_path=HERE/'results/round_metrics.json';round_table='Round evaluation is still running; no monotonic-improvement claim.'
    if round_path.exists() and read(round_path)['status']=='complete':
        summary['round_status']='complete';summary['rounds']={};fig,axes=plt.subplots(1,2,figsize=(9,3.5))
        round_table='| Dataset | Round | Seen cases | Correct | Fixes / regressions |\n|---|---:|---:|---:|---:|\n'
        for j,(dataset,cases) in enumerate([('rxsafebench',data['parts']['test']),('rxqa',data['transfer'])]):
            curve=[];before=all_correct[dataset]['fixed_grounded']
            for r,(name,nseen) in enumerate([('fixed_grounded',0),('fixed_grounded',157),('round_2',314),('round_3',471),('round_4',625)]):
                rows=read(FOLDER/'round_evaluation'/(name+'-'+dataset+'.json'));assert [x['case_id'] for x in rows]==[c['id'] for c in cases]
                a=np.array([x['prediction']==c['gold'] for x,c in zip(rows,cases)],dtype=int);d=a-before
                row={'round':r,'training_cases':nseen,'correct':int(a.sum()),'accuracy':float(a.mean()),'fixes':int((d>0).sum()),'regressions':int((d<0).sum())};curve.append(row);before=a
                round_table+=f"| {dataset} | {r} | {nseen} | {row['correct']}/{len(cases)} | {row['fixes']} / {row['regressions']} |\n"
            assert np.array_equal(before,all_correct[dataset]['evolving_grounded'])
            summary['rounds'][dataset]=curve;axes[j].plot(range(5),[100*c['accuracy'] for c in curve],marker='o')
            axes[j].axhline(100*all_correct[dataset]['author_grasp'].mean(),linestyle='--',color='gray',label='Author core, no labels');axes[j].set(title=dataset,xlabel='Feedback round',ylabel='Accuracy (%)',xticks=range(5));axes[j].grid(alpha=.2);axes[j].legend(fontsize=8)
        fig.tight_layout();fig.savefig(HERE/'round_curves.png',dpi=180);plt.close(fig)
    (HERE/'results/summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    for lang in ['en','zh']:
        if lang=='en':
            text='''# v0.17 — Grounded skill evolution and matched component controls

## Design and main result

The unchanged GRASP core (pin `9d7d125a`) learns skill files over the fixed openFDA excerpt tool. Both evidence/no-evidence and skill/no-skill controls use the same actor prompt, DeepSeek-V4.1-Flash and one 512-token call. 625 training cases are exposed in four batches; the original core uses balanced training probes and end-of-epoch validation on 387 cases. LLM weights, retrieval code and label snapshot stay fixed. This is a grounded task harness with a credited optimizer, not a novel optimizer claim.

### Same 988 derived RxSafeBench questions

'''+tables['rxsafebench']+'''
### Separate 300-question RxQA transfer

'''+tables['rxqa']+'''
Combining the components yields only two additional correct test answers over fixed grounded inference and one fewer than author-core GRASP without evidence. Transfer declines by five answers versus the fixed grounded control. The validation gain (49.1% to 53.2%) does not establish a test or transfer benefit. The paired factorial interaction is also reported; it tests whether the combined gain exceeds the sum of separate component gains. Negative results are retained.

## What changed and when?

Round 1 accepts no skill. Round 2 adds `label_indication_and_caution_parsing`; rounds 3 and 4 modify it. Exact generated text and SHA-256 hashes are released under `artifacts/` and `results/round_artifacts.json`. The artifacts contain model-generated decision guidance and are not clinical authority. Test and transfer labels never select the skill state. Intermediate evaluations are descriptive process evidence on an already observed development benchmark.

'''+round_table+'''

All final predictions are independently recounted and case-aligned; paired scenario/item intervals and repairs/regressions are in `results/summary.json`. Test-time costs are logical cached-or-new usage; actual charged calls remain in the local shared ledger. No restricted patient data is used.
'''
        else:
            text='''# v0.17：说明书证据与技能进化的完整组件对照

## 设计与主结果

使用未改源码的 GRASP 作者核心（`9d7d125a`）学习技能文件，底层证据工具固定为 openFDA 连续片段。证据/无证据、技能/无技能共用同一答案提示、DeepSeek-V4.1-Flash 和一次 512-token 调用。625 个训练病例分四批；作者核心用训练集平衡探针筛选，并在每个 epoch 结束后用 387 个验证病例选择状态。模型权重、检索代码与说明书快照不变。这是引用已有优化器的处方 harness 集成，不宣称新优化器。

### 同一 988 题 RxSafeBench 衍生任务

'''+tables['rxsafebench']+'''
### 单独的 300 题 RxQA 迁移

'''+tables['rxqa']+'''
组合后仅比固定证据多答对 2 题，比无证据作者 GRASP 少答对 1 题；迁移比固定证据少答对 5 题。验证集 49.1%→53.2% 不足以证明测试/迁移收益。另报告四格组件交互量，检查组合增益是否超过两个单独增益之和；负结果完整保留。

## 究竟进化了什么，哪一轮改变？

第 1 轮不接受技能；第 2 轮新增 `label_indication_and_caution_parsing`，第 3/4 轮修改它。`artifacts/` 公开每个版本的实际文本，`results/round_artifacts.json` 保存哈希。这些是模型生成的决策指引，不是临床权威资料。测试/迁移标签不参与状态选择；中间版本评价用于已观察开发基准上的过程分析。

'''+round_table+'''

已独立核对全部最终预测、病例对应和分数，配对场景/题目区间及修复退化见 `results/summary.json`。推理成本记录逻辑使用量（包括缓存），实际扣费另记本地共享账本。未使用受限患者数据。
'''
        if summary['round_status']=='complete':text+='\n![Frozen skill trajectories](round_curves.png)\n'
        (HERE/f'RESULTS.{lang}.md').write_text(text)
    print(json.dumps({'datasets':summary['datasets'],'round_status':summary['round_status']}))

if __name__=='__main__':main()
