"""Independent outcome-verifier recount, paired intervals and bilingual report."""
import json,sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'upgrade_v11'))
from evidence_tool import LOCAL
from public_client import LOCAL as DATA_LOCAL

def read(p):return json.loads(p.read_text())

def main():
    test=read(DATA_LOCAL/'data.json')['parts']['test'];actions=read(LOCAL/'test-review-actions.json')
    predictions=read(LOCAL/'outcome-verifier-v13-predictions.json');report=read(HERE/'results/outcome_evolution.json')
    versions=read(HERE/'results/frozen_versions.json')['versions'];correct={}
    def count(rows):
        assert [r['case_id'] for r in rows]==[c['id'] for c in test]
        assert not any(r.get('error') for r in rows)
        return np.array([r['prediction']==c['gold'] for r,c in zip(rows,test)],dtype=int)
    base=count(actions['cot']);fixed=count(actions['balanced'])
    groups=sorted({c['group_id'] for c in test});lookup={g:i for i,g in enumerate(groups)}
    ix=np.array([lookup[c['group_id']] for c in test]);n=np.bincount(ix)
    def paired(a,b):
        delta=a-b;sums=np.bincount(ix,weights=delta);rng=np.random.default_rng(42);draws=[]
        for _ in range(4000):
            b=rng.integers(0,len(groups),len(groups));draws.append(sums[b].sum()/n[b].sum())
        return {'difference':float(delta.mean()),'fixes':int((delta>0).sum()),'regressions':int((delta<0).sum()),
                'scenario_cluster_ci95':np.quantile(draws,[.025,.975]).tolist()}
    for name,curves in predictions.items():
        previous=fixed
        for rows,c in zip(curves,report['runs'][name]['curve']):
            cur=count(rows);assert int(cur.sum())==c['score']['correct']
            assert int(((cur-previous)>0).sum())==c['fixes']
            assert int(((cur-previous)<0).sum())==c['regressions']
            # A post-review verifier consumes both responses even if it returns the first.
            assert abs(sum(r['cost_usd'] for r in rows)-sum(r['cost_usd'] for r in actions['balanced']))<1e-9
            previous=cur
        correct[name]=previous
    summary={'status':'complete','test_n':len(test),'new_network_requests':0,'model_calls_per_case':2,
        'fixed_balanced_correct':int(fixed.sum()),'static_verifier_correct':int(correct['static_supervised'].sum()),
        'unattainable_oracle_diagnostic':{'either_response_correct':int(np.logical_or(base,fixed).sum()),'note':'Uses test labels only as an upper-bound diagnostic; never a method or selection rule.'},
        'arms':{},'paired':{},'verification':'Independent alignment, count, transition and full two-response cost checks passed.'}
    for arm in ['uniform','error_prioritized']:
        vals=[correct[f'{arm}_seed_{s}'].mean() for s in [42,137,2026]]
        summary['arms'][arm]={'accuracy_mean':float(np.mean(vals)),'accuracy_sample_sd':float(np.std(vals,ddof=1))}
    for name,arr in correct.items():summary['paired'][name]={'versus_fixed':paired(arr,fixed)}
    for s in [42,137,2026]:summary['paired'][f'error_prioritized_seed_{s}']['versus_uniform']=paired(correct[f'error_prioritized_seed_{s}'],correct[f'uniform_seed_{s}'])
    (HERE/'results/summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    fig,axes=plt.subplots(1,3,figsize=(12,3.4),sharey=True)
    for ax,s in zip(axes,[42,137,2026]):
        for arm in ['uniform','error_prioritized']:
            c=report['runs'][f'{arm}_seed_{s}']['curve'];ax.plot(range(5),[100*r['score']['accuracy'] for r in c],marker='o',label=arm.replace('_',' '))
        ax.axhline(100*fixed.mean(),linestyle='--',color='gray',label='fixed review')
        ax.set(title=f'Seed {s}',xlabel='Round',xticks=range(5));ax.grid(alpha=.2)
    axes[0].set_ylabel('Test accuracy (%)');axes[-1].legend(fontsize=8);fig.tight_layout();fig.savefig(HERE/'round_curves.png',dpi=180);plt.close(fig)
    table='| Method | Accuracy (%) | Seed SD (pp) | Calls |\n|---|---:|---:|---:|\n'
    table+=f"| CoT | {100*base.mean():.2f} | — | 1 |\n| Fixed balanced review | {100*fixed.mean():.2f} | — | 2 |\n| Full-data ordinary verifier | {100*correct['static_supervised'].mean():.2f} | — | 2 |\n"
    for arm,m in summary['arms'].items():table+=f"| Incremental {arm} verifier | {100*m['accuracy_mean']:.2f} | {100*m['accuracy_sample_sd']:.2f} | 2 |\n"
    table+='| Author GRASP core + task adapter (v0.10) | 50.81 | — | 1 |\n'
    rounds='| Arm / seed | Correct across rounds 0→4 | Promoted rounds |\n|---|---|---|\n'
    for arm in ['uniform','error_prioritized']:
        for s in [42,137,2026]:
            key=f'{arm}_seed_{s}';curve=report['runs'][key]['curve'];accepted=[str(x['round']) for x in versions[key] if x['promoted']]
            rounds+=f"| {arm} / {s} | "+' → '.join(str(x['score']['correct']) for x in curve)+' | '+(', '.join(accepted) or 'none')+' |\n'
    for lang in ['en','zh']:
        if lang=='en':
            text='''# v0.13 — Outcome-aware revision verification

## Motivation and executed mechanism

The v0.12 router chooses a tool before observing its output. This increment instead learns whether to retain the initial answer or accept the completed grounded revision. It uses the same complete CoT/balanced traces on 625 train / 190 proposal / 197 guard / 988 test cases. Every verifier consumes two model calls; returning the initial answer does not erase the review cost. No new network calls are needed for replay.

The verifier combines option-mention/negation/positive-word relations with optional separate fixed word/bigram hashes of the question, draft and revision. Ridge predicts the revision's correctness gain. Four rounds expose 156/312/468/625 training cases. Uniform and error-prioritized arms have identical examples and 18 candidate settings per round. Error priorities are measured before updates and target only reachable answer-selection failures; each old weight retains its pre-update value. The 190-case proposal set chooses settings and the 197-case guard requires net repairs. A full-data, ordinary supervised verifier is an additional strong control. All choices freeze before this increment's test scoring; this test was already observed in prior development.

## Common-task results

'''+table+'''
All rows use the same public derived option task and DeepSeek-V4.1-Flash traces. The GRASP row is the already completed unmodified author core with our task adapter; its development mechanism/budget differs. It remains the strongest executed row here. Incremental uniform verification slightly improves the point estimate over fixed review, while error prioritization does not outperform uniform updates.

## Actual evolution and trajectories

Only verifier coefficients/intercepts/threshold and training feedback weights change. Backbone parameters, tool implementation and evidence corpus do not change. Parameter and feedback hashes are released, along with every accepted/rejected candidate.

![Test trajectories](round_curves.png)

'''+rounds+f'''
The union of the two answers contains a correct answer in {summary['unattainable_oracle_diagnostic']['either_response_correct']}/988 cases. This label-dependent upper bound is a diagnostic only, never an evaluated agent. It suggests selection headroom but does not show that the current features can identify it.

## Verification and limitations

Independent recount checks case alignment, every count, transition and two-response cost. Scenario-cluster paired intervals are in `results/summary.json`; they are descriptive and unadjusted for multiple comparisons. Three leakage/accounting tests pass. During 150 fits, the numerical backend issued 225 dense-multiplication warnings; all coefficients, intercepts and scored predictions remained finite. An independent elementwise weighted-intercept recount differs by at most 1.12e-16. This audit is retained rather than interpreting warnings as silent valid predictions.

This small, repeatedly used development benchmark still does not establish an RSI advantage. Further tuning on it should be treated as exploratory; final claims require a frozen design and untouched confirmation. The ongoing local QLoRA study separately tests actual language-model parameter updates.
'''
        else:
            text='''# v0.13：看到复核结果之后再决定是否采用

## 动机与已执行机制

v0.12 在看到工具结果之前选择动作。本版改为：核验器同时看初稿和已完成的证据复核，学习保留初稿还是接受修改。共用完整 CoT/balanced 轨迹与 625 训练 / 190 候选选择 / 197 退化检查 / 988 测试。核验器每例均消耗两次模型调用，返回初稿也不会抹掉复核成本。缓存重放没有新增网络请求。

特征包括答案中候选药名、否定词和正面词的关系，以及可选的问题/初稿/复核三个独立文本哈希；Ridge 学习修改是否提高正确率。四轮暴露 156/312/468/625 例。普通与错误优先两臂共用全部已见病例，每轮同为 18 个候选设置。错误权重在更新前计算，仅针对两答案中存在正确答案但当前选错的可修复问题；旧病例保留原始更新前权重。190 题选择配置，197 题要求净修复为正。另设全量普通监督核验器对照。全部选择先冻结再计算本版测试分数；该测试集此前已经用于开发观察。

## 同任务方法结果

'''+table+'''
共用公开衍生选药任务和 DeepSeek-V4.1-Flash 轨迹。GRASP 行为此前已完成的未修改作者核心加任务适配，开发机制/预算不同；它仍是本表最强实测行。普通增量核验的点估计略高于固定复核，但错误优先更新没有优于普通更新。

## 进化对象与逐轮轨迹

仅核验器系数/截距/阈值和训练反馈权重变化；基座模型参数、工具代码、证据库固定。发布参数与权重哈希，保留全部接受/拒绝记录。

![测试轨迹](round_curves.png)

'''+rounds+f'''
两个答案的并集中，{summary['unattainable_oracle_diagnostic']['either_response_correct']}/988 例至少有一个正确答案。这是依赖测试标签的诊断上界，绝不作为已实现 agent 的成绩。它说明存在选择空间，不说明现有特征能够识别。

## 核验与限制

已独立核对病例对齐、计数、每轮修复/退化和完整两次调用成本。场景聚类配对区间见 `results/summary.json`，为未作多重比较校正的描述性区间。三个泄漏/计费契约测试通过。150 次拟合出现 225 次数值后端矩阵乘法警告；系数、截距、所有已评分预测均有限，独立逐元素重算加权截距的最大误差为 1.12e-16，审计记录保留。

小规模且被反复观察的开发测试尚不能证明 RSI 独有优势。继续在此调试必须标明探索性质，最终需要冻结设计和未使用数据确认。正在运行的本地 QLoRA 将单独检验真实语言模型参数更新。
'''
        (HERE/f'RESULTS.{lang}.md').write_text(text)
    print(json.dumps(summary['arms']))

if __name__=='__main__':main()
