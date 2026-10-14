"""Independent method/trajectory recount on the newly time-controlled cohort."""
import json,sys
from pathlib import Path
import joblib,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parent;PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v21'
sys.path.insert(0,str(HERE.parent/'upgrade_v9'))
from summarize import counts,scores

LABELS={'word_policy_global':'Word policy + global templates','word_policy_conditional_tool':'Word policy + conditional tool',
    'retrieval_global':'Case retrieval + global templates','retrieval_conditional_tool':'Case retrieval + conditional tool',
    'word':'Tuned word policy + tool','char':'Tuned character policy + tool','word_char_ensemble':'Word/character ensemble + tool',
    'multinomial_nb':'Naive Bayes + tool','rxrsi_selected':'RxRSI selected artifact state','without_parameters_evolution':'Freeze initial policy',
    'without_tool_evolution':'Freeze initial tool','without_memory_evolution':'Freeze initial memory','prevalence':'Training prevalence',
    'reuse_prior_orders':'Reuse recorded prior orders'}

def read(p):return json.loads(p.read_text())

def main():
    manifest=read(HERE/'results/execution_manifest.json');assert manifest['status']=='complete'
    data=joblib.load(PRIVATE/'data.joblib');truth=data['truth']['test'];n=len(truth)
    subjects=data['parts']['test'].subject_id;_,ix=np.unique(subjects.to_numpy(),return_inverse=True);ng=int(ix.max()+1)
    results=[];audits=[];rounds={};decisions={};contrasts={};simple=joblib.load(PRIVATE/'simple_controls.joblib')
    for seed in [42,137,2026]:
        r=read(HERE/f'results/round_results_seed_{seed}.json');strong=read(HERE/f'results/strong_results_seed_{seed}.json')
        saved=joblib.load(PRIVATE/f'run_seed_{seed}.joblib');other=joblib.load(PRIVATE/f'strong_seed_{seed}.joblib')
        predictions={**saved['predictions'],**other['predictions'],**simple};del saved,other
        reported={**r['method_scores'],**strong['method_scores'],**read(HERE/'results/simple_control_results.json')};matrices={}
        for name,pred in predictions.items():
            assert len(pred)==n
            matrix=np.array([counts(p,g) for p,g in zip(pred,truth)]);matrices[name]=matrix
            expected=r['rounds'][int(name.split('_')[1])]['metrics'] if name.startswith('round_') else reported[name]
            assert np.allclose(scores(matrix),[expected['drug_micro_f1'],expected['core_order_micro_f1']],atol=1e-12,rtol=0)
            assert int(matrix[:,1].max())<=20
        audited={k:{'drug_f1':float(scores(v)[0]),'order_f1':float(scores(v)[1]),'mean_predicted_drugs':float(v[:,1].mean()),'empty_fraction':float((v[:,1]==0).mean())} for k,v in matrices.items() if not k.startswith('round_')}
        results.append({'seed':seed,'methods':audited});audits.append({'seed':seed,'method_and_round_prediction_recounts':'passed','n_test':n})
        grouped={}
        for key,m in matrices.items():
            grouped[key]=np.zeros((ng,6));np.add.at(grouped[key],ix,m)
        contrasts[str(seed)]={}
        for left,right in [('rxrsi_selected','word_char_ensemble'),('rxrsi_selected','word_policy_conditional_tool'),('rxrsi_selected','round_0'),('rxrsi_selected','without_tool_evolution'),('rxrsi_selected','without_memory_evolution'),('rxrsi_selected','without_parameters_evolution')]:
            rng=np.random.default_rng(42);draws=[]
            for _ in range(2000):
                choice=rng.integers(0,ng,ng);draws.append(scores(grouped[left][choice])-scores(grouped[right][choice]))
            contrasts[str(seed)][left+'__minus__'+right]={'drug_order_difference':(scores(matrices[left])-scores(matrices[right])).tolist(),'patient_ci95':np.quantile(draws,[.025,.975],axis=0).tolist()}
        curve=[];before=None
        for i in range(5):
            m=matrices[f'round_{i}'];per=.5*(2*m[:,0]/np.maximum(1,m[:,1]+m[:,2])+2*m[:,3]/np.maximum(1,m[:,4]+m[:,5]))
            delta=per-before if before is not None else np.zeros(n);before=per
            curve.append({'round':i,'training_cases':8000*(i+1),'drug_f1':float(scores(m)[0]),'order_f1':float(scores(m)[1]),
                'improved_cases':int((delta>1e-12).sum()),'regressed_cases':int((delta< -1e-12).sum()),'empty_fraction':float((m[:,1]==0).mean())})
        rounds[str(seed)]=curve
        dec=read(HERE/f'results/decisions_seed_{seed}.json')
        decisions[str(seed)]=[{k:d[k] for k in ['round','training_cases','accepted','active','parameter_sha256','memory_sha256','tool_sha256','conditional_tool_drugs','guard_case_improvements','guard_case_regressions']} for d in dec]
    methods={}
    for name in LABELS:
        v=np.array([[r['methods'][name][key] for key in ['drug_f1','order_f1','mean_predicted_drugs','empty_fraction']] for r in results])
        methods[name]={k:float(value) for k,value in zip(['drug_f1_mean','order_f1_mean','mean_predicted_drugs','empty_fraction'],v.mean(0))}
        methods[name].update(drug_f1_sd=float(v[:,0].std(ddof=1)),order_f1_sd=float(v[:,1].std(ddof=1)))
    classes=set(data['classes']);goldsets=[{o['drug_name'] for o in row} for row in truth]
    summary={'status':'complete','test_admissions':n,'test_patients':ng,'methods':methods,'per_seed':results,'rounds':rounds,'artifact_updates':decisions,'paired':contrasts,'audits':audits,
      'gold_drug_instances':sum(map(len,goldsets)),'vocabulary_recall_ceiling':sum(len(g&classes) for g in goldsets)/sum(map(len,goldsets)),
      'inference_scope':'Matched recorded-availability inputs,128 raw-name labels,20-order cap; no LLM/API calls. Separate from old start-time task.',
      'statistics':'Sample SD across3 seeds; descriptive paired patient-cluster intervals2000 draws; no multiplicity correction.'}
    (HERE/'results/summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    fig,axes=plt.subplots(1,2,figsize=(10,3.6))
    for j,(key,label) in enumerate([('drug_f1','Drug micro-F1'),('order_f1','Core-order micro-F1')]):
        for seed,curve in rounds.items():axes[j].plot(range(5),[x[key] for x in curve],marker='o',label=f'Seed {seed}')
        axes[j].axhline(methods['word_char_ensemble'][key+'_mean'],linestyle='--',color='gray',label='Full-data ensemble mean')
        axes[j].set(xlabel='Feedback round (8k to40k cumulative cases)',ylabel=label,xticks=range(5));axes[j].grid(alpha=.2);axes[j].legend(fontsize=7)
    fig.tight_layout();fig.savefig(HERE/'round_curves.png',dpi=180);plt.close(fig)
    table='| Method | Drug F1 mean ± SD | Core-order F1 mean ± SD | Mean drugs | Empty (%) |\n|---|---:|---:|---:|---:|\n'
    for name,label in LABELS.items():
        m=methods[name];table+=f"| {label} | {m['drug_f1_mean']:.5f} ± {m['drug_f1_sd']:.5f} | {m['order_f1_mean']:.5f} ± {m['order_f1_sd']:.5f} | {m['mean_predicted_drugs']:.2f} | {100*m['empty_fraction']:.2f} |\n"
    rt='| Seed | Round | Training cases | Drug F1 | Order F1 | Improved / regressed |\n|---|---:|---:|---:|---:|---:|\n'
    for seed,curve in rounds.items():
        for c in curve:rt+=f"| {seed} | {c['round']} | {c['training_cases']} | {c['drug_f1']:.5f} | {c['order_f1']:.5f} | {c['improved_cases']} / {c['regressed_cases']} |\n"
    for lang in ['en','zh']:
        intro='''# v0.21 — Recorded-availability-controlled order comparison

## Task and cohort

The decision is actual hospital admission plus6h; targets are new/changed orders during the next6h. Provider and pharmacy entry clocks must both lie in the target window with exact patient/admission/POE linkage and pharmacy verification by its end. Cases with inconsistent potential targets are excluded. Inputs contain demographics, previously recorded orders and blood tests available by the decision; untimed triage, discharge diagnoses and future results are omitted.

Of201,750 source admissions,54,959 meet the coherent-time, nonempty-target and complete-followup criteria. Sampling and previous-test exclusions yield40,000 training,2,000 proposal,2,000 guard and1,082 test admissions (1,024 test patients). All splits are patient-disjoint, and old v6/v7/v9 test patients are excluded from this test. An independent source/serialization audit passes all12 clock/identity/finiteness checks. The cohort remains retrospectively selected and released tables lack full field-version history.

## Matched methods

All rows share inputs, initial8k-frozen128-name vocabulary, an at-most20-order output cap, and drug/core-order scoring. Gold names outside the vocabulary remain in recall. This repeats the frozen artifact-learning method family under a repaired time protocol; it is not a GAMENet/SafeDrug reproduction or new LLM architecture. Full-data models control for accumulated supervision. Hyperparameters use proposal labels; evolving states additionally pass the independent guard. Three seeds were registered before training.

''' if lang=='en' else '''# v0.21：控制记录可用时间后的订单方法对比

## 任务与队列

决策时间是实际入院后第6小时，预测随后6小时新增/修改的订单。目标要求医生下单时间和药房录入时间同时处于预测窗口，患者/住院/POE关联一致，并在窗口结束前得到药房验证。存在不一致潜在目标的住院病例被排除。输入只含人口学信息、决策前已记录的订单和血液检验，不使用无时间戳分诊、出院诊断及未来检验。

201,750次源住院中，54,959次满足时间一致、窗口内有订单、随访完整。固定抽样并排除旧测试患者后，得到40,000训练、2,000候选验证、2,000退化检查和1,082测试住院（1,024位测试患者）。各集合患者不交叉，新测试也排除了v6/v7/v9测试患者。独立源表/序列化复核的12项身份、时间和数值检查全部通过。仍需注意：这是事后筛选的队列，公开表没有完整字段修改历史。

## 相同协议的方法比较

所有行共用输入、初始8k冻结的128药名词表、最多20订单和相同药物/核心订单评分；词表外GT仍在召回分母中。本轮是在修正时间协议下重跑固定的方法族，并非复现GAMENet/SafeDrug或提出新的LLM结构。全量监督对照控制新增训练数据本身的收益；超参数用候选验证集，进化版本还必须通过独立退化检查。三个种子在训练前注册。

'''
        tail='''
## Evolution scope and limits / 进化范围与边界

Persistent selection parameters, training memory and conditional order-tool parameters change. LLM weights and executable code do not change in this experiment. Parameter, memory and tool hashes, promotion decisions and paired intervals are in `results/summary.json`. Freeze-one-object ablations retain the other final settings and are not separately optimized. The same-data full-data control is necessary: improvement over an8k initial checkpoint alone is not an RSI advantage.

Every saved method/checkpoint prediction has been independently recounted. Historical order agreement does not establish clinical indication, DDI or renal safety; missing clinical fields remain unknown. This table belongs to its own recorded-availability task and must not be numerically merged with the earlier start-time task or author-reported paper scores. Restricted cases, features, predictions and models stay local.
'''
        if lang=='zh':tail='''
## 进化范围与边界

变化对象是持久的处方选择参数、训练病例记忆和条件订单工具参数；本轮不修改LLM权重或可执行代码。参数/记忆/工具哈希、接纳决定及配对区间见 `results/summary.json`。冻结单个对象的消融保留其他最终设置，没有重新调优。必须与相同40k数据的强对照比较：仅超过初始8k版本不足以证明RSI独特收益。

所有方法和逐轮检查点的保存预测均已独立重算。历史医嘱一致性不等于指征、DDI或肾功能安全，缺失字段保持未知。本表属于独立的记录可用时间任务，不能与旧starttime任务或论文原始分数直接混排。受限病例、特征、预测及模型均保留本地。
'''
        (HERE/f'RESULTS.{lang}.md').write_text(intro+table+'\n## Fixed-test trajectories / 固定测试逐轮轨迹\n\n![Round trajectories](round_curves.png)\n\n'+rt+tail)
    print(json.dumps({'status':'complete','methods':methods}),flush=True)

if __name__=='__main__':main()
