"""Maintain bilingual identity provenance and completed subgroup results."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=HERE/'exposure_registry.json';data=json.loads(p.read_text());a=json.loads((HERE/'exposure_registry_audit.json').read_text());assert a['status']=='passed' and a['registry_sha256']==sha(p) and a['auditor_sha256']==sha(HERE/'audit_exposure_registry.py')
    completed=HERE/'prior_case_subset_results.json';summary=json.loads(completed.read_text()) if completed.exists() else None
    if summary:assert summary['status']=='complete' and summary['registry_audit_sha256']==sha(HERE/'exposure_registry_audit.json') and summary['source_sha256']==sha(HERE/'evaluate_prior_case_subsets.py')
    for lang in ('en','zh'):
        text=('# Prior-case exposure and frozen test-subset analysis\n\n' if lang=='en' else '# 历史病例使用记录与冻结测试子集\n\n')
        text+=('## 1. Actual independent membership audit\n\n' if lang=='en' else '## 1. 已实际完成的独立成员核验\n\n')
        text+=(f"Before current common-test inference, independently reconstructing **{a['families_checked']} experiment families / {a['roles_checked']} roles** identifies **{data['prior_union_patients']:,} prior or conservatively reserved patients**. Among the890 current test patients, **{data['excluded_test_patients']}** occur in this union; the frozen complementary subset retains **{data['retained_test_patients']} patients / {data['retained_test_visits']} visits**. All visits of retained patients remain. The retained/prior intersection is zero.\n\n" if lang=='en' else f"在当前统一测试尚未开始时，独立重建 **{a['families_checked']}类实验／{a['roles_checked']}种数据角色**，得到 **{data['prior_union_patients']:,}位历史使用或保守预留患者**。原890位测试患者中，**{data['excluded_test_patients']}位**出现在该并集中；冻结的补充子集保留 **{data['retained_test_patients']}位患者／{data['retained_test_visits']}次就诊**，保留每位患者全部原测试就诊，与历史并集交叉为零。\n\n")
        text+=('The original all-patient main table remains unchanged. Exclusion uses identity/history only, never outcomes or predictions. The full and molecular panels use exactly the same patient subset. Every eligible repeated-visit patient in the source panel is already allocated (8,905/8,905); relabeling another existing split would not create new data.\n\n' if lang=='en' else '原完整测试主表保持不变；排除只依赖身份和历史角色，不使用成绩或预测。两个药物空间使用完全相同的患者子集。源协议的全部合格重复就诊患者已经分配（8,905/8,905），重新命名已有划分不会产生新数据。\n\n')
        text+='| Recorded family | Patients overlapping the890 current test patients | Membership evidence |\n|---|---:|---|\n'
        for name,z in data['families'].items():text+=f"| {name} | {z['test_patient_overlap']} | {z['proof']} |\n"
        text+=('\nRows overlap and must not be added. Early deterministic samples have source/code hashes and matching counts but lack original membership digests; later samples match saved membership hashes or exact stored identities. Prepared reviewer cases are excluded conservatively even though clinician ratings were never obtained. This is bookkeeping, not a requirement for clinician review of GT metrics.\n\n' if lang=='en' else '\n各行有交叉，不能相加。早期确定性样本有源文件／代码哈希及匹配计数，但未保存当年的成员摘要；后期样本与原始成员摘要或实际存储身份一致。已预留审核病例也保守排除，即使尚无医生标注；这属于使用记录，不要求医生审核后才能计算GT指标。\n\n')
        text+=('## 2. Scope and pending comparison\n\nThis registry covers the named PRISMATIC MIMIC-IV history. It does not establish absence from foundation-model pretraining, undocumented experiments or external use. Population-level source audits are distinct from model-exposure records. The subset is a registered prior-record-excluded sensitivity analysis, not proof of globally untouched confirmation or a new external dataset. Composition differences between retained and excluded patients cannot be interpreted as a causal effect of exposure.\n\n' if lang=='en' else '## 2. 证据范围与后续对照\n\n登记册覆盖列出的PRISMATIC MIMIC-IV实验历史，不能证明患者从未进入基础模型预训练、未留记录的实验或外部使用。总体数据审计与模型使用记录不同。本子集是预先登记的历史记录排除敏感性分析，不是全球完全未触碰的确认集，也不是新外部数据；两组患者构成不同，成绩差异不能解释为“接触过病例”的因果效应。\n\n')
        if summary:
            for panel,strata in summary['panels'].items():
                for stratum,z in strata.items():
                    text+=f"### {panel} / {stratum}: {z['patients']} patients, {z['visits']} visits\n\n| Method | Runs | Patient F1 | Patient Jaccard | Micro F1 |\n|---|---:|---:|---:|---:|\n"
                    for method,r in z['methods'].items():
                        vals=[]
                        for key in ('patient_f1','patient_jaccard','micro_f1'):
                            m=r['metrics'][key];vals.append(f"{m['mean']:.5f} ± {m['seed_sd']:.5f}" if m['seed_sd'] is not None else f"{m['mean']:.5f}")
                        text+=f"| {method} | {r['runs']} | "+' | '.join(vals)+' |\n'
            text+='\n[All method differences, patient intervals and source checks](prior_case_subset_results.json)\n\n'
        else:text+=('**Performance results remain pending.** After both common-test audits pass, the evaluator regrades their exact immutable predictions on the retained and excluded groups, reporting every selected method with seed variation and descriptive patient-cluster intervals. No new fitting, API call or checkpoint selection occurs.\n\n' if lang=='en' else '**模型成绩待执行。** 两套共同测试核验完成后，评估器对相同不可变预测分别计算保留组与排除组结果，报告所有已选择方法、种子波动和描述性患者聚类区间，不新增拟合、API调用或检查点选择。\n\n')
        text+='[Registered protocol](prior_case_exclusion_protocol.json) · [Registry aggregates](exposure_registry.json) · [Independent membership audit](exposure_registry_audit.json)\n'
        (HERE/f'EXPOSURE.{lang}.md').write_text(text)
if __name__=='__main__':main()
