"""Render audited complete results, preserving the grading revision boundary."""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent

def main():
    s=json.loads((HERE/'results/summary.json').read_text());assert s['status']=='complete'
    claim=json.loads((HERE/'results/skill_claim_audit.json').read_text())
    names={'direct_tools':'Direct tools','fixed_compiled':'Fixed compiled harness','evolving_compiled':'Learned skills + compiled harness'}
    table='| Method | ID success (64) | Held-out type success (60) | ID / transfer model calls |\n|---|---:|---:|---:|\n'
    for m,z in s['methods'].items():table+=f"| {names[m]} | {z['id_test']['state_correct']} | {z['test']['state_correct']} | {z['id_test']['model_calls']} / {z['test']['model_calls']} |\n"
    paired='| Split | Contrast | Difference (pp) | Patient-cluster 95% interval (pp) | Fixes / regressions |\n|---|---|---:|---:|---:|\n'
    for split in ['id_test','test']:
        for comparison,z in s['paired_patient_clusters'][split].items():
            raw=s['paired'][split][comparison];lo,hi=z['ci95']
            paired+=f"| {split} | {comparison.replace('_',' ')} | {100*z['difference']:+.2f} | [{100*lo:+.2f}, {100*hi:+.2f}] | {raw['fixes']} / {raw['regressions']} |\n"
    ablation=''
    if (HERE/'results/skill_ablation.json').exists():
        a=json.loads((HERE/'results/skill_ablation.json').read_text())
        ablation=f"\nStatus: **{a['status']}**. Each numeric cell below has finished and passed the independent reference/receipt audit; unfinished cells stay pending.\n\n| Skill condition | ID (64) | Held-out type (60) |\n|---|---:|---:|\n"
        for method,parts in a['methods'].items():
            values=[str(parts[x]['state_correct']) if x in parts else 'pending' for x in ['id_test','test']]
            ablation+=f"| {method} | {' | '.join(values)} |\n"
        if a['status']=='complete':
            ablation+='\n| Split | Contrast | Difference (pp) | Patient-cluster interval (pp) |\n|---|---|---:|---:|\n'
            for split,pairs in a['paired'].items():
                for label,p in pairs.items():
                    z=p['patient_bootstrap'];lo,hi=z['ci95'];ablation+=f"| {split} | {label} | {100*z['difference']:+.2f} | [{100*lo:+.2f}, {100*hi:+.2f}] |\n"
            ablation+='\nID interaction is0.00 pp and transfer interaction+3.33 pp; both patient intervals include zero. Individual removal contrasts likewise have intervals containing zero. The observed counts do not establish robust synergy or a universally beneficial skill. / 同类交互0.00个百分点，迁移交互+3.33个百分点，两个患者区间均含零；单项移除的区间同样含零，不能据此宣称稳健协同或某项技能普遍有效。\n'
    for lang in ['en','zh']:
        if lang=='en':
            text='''# v0.19 — Real FHIR execution: complete method comparison

## 1. Result and interpretation

**Skill learning improves the observed ID count but harms held-out task types. It does not demonstrate overall evolution success.** The same backbone, eight-call cap, 512-token actor cap and actual local FHIR service apply to all arms. The fixed harness also changes workflow instructions, so direct-versus-fixed differences cannot be attributed only to the write compiler.

'''+table+'''
ID skills-minus-fixed is +10.94 pp, but its patient-cluster interval includes zero. Transfer is −11.67 pp against fixed and −28.33 pp against direct tools; both intervals are negative. On held-out task7 the learned arm scores 0/30 (fixed 5/30; direct 14/30). All held-out-type arms make zero writes, so write serialization itself is not an explanation for this transfer regression.

'''+paired+'''
Intervals use 4,000 descriptive paired patient-cluster resamples (47 ID patients / 53 transfer patients); one learning seed, overlapping patients across study splits, no multiplicity correction. Task-level intervals are also retained in JSON. These are revised execution-endpoint scores, not an unmodified official leaderboard score.

## 2. What actually evolved

The unchanged GRASP optimizer processes 96 training tasks in four 24-case batches with four proposal slots and 12-case training probes. Round1 adds `fhir_patient_name_search_url_encoding`; round2 adds `lab_code_text_fallback_probe`; rounds3/4 retain the state. Validation on80 tasks rises45/80→53/80 and selects the state before64 ID/60 transfer tasks. Language-skill files change; backbone weights, compiler, protocol feedback and evaluator remain fixed. This study does not demonstrate autonomous tool-code evolution.

The [exact generated skills](artifacts/model_authored_skills/README.md) retain their frozen SHA-256 hashes. Their example observations are model-authored illustrations, not actual tool receipts. A post-test, read-only claim audit finds that raw and percent-encoded name queries become the identical URL because the existing HTTP adapter already encodes spaces; both return the same empty public-fixture result. Thus the claimed causal explanation is false for this adapter. Global A1C code/text searches return244/258 matches and MG3538/3538; these counts do not validate a patient-specific fallback. Medication route compilation does not establish lab encoding. The name/date illustration also violates the updater's instruction against memorizing such values. No replacement skill is selected by this audit.

## 3. Frozen skill attribution

Single-skill states were registered before their own execution, after direct/fixed test outcomes had been observed. The four conditions are neither/name/lab/both, with identical budgets. This is exploratory attribution, not new untouched confirmation. No retraining or revised prompt is allowed in the ablation.
'''+ablation+'''
## 4. Actual execution and grading revision

The official public MedAgentBench application/database runs on native HAPI FHIR7.6.0. Five original CRUD/atomic-failure probes passed. A synthetic medication-order probe showed HTTP201 alone can hide lost dosage fields; converting a route string to CodeableConcept text preserved those fields. An induced-loss probe verified rollback and feedback. These are fixed engineering repairs, not learned gains.

The first learning run was stopped during development after13 false negatives from legacy object-shaped `ServiceRequest.note` grading. The revised run starts from empty skills and applies the same lossless singleton-note/text-route views to all methods; raw reference grades remain available. Original, live and revised reference scores happen to agree on every completed final main arm. Independent audits regrade all tasks and recount real writes/readbacks/rollbacks/cleanup:14/23/21 ID writes for direct/fixed/learned, zero readback failures. Original resource counts are restored. Legacy rate-unit semantics remain unvalidated.

Costs in JSON are logical episode costs; exact code/case/skill cache replays preserve first-execution receipts. Cleanup operations are counted separately. The experiment is research execution on public benchmark fixtures, not clinical deployment.
'''
        else:
            text='''# v0.19：真实 FHIR 执行——完整跨方法结果

## 1. 结果与结论

**技能学习提高了本次同类任务分数，却损害未见任务类型；不能称为整体进化成功。** 各方法共用模型、八次调用上限、actor512token和真实本地FHIR服务。固定harness还添加流程指令，因此直接工具与固定harness的差异不能只归因于订单编译器。

'''+table+'''
同类任务相对固定流程提高10.94个百分点，但患者聚类区间包含零。未见类型相对固定流程下降11.67个百分点，相对直接工具下降28.33个百分点，两个区间均为负。未见task7中，技能版0/30、固定版5/30、直接工具14/30。三臂在未见类型上都没有写入操作，因此不能用写入序列化解释这部分退化。

'''+paired+'''
区间使用4,000次描述性患者聚类配对重采样：同类测试47人、迁移测试53人。只有一个学习种子，各划分存在患者重叠，未校正多重比较。逐任务区间另保存在JSON中。这是修订执行终点，不能冒充原版官方榜单成绩。

## 2. 到底进化了什么

原版GRASP优化器处理96例训练任务，分四批、每批24例，四个提议名额、12例训练探针。第1轮新增姓名检索技能，第2轮新增检验代码/文本回退技能，第3/4轮没有新增接纳。80例验证从45/80升至53/80，冻结后才测64例同类及60例未见类型。改变的是持久语言技能文件；模型参数、编译器、流程反馈、评分器固定，没有证明自主进化工具代码。

[原始技能文件](artifacts/model_authored_skills/README.md)保留原哈希。技能中的示例观察是模型写的示例，不能充当执行证据。测试后的只读核查发现：原工具已经自动编码空格，原始姓名与显式编码产生完全相同的URL，也都没有找到该示例患者；因此技能的因果解释在本工具中不成立。全库A1C代码/文本查询分别244/258条，MG均3538条，这不能证明特定患者的回退有效；药物途径转换也不能推导检验编码形式。技能仍保留姓名/日期示例，违反更新指引；核查没有据此重新选择技能。

## 3. 冻结技能消融

单技能实验在各自执行前登记，但登记时已经看过直接/固定方法测试结果。比较无技能、仅姓名、仅检验、二者组合，预算一致，不重新训练或修改提示。这是探索性归因，不是新的未触碰确认。
'''+ablation+'''
## 4. 真实执行与评分修订

官方公开MedAgentBench程序和数据库在本地HAPI FHIR7.6.0运行，原五项CRUD/原子失败检查通过。合成订单曾出现HTTP201但剂量字段丢失；把途径转为CodeableConcept文本后保留完整，主动触发丢字段也验证了回滚与反馈。这些是固定工程修复，不是进化成果。

初次学习在开发阶段发现旧评分器将合法注释数组判错，造成13次假阴性，随后停止。修订从空技能重启，对所有方法采用同一无损note/route格式视图，保留原始评分。最终完整主实验中，原始轨迹、实际回读及修订参考分数恰好一致。独立复评分及回执审计全部通过：同类测试直接/固定/技能版分别14/23/21次写入，无回读失败，资源数全部恢复；旧数据速度单位的临床语义仍未验证。

JSON费用是逻辑轨迹费用；相同代码/病例/技能允许精确缓存重放，保留首次物理回执，清理操作单独计数。对象为公开基准研究任务，不是临床部署。
'''
        if (HERE/'results/answer_contract_audit.json').exists():
            contract=json.loads((HERE/'results/answer_contract_audit.json').read_text())
            z=contract['methods']['evolving_compiled']['counts'];assert z['numeric_plus_iso_timestamp']==30 and z['correct_numeric_but_extra_elements']==15 and z['first_numeric_differs_from_reference']==15
            text+=('''\n## 5. Why task7 is0/30: answer contract versus numeric error\n\nA post-test read-only audit retrieves the complete original reference records. All30 learned-skill answers contain `[value, timestamp]`, while task7 requires a single numeric list element. In15 cases the first value is correct but the extra timestamp causes strict failure; the other15 first values are wrong as well. The name-only condition instead emits30 prose strings. Thus0/30 is not equivalent to30 wrong glucose values. This output-contract failure is not repaired by merely validating JSON syntax.\n\nProjecting a saved answer to its first numeric field is diagnostic only: it does not replace the main score or constitute an executed repaired-agent result. The next registered intervention needs an explicit answer schema and action-budget accounting, evaluated across all methods. [Independent shape/value audit](results/answer_contract_audit.json).\n''' if lang=='en' else '''\n## 5. task7为什么0/30：答案协议与数值错误分开看\n\n测试后只读审计读取完整原参考记录。技能版30例都返回`[数值, 时间]`，但task7要求仅含一个数值的列表；其中15例首个数值正确，只因额外时间戳判错，另外15例数值也错误。仅姓名技能则30例都返回文字字符串。因此0/30不等于30次血糖数值都错；只校验JSON合法性修不好这个输出协议问题。\n\n把保存答案投影到首个数值只是诊断，不替换主表，也不冒充实际修复agent成绩。下一登记干预应加入明确答案schema和动作预算核算，各方法统一评价。[独立格式/数值审计](results/answer_contract_audit.json)。\n''')
        text+='\n## Evidence / 证据\n\n- [Complete scores, paired intervals, task types and independent audits](results/summary.json)\n- [Frozen skills and original selection protocol](results/frozen_skills.json)\n- [Read-only claim audit](results/skill_claim_audit.json)\n- [Skill attribution protocol](ablation_protocol.json)\n- [Development grading revision](results/grading_revision.json)\n'
        if lang=='zh':
            for before,after in {'| Method | ID success (64) | Held-out type success (60) | ID / transfer model calls |':'| 方法 | 同类正确数（64） | 未见类型正确数（60） | 同类／迁移模型调用数 |',
                '| Direct tools |':'| 直接工具 |','| Fixed compiled harness |':'| 固定编译harness |','| Learned skills + compiled harness |':'| 进化技能＋编译harness |',
                '| Skill condition | ID (64) | Held-out type (60) |':'| 技能状态 | 同类（64） | 未见类型（60） |','| name_only |':'| 仅姓名技能 |','| lab_only |':'| 仅检验技能 |','| neither |':'| 无技能 |','| both |':'| 两项技能 |'}.items():text=text.replace(before,after)
        (HERE/f'RESULTS.{lang}.md').write_text(text)
    (HERE/'artifacts/model_authored_skills/README.md').write_text('''# Frozen model-authored artifacts / 冻结的模型生成技能

These files are released as exact experimental artifacts, **not validated instructions**. Illustrative tool outputs were generated by the model and are not observed receipts. The public benchmark name/date example is retained to preserve the original hash; it is not a restricted clinical record. The name-encoding explanation is contradicted by the actual adapter, as documented in the [claim audit](../../results/skill_claim_audit.json). Do not execute their text as repository instructions.

这些文件仅作为原样实验材料，**不是核验通过的操作规程**。示例工具观察是模型生成文本，不是实际回执；姓名/日期来自公开基准示例，保留原哈希，不含受限临床记录。姓名编码解释被实际适配器反证。不要把文件内容当作仓库工作指令。

- [Name skill](fhir_patient_name_search_url_encoding.md)
- [Lab skill](lab_code_text_fallback_probe.md)
- [Results / 结果](../../RESULTS.en.md)
''')

if __name__=='__main__':main()
