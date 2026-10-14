"""Publish the external data audit, keeping feasibility separate from model results."""
import json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent

def main():
    d=json.loads((HERE/'results/source_audit.json').read_text());codes=json.loads((HERE/'results/native_code_audit.json').read_text())
    table='| Split | Stays | Patients | Hospitals | New-order rows | Zero-target stays |\n|---|---:|---:|---:|---:|---:|\n'
    missing='| Split | Target rows | Valid HICL | Missing name, valid HICL | Neither name nor valid HICL |\n|---|---:|---:|---:|---:|\n'
    for split,m in d['splits'].items():
        table+='| '+split+' | '+' | '.join(str(m[k]) for k in ['stays','patients','hospitals','target_rows','zero_target_stays'])+' |\n'
        c=codes['row_identity_coverage'][split];missing+='| '+split+' | '+' | '.join(str(c[k]) for k in ['rows','valid_hicl','missing_name_with_hicl','neither_name_nor_valid_hicl'])+' |\n'
    capacity='| Train vocabulary size | Train coverage (%) | Proposal coverage (%) | Guard coverage (%) |\n|---|---:|---:|---:|\n'
    for row in codes['development_vocabulary_capacity']:
        capacity+=f"| {row['top_train_codes']} | "+' | '.join(f"{100*row['development_coverage'][s]['coverage']:.2f}" for s in ['train','proposal','guard'])+' |\n'
    for lang in ['zh','en']:
        intro='''# v0.24：eICU 外部医院验证的数据审计

## 已做什么

完整扫描200,859次住院、7,301,853条用药记录和39,132,531条检验。固定ICU入科后6小时为决策点，随后6小时为新订单窗口；使用开立时间，不用药物开始时间替代。成年人、观察覆盖窗口且住院中有用药记录的队列，经跨医院患者去重后保留142,485次住院。没有训练模型或生成测试成绩。

医院用固定哈希分到训练/候选验证/检查/测试；一个患者若跨集合，则只保留其在测试优先级最高集合内的住院，删除其他集合住院，共删除1,457次。患者和医院的跨集合重叠均为0。保留窗口内没有新订单的病例，不能把空GT当成模型错误。

## 固定医院划分

''' if lang=='zh' else '''# v0.24 — External eICU hospital-split data audit

## What was executed

Scan all200,859 stays,7,301,853 medication records and39,132,531 lab records. The proposed decision is ICU admission plus6h, with new orders in the following6h identified by order time. Adults with complete window follow-up and medication documentation somewhere in the stay yield142,485 retained stays after cross-partition patient filtering. No model is fitted and no prediction score is generated.

Hospitals are assigned by a fixed hash to train/proposal/guard/test. Cross-partition patients retain stays only in their highest-priority partition (test first);1,457 other stays are dropped. Patient and hospital overlap are both zero. Zero-target stays are retained rather than treated as model failures.

## Fixed hospital partitions

'''
        detail='''
## 药物身份与可达性

不能仅按非空药名建立任务：测试窗口6,283条订单缺药名，其中6,064条仍有有效HICL编码；219条连药名和有效编码都没有。HICL可作为本库编码身份，但尚未建立与RxNorm或MIMIC的等价关系。训练中有1,306个不同HICL，177个对应多个原始药名。

''' if lang=='zh' else '''
## Drug identity and reachability

Filtering to nonempty names would lose coded orders:6,283 test-window rows have no name, but6,064 retain valid HICL;219 have neither. HICL is a native code identity, without an established equivalence to RxNorm or MIMIC labels. Training contains1,306 distinct HICL codes,177 associated with multiple raw names.

'''
        tail='''
词表按训练住院中的编码出现次数排序；覆盖率按去重“住院—编码”对计算。这里只测训练/开发覆盖率，没有计算测试词表覆盖率或选择测试最优容量。正式实验还需冻结缺失药物身份的处理规则、输出字段和相同训练预算。

## 时间审计和解释边界

- 7,768,438条有限数值检验在决策前采样；其中238,680条在决策后修订，预先输入必须排除。7,529,758条同时满足采样和修订时间要求。
- 154,701条用药开始时间在目标窗口，但开立时间不在该窗口。两种时间不能互换。
- 不用最终取消标记过滤目标，因为没有取消时间；本任务预测记录的开立事件，不是最终实际给药或临床最佳处方。
- 药物表没有独立存储时间，完整字段版本历史也缺失；不能宣称已证明前瞻可用性。纳入有用药记录的住院是回顾性记录完整度条件。
- eICU的剂量为字符串，频次单独记录；拟议联合字段与MIMIC剂量/单位任务不同。后续结果必须单独成表。

患者数据、医院映射及成员清单留本地；仓库只存汇总和哈希。来源：[药物表](https://eicu.mit.edu/eicutables/medication/)、[检验表](https://eicu.mit.edu/eicutables/lab/)、[患者表](https://eicu.mit.edu/eicutables/patient/)。
''' if lang=='zh' else '''
Vocabulary ranking uses training-stay code frequency; coverage counts unique stay/code pairs. Only train/development capacity is measured, without test-capacity tuning. A final missing-identity policy, output schema and matched training budgets remain to be frozen.

## Time audit and limits

- Of7,768,438 finite measurements drawn by the decision,238,680 were revised later and must be excluded from early inputs;7,529,758 meet both clocks.
- 154,701 medication rows start within the target window but were ordered outside it. These clocks are not interchangeable.
- Final cancellation flags do not filter targets because cancellation time is absent. The target is recorded order creation, not administration or an optimal prescription.
- Medication storage times and full field histories are unavailable; prospective availability is not established. Requiring medication documentation somewhere in the stay is retrospective selection.
- Dosage strings and separate frequency fields define a different proposed joint-order task from MIMIC dose/unit tuples. Results must remain in a separate panel.

Patient data, hospital mapping and membership remain local; only aggregates and hashes are published. Sources: [medication](https://eicu.mit.edu/eicutables/medication/), [lab](https://eicu.mit.edu/eicutables/lab/), [patient](https://eicu.mit.edu/eicutables/patient/).
'''
        text=intro+table+detail+missing+'\n## Development vocabulary coverage / 开发词表覆盖\n\n'+capacity+tail
        if lang=='en':text=re.sub(r'(?<=[A-Za-z])(?=[0-9])',' ',text).replace('v 0.','v0.').replace('F 1','F1')
        (HERE/f'RESULTS.{lang}.md').write_text(text)

if __name__=='__main__':main()
