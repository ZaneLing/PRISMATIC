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
        text+='\n## Artifacts / 交付文件\n\n- [Registered protocol](protocol.json)\n- [Cohort manifest](results/cohort_manifest.json)\n- [Independent audit and missing classes](results/cohort_audit.json)\n- [Public molecule receipts](results/molecular_resource_audit.json)\n- [Author-core execution probe](results/author_core_probe.json)\n- [Recent-method source audit](../paper/LATEST_METHODS.'+lang+'.md)\n\nRestricted cases, fitted artifacts and patient-level outputs remain local. Public reports contain aggregates and hashes.\n'
        (HERE/f'RESULTS.{lang}.md').write_text(text)
if __name__=='__main__':main()
