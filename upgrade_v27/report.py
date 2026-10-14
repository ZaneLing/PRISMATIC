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
                z=json.loads(p.read_text());l=z['lock'];table+=f"| {l['panel']} | {l['method']} | {l['seed']} | {len(z['epochs'])} | {z['status']} |\n"
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
        text+='\n## Artifacts / 交付文件\n\n- [Registered protocol](protocol.json) and [training addendum](training_addendum.json)\n- [Implementation details](implementation_notes.json)\n- [Cohort manifest](results/cohort_manifest.json)\n- [Independent audit and missing classes](results/cohort_audit.json)\n- [Public molecule receipts](results/molecular_resource_audit.json)\n- [Actual molecular/graph resources](results/model_resource_manifest.json)\n- [Author-core execution probe](results/author_core_probe.json) and [training runtime equivalence](results/training_runtime_probe.json)\n- [Independent control audit](results/control_audit.json)\n- [Recent-method source audit](../paper/LATEST_METHODS.'+lang+'.md)\n\nRestricted cases, fitted artifacts and patient-level outputs remain local. Public reports contain aggregates and hashes.\n'
        (HERE/f'RESULTS.{lang}.md').write_text(text)
if __name__=='__main__':main()
