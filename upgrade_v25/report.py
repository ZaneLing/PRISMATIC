"""Bilingual external-cohort report, never treating partial scores as final."""
import json
from pathlib import Path
import numpy as np
from data_contract import sha
HERE=Path(__file__).resolve().parent
LABELS={
 'initial_state':('初始 8k 状态','Initial 8k state'),
 'prevalence_global':('训练频率＋全局订单','Training prevalence + global orders'),
 'reuse_prior_orders':('复用近期订单','Reuse prior orders'),
 'retrieval_conditional':('30 邻居病例检索＋条件工具','30-neighbor retrieval + conditional tool'),
 'word_global':('词特征策略＋全局订单','Word policy + global orders'),
 'word_conditional':('词特征策略＋条件工具','Word policy + conditional tool'),
 'word_char_ensemble':('词/字符集成＋条件工具','Word/character ensemble + conditional tool'),
 'full_data_uniform':('全量普通监督策略','Full-data uniform policy'),
 'uniform':('普通逐轮更新','Uniform round updates'),
 'error_prioritized':('自身错误优先更新','Own-error-prioritized updates'),
 'permuted_priority':('同分布打乱权重','Same-distribution shuffled priorities'),
 'error_priority_initial_tool':('错误优先＋冻结初始工具','Error priorities + initial tool frozen'),
 'initial_policy_final_tool':('初始策略＋最终工具','Initial policy + final tool')}
ARMS={'uniform':'Uniform','error_prioritized':'Own-error priorities','permuted_priority':'Shuffled priorities'}

def read(p):return json.loads(p.read_text())

def plot(d):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(10.5,4))
    for j,key in enumerate(['drug_f1','order_f1']):
        for arm,label in ARMS.items():
            values=np.array([[r[key] for r in s[arm]] for s in d['accepted_curves'].values()])
            avg=values.mean(0);sd=values.std(0,ddof=1)
            line=axes[j].plot(range(5),avg,marker='o',label=label)[0]
            axes[j].fill_between(range(5),avg-sd,avg+sd,color=line.get_color(),alpha=.13)
        axes[j].axhline(d['methods']['word_char_ensemble'][key+'_mean'],ls='--',color='black',lw=1,label='Static word/character')
        axes[j].set(xlabel='Round (8k to 40k cumulative stays)',ylabel=['Native-code micro-F1','Complete joint-order micro-F1'][j],xticks=range(5));axes[j].grid(alpha=.2)
    axes[1].legend(fontsize=7);fig.tight_layout();fig.savefig(HERE/'round_curves.png',dpi=180);plt.close(fig)

def main():
    cohort=read(HERE/'results/cohort_manifest.json');p=HERE/'results/summary.json';d=read(p) if p.exists() else None
    complete=d is not None and d['status']=='complete'
    if complete:plot(d)
    cohort_table='| Split | Stays | Patients | Hospitals | Zero-target stays | Complete / all joint targets |\n|---|---:|---:|---:|---:|---:|\n'
    for name,s in cohort['splits'].items():cohort_table+=f"| {name} | {s['stays']:,} | {s['patients']:,} | {s['hospitals']} | {s['zero_target_stays']:,} | {s['complete_joint_targets']:,} / {s['all_joint_targets']:,} |\n"
    for lang,col in [('zh',0),('en',1)]:
        intro='''# v0.25：eICU 原生药物编码、医院留出与反馈机制比较

## 研究问题与数据

在独立的 eICU 数据上检验方法和反馈机制。固定 v0.24 的医院划分及跨分区患者排除规则；全部分区之间没有患者或医院重叠。这是在 eICU 内训练、在未见医院测试，不能称为 MIMIC 模型零样本迁移。

决策点为 ICU 入科后 6 小时，预测接下来 6 小时的新记录订单。目标以原生 HICL 编码表示，不冒充 RxNorm、ATC 或成分等价。若某住院任意目标订单缺少有效 HICL，则整次住院排除；无目标订单住院保留。142,485 次父队列住院中排除 8,003 次编码不完整住院，剩余 134,482 次，再按事先固定的哈希取样。该选择依赖回顾性标签完整性和文档记录，不代表全部临床人群。

''' if lang=='zh' else '''# v0.25 — Native-code eICU methods, held-out hospitals and feedback controls

## Question and cohort

Evaluate prescription methods and feedback mechanisms on the external eICU dataset. Keep the v0.24 hospital partitions and cross-partition patient exclusions: no hospital or patient crosses partitions. Models train within eICU and test on unseen hospitals; this is not zero-shot transfer of a MIMIC model.

The decision is ICU admission plus six hours, predicting newly documented orders in the next six hours. Labels are native HICL codes, without claiming RxNorm, ATC or ingredient equivalence. Exclude an entire stay if any target lacks a valid HICL code; retain zero-target stays. From 142,485 parent-cohort stays, 8,003 fail target-identity completeness, leaving 134,482 before fixed hash sampling. This retrospective label/documentation selection does not represent all clinical stays.

'''
        if lang=='en':
            methods='''
## Inputs, order protocol and methods

Inputs contain age decade/gender, the latest 24 early medication records and 32 distinct finite lab-name/unit measurements. Lab draw and revision timestamps must precede the decision. Hospital/patient IDs, future orders, cancellation/discharge status and untimed diagnoses are excluded. Medication storage times and full field histories are absent, so actual prospective availability is not proven.

The complete order tuple is HICL, route, dosage string and frequency string. Normalize case/whitespace only, without inferring dose units. Missing values remain null. Drug recall includes out-of-vocabulary GT; joint-order metrics score complete observed labels with coverage reported separately.

Three seeds run five rounds of 8k/16k/24k/32k/40k stays. Vocabulary (512 codes) and word/character/numerical maps freeze on the initial 8k. The three feedback arms have identical cases, order and exactly 60 epochs per classifier. Compare uniform learning, priorities from the prior accepted policy's own errors, and the exact same weights shuffled among the new cases. Tools fit only currently seen orders. Proposal selects thresholds; a separate guard promotes states. Rejected versions retain the previous policy/tool bundle. Every seed and static selection freezes before test-feature inference.

Changing artifacts are policy parameters, persistent feedback weights and order-tool parameters. No LLM/API is used; this is supervised artifact evolution. Static controls include prevalence, prior-order reuse, 30-neighbor retrieval, word models, word/character ensembles and full-data uniform learning. Extra ensemble fit/search budgets are disclosed; matched-arm contrasts isolate priority assignment. Component ablations do not retune other components.
'''
        else:
            # Keep the Chinese protocol in the same source without translating results mechanically.
            methods='''
## 输入、订单协议与方法

输入仅含年龄段/性别、最近 24 条早期药物记录和最近 32 个不同检测项目/单位的有限值；检验采样及修订时间都不晚于决策点。排除医院/患者 ID、未来订单、取消/出院状态和无时间戳诊断。药物缺少存储时钟与完整字段版本，因此不能证明临床现场可用性。

订单元组为 HICL、route、dosage 字符串、frequency 字符串。只规范小写/空白，缺失保持 null，不臆造剂量单位。药物召回包括词表外 GT；完整订单指标只评分观察完整的标签并报告覆盖率。

三个种子、五轮 8k/16k/24k/32k/40k 病例。初始 8k 冻结 512 编码及词/字符/数值特征。普通更新、自身错误优先、同分布打乱权重三臂具有相同病例/次序及每分类器 60 个 epoch。工具仅学当轮已见订单；proposal 选阈值、独立 guard 决定接纳，拒绝后保留旧策略/工具。全部种子及静态选择冻结后才进行测试推理。

真实更新对象是策略参数、持久病例权重及订单工具；无 LLM/API。静态对照包括频率、近期订单复用、30 邻居病例检索、词模型、词/字符集成、全量普通监督。集成额外拟合/搜索预算单列，严格因果比较是匹配预算的三臂。冻结工具/策略消融不重新调参。
'''
        text=intro+cohort_table+methods
        development_path=HERE/'results/development_curves.json'
        if development_path.exists():
            development=read(development_path)
            assert development['status']=='passed' and development['script_sha256']==sha(HERE/'recount_development.py')
            assert all(sha(HERE/name)==value for name,value in development['source_sha256'].items())
            text+=('\n## 已完成的开发集逐轮复算\n\n45 个参数／工具状态已重新执行，独立核对全部 proposal 阈值、guard 指标与接纳决定。原始曲线和接纳曲线分别展示；这些病例参与开发选择，不能当成留出测试成绩。\n\n' if lang=='zh' else '\n## Completed development trajectory replay\n\nAll 45 policy/tool states are reexecuted, with independent checks of proposal thresholds, guard metrics and acceptance decisions. Raw and accepted curves are separate; these cases participate in development selection and are not a held-out test result.\n\n')
            text+=f'[Development curves and every feedback control](DEVELOPMENT_CURVES.{lang}.md)\n'
        if not complete:
            frozen=HERE/'results/frozen_before_test.json'
            if frozen.exists():
                lock=read(frozen)
                assert all(sha(HERE/f'results/selection_seed_{s}.json')==value for s,value in lock['selections_sha256'].items())
                text+=('\n## 当前交付\n\n三个种子和全部静态对照的选择已冻结，原队列正在执行 8,005 次住院的留出医院统一测试和独立核验。最终测试表等待全部结果及核验完成；上方开发曲线不替代测试结果。\n' if lang=='zh' else '\n## Execution status\n\nAll three seeds and static-control choices are frozen. The original queue is executing the unified 8,005-stay held-out hospital test and independent audit. The final method table waits for completion of all results and checks; the development curves above do not replace it.\n')
            else:
                text+=('\n## 当前交付\n\n队列构建和独立时序/成员/编码核验已通过，三个种子训练已启动。测试集尚未评分；不将部分开发分数当主表。完成后自动执行冻结检查、统一测试、独立计数和双语报告。\n' if lang=='zh' else '\n## Execution status\n\nCohort construction and independent timing/membership/code audits passed. Three seed runs have started. The test has not been scored; partial development scores are not a method table. Completion runs freeze checks, sealed evaluation, independent recounting and bilingual reporting.\n')
        else:
            table='\n## Completed method comparison / 完整方法主表\n\n| Method | Drug F1 mean ± SD | Joint-order F1 mean ± SD | Empty (%) | Complete predicted tuples (%) |\n|---|---:|---:|---:|---:|\n'
            for name,labels in LABELS.items():
                m=d['methods'][name];table+=f"| {labels[col]} | {m['drug_f1_mean']:.5f} ± {m['drug_f1_sd']:.5f} | {m['order_f1_mean']:.5f} ± {m['order_f1_sd']:.5f} | {100*m['empty_fraction']:.2f} | {100*m['predicted_order_completion']:.2f} |\n"
            growth='\n## Round trajectories / 逐轮轨迹\n\n| Round | Stays | Uniform drug/order | Own-error drug/order | Shuffled drug/order |\n|---|---:|---:|---:|---:|\n'
            for r in range(5):growth+=f'| {r} | {8000*(r+1):,} | '+' | '.join('/'.join(f"{np.mean([v[a][r][k] for v in d['accepted_curves'].values()]):.5f}" for k in ['drug_f1','order_f1']) for a in ARMS)+' |\n'
            pairs='\n## Paired contrasts / 配对差异\n\n| Seed | Contrast | Drug/order Δ | Hospital 95% CI drug; order | Patient 95% CI drug; order |\n|---|---|---:|---|---|\n'
            for seed,contrasts in d['paired'].items():
                for name,v in contrasts.items():
                    def interval(key):return '; '.join(f'[{v[key][0][j]:+.5f}, {v[key][1][j]:+.5f}]' for j in [0,1])
                    pairs+=f"| {seed} | {name} | {v['drug_order_difference'][0]:+.5f}/{v['drug_order_difference'][1]:+.5f} | {interval('hospital_ci95')} | {interval('patient_ci95')} |\n"
            strata='\n## Zero-target stratum / 无新订单亚组\n\n| Method | False nonempty (%) | Mean predicted codes | Nonempty-stratum drug/order F1 |\n|---|---:|---:|---:|\n'
            for name,labels in LABELS.items():
                rows=[s[name] for s in d['strata'].values()];f=np.mean([r['zero_target_false_nonempty_rate'] for r in rows]);n=np.mean([r['zero_target_mean_predicted_codes'] for r in rows]);z=np.mean([r['nonempty_drug_order_f1'] for r in rows],axis=0)
                strata+=f'| {labels[col]} | {100*f:.2f} | {n:.3f} | {z[0]:.5f}/{z[1]:.5f} |\n'
            text+=table+growth+'\n![Accepted-state means and seed SD](round_curves.png)\n'+pairs+strata
            text+=('\n所有最终及逐轮预测、参数哈希、反馈权重、60 epoch 曝光和工具成员已独立重算。曲线阴影为种子标准差，配对区间为 2,000 次医院/患者聚类重采样，未校正多重比较。测试未参与选择。不能仅凭超过初始模型宣称独特 RSI 优势。\n' if lang=='zh' else '\nAll final/checkpoint predictions, actual parameter hashes, feedback weights, 60-epoch exposures and seen-only tool members are independently checked. Curve shading is seed SD. Intervals use 2,000 paired hospital/patient-cluster draws without multiplicity correction. Test scores did not select models. Growth over the initial state alone does not demonstrate a unique RSI advantage.\n')
        text+=('\n## 可复现材料与边界\n\n`protocol.json`、`results/cohort_manifest.json`、`results/cohort_audit.json` 和逐轮日志记录协议、样本数和状态变化。病例、预测、权重均保留受限本地目录。GT 一致性不等于临床安全；本原生编码/字段协议不能与论文 ATC 分数直接排名。\n' if lang=='zh' else '\n## Reproducibility and scope\n\n`protocol.json`, `results/cohort_manifest.json`, `results/cohort_audit.json` and round journals record the protocol, membership counts and transitions. Restricted cases, predictions and weights remain local. Agreement with recorded GT does not establish clinical safety. This native-code/field protocol cannot be ranked directly against published ATC scores.\n')
        (HERE/f'RESULTS.{lang}.md').write_text(text)

if __name__=='__main__':main()
