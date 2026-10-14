"""Independent aggregate verification, process curves, and bilingual release report."""
import json,sys
from pathlib import Path
import joblib,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from prepare_data import PRIVATE
HERE=Path(__file__).resolve().parent

def counts(pred,gold):
    fields=['drug_name','route','dose_value','dose_unit']
    p={x['drug_name'] for x in pred};g={x['drug_name'] for x in gold}
    a={tuple(x.get(f) for f in fields) for x in pred if all(x.get(f) is not None for f in fields)}
    b={tuple(x.get(f) for f in fields) for x in gold if all(x.get(f) is not None for f in fields)}
    return [len(p&g),len(p),len(g),len(a&b),len(a),len(b)]
def calc(c):return np.array([2*c[0]/max(1,c[1]+c[2]),2*c[3]/max(1,c[4]+c[5])])

def run():
    b=joblib.load(PRIVATE/'data.joblib');reports=[];audits=[]
    for seed in [42,137,2026]:
        r=json.loads((HERE/f'results/round_results_seed_{seed}.json').read_text());reports.append(r)
        saved=joblib.load(PRIVATE/f'run_seed_{seed}.joblib');matrices={}
        strong=json.loads((HERE/f'results/strong_results_seed_{seed}.json').read_text())
        strong_saved=joblib.load(PRIVATE/f'strong_seed_{seed}.joblib')
        r['method_scores'].update(strong['method_scores'])
        saved['predictions'].update(strong_saved['predictions'])
        del strong_saved
        for name,pred in saved['predictions'].items():
            c=np.array([counts(p,g) for p,g in zip(pred,b['truth']['test'])]);matrices[name]=c
            expected=r['rounds'][int(name.split('_')[1])]['metrics'] if name.startswith('round_') else r['method_scores'][name]
            assert np.allclose(calc(c.sum(0)),[expected['drug_micro_f1'],expected['core_order_micro_f1']],atol=1e-12,rtol=0)
        _,ix=np.unique(b['parts']['test'].subject_id.to_numpy(),return_inverse=True);n=ix.max()+1
        chosen=np.zeros((n,6));control=np.zeros((n,6));np.add.at(chosen,ix,matrices['rxrsi_selected']);np.add.at(control,ix,matrices['word_char_ensemble'])
        rng=np.random.default_rng(42);delta=[]
        for _ in range(2000):
            idx=rng.integers(0,n,n);delta.append(calc(chosen[idx].sum(0))-calc(control[idx].sum(0)))
        ci=np.quantile(delta,[.025,.975],axis=0)
        audits.append({'seed':seed,'independent_counts':'passed','comparison':'RxRSI minus same-data word/character ensemble and conditional-tool control',
          'drug_difference':float(calc(chosen.sum(0))[0]-calc(control.sum(0))[0]),'drug_ci95':ci[:,0].tolist(),
          'order_difference':float(calc(chosen.sum(0))[1]-calc(control.sum(0))[1]),'order_ci95':ci[:,1].tolist()})
    names=list(reports[0]['method_scores']);summary={}
    for name in names:
        values=np.array([[r['method_scores'][name][k] for k in ['drug_micro_f1','core_order_micro_f1']] for r in reports])
        summary[name]={'drug_f1_mean':float(values[:,0].mean()),'drug_f1_sd':float(values[:,0].std(ddof=1)),
                       'order_f1_mean':float(values[:,1].mean()),'order_f1_sd':float(values[:,1].std(ddof=1))}
    (HERE/'results/summary.json').write_text(json.dumps({'methods':summary,'seed_audits':audits,'n_test':4000,'n_test_patients':int(n)},indent=2)+'\n')
    fig,axes=plt.subplots(1,2,figsize=(10,3.7))
    for ax,key,title in zip(axes,['drug_micro_f1','core_order_micro_f1'],['Drug-set micro-F1','Joint-order micro-F1']):
        for r in reports:ax.plot([x['round'] for x in r['rounds']],[x['metrics'][key] for x in r['rounds']],marker='o',label=f"Seed {r['seed']}")
        ax.set(title=title,xlabel='Accepted-state checkpoint (0–4)',ylabel='Fixed-test F1',xticks=range(5));ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.suptitle('RxRSIAgent v0.7: fixed 4,000-case test; 8k → 40k training admissions')
    fig.tight_layout();fig.savefig(HERE/'round_curves.png',dpi=170);plt.close(fig)
    labels={'word_policy_global':('词模型＋全局订单模板','Word policy + global templates'),
      'word_policy_conditional_tool':('词模型＋条件化订单工具','Word policy + conditional order tool'),
      'retrieval_global':('病例检索＋全局模板','Case retrieval + global templates'),
      'retrieval_conditional_tool':('病例检索＋条件化工具','Case retrieval + conditional tool'),
      'rxrsi_selected':('RxRSI 逐轮接纳版本','RxRSI accepted version'),
      'without_parameters_evolution':('冻结初始处方策略参数','Freeze initial policy parameters'),
      'without_tool_evolution':('冻结初始订单工具','Freeze initial order tool'),
      'without_memory_evolution':('冻结初始病例记忆','Freeze initial episode memory'),
      'word':('调参词模型＋订单工具','Tuned word policy + order tool'),
      'char':('字符模型＋订单工具','Character policy + order tool'),
      'word_char_ensemble':('词/字符集成＋订单工具','Word/character ensemble + order tool'),
      'multinomial_nb':('朴素贝叶斯＋订单工具','Naive Bayes + order tool')}
    for lang,index in [('zh',0),('en',1)]:
        table='| '+('方法 | 药物 F1：均值±标准差 | 核心订单 F1：均值±标准差' if lang=='zh' else 'Method | Drug F1: mean ± SD | Core-order F1: mean ± SD')+' |\n|---|---:|---:|\n'
        for name,m in summary.items():table+=f"| {labels[name][index]} | {m['drug_f1_mean']:.5f} ± {m['drug_f1_sd']:.5f} | {m['order_f1_mean']:.5f} ± {m['order_f1_sd']:.5f} |\n"
        curves='| '+('轮次 | 训练病例 | Seed 42 药物 F1 | Seed 42 订单 F1 | 改善病例 / 退化病例' if lang=='zh' else 'Round | Training cases | Seed 42 drug F1 | Seed 42 order F1 | Improved / regressed cases')+' |\n|---|---:|---:|---:|---:|\n'
        for r in reports[0]['rounds']:curves+=f"| {r['round']} | {r['training_cases']} | {r['metrics']['drug_micro_f1']:.5f} | {r['metrics']['core_order_micro_f1']:.5f} | {r['case_improvements']} / {r['case_regressions']} |\n"
        if lang=='zh':
            text='''# RxRSIAgent v0.7：逐轮、逐对象的进化验证

目标：ACL 2027。已删除“盐水出现 F1”作为论文和后续实验指标。处方中的药物仍按统一药物/订单指标评价。

## 数据与可比性

本轮使用 40,000 训练入院、2,000 候选选择、2,000 独立退化检查、4,000 测试入院。验证/检查/测试均排除了 v0.6 相应集合中的所有患者；各集合患者不交叉。测试共 3,440 患者。所有方法输入、128 药名词表、最大 20 个输出及计分相同。词表和文本表示由最初 8k 训练例固定。

## 实际更新了什么

1. **处方策略参数**：累计病例重新拟合药物选择模型。
2. **病例记忆**：更新可检索训练病例与相应处方。
3. **订单工具**：更新联合订单模板，并训练按患者文本选择途径/剂量/单位/频次组合的条件模型。
4. **选择状态**：每轮比较单对象更新和组合更新；先选候选，再用独立退化检查集决定是否接纳。测试分数在全部选择冻结后计算。

每轮保存参数、记忆、工具及完整检查点的哈希，并记录接纳与拒绝原因。代码见 `run_rounds.py` 和 `order_tools.py`。**此轮是监督式策略/工具学习；LLM 参数和自然语言技能未在本轮更新。**

## 相同数据上的三种子对照

'''+table+'''
## 随轮次是否更好

![固定测试集上的逐轮曲线](round_curves.png)

'''+curves+'''
三个种子的已接纳版本在该固定测试集上均非递减；seed 137 最后一轮被拒绝，因此保持上一版本。每轮仍有个别病例退化，不能把总体曲线改善解释为所有患者都改善。

## 反思与下一轮

订单工具更新提供了可测贡献；病例记忆扩张没有稳定增益。完整 RSI 在三种子均值上没有胜过“同数据量策略＋条件工具”对照，因此这一版本不够成熟，不能声称 RSI 机制已优于普通训练。

v0.8 已继续执行：冻结基座，比较直接作答、CoT、Self-Refine、病例 RAG、Reflexion/GRASP/EvoTool 的明确任务适配及 RxRSI；真正更新自然语言技能和证据提取工具配置，保留每轮修改文本。受限患者数据仍只在本地运行。

## 核验

三种子全部预测均由独立集合计数重算；患者聚类配对 bootstrap 区间见 `results/summary.json`。上述留一对象消融使用最终状态，仅冻结指定对象，未另行重调其他对象；它测量该状态下的依赖，不等于重新训练最优消融模型。原始处方字段缺失按既定协议处理，入院代理输入的时间可用性限制仍然存在。
'''
        else:
            text='''# RxRSIAgent v0.7: round-wise, artifact-wise evolution audit

Target: ACL 2027. The saline-presence endpoint has been removed. All prescription items use the common drug/order metrics.

## Protocol

40k training / 2k proposal validation / 2k regression guard / 4k test admissions, with 3,440 test patients. New development and test subsets exclude every patient in the corresponding v0.6 subsets. All splits are patient-disjoint. The 128-name vocabulary and text representation are frozen from the initial 8k training examples. Methods share inputs, labels, scorer and the maximum 20-order output budget.

Updated objects are drug-selection parameters, episodic memory and a context-conditioned joint-order completion tool. Each round stores hashes, candidate configurations, independent guard scores and acceptance decisions. All decisions are frozen before test scoring. LLM weights and language skills do not change in this experiment.

## Three-seed method comparison

'''+table+'''
## Fixed-test trajectory

![Round-wise held-out curves](round_curves.png)

'''+curves+'''
Accepted-state curves are non-decreasing for all three seeds on this test; seed 137 rejects its final update. Individual cases can still regress. A monotonic aggregate curve is not a per-patient guarantee.

## Reflection and continued iteration

The conditional order tool contributes measurable gains. Expanding episode memory is not consistently useful. The full RSI mean does not exceed the equal-data policy-plus-conditional-tool control. This increment does not establish a unique RSI advantage.

v0.8 therefore proceeds with actual LLM-authored skill and evidence-tool-configuration changes, comparing direct, CoT, Self-Refine, case RAG, explicit Reflexion/GRASP/EvoTool task adaptations and RxRSI. Restricted patient text remains local.

All saved scores were independently recomputed. Patient-cluster paired bootstrap results are in `results/summary.json`. Leave-one-object-out results freeze the specified object within the final policy without retuning other objects; they are conditional dependence tests, not optimally retrained ablations. The admission-proxy input and source-field missingness limitations persist.
'''
        (HERE/f'RESULTS.{lang}.md').write_text(text)
    print(json.dumps({'summary':summary,'verification':'passed'},indent=2))

if __name__=='__main__':run()
