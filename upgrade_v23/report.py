"""Publish the complete causal-control table and fixed-test trajectories."""
import json,re
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parent
LABELS={'initial_state':('初始8k状态','Initial8k state'),'full_data_uniform':('全量普通监督版本','Full-data uniform state'),
    'uniform':('普通逐轮更新','Uniform round updates'),'error_prioritized':('自身错误优先更新','Own-error-prioritized updates'),
    'permuted_priority':('同分布随机权重对照','Same-distribution shuffled priorities'),
    'error_priority_freeze_initial_tool':('错误优先＋冻结初始订单工具','Error priorities, initial tool frozen'),
    'legacy_word_char_reference':('v0.21词/字符参考（优化预算不同）','v0.21 word/character reference (different optimization budget)')}

def main():
    d=json.loads((HERE/'results/summary.json').read_text());assert d['status']=='complete'
    fig,axes=plt.subplots(1,2,figsize=(10,3.7));styles={'uniform':'Uniform','error_prioritized':'Own-error priorities','permuted_priority':'Shuffled priorities'}
    for j,key in enumerate(['drug_f1','order_f1']):
        for arm,label in styles.items():
            values=np.array([[row[key] for row in v[arm]] for v in d['accepted_curves'].values()]);mean=values.mean(0);sd=values.std(0,ddof=1)
            line=axes[j].plot(range(5),mean,marker='o',label=label)[0];axes[j].fill_between(range(5),mean-sd,mean+sd,color=line.get_color(),alpha=.12)
        axes[j].axhline(d['methods']['full_data_uniform'][key+'_mean'],linestyle='--',color='gray',label='Final full-data uniform')
        axes[j].set(xlabel='Round (8k to 40k cumulative cases)',ylabel=['Drug micro-F1','Core-order micro-F1'][j],xticks=range(5));axes[j].grid(alpha=.2)
    axes[1].legend(fontsize=7);fig.tight_layout();fig.savefig(HERE/'round_curves.png',dpi=180);plt.close(fig)
    for lang,col in [('zh',0),('en',1)]:
        table='| Method / 方法 | Drug F1 mean ± SD | Core-order F1 mean ± SD | Empty (%) |\n|---|---:|---:|---:|\n'
        for name,label in LABELS.items():
            m=d['methods'][name];table+=f"| {label[col]} | {m['drug_f1_mean']:.5f} ± {m['drug_f1_sd']:.5f} | {m['order_f1_mean']:.5f} ± {m['order_f1_sd']:.5f} | {100*m['empty_fraction']:.2f} |\n"
        changes='| Seed | Contrast | Drug Δ | Order Δ | Drug95% interval | Order95% interval |\n|---|---|---:|---:|---:|---:|\n'
        for seed,pairs in d['paired'].items():
            for control in ['uniform','permuted_priority','full_data_uniform']:
                m=pairs['error_prioritized__minus__'+control];delta=m['drug_order_difference'];ci=m['patient_ci95']
                changes+=f"| {seed} | Error priority − {control} | {delta[0]:+.5f} | {delta[1]:+.5f} | [{ci[0][0]:+.5f},{ci[1][0]:+.5f}] | [{ci[0][1]:+.5f},{ci[1][1]:+.5f}] |\n"
        growth='| Round | Cumulative cases | Uniform drug/order F1 | Own-error drug/order F1 | Shuffled drug/order F1 |\n|---|---:|---:|---:|---:|\n'
        for i in range(5):
            growth+=f'| {i} | {8000*(i+1):,} | '
            growth+=' | '.join('/'.join(f"{np.mean([s[arm][i][key] for s in d['accepted_curves'].values()]):.5f}" for key in ['drug_f1','order_f1']) for arm in styles)+' |\n'
        text='''# v0.23：按自身错误更新，是否真的优于普通学习？

## 问题与公平对照

接续v0.22表示改进，冻结词＋数值特征和128药名词表。三个种子各跑五轮8k/16k/24k/32k/40k病例，比较普通更新、按当前已接纳策略的错误给新病例加权、将同批权重随机打乱。错误权重为1+3×可达药物F1错误；进入累计训练时归一化为均值1。后两臂的权重分布相同，只有分配到病例的方式不同。

三臂每轮都训练128个药物分类器，每个恰好60轮，没有提前停止；训练病例、曝光次序和更新次数在种子内相同。初始8k模型共享。订单工具只在当轮已见病例上拟合，种子/轮次内共享；被拒绝的版本保留旧策略与工具。七个阈值只用候选验证选择，再通过独立检查集决定接纳。三个种子、全部臂都冻结后才统一测试。

本轮确实更新选择参数、持久病例反馈权重及订单工具参数；不更新LLM或可执行代码。它检验监督式反馈更新，不把新增病例或更好的表示单独称为RSI。轮次是事后病例块，并非真实时间部署，训练患者可能跨轮次出现。

## 完整方法结果

同一1,082次测试住院、1,024位患者。**v0.21测试此前已经观察，本轮是明确标注的探索性复用，仍需要新的确认数据。** v0.21词/字符行使用不同的早停/调参预算，只作上下文参考；严格相同步数的因果比较是当前三臂。

''' if lang=='zh' else '''# v0.23 — Does own-error feedback outperform ordinary learning?

## Question and matched controls

Following v0.22, freeze word+numeric features and 128 drug names. Three seeds run 8k/16k/24k/32k/40k cumulative cases, comparing uniform updates, priorities from the currently accepted policy's errors, and the same block's weights randomly permuted. Error weights are 1+3×reachable-drug-F1 error, normalized to mean 1 during fitting. The two priority arms have the same weight distributions; only case assignments differ.

Every arm trains 128 classifiers for exactly 60 epochs per round, without early stopping. Within each seed, cases, exposure order and update counts match. The initial 8k model is shared. Order tools use only currently observed cases and are shared within seed/round; rejected versions retain the previous policy/tool bundle. Seven thresholds compete on proposal, followed by a separate guard. All seeds/arms freeze before new test inference.

Changing objects are selection parameters, persistent case-feedback weights and conditional-tool parameters. LLM weights and executable code stay fixed. This tests supervised feedback updates, not autonomous LLM evolution. Rounds are retrospective case blocks rather than calendar deployment; training patients may occur in several rounds.

## Completed method comparison

Same 1,082 test admissions and 1,024 patients. **The v0.21 test was previously observed; this is exploratory reuse and still requires untouched confirmation.** The older word/character row has a different early-stopping/search budget and is contextual only. The three present feedback arms have strictly matched epochs and case exposures.

'''
        tail='''
## 独立核验与解释边界

已从旧接纳检查点重新推理每批反馈，独立按药物集合重算错误权重；核对打乱后的分布、全部分类器60轮预算、工具训练成员、状态冻结和所有测试预测。逐病例改善/退化、接纳/拒绝及参数/工具/权重哈希见 `results/summary.json` 与逐轮日志。冻结初始工具消融没有重新调参，测量的是最终状态中的条件依赖。

曲线阴影是三个种子的标准差；患者聚类配对区间为2000次重采样的描述性区间，没有多重比较校正。错误优先必须同时比较普通更新和随机权重对照，不能只凭超过初始模型宣称独特收益。所有病例、权重和预测保留本地。
''' if lang=='zh' else '''
## Independent verification and interpretation

Re-infer every feedback block with the prior accepted checkpoint, independently recount set errors, verify shuffled distributions, every classifier's 60 epochs, seen-only tool members, frozen selections and every test prediction. Per-case repairs/regressions, promotions/rejections and parameter/tool/weight hashes are retained in `results/summary.json` and journals. Freezing the initial tool does not retune other components and measures conditional dependence within the final state.

Shading shows SD across three seeds. Paired patient-cluster intervals use 2,000 descriptive bootstrap draws without multiplicity correction. Error prioritization must be compared with both uniform and shuffled-weight controls; improvement over the initial model alone is insufficient. Restricted cases, weights and predictions remain local.
'''
        conclusion=('\n## 结论\n\n普通更新为0.20446/0.12403，自身错误加权为0.20143/0.12219，打乱权重为0.20204/0.12197。错误加权没有优于普通更新；三个种子的药物与订单差异区间均含零，因此也不宣称已经证明其劣势。与随机分配的比较没有一致优势。普通更新的数值高于旧词/字符参考，但二者优化预算不同，不能单独归因于数值表示。\n\n错误加权的逐轮均值从0.16840/0.10130升至0.20143/0.12219，但个别种子/指标仍有下降。冻结初始工具后订单F1为0.11909；工具更新的平均差异为+0.00311，只有一个种子的配对区间不含零。这些证据支持实际参数/工具变化，尚不支持独特RSI收益或稳定的工具因果优势。全量普通监督行与普通逐轮最终状态相同，因为各种子均接纳了最后检查点。\n' if lang=='zh' else '\n## Findings\n\nUniform updates score0.20446/0.12403, own-error priorities0.20143/0.12219 and shuffled priorities0.20204/0.12197. Priorities do not outperform uniform updates. Drug and order intervals include zero in all three seeds, so established inferiority is not claimed either. The shuffled-assignment contrast shows no consistent advantage. The uniform point estimate exceeds the older word/character reference, but different optimization budgets prevent attributing that difference solely to numerical representation.\n\nOwn-error round means rise from0.16840/0.10130 to0.20143/0.12219, with regressions in individual seed/endpoint trajectories. Freezing the initial tool yields order F1 0.11909: the updated-tool mean difference is+0.00311, with an interval excluding zero in only one seed. These are actual parameter/tool changes without an established unique RSI benefit or stable tool effect. Full-data uniform and the final accepted uniform state coincide because every seed accepts its last checkpoint.\n')
        text=text+table+conclusion+'\n## Fixed-test trajectories / 固定测试轨迹\n\n'+growth+'\n![Accepted-state curves](round_curves.png)\n\n## Paired causal controls / 配对机制对照\n\n'+changes+tail
        if lang=='en':text=re.sub(r'(?<=[A-Za-z])(?=[0-9])',' ',text).replace('v 0.','v0.').replace('F 1','F1')
        (HERE/f'RESULTS.{lang}.md').write_text(text)

if __name__=='__main__':main()
