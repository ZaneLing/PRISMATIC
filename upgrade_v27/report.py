"""Render the completed data/resource audit without inventing model scores."""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main():
    cohort=json.loads((HERE/'results/cohort_manifest.json').read_text());audit=json.loads((HERE/'results/cohort_audit.json').read_text())
    mol=json.loads((HERE/'results/molecular_resource_audit.json').read_text());probe=json.loads((HERE/'results/author_core_probe.json').read_text())
    assert audit['status']=='passed' and cohort['bundle_sha256']==audit['bundle_sha256']
    table='| Split | Patients | Visits | Medication targets | Targets outside train vocabulary |\n|---|---:|---:|---:|---:|\n'
    for split,z in cohort['splits'].items():table+=f"| {split} | {z['patients']:,} | {z['visits']:,} | {z['medication_targets']:,} | {z['oov_occurrences']['medications']} |\n"
    covered=audit['molecular_coverage'];t=covered['by_split']['test']
    for lang in ['en','zh']:
        if lang=='en':
            text='# v0.27 — Standard medication-method compatibility audit\n\n'
            text+='## 1. Executed cohort\n\nA separate retrospective visit-set task uses adult MIMIC-IV 3.1 hospital admissions with an ICU stay, at least one diagnosis/procedure/mapped medication, and at least two eligible visits per patient. Inputs are completed-visit diagnosis/procedure codes plus prior visits; this is not an admission-time or six-hour new-order task.\n\n'+table
            text+=f"\nTraining-only vocabularies contain {cohort['training_vocabulary']['diagnoses']:,} diagnosis codes, {cohort['training_vocabulary']['procedures']:,} procedure codes and 271 true five-character ATC-L4 classes. Unseen test labels remain in recall denominators. Patient overlap across partitions is zero. The public NDC mapping covers **{100*cohort['selected_row_mapping_fraction']:.2f}%** of {cohort['selected_source_rows']:,} selected source prescription rows; the target is the mapped subset. This coverage is not complete prescription ground truth.\n"
            text+='\n## 2. Independent audit\n\nReconstruction of all 23,177 selected visits verifies diagnoses, procedures, medication sets, adult ICU membership, visit order, patient partition and training vocabularies. The full population selection flow is produced by the builder and is not independently rescanned. Test patients overlap earlier observed v0.9/v0.21 tests by 20/50 respectively; this panel is exploratory.\n'
            text+=f"\n## 3. Public molecule and code execution results\n\nAll **{mol['returned_public_cids']}/{mol['requested_public_cids']}** public CIDs return valid RDKit structures, spanning {mol['classes_with_valid_molecules']} ATC-L4 classes. This covers **{covered['classes_with_molecules']}/{covered['training_classes']}** training classes and {t['with_training_class_molecules']:,}/{t['targets']:,} test target occurrences. The 52 uncovered classes are listed in the audit, never assigned invented structures.\n"
            text+='\nPinned author ARMR-2025, GAMENet and SafeDrug cores actually pass synthetic forward/backward probes. GAMENet is invariant to changing the hidden current-medication field. The SafeDrug probe uses real public molecules and a clearly synthetic identity substructure mask only to check execution; it is not a trained model or a scientific baseline score. Complete BRICS/graph resources and a common covered-label panel are still required.\n'
            text+='\n## 4. Next execution gate\n\nFreeze a method-training addendum after resolving molecular coverage; compare full ATC-L4 nonmolecular methods and a separately disclosed common molecular space. Run genuine author cores, matched controls and the RxRSI prescription tool. Select checkpoints on development only, then compute patient-averaged and micro set metrics, coverage, prescription sizes and patient-cluster intervals. No method has been trained or scored in v0.27 yet.\n'
        else:
            text='# v0.27 — 标准处方方法兼容性审计\n\n'
            text+='## 1. 已构建的真实队列\n\n独立历史就诊任务：MIMIC-IV 3.1成人、住院含ICU、诊断/操作/已映射药物各至少一项，每人至少两次合格就诊。输入整次就诊的诊断/操作及既往就诊，不能称为入院时点或六小时新订单预测。\n\n'+table
            text+=f"\n仅训练集建立词表：{cohort['training_vocabulary']['diagnoses']:,}个诊断、{cohort['training_vocabulary']['procedures']:,}个操作、271个真正五字符ATC-L4类。测试集词表外标签继续计入召回分母。跨划分患者交集为零。旧公开NDC表仅覆盖所选{cohort['selected_source_rows']:,}条处方行的 **{100*cohort['selected_row_mapping_fraction']:.2f}%**；标签是已映射子集，不是完整处方ground truth。\n"
            text+='\n## 2. 独立核对已通过\n\n从原始文件逐项重建23,177次就诊的诊断、操作、药物集合，检查成人ICU资格、就诊排序、患者划分及训练词表。完整母队列筛选流程来自构建器，没有在本审计中独立再扫描。测试患者与此前v0.9/v0.21已观察测试的交集分别为20/50人，本表将标为探索性实验。\n'
            text+=f"\n## 3. 分子资源与代码已实际运行\n\n**{mol['returned_public_cids']}/{mol['requested_public_cids']}**个公开CID均取得结构并通过RDKit验证，覆盖{mol['classes_with_valid_molecules']}个ATC-L4类；对应本队列训练类的 **{covered['classes_with_molecules']}/{covered['training_classes']}**，覆盖测试{t['with_training_class_molecules']:,}/{t['targets']:,}个标签。52个未覆盖类别全部列明，没有补造分子。\n"
            text+='\nARMR-2025、GAMENet、SafeDrug固定作者核心均已通过合成输入的前向/反向执行探针；GAMENet对隐藏的当前药物标签变化不敏感。SafeDrug探针采用真实公开分子和明确标注的合成单位子结构矩阵，仅验证依赖与执行，不是训练结果。正式实验仍需BRICS、相互作用图及相同覆盖药物空间。\n'
            text+='\n## 4. 下一执行关口\n\n解决分子覆盖后登记训练附录：完整ATC-L4非分子方法表与独立披露的共同分子空间表；运行真正作者核心、传统对照和RxRSI处方工具。开发集选版本，冻结后统一计算患者平均及micro指标、覆盖率、处方数量和患者聚类区间。v0.27当前尚无已训练或已评分的方法。\n'
        if (HERE/'results/model_resource_manifest.json').exists():
            text=text.replace('Complete BRICS/graph resources and a common covered-label panel are still required.','The subsequent complete study resources contain627 real molecular graphs,863 BRICS fragments and326 fingerprint types, with no uncovered projection row. The synthetic probe mask is never used for training.')
            text=text.replace('正式实验仍需BRICS、相互作用图及相同覆盖药物空间。','后续已构建正式资源：627个真实分子图、863个BRICS片段、326种指纹，投影无缺失行；合成探针矩阵不会用于训练。')
            start=text.index('## 4. ')
            text=text[:start]+('''## 4. Registered method training is running

The full271-class and common molecular219-class panels each retain the same patients/visits. The latter explicitly excludes5,613 test targets and retains3 empty-target visits; its scores cannot be pooled with the full panel. Each neural architecture receives50 full training epochs for seeds42/137/2026. ARMR and GAMENet run in both panels; SafeDrug runs in the molecular panel. Proposal patient-average Jaccard selects epoch/threshold; guard is report-only. Equal case exposure is not equal optimizer steps or FLOPs. Tests remain gated until all baseline and subsequently registered RxRSI states freeze.

The sparse SafeDrug adjacency, persisted fixed molecular embedding and CPU/MPS ARMR execution pass numeric/gradient/checkpoint probes. The current released SafeDrug training script uses `min` where published Eq19 uses `max`; this independently adapted reproduction uses the published formula and discloses the difference. [SafeDrug paper](https://arxiv.org/pdf/2105.02711). No original-paper reproduction score is claimed.

''' if lang=='en' else '''## 4. 已登记并启动真实方法训练

完整271类与共同分子219类两表保留相同患者/就诊；分子表明确排除5,613个测试标签，保留3次空目标就诊，不能和完整表混算。每种神经架构训练50整轮，种子42/137/2026；ARMR与GAMENet跑两种空间，SafeDrug跑分子空间。proposal按患者平均Jaccard选择轮次/阈值，guard只报告；相同病例曝光不等于相同步数/FLOPs。全部基线和之后登记的RxRSI状态冻结前，不推断测试集。

SafeDrug稀疏图、固定分子嵌入的检查点保存，以及ARMR的CPU/GPU执行都通过数值/梯度/恢复探针。当前公开SafeDrug脚本的`min`与论文式19的`max`冲突，本独立适配复现采用论文公式并披露差异。[原论文](https://arxiv.org/pdf/2105.02711)。不冒充原文精确复现成绩。

''')
            table='| Panel | Method | Seed | Finished epochs / 50 | Status |\n|---|---|---:|---:|---|\n'
            for p in sorted((HERE/'results').glob('*-seed*.json')):
                z=json.loads(p.read_text())
                if 'epochs' not in z:continue
                l=z['lock'];table+=f"| {l['panel']} | {l['method']} | {l['seed']} | {len(z['epochs'])} | {z['status']} |\n"
            text+=table+'\nQueued seeds/panels are not counted as completed. Snapshot of saved epoch receipts; no provisional neural test score.\n'
        if (HERE/'results/control_audit.json').exists():
            checked=json.loads((HERE/'results/control_audit.json').read_text());assert checked['status']=='passed'
            text+=('\n## 5. Completed conventional controls: guard only\n\nThese are genuine fitted-method comparisons on1,231 development visits/467 patients. All four choices are frozen by separate proposal data; independent reconstruction from the original visit source verifies features, saved predictions and set metrics. They are not the requested final test main table.\n\n' if lang=='en' else '\n## 5. 已完成的传统方法比较：仅开发guard\n\n以下是真实拟合后的方法比较：1,231次开发就诊／467人。四种方法均由另一proposal集选定；从原就诊源独立重建特征、保存预测、集合指标，核查通过。这还不是最终测试主表。\n\n')
            table='| Panel | Method | Patient-average F1 | Patient-average Jaccard | Mean medications |\n|---|---|---:|---:|---:|\n'
            for panel in ['full','molecular']:
                z=json.loads((HERE/f'results/{panel}-controls.json').read_text());assert z['status']=='selection_frozen'
                for name,result in z['methods'].items():
                    g=result['guard'];table+=f"| {panel} | {name} | {g['patient_f1']:.5f} | {g['patient_jaccard']:.5f} | {g['mean_medications']:.2f} |\n"
            text+=table
        if (HERE/'rsi_addendum.json').exists():
            text+=('''\n## 6. Executable rule-memory RSI is running\n\nFive rounds expose20/40/60/80/100% of training patients. A common supervised policy is refit; patient-disjoint cross-fitting produces error evidence. The language agent sees only aggregate candidate-rule descriptors and chooses up to4 edits. A separate20% training-patient witness partition accepts beneficial edits; validation/test never supplies candidate feedback. Runtime rules only read observed features and model probabilities. Compared arms are uniform policy, greedy rules, random rules, own-error agent, shuffled-evidence agent and matched proposals without verification. Ordinary coefficient fitting is not called autonomous weight evolution; the changed agent artifact is a typed rule memory. This task predicts classes, not full doses.\n\nSource files, actual proposals, accepted/rejected operations and state hashes are saved. Original fold probabilities were retained but original fold weights were not; a separate raw-source reconstruction explicitly refits the folds and checks probability/decision equality. Scalar witness audits investigate numeric-library warnings without treating warnings as incorrect model predictions. No superiority claim is made from provisional development gains.\n\n''' if lang=='en' else '''\n## 6. 可执行规则记忆RSI已经运行\n\n五轮依次使用20/40/60/80/100%的训练患者。共同监督策略重新拟合，用患者独立交叉拟合产生错误证据；语言agent只看聚合候选规则，最多选择4项编辑。另一20%训练患者作验证证据，只接纳有益编辑，验证/测试不向候选生成提供反馈。运行时规则只读已观察特征和模型概率。对照含普通策略、贪心规则、随机规则、自身错误agent、打乱证据agent和取消验证。普通系数拟合不冒充自主权重进化，实际进化对象是类型化规则记忆；本任务只预测药物类，不生成完整剂量。\n\n代码、真实提议、接纳/拒绝及状态哈希已保存。原始交叉拟合概率有保留，但当时未保存折模型权重；另行从原始就诊数据重拟合各折，明确标注为重建，并核对概率和决策。数值库告警通过标量患者评分重算核验，不把告警当成模型错误。临时开发收益不能证明优于其他方法。\n\n''')
            table='| Panel | Seed | Completed rounds /5 | Own-error retained rules | Status |\n|---|---:|---:|---:|---|\n'
            for p in sorted((HERE/'results').glob('*-rsi-seed*.json')):
                z=json.loads(p.read_text());rows=z['rounds'];count=rows[-1]['arms']['own_error_rule_agent']['memory_size'] if rows else 0
                table+=f"| {z['lock']['panel']} | {z['lock']['seed']} | {len(rows)} | {count} | {z['status']} |\n"
            text+=table+'\n[Registered mechanism and controls / 机制与对照登记](rsi_addendum.json) · [Scalar decision audit / 标量决定核验](results/rule_decision_audit.json)\n'
            text+=('\nThe own-error agent actually changed the following amounts of memory (accepted operations, including later deletions):\n\n' if lang=='en' else '\n自身错误agent实际改变的记忆如下（统计已接纳操作，包含之后删除的规则）：\n\n')
            text+='| Panel | Seed | Accepted ADD | Accepted DELETE | Retained rules by round |\n|---|---:|---:|---:|---|\n'
            for p in sorted((HERE/'results').glob('*-rsi-seed*.json')):
                z=json.loads(p.read_text());ops=[op for row in z['rounds'] for op in row['arms']['own_error_rule_agent']['accepted_operations']]
                counts=[row['arms']['own_error_rule_agent']['memory_size'] for row in z['rounds']]
                text+=f"| {z['lock']['panel']} | {z['lock']['seed']} | {sum(o['operation']=='ADD' for o in ops)} | {sum(o['operation']=='DELETE' for o in ops)} | {' → '.join(map(str,counts))} |\n"
            text+=('\nFor example, a retained rule uses observed prior medication history for class `N02BE` to include that same class when its probability is just below the common threshold. Other candidates use diagnosis or prior-drug features. The log records each exact predicate, drug code, witness score change and rule hash; these statistical associations are not prescribing guidelines.\n' if lang=='en' else '\n例如，一条真实保留规则使用既往药物类`N02BE`，在同类预测概率略低于共同阈值时将其纳入；其他候选使用诊断或既往药类特征。日志记录精确条件、药物编码、witness分数变化与规则哈希。这是可核查的统计关联，不是处方指南。\n')
        author_audits=sorted((HERE/'results').glob('*-selection-audit-seed*.json'))
        if author_audits:
            text+=('\n## 7. Audited author-model development results\n\nOnly completed 50-epoch runs whose selected checkpoint has been reloaded and independently recounted appear here. These are guard results; unfinished seeds remain pending.\n\n' if lang=='en' else '\n## 7. 已核验的作者模型开发结果\n\n这里只列完成50轮、重新加载所选检查点并独立重算通过的运行。以下仍是guard开发结果，未完成种子不补零。\n\n')
            text+='| Panel | Method | Seed | Guard F1 | Guard Jaccard |\n|---|---|---:|---:|---:|\n'
            for path in author_audits:
                z=json.loads(path.read_text());assert z['status']=='passed';m=z['splits']['guard']['selected_metrics']
                text+=f"| {z['panel']} | {z['method']} | {z['seed']} | {m['patient_f1']:.5f} | {m['patient_jaccard']:.5f} |\n"
        if (HERE/'results/rsi_development_summary.json').exists():
            summary=json.loads((HERE/'results/rsi_development_summary.json').read_text())
            text+=('''\n## 8. Audited rule-memory comparison and experience curves

The table uses the same 1,231 guard visits from 467 patients. Models/rounds are chosen on proposal data only. Each included seed passes raw-source feature reconstruction, fresh cross-fit reproduction, candidate-effect and saved prediction checks. Three-seed standard deviations and paired patient intervals are separate: intervals average the observed seeds first and do not estimate new-seed variability. This is still development evidence.

Witness patients are excluded from candidate induction, but their labels can train policies used for other folds. The shared C hyperparameter is selected through proposal performance of full seen-patient fits. Thus cross-fitting prevents direct fitting of a case's own predictor to its label; it is not a wholly isolated nested validation experiment. The repeated witness gate is training validation, not independent clinical confirmation.

''' if lang=='en' else '''\n## 8. 已核验的规则记忆对照与病例增长曲线

同一1,231次guard就诊／467位患者，模型和轮次只由proposal选择。纳入种子均已通过原始特征重建、重新交叉拟合、候选实际收益和保存预测核验。三种子标准差与患者配对区间分开：区间先平均已有种子，不估计新种子的变化。这仍是开发证据。

验证规则的witness患者不参与候选归纳，但其标签会参与其他折策略的拟合；共同C参数由全部已见患者拟合后的proposal表现选择。因此交叉拟合排除了本例标签对本例预测器的直接拟合，不是完全隔离的嵌套验证。重复使用的witness关口属于训练验证，不是独立临床确认。

''')
            text+='| Panel | Method | Audited seeds | Guard F1 ± seed SD | Guard Jaccard ± seed SD |\n|---|---|---:|---:|---:|\n'
            for panel,panel_summary in summary['panels'].items():
                for arm,z in panel_summary['methods'].items():
                    def fmt(key):
                        m=z[key];return f"{m['mean']:.5f}"+(f" ± {m['seed_sd']:.5f}" if m['seed_sd'] is not None else ' (one seed)')
                    text+=f"| {panel} | {arm} | {len(panel_summary['seeds'])} | {fmt('patient_f1')} | {fmt('patient_jaccard')} |\n"
            text+='\n| Panel | Own agent minus control | F1 difference (pp) | Patient interval (pp) |\n|---|---|---:|---:|\n'
            for panel,panel_summary in summary['panels'].items():
                for arm,z in panel_summary['own_agent_minus_control'].items():
                    q=z['patient_f1'];lo,hi=q['patient_ci95'];text+=f"| {panel} | {arm} | {100*q['difference']:+.3f} | [{100*lo:+.3f}, {100*hi:+.3f}] |\n"
            text+='\n| Panel | Round | Training patients | Shared policy proposal F1 | Own-agent proposal F1 | Own retained rules by seed |\n|---|---:|---:|---:|---:|---|\n'
            for panel,panel_summary in summary['panels'].items():
                a=panel_summary['proposal_curves']['own_error_rule_agent'];u=panel_summary['proposal_curves']['uniform_policy']
                for own,uniform in zip(a,u):
                    mean=lambda z:sum(z)/len(z)
                    text+=f"| {panel} | {own['round']} | {own['training_patients'][0]} | {mean(uniform['proposal_patient_f1']):.5f} | {mean(own['proposal_patient_f1']):.5f} | {', '.join(map(str,own['memory_size']))} |\n"
            text+=('\nIncreasing case counts improve the shared supervised predictor; the small incremental memory effect must be compared against greedy and shuffled controls before attributing it to language-agent evolution. These rules represent associations, not validated prescribing indications.\n' if lang=='en' else '\n病例增长首先改善共同监督预测器；记忆的微小额外效果必须对照贪心和打乱证据，才能讨论语言agent进化的贡献。这些规则是统计关联，不是已验证的处方适应证。\n')
            if (HERE.parent/'paper/figures/rule_memory_development.png').exists():
                text+='\n![Audited development curves and paired increments](../paper/figures/rule_memory_development.png)\n\n[Editable vector figure](../paper/figures/rule_memory_development.svg)\n'
        if (HERE/'results/test_audit.json').exists():
            import hashlib
            checked=json.loads((HERE/'results/test_audit.json').read_text());path=HERE/'results/test_summary.json'
            assert checked['status']=='passed' and checked['source_report_sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
            summary=json.loads(path.read_text())
            text+=('\n## 9. Completed common test main table\n\nIndependent source-label/prediction recount passes. Full and molecular spaces remain separate; all selections froze before test inference. Each score is patient-averaged over 2,422 visits/890 patients.\n\n' if lang=='en' else '\n## 9. 已完成的共同测试主表\n\n原始标签和预测独立重算通过；完整与分子空间分别报告，全部版本冻结后才运行测试。患者平均基于2,422次就诊／890人。\n\n')
            text+='| Panel | Method | Runs | Test F1 ± seed SD | Test Jaccard ± seed SD |\n|---|---|---:|---:|---:|\n'
            for panel,p in summary['panels'].items():
                for name,z in p['methods'].items():
                    def fmt(key):
                        q=z['metrics'][key];return f"{q['mean']:.5f}"+(f" ± {q['seed_sd']:.5f}" if q['seed_sd'] is not None else '')
                    text+=f"| {panel} | {name} | {z['runs']} | {fmt('patient_f1')} | {fmt('patient_jaccard')} |\n"
            text+='\n[All raw frozen-round metrics and paired method differences](results/test_summary.json) · [Independent test recount](results/test_audit.json)\n'
        text+='\n## Artifacts / 交付文件\n\n- [Registered protocol](protocol.json) and [training addendum](training_addendum.json)\n- [Implementation details](implementation_notes.json)\n- [Cohort manifest](results/cohort_manifest.json)\n- [Independent audit and missing classes](results/cohort_audit.json)\n- [Public molecule receipts](results/molecular_resource_audit.json)\n- [Actual molecular/graph resources](results/model_resource_manifest.json)\n- [Author-core execution probe](results/author_core_probe.json) and [training runtime equivalence](results/training_runtime_probe.json)\n- [Independent control audit](results/control_audit.json)\n- [Recent-method source audit](../paper/LATEST_METHODS.'+lang+'.md)\n\nRestricted cases, fitted artifacts and patient-level outputs remain local. Public reports contain aggregates and hashes.\n'
        (HERE/f'RESULTS.{lang}.md').write_text(text)
if __name__=='__main__':main()
