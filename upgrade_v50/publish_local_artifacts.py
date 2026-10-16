"""Refresh current bilingual indexes after real experiments complete."""
import json,datetime
from common import *

def main():
    status=json.loads((HERE/'results/pipeline_status.json').read_text());assert status['complete']
    audit=json.loads((HERE/'results/audit.json').read_text());m=audit['methods']['rxrsi_selected']['metrics']
    learning=json.loads((HERE/'results/learning_scope.json').read_text());n=len(learning['selected_state']['cards'])
    date=datetime.date.today().isoformat();pct=lambda x:f'{100*x:.2f}'
    for lang in ['en','zh']:
        current=ROOT/f'paper/CURRENT_RESULTS.{lang}.md';archive=ROOT/f'paper/versions/qa-results-before-local-2026-10-16.{lang}.md'
        if not archive.exists():archive.write_text(current.read_text())
        new=(HERE/f'RESULTS.{lang}.md').read_text()
        if lang=='en':
            intro=f'# RxRSIAgent: current experimental evidence\n\nUpdated {date}. Local order results below are new; public-QA results remain unchanged.\n\n'
            qa='''\n## 10. Public-QA results retained alongside the order task

| Method | RxSafe 988 | RxQA 300 | Output allowance |
|---|---:|---:|---:|
| GRASP task adaptation | 50.10% | 61.67% | 4,608 |
| MedAgents task adaptation | 46.76% | 66.67% | 4,608 |
| MDAgents task adaptation | 48.08% | 65.67% | 4,608 |
| Supervised calibration control | 56.28% | 66.33% | 4,608 |
| **RxRSIAgent (hosted QA adapter)** | **49.70%** | **65.33%** | **4,608** |
| MedAgents, higher allowance | 47.37% | 69.33% | 24,000 |

MedPIC remains 274/467 (58.67%), with 3/35 strict pairs both correct. The QA learner retained zero changes. These are different tasks and backbones from the local MIMIC table; accuracy is not prescription recall. Two-QA-benchmark superiority remains unachieved.

[Earlier detailed QA record](versions/qa-results-before-local-2026-10-16.en.md) · [English ACL source](latex/v0.3/prismatic_v03_en.tex) · [Local reproduction](../upgrade_v50/README.md).
'''
        else:
            intro=f'# RxRSIAgent：当前实验结果\n\n更新日期：{date}。下面是新完成的本地处方实验；此前公开选择题结果保持不变。\n\n'
            qa='''\n## 十、同时保留公开选择题结果

| 方法 | RxSafe 988 | RxQA 300 | 输出额度 |
|---|---:|---:|---:|
| GRASP 任务适配 | 50.10% | 61.67% | 4,608 |
| MedAgents 任务适配 | 46.76% | 66.67% | 4,608 |
| MDAgents 任务适配 | 48.08% | 65.67% | 4,608 |
| 普通监督校准对照 | 56.28% | 66.33% | 4,608 |
| **RxRSIAgent（公开QA适配）** | **49.70%** | **65.33%** | **4,608** |
| MedAgents，高额度 | 47.37% | 69.33% | 24,000 |

MedPIC仍为274/467（58.67%），35组严格配对中3组两题全对。QA学习轨迹未保留变化。这里的任务和底座与本地MIMIC处方表不同，选择题准确率不是处方覆盖率；两个QA bench同时超过最强对照仍未实现。

[此前完整QA档案](versions/qa-results-before-local-2026-10-16.zh.md) · [英文ACL论文](latex/v0.3/prismatic_v03_en.tex) · [本地复现实验](../upgrade_v50/README.md)。
'''
        body=new.split('\n',1)[1]
        current.write_text(intro+body+qa+'\n![Local prescription results](../upgrade_v50/figures/prescription_results.svg)\n')
    root_readme=ROOT/'README.md';old=root_readme.read_text();original=old[old.index('## Original 2025 project description'):]
    head=f'''# RxRSIAgent — PRISMATIC research repository

## Current evidence — {date}

**New complete local MIMIC-IV experiment: 1,082 admissions. RxRSIAgent drug F1 {pct(m['drug_micro_f1'])}%; Core4 F1 {pct(m['core_order_micro_f1'])}%.** The corrected-interface trajectory retains {n} conditional update(s); paired intervals, component ablations and frozen-state transfer are reported. This is a catalogue-constrained local Qwen3-4B prescription adapter.

- [中文完整结果与跨方法主表](paper/CURRENT_RESULTS.zh.md) · [Full English results](paper/CURRENT_RESULTS.en.md).
- [Local experiment and comparator fidelity](upgrade_v50/README.md) · [aggregate audit](upgrade_v50/results/audit.json) · [round trajectory](upgrade_v50/results/round_curve.json).
- [English ACL manuscript](paper/latex/v0.3/prismatic_v03_en.tex) · [paper index and archives](paper/README.md).
- [Prescription actor](upgrade_v50/actor.py) · [frozen prescription state](upgrade_v50/test_freeze_scope.json).
- [Hosted QA actor](rxrsiagent/selected_agent.py) · [QA profile](rxrsiagent/selected_profile.json).

SafeRx-Agent is a limited independent task adaptation; SkeMex executes the pinned author memory core with a common actor; FLAME transfers the actual released trained list-policy component. Complete original workflows are not reproduced, and no superiority over the original papers is claimed. Published reference scores stay in a separate protocol-qualified file.

Public QA remains RxSafe 491/988 (49.70%), RxQA 196/300 (65.33%), and MedPIC 274/467 (58.67%). The QA learner retains no change. Historical supervised calibration is a separate control.

**Incremental paid API spend: USD 0 / USD 10 authorized.** Restricted records, raw responses, private case studies and checkpoints stay local. Local compute is unpriced; historical located response expenditure remains about USD 89.53. Older queues remain paused.

---

'''
    root_readme.write_text(head+original)
    index=ROOT/'paper/README.md';old=index.read_text();versions=old[old.index('## Versions'):]
    row='| v0.50 | [Local prescription experiment](versions/v0.50-2026-10-17.en.md) · [中文](versions/v0.50-2026-10-17.zh.md) | 1,082 MIMIC admissions; qualified SafeRx/SkeMex/FLAME adapters; sequential updates, transfer and diagnostics |\n'
    if '| v0.50 |' not in versions:versions=versions.replace('| --- | --- | --- |\n','| --- | --- | --- |\n'+row,1)
    index.write_text(f'''# RxRSIAgent: manuscript and evidence index

Target: ACL 2027. Updated {date}. Only the English ACL manuscript is maintained, in its original editor path.

## Read first

- [中文当前结果](CURRENT_RESULTS.zh.md) · [Current English results](CURRENT_RESULTS.en.md).
- [English ACL source](latex/v0.3/prismatic_v03_en.tex) · [evidence manifest](latex/v0.3/manuscript_evidence.json) · [compile check](latex/v0.3/compile_check.json).
- [Complete local prescription experiment](../upgrade_v50/README.md) · [audit](../upgrade_v50/results/audit.json) · [frozen state](../upgrade_v50/test_freeze_scope.json).
- [Earlier public-QA details](versions/qa-results-before-local-2026-10-16.en.md) · [historical cost audit](TOTAL_COST.en.md).

## Where the evidence appears

| Question | Manuscript location | Evidence |
|---|---|---|
| Complete workflows | QA and local prescription figures | Inputs, candidate tool, evidence, checks, output and update gates |
| Prescription comparison | Local structured-prescription table | 1,082 cases; Direct, SafeRx adaptation, SkeMex memory core, RxRSIAgent |
| FLAME | Separate component table | Released trained list policy and its fixed initializer; no full-method claim |
| What evolves | Local trajectory and component tables | Procedural card and bounded verifier scope; weights/code fixed |
| Transfer | Local order subsection | Frozen memory, Qwen to Llama, all 1,082 cases |
| Failure mechanisms | Cases and intervention paragraphs | Format failures, candidate coverage, fact scope, evidence removal, position sensitivity |
| Earlier public QA | Named-agent table and independent task | RxSafe, RxQA, MedPIC; unchanged QA state |
| Costs | Appendix and local expenditure | USD 0 new paid API spend; approximately USD 89.53 historical receipts |

Local prescription drug/Core4 F1 is {pct(m['drug_micro_f1'])}/{pct(m['core_order_micro_f1'])}%. Acceptance and measured test improvement are separate claims. Clinical effectiveness, full author-method superiority and model-independent benefit are not established. Restricted case-level examples remain local.

'''+versions)
    print('Updated bilingual current results and repository indexes')
if __name__=='__main__':main()
