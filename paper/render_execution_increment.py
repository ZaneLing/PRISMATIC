# -*- coding: utf-8 -*-
"""Update a stable bilingual entry block from executed, audited artifacts."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent;PAPER=ROOT/'paper'
START='<!-- RXRSI_CURRENT_EXECUTION_START -->';END='<!-- RXRSI_CURRENT_EXECUTION_END -->'
def update(path,block):
    text=path.read_text();new=START+'\n'+block.strip()+'\n'+END
    if START in text:
        a=text.index(START);b=text.index(END,a)+len(END);text=text[:a]+new+text[b:]
    else:
        a=text.index('\n')+1;text=text[:a]+'\n'+new+'\n\n'+text[a:]
    path.write_text(text)
def main():
    rules=[json.loads(p.read_text()) for p in (ROOT/'upgrade_v27/results').glob('*-rsi-seed*.json')]
    neural=[json.loads(p.read_text()) for p in (ROOT/'upgrade_v27/results').glob('*-seed*.json') if 'epochs' in json.loads(p.read_text())]
    complete=sum(z['status']=='selection_frozen' for z in rules);nr=sum(z['status']=='selection_frozen' for z in neural);epochs=sum(len(z['epochs']) for z in neural)
    summary=json.loads((ROOT/'upgrade_v27/results/rsi_development_summary.json').read_text());repair=json.loads((ROOT/'upgrade_v28/results/summary.json').read_text())
    for lang in ['en','zh']:
        block=('## Current executed increment — rule memory and tool repair\n\n' if lang=='en' else '## 当前增量：真实规则进化与工具修复\n\n')
        block+=('**Manuscript navigation:** Study A contains the common ATC-L4 method comparison; Study B covers structured orders and external hospitals; Study C language skills; Study D parameter updates; Study E real FHIR execution. The agent-state section maps each task to its output and evolving objects, and states the actual selection roles. [Reading index](README.md).\n\n' if lang=='en' else '**论文阅读入口：** Study A 是同一 ATC-L4 数据上的跨方法比较；Study B 是完整订单与外部医院；Study C 是语言经验；Study D 是参数更新；Study E 是真实 FHIR 执行。方法章节逐项对应任务、输出、实际进化对象和各自的版本选择规则。[阅读索引](README.md)。\n\n')
        if (PAPER/'execution_status.json').exists() and json.loads((PAPER/'execution_status.json').read_text())['api']['status']=='waiting_for_credit':
            block+=('**Execution notice:** new OpenRouter requests returned HTTP402 after the previous recharge. Unfinished API branches retain checkpoints and await credit; completed results and independent local training/audits continue. Missing requests are never scored as model errors.\n\n' if lang=='en' else '**执行状态：** 上次充值后，新OpenRouter请求再次返回HTTP402。未完成的API分支已保存断点，等待补充额度；已完成结果及独立本地训练／审计继续。缺失请求不计作模型错误。\n\n')
        elif (PAPER/'execution_status.json').exists() and json.loads((PAPER/'execution_status.json').read_text())['api']['status']=='restored_actual_completion_verified':
            block+=('**Execution notice:** a real OpenRouter completion verified restored access after recharge. Interrupted studies resume from saved receipts under their original protocols and budgets; missing requests are not model errors.\n\n' if lang=='en' else '**执行状态：** 充值后已用真实OpenRouter响应验证访问恢复。中断实验从原回执继续，保持原协议和预算；缺失请求不计作模型错误。\n\n')
        block+=(f'**Actual training:** {complete}/6 rule runs finish five rounds; {nr}/15 author-model runs finish their full 50 epochs, with {epochs}/750 completed epochs overall. Training/audit queues continue. The final common ATC-L4 test table opens only after all registered choices and audits freeze.\n\n' if lang=='en' else f'**实际运行：** {complete}/6组规则实验完成五轮；作者神经方法{nr}/15组完成各自50轮，总计已完成{epochs}/750轮。训练与审计队列继续，正式ATC-L4测试主表等待全部已登记版本和核验完成后统一运行。\n\n')
        accounting=PAPER/'compute_accounting.json'
        if accounting.exists():
            ledger=json.loads(accounting.read_text())
            block+=('**Recorded method budgets:** the receipt ledger separates shared fits, optimizer steps, proposal searches and logical response prices. It checks completed author-epoch records against their original logs, counts shared policy fitting once, and identifies exact v29-to-v30 model reuse. ' if lang=='en' else '**实际方法预算：** 回执账本分别列出共享拟合、优化步数、proposal 搜索及逻辑响应价格；将已完成作者方法的逐轮记录与原日志对齐，共享拟合只计一次，并核对 v29 到 v30 的模型原样复用。')
            sd=ledger['author_method_summary'].get('molecular/SafeDrug')
            if sd:
                f=sd['guard_patient_f1'];formatted=f"{f['mean']:.5f}"+(f" ± {f['seed_sd']:.5f}" if f['seed_sd'] is not None else '')
                block+=(f"SafeDrug has {len(sd['seeds'])} audited seeds; molecular guard patient F1 is {formatted}. " if lang=='en' else f"SafeDrug 已核验 {len(sd['seeds'])} 个种子，分子药物空间 guard 患者平均 F1 为 {formatted}。")
            block+=f'[Actual compute and development results](COMPUTE_ACCOUNTING.{lang}.md)\n\n'
        development=ROOT/'upgrade_v27/results/development_methods.json'
        if development.exists():
            d=json.loads(development.read_text());count=sum(sum(r['runs'] for r in p['methods'].values()) for p in d['panels'].values())
            block+=(f"**Executed cross-method recount:** {count} completed method runs are recounted on the same 1,231 guard visits / 467 patients, with patient-paired intervals using matched seeds. All available conventional, author-core and rule-memory methods are included. This remains a development comparison; the final test is gated. " if lang=='en' else f"**已执行跨方法复算：** 同一 1,231 次 guard 就诊／467 人上，重算 {count} 组已完成方法运行，并按匹配种子给出患者配对区间。所有已完成的传统、作者核心及规则记忆方法均纳入。此表属于开发集对照；最终测试继续等待前置条件。")
            block+=f'[Cross-method table and every paired contrast](../upgrade_v27/DEVELOPMENT_METHODS.{lang}.md)\n\n'
        eicu_development=ROOT/'upgrade_v25/results/development_curves.json'
        if eicu_development.exists():
            ec=json.loads(eicu_development.read_text())
            assert ec['status']=='passed' and ec['script_sha256']==hashlib.sha256((ROOT/'upgrade_v25/recount_development.py').read_bytes()).hexdigest()
            assert all(hashlib.sha256((ROOT/'upgrade_v25'/name).read_bytes()).hexdigest()==value for name,value in ec['source_sha256'].items())
            block+=('**Executed eICU learning curves:** all 45 completed policy/tool states are reexecuted on the 2,000-stay development guard, with independent set counts, original proposal choices and acceptance decisions. Raw and accepted trajectories are separate. ' if lang=='en' else '**已执行 eICU 学习曲线复算：** 在 2,000 次住院的开发 guard 上，重新运行全部 45 个已完成策略／工具状态，独立核对集合计数、原 proposal 选择及接纳决定；原始和接纳曲线分别报告。')
            delta=ec['final_own_error_minus_control']['raw']['uniform']['mean']
            block+=(f"At 40k encountered cases, raw own-error-minus-uniform drug/order F1 is {delta['drug_micro_f1']:+.5f}/{delta['core_order_micro_f1']:+.5f}. These guard cases participate in selection; this is not the held-out hospital test. " if lang=='en' else f"累计 40k 病例时，原始状态中自身错误优先相对普通训练的药物／订单 F1 差为 {delta['drug_micro_f1']:+.5f}/{delta['core_order_micro_f1']:+.5f}。此 guard 参与版本选择，不能当作留出医院测试。")
            block+=f'[Raw/accepted curves, three seeds and regressions](../upgrade_v25/DEVELOPMENT_CURVES.{lang}.md)\n\n'
            if (ROOT/'upgrade_v25/results/frozen_before_test.json').exists() and not (ROOT/'upgrade_v25/results/summary.json').exists():
                block+=('All three eICU seeds and static-control choices are now frozen. The original queue is executing the 8,005-stay held-out hospital test and independent audit; its results remain pending.\n\n' if lang=='en' else 'eICU 三个种子及全部静态对照的选择现已冻结；原队列正在执行 8,005 次住院的留出医院统一测试及独立核验，测试成绩尚待完成。\n\n')
            if (ROOT/'upgrade_v25/results/interval_numeric_audit.json').exists():
                numeric=json.loads((ROOT/'upgrade_v25/results/interval_numeric_audit.json').read_text());assert numeric['status']=='passed'
                assert numeric['script_sha256']==hashlib.sha256((ROOT/'upgrade_v25/audit_interval_numerics.py').read_bytes()).hexdigest()
                assert all(hashlib.sha256((ROOT/'upgrade_v25'/name).read_bytes()).hexdigest()==value for name,value in numeric['source_sha256'].items())
                test=json.loads((ROOT/'upgrade_v25/results/summary.json').read_text());assert test['status']=='complete'
                block+=('### Completed eICU held-out hospital test\n\n' if lang=='en' else '### eICU 留出医院测试已完成\n\n')
                block+=('All three seeds and 13 methods/components finish the same 8,005 stays / 6,227 patients / 16 unseen hospitals. Independent checks cover frozen selections, feedback weights, all saved prediction scores and per-seed patient/hospital intervals. Integer accumulation exactly reproduces all 144 interval bounds after a numerical warning; no scores were replaced. Selected results below are three-seed means; the full report retains all methods, seed SD and raw/accepted curves.\n\n' if lang=='en' else '三个种子、13 个方法／组件配置完成同一 8,005 次住院／6,227 人／16 家未见医院测试。已独立核验冻结选择、反馈权重、全部保存预测的计分及逐种子患者／医院区间。数值警告后，整数累加完全复现 144 个区间边界，未替换分数。下表为三个种子的均值；完整报告保留全部方法、种子标准差及原始／接纳曲线。\n\n')
                block+='| Method | Drug F1 | Joint-order F1 |\n|---|---:|---:|\n'
                for name in ['retrieval_conditional','word_char_ensemble','full_data_uniform','uniform','error_prioritized','permuted_priority','error_priority_initial_tool']:
                    v=test['methods'][name];block+=f"| {name} | {v['drug_f1_mean']:.5f} | {v['order_f1_mean']:.5f} |\n"
                block+=f'\n[Complete external method table, uncertainty and fitting budgets](../upgrade_v25/RESULTS.{lang}.md)\n\n'
                sensitivity_proof=ROOT/'upgrade_v25/results/order_denominator_audit.json'
                if sensitivity_proof.exists():
                    sensitivity_path=ROOT/'upgrade_v25/results/order_denominator_summary.json';proof=json.loads(sensitivity_proof.read_text());sensitivity=json.loads(sensitivity_path.read_text())
                    assert proof['status']=='passed' and proof['summary_sha256']==hashlib.sha256(sensitivity_path.read_bytes()).hexdigest()
                    assert proof['auditor_sha256']==hashlib.sha256((ROOT/'upgrade_v25/audit_order_denominator.py').read_bytes()).hexdigest()
                    before=sensitivity['all_states']['error_priority_initial_tool'];after=sensitivity['all_states']['error_prioritized']
                    block+=(f"**Incomplete-output sensitivity:** a post-test analysis independently recounts all 129 frozen states and includes incomplete outputs in the prediction denominator. For the identical selected drug sets, the initial-to-updated order tool changes this score from **{before['all_output_denominator_f1']['mean']:.5f} to {after['all_output_denominator_f1']['mean']:.5f}**, while output completeness falls from **{100*before['complete_output_fraction']['mean']:.2f}% to {100*after['complete_output_fraction']['mean']:.2f}%**. Exact matching improves, but completeness does not. Original primary scores and selections are unchanged; missing reference fields remain unscorable.\n\n" if lang=='en' else f"**不完整输出敏感性：** 测试后新增分析独立重算全部 129 个冻结状态，把缺字段输出也计入预测分母。逐例选药集合相同，初始→更新订单工具的分数由 **{before['all_output_denominator_f1']['mean']:.5f} 提高到 {after['all_output_denominator_f1']['mean']:.5f}**，但完整率由 **{100*before['complete_output_fraction']['mean']:.2f}% 降到 {100*after['complete_output_fraction']['mean']:.2f}%**。精确匹配改善，完整率没有改善。原主评分与选择不变，真值缺失字段仍不可评分。\n\n")
        if (PAPER/'public_benchmark_coverage.json').exists():
            block+=('**Public-data coverage:** a source/identity recount confirms all300 released RxQA OpenFDA questions and all2,000 deduplicated RxSafeBench cases in the historical full-set runs. Later adaptive comparisons use988 frozen test cases, keeping their625/190/197 development cases separate. The unavailable BNF component is excluded. ' if lang=='en' else '**公开数据覆盖：** 源记录／题目身份复核证实RxQA公开OpenFDA全部300题已覆盖，历史全量实验覆盖RxSafeBench去重后全部2,000题；后续进化方法使用988题冻结测试，625／190／197开发题分别保留。未获得的BNF部分不计入。')
            block+=f'[Exact scope, recounted results and metadata correction](PUBLIC_BENCHMARKS.{lang}.md)\n\n'
        if (ROOT/'upgrade_v30/common_test_addendum.json').exists():
            block+=('**Common main-table extension:** all v29/v30 program methods, frozen raw rounds and proposal-selected states are now registered for the exact v27 test cases and label spaces. The evaluator and independent prediction reexecution are implemented; execution waits for every author method and all program audits. ' if lang=='en' else '**统一主表衔接：** v29/v30全部程序方法、冻结原始轮次和proposal选择状态，已登记在完全相同的v27测试病例与药物空间中对比。评估器和独立预测重执行已实现，等待全部作者方法与程序核验完成后执行。')
            block+=f'[Common test table and protocol](../upgrade_v30/COMMON_TEST.{lang}.md)\n\n'
        if (PAPER/'exposure_registry_audit.json').exists():
            exposure=json.loads((PAPER/'exposure_registry_audit.json').read_text());assert exposure['status']=='passed'
            block+=(f"**Prior-case audit:** {exposure['families_checked']} recorded families and {exposure['roles_checked']} roles are independently reconstructed. Excluding prior/reserved patients from the890 current test patients freezes **{exposure['retained_test_patients']} patients / {exposure['retained_test_visits']} visits** before test predictions. The full main table is unchanged; this is a separate sensitivity subset with explicit registry-coverage limits. " if lang=='en' else f"**历史病例核验：** 独立重建{exposure['families_checked']}类记录／{exposure['roles_checked']}种角色。在原890位测试患者中排除历史使用／预留患者后，于测试预测前冻结 **{exposure['retained_test_patients']}位患者／{exposure['retained_test_visits']}次就诊**。完整主表不变，新增单独的敏感性子集，并明确登记记录的覆盖局限。")
            block+=f'[Membership audit and subgroup results](EXPOSURE.{lang}.md)\n\n'
        if (ROOT/'upgrade_v31/results/progress.json').exists():
            progress=json.loads((ROOT/'upgrade_v31/results/progress.json').read_text())
            block+=('### Parameter repair: randomized positions and causal learning controls\n\n' if lang=='en' else '### 参数修复：候选位置随机化与学习机制对照\n\n')
            block+=('v0.31 runs four arms across three seeds and three rounds: ranked uniform, permuted uniform, permuted own-error and permuted shuffled-error updates. Each round uses the same 400-example/100-step budget. Original retrieval ranks and candidate order fields remain visible. This tests whether weight updates learn drug decisions beyond display position, and whether own errors add value over ordinary training. Candidate tools and order templates stay fixed.\n\n' if lang=='en' else 'v0.31已登记四种方法、三个种子、三轮，当前正逐组执行：原排序普通更新、随机位置普通更新、随机位置自身错误优先、随机位置打乱错误权重。每轮均为400样本／100步，保留原检索排名和候选订单字段。它检验参数更新能否摆脱展示位置依赖，以及自身错误是否比普通学习更有价值。候选工具和订单模板固定。\n\n')
            block+=(f"Completed optimizer runs: **{progress['optimizer_runs_with_complete_receipts']}/36**; fully audited seeds: **{len(progress['seeds_fully_audited'])}/3**. Old test cases are excluded. Proposal selects checkpoints; the reused 200-case guard is exploratory development evidence, not an untouched test.\n\n" if lang=='en' else f"已完成训练回执：**{progress['optimizer_runs_with_complete_receipts']}/36**；完整核验种子：**{len(progress['seeds_fully_audited'])}/3**。排除旧测试病例。proposal选择检查点；复用的200例guard属于探索性开发证据，不是未触碰测试。\n\n")
            p=ROOT/'upgrade_v31/results/audit-seed42.json'
            if p.exists():
                base=json.loads(p.read_text())['base_proposal']
                block+='| State on 100 proposal cases | Ranked drug/order F1 | Permuted drug/order F1 |\n|---|---:|---:|\n'
                block+=f"| Frozen base | {base['ranked']['drug_micro_f1']:.5f}/{base['ranked']['core_order_micro_f1']:.5f} | {base['permuted']['drug_micro_f1']:.5f}/{base['permuted']['core_order_micro_f1']:.5f} |\n"
                evidence=json.loads((ROOT/'upgrade_v31/results/audit-seed42.json').read_text())
                for arm,rows in evidence['arms'].items():
                    for row in rows:
                        a=row['proposal']['ranked'];b=row['proposal']['permuted'];block+=f"| {arm}, round {row['round']} | {a['drug_micro_f1']:.5f}/{a['core_order_micro_f1']:.5f} | {b['drug_micro_f1']:.5f}/{b['core_order_micro_f1']:.5f} |\n"
                block+='\n'
                failed=[(arm,row) for arm,rows in evidence['arms'].items() for row in rows if all(m['empty_fraction']==1 for m in row['proposal'].values())]
                for arm,row in failed:
                    block+=(f"**Observed failure:** seed42/{arm}/round{row['round']} has 100% empty predictions in both proposal views and drug/order micro-F1=0. The frozen promotion rule rejects it; original results remain.\n\n" if lang=='en' else f"**已发现失败：** seed42／{arm}／第{row['round']}轮在两种proposal视图下均100%空输出，药物／订单micro-F1=0；既定升级规则已拒绝该版本，原结果保留。\n\n")
                if failed:
                    diagnosis=ROOT/'upgrade_v31/results/collapse_diagnostic.json';diagnostic_audit=ROOT/'upgrade_v31/results/collapse_diagnostic_audit.json'
                    if diagnosis.exists() and diagnostic_audit.exists():
                        d=json.loads(diagnosis.read_text())['states']['permuted_uniform_seed42_round1']['proposal_permuted'];before=d['teacher_forced_ground_truth_prefix']['auroc'];after=d['all_zero_prefix_without_ground_truth']['auroc']
                        block+=(f"The separate probability diagnostic covers the first permuted-uniform adapter (seed42, round1) and independently recounts 384 vectors. On 32 permuted proposal cases, AUROC changes from {before:.4f} with oracle GT prefixes to {after:.4f} with label-free zero prefixes, where no decision probability reaches 0.5. " if lang=='en' else f"单独的概率诊断针对首个随机位置普通更新适配器（seed42，第1轮），独立复算384组向量：32例打乱排序proposal上，AUROC从真值前缀的{before:.4f}降为无标签全零前缀的{after:.4f}，后者无一位置的选择概率达到0.5。")
                        block+=f'[Diagnosis and figure](../upgrade_v31/COLLAPSE.{lang}.md)\n\n'
            block+=f'[Actual parameter updates, audit and results](../upgrade_v31/RESULTS.{lang}.md)\n\n'
        if (ROOT/'upgrade_v32/results/training_progress.json').exists():
            p=json.loads((ROOT/'upgrade_v32/results/training_progress.json').read_text())
            progress_path=ROOT/'upgrade_v32/results/progress.json';rp=json.loads(progress_path.read_text()) if progress_path.exists() else {'completed_optimizer_fits':len(p['arms']),'audited_splits':[]}
            block+=(f"**Controlled decision repair:** v32 crosses teacher/zero answer prefixes with uniform/balanced binary-decision loss on the same 400 examples and 100 steps per arm. {rp['completed_optimizer_fits']}/4 fits have completion receipts. " if lang=='en' else f"**受控决策修复：** v32 将真实／全零答案前缀与普通／平衡二元决策损失交叉，四组均用相同 400 例、100 步；目前 {rp['completed_optimizer_fits']}/4 组训练回执完成。")
            if rp['audited_splits']:
                block+=(f"Independently recounted score panels: {', '.join(rp['audited_splits'])}. All four repairs, the base, failed adapter and direct retrieval controls remain in the report. " if lang=='en' else f"已独立复算成绩分组：{', '.join(rp['audited_splits'])}。四种修复、基础模型、原失败适配器及直接检索对照均完整保留。")
            else:
                block+=('No repair performance score is available yet. ' if lang=='en' else '尚无修复性能成绩。')
            block+=('The implemented scorer separates fixed 0.5 decisions, proposal calibration and weight-update effects. Its independent recount covers all thresholds, unreachable GT, patient intervals and empty-output/invariance diagnostics; the 120 synthetic bindings are preflight checks, not clinical results. ' if lang=='en' else '已实现评分器分开报告固定 0.5 阈值、proposal 校准及权重更新的效果；独立复算覆盖全部阈值、候选外真值、患者区间、空输出与位置不变性。120 个合成绑定是执行预检，不属于临床成绩。')
            block+=f'[Actual repair results and gates](../upgrade_v32/RESULTS.{lang}.md)\n\n'
            if 'proposal' in rp['audited_splits']:
                repair_path=ROOT/'upgrade_v32/results/proposal_summary.json';repair_proof=json.loads((ROOT/'upgrade_v32/results/proposal_audit.json').read_text())
                assert repair_proof['status']=='passed' and repair_proof['summary_sha256']==hashlib.sha256(repair_path.read_bytes()).hexdigest()
                assert repair_proof['auditor_sha256']==hashlib.sha256((ROOT/'upgrade_v32/audit_evaluation.py').read_bytes()).hexdigest()
                repair_summary=json.loads(repair_path.read_text());repair_views=repair_summary['endpoints']['proposal_calibrated']
                repair_labels={'frozen_base':('基础模型','Frozen base'),'original_failed_adapter':('原失败适配器','Original failed adapter'),'teacher_uniform':('真实前缀＋普通损失','GT prefix / uniform'),'zero_uniform':('全零前缀＋普通损失','Zero prefix / uniform'),'teacher_balanced':('真实前缀＋类别平衡','GT prefix / balanced'),'zero_balanced':('全零前缀＋类别平衡','Zero prefix / balanced'),'original_retrieval_top8':('直接检索前8','Direct retrieval top-8'),'all20_candidate_tools':('全部20个候选','All 20 candidates')}
                block+=('**Completed repair mechanism comparison:** 100 proposal admissions / 97 patients, one training seed. Below are registered calibration results; these same cases select thresholds. Every repair remains below top-8 retrieval in drug/order F1 point estimates under both fixed and calibrated endpoints.\n\n' if lang=='en' else '**已完成修复机制对照：** 100 次 proposal 住院／97 人、一个训练种子。下表为已登记校准结果，同一批病例参与阈值选择。固定及校准两个端点下，全部修复的药物／订单 F1 点估计仍低于前8检索。\n\n')
                block+=('| Method | Ranked drug/order F1 | Permuted drug/order F1 | Mean drugs ranked/permuted |\n' if lang=='en' else '| 方法 | 原排序药物／订单 F1 | 随机排序药物／订单 F1 | 平均开药数：原／随机 |\n')+'|---|---:|---:|---:|\n'
                for name,labels in repair_labels.items():
                    ranked=repair_views['ranked']['methods'][name];permuted=repair_views['permuted']['methods'][name]
                    block+=f"| {labels[1 if lang=='en' else 0]} | {ranked['drug_micro_f1']:.5f}/{ranked['core_order_micro_f1']:.5f} | {permuted['drug_micro_f1']:.5f}/{permuted['core_order_micro_f1']:.5f} | {ranked['mean_predicted_drugs']:.2f}/{permuted['mean_predicted_drugs']:.2f} |\n"
                block+=('\nCalibration can eliminate empty outputs by selecting almost every candidate. The zero-prefix/balanced repair selects 20.00/19.91 drugs on average; near-perfect nonempty position agreement therefore does not establish useful discrimination. Three neural states choose the lower grid boundary, so the fixed grid is not exhaustive calibration.\n\n' if lang=='en' else '\n校准可以通过几乎全选来消除空输出：全零前缀／平衡损失平均选20.00／19.91个药物，接近满分的非空位置一致性不能证明区分能力提高。三个神经状态选择网格下界，因此固定网格不是穷尽校准。\n\n')
                if 'guard' not in rp['audited_splits']:
                    block+=('The report-only guard is still pending; its original selection gate and current prerequisites remain in the full report.\n\n' if lang=='en' else '只用于报告的 guard 尚未完成，原选择门槛和当前前置条件见完整报告。\n\n')
                ranking_path=ROOT/'upgrade_v32/results/proposal_rank_diagnostic.json';ranking_audit=ROOT/'upgrade_v32/results/proposal_rank_diagnostic_audit.json'
                if ranking_audit.exists():
                    ranking_proof=json.loads(ranking_audit.read_text());assert ranking_proof['status']=='passed' and ranking_proof['summary_sha256']==hashlib.sha256(ranking_path.read_bytes()).hexdigest()
                    ranking=json.loads(ranking_path.read_text());ranking_views=ranking['panels']['drug_sha256']
                    block+=('**New fixed-cardinality diagnosis:** all states select exactly eight candidates from their saved probabilities. This post-proposal development analysis adds no inference or selection. It distinguishes ranking from output-count effects.\n\n' if lang=='en' else '**新增固定开药数量诊断：** 每个模型按已保存的分数恰好选8个药物。这是事后提出的开发分析，不新增推理或选择，用于区分排序能力与开药数量效应。\n\n')
                    block+=('| Method | Ranked drug/order F1 | Permuted drug/order F1 |\n' if lang=='en' else '| 方法 | 原排序药物／订单 F1 | 随机排序药物／订单 F1 |\n')+'|---|---:|---:|\n'
                    for name,m in ranking_views['ranked']['methods'].items():
                        other=ranking_views['permuted']['methods'][name]
                        block+=f"| {repair_labels[name][1 if lang=='en' else 0]} | {m['drug_micro_f1']:.5f}/{m['core_order_micro_f1']:.5f} | {other['drug_micro_f1']:.5f}/{other['core_order_micro_f1']:.5f} |\n"
                    block+=('\nNo neural state exceeds retrieval in either F1 under either declared tie rule. Same-slot correlations exceed identity-aligned correlations; frequent cutoff ties make the zero-prefix states sensitive to tie handling. The full report retains both tie rules, within-case AUROC and patient intervals. A numerical-readout precision check remains a next investigation, not an implemented repair.\n\n' if lang=='en' else '\n两种已声明同分规则下，神经模型均未超过检索的药物或订单F1。按展示位置对齐的相关性高于药物身份对齐；全零前缀状态的截断同分频繁，结果对同分处理敏感。完整报告保留两种规则、病例内AUROC及患者区间。数值读出精度检查属于下一步调查，尚未实现为修复。\n\n')
                    block+=f'[Fixed-cardinality ranking diagnosis](../upgrade_v32/RANKING_DIAGNOSTIC.{lang}.md)\n\n'
        if (ROOT/'upgrade_v30/protocol.json').exists():
            repaired=json.loads((ROOT/'upgrade_v30/results/summary.json').read_text()) if (ROOT/'upgrade_v30/results/summary.json').exists() else {'panels':{}}
            block+=('### Memory repair now executing: compatibility and separate confirmation\n\n' if lang=='en' else '### 记忆改进已实际运行：旧记忆兼容性与独立确认\n\n')
            block+=('The 14-arm v0.30 factorial revalidates old memory after policy changes and checks the whole update on patients separate from individual-edit verification. Greedy, own-error and shuffled-evidence methods each run all four gate combinations. Resetting correction memory retains the calibrated prescription policy. Original v0.29 fits are reused exactly; source probabilities, every gate and outputs receive independent audits.\n\n' if lang=='en' else 'v0.30已启动14臂组合实验：策略改变后核验旧记忆，并用独立于逐项编辑验证的患者确认整套更新。贪心、自身错误驱动、打乱证据三种方法均运行四种验证组合。清空纠错记忆仍保留校准后的处方策略。原样复用v0.29拟合；独立核验源概率、每次验证和输出。\n\n')
            if repaired['panels']:
                block+='| Panel | Audited seeds | Calibration F1 | Own C0P0 F1 | Own C1P1 F1 | Greedy C1P1 F1 |\n|---|---:|---:|---:|---:|---:|\n'
                for panel,p in repaired['panels'].items():
                    m=p['endpoints']['selected']['methods'];vals=[m[k]['patient_f1']['mean'] for k in ['calibrated_policy','own_C0P0','own_C1P1','greedy_C1P1']]
                    block+=f"| {panel} | {len(p['seeds'])} | "+' | '.join(f'{v:.5f}' for v in vals)+' |\n'
            else:block+=('Guard scores remain pending audit.\n' if lang=='en' else 'guard分数等待独立核验。\n')
            block+=f'\n[All gate combinations, raw rounds and independent audits](../upgrade_v30/RESULTS.{lang}.md)\n\n'
        if (ROOT/'upgrade_v29/results/summary.json').exists():
            new=json.loads((ROOT/'upgrade_v29/results/summary.json').read_text());states=[]
            for p in (ROOT/'upgrade_v29/results').glob('*-seed*.json'):
                z=json.loads(p.read_text())
                if 'lock' in z:states.append(z)
            done=sum(z['status']=='selection_frozen' for z in states);audited=sum(len(p['seeds']) for p in new['panels'].values())
            block+=('### New executed mechanism: isolated witnesses and program synthesis\n\n' if lang=='en' else '### 新机制已执行：隔离witness与条件程序生成\n\n')
            block+=(f'{done}/6 runs have frozen five rounds; {audited}/6 pass independent model/program audits. Each seed uses 5,692 fit patients and permanently excludes 1,423 witness patients from all model fits and candidate statistics. The agent generates one/two-predicate programs; raw policy, ordinary class calibration, greedy/random programs and shuffled evidence are separate controls. These are development results.\n\n' if lang=='en' else f'{done}/6组已完成并冻结五轮，{audited}/6组通过模型与程序独立核验。每个种子用5,692人拟合，1,423位witness永久不参与模型拟合或候选统计。agent生成一到两个条件的程序；原策略、普通逐药物校准、贪心／随机程序及打乱证据分别作对照。以下仍是开发结果。\n\n')
            if new['panels']:
                block+='| Panel | Audited seeds | Raw policy F1 | Class calibration F1 | Greedy program F1 | Own-agent F1 |\n|---|---:|---:|---:|---:|---:|\n'
                for panel,p in new['panels'].items():
                    vals=[p['methods'][k]['patient_f1']['mean'] for k in ['raw_policy','calibrated_policy','greedy_conditional_memory','own_error_program_agent']]
                    block+=f"| {panel} | {len(p['seeds'])} | "+' | '.join(f'{v:.5f}' for v in vals)+' |\n'
            block+=f'\n[Actual conditional-program experiment and replay diagnosis](../upgrade_v29/RESULTS.{lang}.md)\n\n'
        block+=('### Development method comparison: same guard set\n\n1,231 visits/467 patients; these are development scores, not the final test main table. Each included seed passes independent source/cross-fit/candidate/prediction audits.\n\n' if lang=='en' else '### 同一guard上的方法对照（开发结果）\n\n1,231次就诊／467人；这是开发结果，不是最终测试主表。纳入种子均通过独立原始数据、交叉拟合、候选和预测核验。\n\n')
        block+='| Panel | Audited seeds | Shared policy F1 | Greedy-rule F1 | Own-error agent F1 | Shuffled-evidence agent F1 |\n|---|---:|---:|---:|---:|---:|\n'
        for panel,p in summary['panels'].items():
            vals=[p['methods'][k]['patient_f1']['mean'] for k in ['uniform_policy','greedy_error_rules','own_error_rule_agent','shuffled_evidence_rule_agent']]
            block+=f"| {panel} | {len(p['seeds'])} | "+' | '.join(f'{v:.5f}' for v in vals)+' |\n'
        block+=('\nThe changed artifact is executable rule memory: aggregate error evidence → LLM edit proposal → training-witness check → retained rules. Policy coefficients update through ordinary supervised fits. Current increments are small; improvement from more data does not establish a unique RSI advantage. The language model maintains the policy offline; it does not generate a full prescription for each patient in this experiment.\n\n' if lang=='en' else '\n真正改变的是**可执行规则记忆**：聚合错误证据→LLM提议编辑→训练witness核验→保留规则。共同策略系数通过普通监督拟合更新。当前额外提升很小；病例增加带来的改善不能直接归因于RSI。此实验的语言模型负责离线维护策略，不为每位患者生成完整处方。\n\n')
        block+=f'[Full method table, five-round trajectories and paired intervals](../upgrade_v27/RESULTS.{lang}.md)\n\n'
        block+=('### FHIR repairs: actual audited executions\n\n' if lang=='en' else '### FHIR修复：已执行并审计的结果\n\n')
        block+='| Contract C | Statistics S | Frozen skills K | Validation /80 | ID /64 | Held-out types /60 |\n|---|---|---|---:|---:|---:|\n'
        for c in [0,1]:
            for s in [0,1]:
                for k in [0,1]:
                    splits=repair['conditions'].get(f'C{c}S{s}K{k}',{}).get('splits',{});vals=[str(splits[x]['state_correct']) if x in splits else 'pending' for x in ['val','id_test','test']]
                    block+=f'| {c} | {s} | {k} | '+' | '.join(vals)+' |\n'
        block+=('\nC enforces the instruction-derived answer shape through actual budgeted retries. S computes source-bound latest/24h Observation statistics with paging and unit separation. K reuses the exact two learned skills. C/S are fixed engineering repairs; no autonomous tool evolution is claimed. All conditions are fixed and all splits reused: exploratory repair, not untouched confirmation.\n\n' if lang=='en' else '\nC按任务文字约束答案形式，不合规时在原预算内重新回答；S从真实分页数据计算最近值／24小时统计并区分单位；K原样复用两条已学技能。C/S属于固定工程修复，不冒充自主工具进化。八种组合固定、划分此前已使用，属于探索性修复。\n\n')
        block+=f'[Execution receipts, costs and repair contrasts](../upgrade_v28/RESULTS.{lang}.md) · [System diagram](RXRSI_DESIGN.{lang}.md)\n\n'
        block+=('Updated 15 October 2026. Versioned historical studies below retain their original protocols and results.\n' if lang=='en' else '更新于2026-10-15。下方是保留原协议和结果的历史版本；运行进度以上方为准。\n')
        update(PAPER/f'CURRENT_RESULTS.{lang}.md',block)
        plan=('''## Current execution queue — concrete delivery status

1. Rule-memory mechanism is implemented and executed on both ATC-L4 spaces, three seeds, five case-growth rounds, six arms. Finish independent cross-fit/candidate/witness/output audits and retain all edit decisions and raw curves.
2. Complete every registered ARMR/GAMENet/SafeDrug run at 50 epochs. The implemented queue reloads each selected checkpoint, audits development predictions, then opens the v27 common test. Its evaluator includes conventional methods, six rule arms, every frozen round and three artifact interventions. The separately registered common-test extension adds all seven v29 and fourteen v30 methods after all choices/audits freeze, with independent reexecution of 315 program states per panel. Test results cannot retune methods.
3. Finish the eight-condition real-FHIR C/S/K factorial across 80 validation, 64 ID and 60 held-out-type tasks. Report every condition, original strict scores, resource integrity, budgets and paired effects. Audit raw-page arithmetic; do not replace old results with posthoc value extraction.
4. Continue the eICU external-hospital study already running. Preserve zero-target stays and frozen selection. This supplies a separate transport test, not a directly pooled ATC score.
5. Complete the seven-arm isolated-witness program study and its registered carryover/new-edit diagnosis. The next 14-arm compatibility/confirmation factorial is now registered, implemented and running, with separately learned trajectories under greedy, own-error and shuffled evidence. Complete every seed and independent gate/output audit; report raw final-round and proposal-selected endpoints before claiming improved transfer.
6. Complete the registered local v0.31 parameter experiment: four arms, three seeds, three rounds, equal 400-example/100-step updates. Independently check feedback before updates, sampled targets, changed adapters, raw/accepted curves, positional invariance and patient intervals. All per-seed choices freeze before guard evaluation; old tests remain excluded.
7. Regrade the exact frozen common-test predictions on the independently audited prior-case-excluded318-patient/801-visit subset and the complementary group, with no reselection. Keep the complete original main table. The implemented queue waits for both parent test audits; report the registry's coverage limits.
8. Keep the existing English LaTeX source, bilingual results entry and versioned reports synchronized. Only completed audited experiments enter score tables; compilation and GitHub pushes are checked explicitly.

''' if lang=='en' else '''## 当前执行队列：具体交付状态

1. 规则记忆机制已实现并真实运行：两种ATC-L4空间、三个种子、五轮病例增长、六种方法。完成交叉拟合、候选、witness和预测的独立核验，保留所有编辑决定及原始曲线。
2. ARMR／GAMENet／SafeDrug各组完成已登记50轮。已实现队列逐组重载所选检查点、核验开发预测，再开启v27统一测试；包含传统方法、六种规则方法、全部冻结轮次和三项对象干预。另已登记并实现共同测试扩展：全部选择／核验冻结后加入v29七种与v30十四种方法，每个药物空间独立重执行315组程序预测。测试结果不用于调参。
3. 完成真实FHIR的C/S/K八组合：80验证、64同类、60未见任务类型。报告每组合原严格成绩、真实资源完整性、预算和配对效果；重建原始分页算术，不用事后提取数值替换旧分数。
4. 继续已启动的eICU跨医院实验，保留零目标病例和冻结版本。它是独立迁移测试，不能直接混入ATC主表。
5. 完成七臂隔离witness程序研究及已登记的旧记忆／新编辑诊断。后续14臂兼容性／独立确认组合实验已经登记、实现并运行；贪心、自身错误和打乱证据各自重新学习轨迹。完成所有种子与验证／输出独立核验，同时报告末轮原状态与proposal选择状态，再判断是否改善迁移。
6. 完成已登记的本地v0.31参数实验：四臂、三个种子、三轮，均为400样本／100步。逐项核验更新前反馈、抽样目标、变化的适配器、原始／接纳曲线、位置不变性与患者区间；每个种子全部选择冻结后评价guard，排除旧测试集。
7. 对同一冻结测试预测，补算已独立核验的历史病例排除子集（318位患者／801次就诊）及补集，不重新选择模型；保留完整原主表。已实现队列等待两套父测试核验，并报告历史记录覆盖局限。
8. 持续同步现有英文LaTeX、中英文总览及版本报告；只有完成且核验的实验填分数，并确认编译和GitHub同步。

''')
        if (ROOT/'upgrade_v32/results/training_progress.json').exists():
            if 'proposal' in rp['audited_splits']:
                plan+=('**Local repair subtask:** all four fits and the complete eight-method proposal comparison pass independent audits. Fixed-threshold class balancing reduces empty outputs, while calibration often selects nearly all candidates; none of the new repairs beats direct top-8 point estimates. Continue the registered multi-round control and report-only guard queue. ' if lang=='en' else '**本地修复子任务：** 四组拟合及完整八方法 proposal 对照均通过独立核验。固定阈值下的类别平衡减少空输出，校准后则常接近全选；新修复的点估计仍未超过直接前8检索。继续已登记的多轮对照和只用于报告的 guard 队列。')
                if (ROOT/'upgrade_v32/results/proposal_rank_diagnostic_audit.json').exists():
                    plan+=('The additional fixed-eight diagnosis is also independently recounted: positional dependence and frequent cutoff ties remain. Next isolate numerical-readout precision before changing training or candidate-specific scoring; this investigation has not yet been executed. ' if lang=='en' else '追加的固定8药诊断也已独立复算：位置依赖和频繁截断同分仍存在。下一步先隔离数值读出精度，再决定训练或逐药评分改动；该精度调查尚未执行。')
            elif rp['completed_optimizer_fits'] == 4 and 'training_audit_sha256' in rp.get('gates', {}).get('proposal', {}).get('proof', {}):
                plan+=('**Local repair subtask:** all four registered v32 fits have passed the training audit. Continue the original proposal scoring and independent recount queue, then wait for all original v31 seed42 selections to freeze before report-only guard evaluation. ' if lang=='en' else '**本地修复子任务：** v32 四组已登记拟合均已通过训练核验。继续原有 proposal 评分与独立复算队列；全部原 v31 seed42 选择冻结后，才能评价只用于报告的 guard。')
            else:
                plan+=('**Local repair subtask now executing:** finish and audit the four registered v32 fits, then run the implemented scoring and independent recount queue. ' if lang=='en' else '**正在执行的本地修复子任务：** 完成并核验 v32 四组已登记拟合，再运行已实现的评分与独立复算队列。')
            plan+=('All four repairs, two neural controls and two retrieval controls receive fixed-threshold and ordinary-calibration comparisons. Every pilot state/threshold freezes before guard. This one-round supervised repair still needs multi-round RSI verification. ' if lang=='en' else '四种修复、两个神经控制和两个检索控制均报告固定阈值与普通校准对比。全部试验状态／阈值在评价 guard 前冻结；这一轮监督修复仍需要多轮 RSI 验证。')
            plan+=f'[Actual repair execution and results](../upgrade_v32/RESULTS.{lang}.md)\n\n'
        if (ROOT/'upgrade_v25/results/interval_numeric_audit.json').exists():
            plan=plan.replace('4. Continue the eICU external-hospital study already running. Preserve zero-target stays and frozen selection. This supplies a separate transport test, not a directly pooled ATC score.', '4. Completed: eICU tests 13 methods/components across three seeds on 8,005 stays from 16 held-out hospitals. Raw/accepted curves, zero-target strata, component interventions, fitting budgets and independently recounted patient/hospital intervals are delivered. Its native-code protocol remains separate from ATC scores.')
            plan=plan.replace('4. 继续已启动的eICU跨医院实验，保留零目标病例和冻结版本。它是独立迁移测试，不能直接混入ATC主表。', '4. 已完成：eICU 在16家留出医院的8,005次住院上测试13个方法／组件、三个种子；交付原始／接纳曲线、无目标亚组、组件干预、拟合预算及独立复算的患者／医院区间。原生编码协议与ATC成绩分别报告。')
        plan+=f'[Current actual results](CURRENT_RESULTS.{lang}.md) · [Rule study](../upgrade_v27/RESULTS.{lang}.md) · [FHIR repair](../upgrade_v28/RESULTS.{lang}.md)\n\n'
        plan+=('Earlier entries below are historical snapshots.\n' if lang=='en' else '下方较早条目是历史状态快照。\n')
        update(PAPER/('COMPLETION_PLAN.en.md' if lang=='en' else 'COMPLETION_PLAN.md'),plan)
    readme=f'''## Current execution snapshot

The rule-memory study completes **{complete}/6 five-round runs**; genuine author-model baselines complete **{nr}/15 full 50-epoch runs** ({epochs}/750 epochs saved). Independent development audits quantify the small memory increment against greedy/random/shuffled controls. A common test evaluator is implemented and stays closed until every selection and audit freezes.

The real-FHIR factorial executes fixed answer-contract/statistics repairs and frozen learned skills in all eight combinations. This is exploratory execution repair, not autonomous tool-code evolution. All completed audited cells, costs and limits are maintained in the reports.

[中文当前结果与方法对照](paper/CURRENT_RESULTS.zh.md) · [English current results](paper/CURRENT_RESULTS.en.md) · [Rule mechanism and rounds](upgrade_v27/RESULTS.en.md) · [FHIR repair](upgrade_v28/RESULTS.en.md)

Earlier paragraphs below describe retained study versions; this snapshot governs current execution status.
'''
    if (ROOT/'upgrade_v29/protocol.json').exists():
        readme+='\n**New mechanism executing:** v0.29 permanently separates fit/witness patients, adds a strong ordinary calibration control and lets the language agent synthesize conditional programs. Only independently audited development results are published. [Conditional-program study](upgrade_v29/RESULTS.en.md) · [中文机制与结果](upgrade_v29/RESULTS.zh.md).\n'
    if (ROOT/'upgrade_v30/protocol.json').exists():
        readme+='\n**Current improvement:** the registered 14-arm v0.30 factorial tests old-memory compatibility and whole-update confirmation on separate patients, with greedy and shuffled controls. [Actual gate study](upgrade_v30/RESULTS.en.md) · [中文验证机制与结果](upgrade_v30/RESULTS.zh.md).\n'
    if (ROOT/'upgrade_v31/protocol.json').exists():
        readme+='\n**Local parameter intervention:** v0.31 randomizes candidate display positions while preserving retrieval ranks, comparing ordinary, own-error and shuffled-error QLoRA under matched budgets. Three seeds and all raw/accepted checkpoints are registered; only independently audited results are reported. [Parameter study](upgrade_v31/RESULTS.en.md) · [中文参数进化](upgrade_v31/RESULTS.zh.md).\n'
    if (PAPER/'execution_status.json').exists() and json.loads((PAPER/'execution_status.json').read_text())['api']['status']=='waiting_for_credit':
        readme+='\n**API status:** a new HTTP402 interrupted unfinished API branches; saved checkpoints and completed scores are retained. Local training/audits continue. [Execution status](paper/execution_status.json).\n'
    update(ROOT/'README.md',readme)
    paper_snapshot=f'''## Live execution snapshot

The common medication-method study has **{nr}/15** completed 50-epoch author runs ({epochs}/750 saved epochs) and **{complete}/6** completed five-round rule runs. The final common test remains gated by the registered selections and audits. These counts describe a saved snapshot; running outputs continue to update.

[中文当前结果](CURRENT_RESULTS.zh.md) · [English current results](CURRENT_RESULTS.en.md) · [Cross-method development comparison](../upgrade_v27/DEVELOPMENT_METHODS.en.md) · [Final common-test table and gate](../upgrade_v30/COMMON_TEST.en.md)
'''
    update(PAPER/'README.md',paper_snapshot)
if __name__=='__main__':main()
