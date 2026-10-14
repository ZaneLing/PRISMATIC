"""Independent development-only recount and patient-cluster uncertainty."""
import json,sys
from pathlib import Path
import joblib,numpy as np
HERE=Path(__file__).resolve().parent;PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v22'
sys.path.insert(0,str(HERE.parent/'upgrade_v9'))
from summarize import counts,scores

def main():
    report=json.loads((HERE/'results/development_results.json').read_text());assert not report['test_used']
    saved=joblib.load(PRIVATE/'pilot.joblib');data=joblib.load(PRIVATE.parent/'prismatic-v21/data.joblib');gold=data['truth']['guard']
    matrices={}
    for name,key,expected in [('typed_candidate','predictions','candidate_guard'),('word_char_control','control_predictions','strong_control_guard')]:
        pred=saved[key];assert len(pred)==len(gold)
        mat=np.array([counts(p,g) for p,g in zip(pred,gold)]);matrices[name]=mat
        assert np.allclose(scores(mat),[report[expected]['drug_micro_f1'],report[expected]['core_order_micro_f1']],rtol=0,atol=1e-12)
    assert all(np.isfinite(m.coef_).all() and np.isfinite(m.intercept_).all() for m in saved['model'].estimators_)
    _,ix=np.unique(data['parts']['guard'].subject_id.to_numpy(),return_inverse=True);n=int(ix.max()+1);grouped={}
    for k,m in matrices.items():grouped[k]=np.zeros((n,6));np.add.at(grouped[k],ix,m)
    rng=np.random.default_rng(42);draws=[]
    for _ in range(2000):
        inds=rng.integers(0,n,n);draws.append(scores(grouped['typed_candidate'][inds])-scores(grouped['word_char_control'][inds]))
    summary={'status':'complete_development_only','test_used':False,'independent_recount':'passed','finite_model_parameters':True,'guard_admissions':len(gold),'guard_patients':n,
      'selected_state':report['selected']['state'],'candidate_guard':report['candidate_guard'],'control_guard':report['strong_control_guard'],
      'drug_order_difference':(scores(matrices['typed_candidate'])-scores(matrices['word_char_control'])).tolist(),'patient_ci95':np.quantile(draws,[.025,.975],axis=0).tolist(),
      'passes_declared_guard_rule':report['passes_declared_guard_rule'],'interpretation':'Development selection evidence only; reused guard and one seed. No test or RSI superiority inference.'}
    (HERE/'results/summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    table='| Method | Guard drug F1 | Guard core-order F1 | Mean drugs | Empty (%) |\n|---|---:|---:|---:|---:|\n'
    for label,k in [('Selected typed-state intervention','candidate_guard'),('Existing word/character control','strong_control_guard')]:
        r=report[k];table+=f"| {label} | {r['drug_micro_f1']:.5f} | {r['core_order_micro_f1']:.5f} | {r['mean_predicted_drugs']:.2f} | {100*r['empty_fraction']:.2f} |\n"
    for lang in ['en','zh']:
        intro='''# v0.22 — Numerical-state representation pilot

## Question and predeclared design

Does a more faithful representation of already-available numerical state improve selection? The v0.21 text policy tokenizes lab numbers and prior doses as words. This pilot adds standardized numerical values with explicit observed flags, prior-drug/route presence and demographics. Input vocabulary and robust numerical scales are fitted only on the initial8k training contexts. Units stay distinct; no clinical threshold or future information is added.

Two feature views (typed alone or word+typed), three regularizers and seven thresholds compete on the2,000-case proposal split. One candidate then faces the same2,000-case guard as the preselected word/character control. Both use40k training cases, seed42,128 labels, at most20 outputs, and the unchanged v0.21 full-data conditional order tool. The comparator keeps its original proposal-selected tool setting. **No v0.21 test score is computed by this pilot.**

## Actual development results

''' if lang=='en' else '''# v0.22：数值状态表示的开发试验

## 问题与事先声明的设计

把已有数值信息表示清楚，是否能改善药物选择？v0.21词模型把检验值、先前剂量等当作文本词处理。本轮增加标准化数值、明确的观测存在标记、已有药物/途径和人口学特征。输入词表和数值尺度仅由初始8k训练上下文拟合，区分单位，没有添加临床阈值或未来信息。

两个表示视图（仅类型化状态、词＋类型化状态）、三个正则参数和七个阈值只在2,000例候选验证上选择。唯一候选再与已选定词/字符强对照在同2,000例检查集比较。两者使用40k训练例、seed42、128标签、最多20订单；候选固定使用原v0.21全量条件订单工具，对照保留其原候选验证选择的工具设置。**本试验不计算v0.21测试分数。**

## 实际开发集结果

'''
        selected=report['selected']['state'];description=f"\nSelected view / 选中表示：`{selected['view']}`; alpha=`{selected['alpha']}`; threshold=`{selected['threshold']}`.\n\n"
        delta=summary['drug_order_difference'];ci=summary['patient_ci95']
        description+=f"Drug/order differences / 药物与订单F1差值：{delta[0]:+.5f}, {delta[1]:+.5f}; patient-cluster95% intervals / 患者聚类区间：[{ci[0][0]:+.5f}, {ci[1][0]:+.5f}], [{ci[0][1]:+.5f}, {ci[1][1]:+.5f}].\n\n"
        description+=f"Declared guard rule passed / 是否通过预设检查：**{report['passes_declared_guard_rule']}**.\n"
        tail='''
## Interpretation

Predictions were independently recounted; learned parameters are finite. This changes the selection representation and parameters, not language-model weights, executable tools or clinical knowledge. It is an engineering/development intervention, not recursive self-improvement or a held-out test win. The guard has been used in preceding development and this pilot has one seed. Even a positive result needs a registered round-wise, equal-data, multi-seed comparison and fresh confirmation. All patient data, features, numerical statistics, weights and predictions remain local.
''' if lang=='en' else '''
## 如何解释

保存预测已独立重算，模型参数均为有限数。本轮改变选择模型的表示和参数，没有改变大模型权重、可执行工具或临床知识。这是工程/开发干预，不是RSI或独立测试胜出。检查集此前已用于开发，本轮只有一个种子；即使通过，也要补注册的逐轮、等数据、多种子对照和新确认测试。病例、特征、数值统计、权重和预测均只保留本地。
'''
        (HERE/f'RESULTS.{lang}.md').write_text(intro+table+description+tail)
    print(json.dumps(summary),flush=True)

if __name__=='__main__':main()
