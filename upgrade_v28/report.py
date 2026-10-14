"""Maintain bilingual results using only independently audited cells."""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main():
    s=json.loads((HERE/'results/summary.json').read_text())
    for lang in ['en','zh']:
        text=('''# v0.28 — Answer contracts and evidence-preserving tool statistics

## 1. Question and registered comparison

The v0.19 failures motivate two fixed execution repairs: **C**, an instruction-derived answer schema with budgeted rejection/retry; **S**, paginated Observation retrieval and source-bound latest/24h arithmetic grouped by code and unit. **K** is the unchanged pair of v0.19 learned skills. All8 combinations are registered before their execution. Neither C nor S is autonomously evolved code.

All conditions keep the same backbone, eight actor calls and512 output tokens per call, real FHIR service and original task/reference logic. Additional paging HTTP calls and token costs are reported. Schema rejection requests another model decision; it never extracts a favorable value after scoring. Complete page receipts support each statistic; missing units/times and future/non-numeric values are flagged. No dose or clinical guideline is invented by the reducer.

All splits were used in prior work: this is a post-test-motivated exploratory repair study. All conditions remain fixed; validation/test scores do not promote a winner. Model/API cache reuse is exact; logical costs are not fresh physical-spend estimates. The shared ledger includes concurrent studies.

## 2. Audited actual results

''' if lang=='en' else '''# v0.28：答案协议与保留证据的工具汇总

## 1. 问题与已登记对照

针对v0.19失败实现两项固定修复：**C**＝从任务文字确定答案schema，不合规时在原预算内反馈重答；**S**＝分页获取Observation，再按编码和单位分别计算最近值／24小时统计，绑定真实来源。**K**＝原样冻结的v0.19两项技能。八种组合在各自执行前登记，C/S不冒充自主进化代码。

各方法保持相同模型、最多八次actor调用、每次512输出token、真实FHIR服务与原任务/评分逻辑。额外分页HTTP调用及token成本另报。schema失败会要求模型再次决策，不在评分后提取有利答案；统计绑定完整分页回执，缺单位/时间、未来/非数值记录明确标记，不推导新剂量或临床指南。

各划分此前已使用，因此这是由已见错误启发的探索性修复；所有组合固定，不根据验证/测试挑选胜者。精确API缓存可复用，逻辑费用不等于新增物理支出，共享账本还包含同时运行的其他试验。

## 2. 已独立核验的真实结果

''')
        text+=f"Status / 状态：**{s['status']}**. Pending / 未完成 cells are not scored as zero.\n\n"
        text+='| C: schema | S: statistics | K: frozen skills | Validation /80 | ID /64 | Held-out types /60 |\n|---|---|---|---:|---:|---:|\n'
        for c in [0,1]:
            for st in [0,1]:
                for k in [0,1]:
                    z=s['conditions'].get(f'C{c}S{st}K{k}',{}).get('splits',{})
                    values=[str(z[x]['state_correct']) if x in z else 'pending' for x in ['val','id_test','test']]
                    text+=f"| {c} | {st} | {k} | {' | '.join(values)} |\n"
        if s['paired']:
            text+='\n| Split | Declared contrast | Difference (pp) | Patient/query-cluster interval (pp) |\n|---|---|---:|---:|\n'
            for split,pairs in s['paired'].items():
                for name,z in pairs.items():
                    lo,hi=z['patient_ci95'];text+=f"| {split} | {name} | {100*z['difference']:+.2f} | [{100*lo:+.2f}, {100*hi:+.2f}] |\n"
            text+=('\nValidation has 62 explicit patients plus two deliberately nonexistent-patient lookup queries; those queries form separate resampling units (64 total). No patient ID is invented. Both test splits have complete explicit patient identities.\n' if lang=='en' else '\n验证集包含62位显式患者及两道特意查询不存在患者的题目；两题各作独立查询重采样单元，共64个单元，不虚构患者编号。两个测试划分均有完整显式患者编号。\n')
        text+=('\nOnly completed cells that pass independent reference regrading, persisted-field/cleanup checks and raw-page arithmetic reconstruction appear above. One frozen run per condition, overlapping patients and descriptive intervals do not establish general RSI superiority. The earlier v0.19 table remains unchanged.\n' if lang=='en' else '\n上表只填已完成且通过独立复评分、字段回读/清理及原始分页算术重建的单元。每组合一次固定运行、患者重叠和描述性区间不能证明普遍RSI优势。v0.19原主表不变。\n')
        text+='\n## Evidence / 证据\n\n- [Preregistered factorial](protocol.json)\n- [Executed runtime probes](results/runtime_probe.json)\n- [Independent cell audits and contrasts](results/summary.json)\n- [Full execution counts](results/method_results.json)\n'
        (HERE/f'RESULTS.{lang}.md').write_text(text)
if __name__=='__main__':main()
