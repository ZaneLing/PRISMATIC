"""Independent raw-order recount for the completed local parameter study."""
import json,sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parent
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v9'
CORE=('drug_name','route','dose_value','dose_unit')

def read(p):return json.loads(p.read_text())

def counts(pred,gold):
    p={r['drug_name'] for r in pred};g={r['drug_name'] for r in gold}
    po={tuple(r[k] for k in CORE) for r in pred if all(r.get(k) is not None for k in CORE)}
    go={tuple(r[k] for k in CORE) for r in gold if all(r.get(k) is not None for k in CORE)}
    return [len(p&g),len(p),len(g),len(po&go),len(po),len(go)]

def scores(c):
    s=c.sum(axis=0);return np.array([2*s[0]/max(1,s[1]+s[2]),2*s[3]/max(1,s[4]+s[5])])

def main():
    result_path=HERE/'results/parameter_results.json'
    if not result_path.exists():raise SystemExit('Parameter test generation still running; no final summary produced.')
    report=read(result_path);arms=['uniform_sft','error_prioritized_sft']
    assert set(report['arms'])==set(arms),'Both arms must finish before final reporting'
    assert (HERE/'results/tool_control_results.json').exists(),'Run the frozen tool control after selection is fixed'
    data=read(PRIVATE/'cases.json');test=data['test'];gold=[c['gold'] for c in test]
    raw={'base':read(PRIVATE/'base-test.json')};journals={};curves={}
    for arm in arms:
        journals[arm]=read(HERE/f'results/{arm}_rounds.json');assert len(journals[arm])==4
        for r in range(1,4):raw[f'{arm}_round_{r}']=read(PRIVATE/f'{arm}-round-{r}-test.json')
    matrices={};validation=[]
    for name,rows in raw.items():
        assert [r['case_id'] for r in rows]==[c['case_id'] for c in test]
        mat=np.array([counts(r['orders'],g) for r,g in zip(rows,gold)]);matrices[name]=mat
        expected=report['base'] if name=='base' else report['arms'][name.split('_round_')[0]]['raw_checkpoint_curve'][int(name[-1])-1]['metrics']
        assert np.allclose(scores(mat),[expected['drug_micro_f1'],expected['core_order_micro_f1']],rtol=0,atol=1e-12)
        validation.append({'method':name,'independent_recount':'passed'})
    selected={'base':matrices['base']}
    for arm in arms:
        choice=report['arms'][arm]['chosen_round'];selected[arm]=matrices['base' if choice==0 else f'{arm}_round_{choice}']
        curve=[];previous=matrices['base']
        for j in journals[arm]:
            k=j['active_round'];mat=matrices['base' if k==0 else f'{arm}_round_{k}'];before=2*previous[:,0]/np.maximum(1,previous[:,1]+previous[:,2]);after=2*mat[:,0]/np.maximum(1,mat[:,1]+mat[:,2])
            curve.append({'round':j['round'],'active_round':k,'scores':scores(mat).tolist(),'cases_improved_drug_f1':int((after>before+1e-12).sum()),'cases_regressed_drug_f1':int((after<before-1e-12).sum()),'mean_predicted_drugs':float(mat[:,1].mean())});previous=mat
        curves[arm]=curve
    tool=read(HERE/'results/tool_control_results.json')
    for name,m in tool.items():
        pred=read(PRIVATE/(name+'-test.json'));mat=np.array([counts(p,g) for p,g in zip(pred,gold)])
        assert np.allclose(scores(mat),[m['drug_micro_f1'],m['core_order_micro_f1']],rtol=0,atol=1e-12);selected[name]=mat
    patients=sorted({c['subject_hash'] for c in test});lookup={s:i for i,s in enumerate(patients)};gi=np.array([lookup[c['subject_hash']] for c in test])
    grouped={k:np.vstack([v[gi==i].sum(axis=0) for i in range(len(patients))]) for k,v in selected.items()}
    contrasts={}
    for a,b in [('uniform_sft','base'),('error_prioritized_sft','base'),('error_prioritized_sft','uniform_sft'),('uniform_sft','guard_selected_top_k_tools'),('error_prioritized_sft','guard_selected_top_k_tools')]:
        rng=np.random.default_rng(42);draws=[]
        for _ in range(2000):
            ix=rng.integers(0,len(patients),len(patients));draws.append(scores(grouped[a][ix])-scores(grouped[b][ix]))
        contrasts[a+'__minus__'+b]={'drug_order_difference':(scores(selected[a])-scores(selected[b])).tolist(),'patient_cluster_ci95':np.quantile(draws,[.025,.975],axis=0).tolist()}
    summary={'status':'complete','test_admissions':len(test),'test_patients':len(patients),'methods':{k:{'drug_f1':float(scores(v)[0]),'core_order_f1':float(scores(v)[1]),'mean_predicted_drugs':float(v[:,1].mean())} for k,v in selected.items()},
        'accepted_state_curves':curves,'paired':contrasts,'verification':validation,'interval_note':'Descriptive paired patient-cluster intervals, 2000 replicates, no multiple-comparison adjustment.',
        'mean_gold_drugs':float(matrices['base'][:,2].mean()),'mean_reachable_gold_drugs':float(np.mean([len(c['target']) for c in test]))}
    (HERE/'results/summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    fig,axes=plt.subplots(1,2,figsize=(9,3.6))
    for index,ax in enumerate(axes):
        for arm,curve in curves.items():ax.plot(range(4),[c['scores'][index] for c in curve],marker='o',label=arm.replace('_',' '))
        ax.axhline(scores(selected['guard_selected_top_k_tools'])[index],linestyle='--',color='gray',label='guard-selected direct tool')
        ax.set(xlabel='Round',ylabel=['Drug F1','Core-order F1'][index],xticks=range(4));ax.grid(alpha=.2)
    axes[-1].legend(fontsize=8);fig.tight_layout();fig.savefig(HERE/'round_curves.png',dpi=180);plt.close(fig)
    table='| Method | Drug F1 | Core-order F1 | Mean predicted drugs |\n|---|---:|---:|---:|\n'
    for k,m in summary['methods'].items():table+=f"| {k} | {m['drug_f1']:.5f} | {m['core_order_f1']:.5f} | {m['mean_predicted_drugs']:.2f} |\n"
    rounds='| Arm | Round | Selected checkpoint | Drug F1 | Order F1 | Cases improved / regressed |\n|---|---:|---:|---:|---:|---:|\n'
    for arm,curve in curves.items():
        for c in curve:rounds+=f"| {arm} | {c['round']} | {c['active_round']} | {c['scores'][0]:.5f} | {c['scores'][1]:.5f} | {c['cases_improved_drug_f1']} / {c['cases_regressed_drug_f1']} |\n"
    for lang in ['en','zh']:
        intro='''# v0.9 — Actual local QLoRA parameter evolution

## Protocol

Qwen3-4B 4-bit, last eight layers with 3.670M trainable adapter parameters. Three patient-disjoint 600-case feedback blocks; uniform and pre-update-error-prioritized sampling train on 400 cases for 100 steps each round. Both arms share the frozen initial-8k candidate/order tools, loss validation (100), guard (200), and new test (500 admissions / 494 patients). All selections were frozen before test evaluation. Optimizers reset per round while the latest adapter continues training. The chosen inference adapter is the best guard checkpoint. Model weights, feedback and patient data remain local.

## Matched method results

''' if lang=='en' else '''# v0.9：真实本地 QLoRA 参数进化

## 协议

Qwen3-4B 量化模型，最后八层共 367 万可训练适配参数。三个患者互不交叉的 600 例反馈块；普通采样与更新前错误优先采样每轮均用 400 例、100 步。两臂共用初始 8k 固定候选/订单工具、100 例损失验证、200 例选择检查及新的 500 次住院（494 位患者）测试。先冻结全部选择再评价测试。每轮重置优化器，继续训练最新适配器；推理保留检查集最优版本。模型权重、反馈和患者数据均只在本地。

## 同数据方法结果

'''
        end='''
## What evolves and what it means

Adapter files and sampling membership hashes change at each round. Candidate retrieval and joint-order templates are fixed. The model selects recorded templates; it does not learn novel dose generation. Clinical indication, DDI and renal safety are not established by agreement with historical orders. Ground truth supports automatic scoring without requiring new clinician review.

Strict versus normalized validity is retained: only an empty Qwen reasoning envelope is stripped. The pre-test parser/cache repair preserves raw outputs. Test predictions were independently recounted using drug sets and complete drug/route/dose/unit tuples, with patient-cluster paired intervals. Unknown fields remain unscored. A higher score than the initial model alone is insufficient evidence of an RSI benefit; error-prioritized updates must be compared with ordinary updates and direct use of the same tools.
''' if lang=='en' else '''
## 到底进化了什么

每轮真实改变适配器权重文件和训练采样成员哈希；候选检索及联合订单模板固定。模型学习选择已有模板，没有学习新剂量生成。历史医嘱一致性不等于指征、DDI 或肾功能安全；已有 GT 可自动评分，不要求医生重新标注后才能计算。

同时保留原始/归一化有效率，仅去除 Qwen 空 reasoning 标签。解析和缓存修复发生在测试前，原始输出保留。已独立按药物集合及药物/途径/剂量/单位完整元组重算，并给出患者聚类配对区间；未知字段不计分。只比初始模型好还不能证明 RSI 优势，必须看错误优先是否优于普通更新，以及是否优于直接使用相同工具。
'''
        (HERE/f'RESULTS.{lang}.md').write_text(intro+table+'\n## Round trajectories / 逐轮轨迹\n\n![Accepted-state trajectories](round_curves.png)\n\n'+rounds+end)
    print(json.dumps(summary['methods']))

if __name__=='__main__':main()
