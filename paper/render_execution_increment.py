"""Update a stable bilingual entry block from executed, audited artifacts."""
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
        block+=(f'**Actual training:** {complete}/6 rule runs finish five rounds; {nr}/15 author-model runs finish their full 50 epochs, with {epochs}/750 completed epochs overall. Training/audit queues continue. The final common ATC-L4 test table opens only after all registered choices and audits freeze.\n\n' if lang=='en' else f'**实际运行：** {complete}/6组规则实验完成五轮；作者神经方法{nr}/15组完成各自50轮，总计已完成{epochs}/750轮。训练与审计队列继续，正式ATC-L4测试主表等待全部已登记版本和核验完成后统一运行。\n\n')
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
2. Complete every registered ARMR/GAMENet/SafeDrug run at 50 epochs. The implemented queue reloads each selected checkpoint, audits development predictions, then opens one shared test gate. The evaluator includes conventional methods, all six rule arms, every frozen round and three artifact interventions. Test results cannot retune the methods.
3. Finish the eight-condition real-FHIR C/S/K factorial across 80 validation, 64 ID and 60 held-out-type tasks. Report every condition, original strict scores, resource integrity, budgets and paired effects. Audit raw-page arithmetic; do not replace old results with posthoc value extraction.
4. Continue the eICU external-hospital study already running. Preserve zero-target stays and frozen selection. This supplies a separate transport test, not a directly pooled ATC score.
5. The next registered improvement must address the measured shortfall: tiny rule gains, no established advantage over greedy/shuffled evidence, restricted rule expressivity, and non-nested witness reuse. Add a strong calibration/conditional-rule control and a genuinely isolated witness design before claiming a language-agent benefit. Register any larger mechanism before fitting; reserve untouched confirmation for final claims.
6. Keep the existing English LaTeX source, bilingual results entry and versioned reports synchronized. Only completed audited experiments enter score tables; compilation and GitHub pushes are checked explicitly.

''' if lang=='en' else '''## 当前执行队列：具体交付状态

1. 规则记忆机制已实现并真实运行：两种ATC-L4空间、三个种子、五轮病例增长、六种方法。完成交叉拟合、候选、witness和预测的独立核验，保留所有编辑决定及原始曲线。
2. ARMR／GAMENet／SafeDrug各组完成已登记50轮。已实现的队列逐组重新加载所选检查点、核验开发预测，之后统一开启测试。评估器包含传统方法、六种规则方法、全部冻结轮次和三项对象干预；测试结果不用于调参。
3. 完成真实FHIR的C/S/K八组合：80验证、64同类、60未见任务类型。报告每组合原严格成绩、真实资源完整性、预算和配对效果；重建原始分页算术，不用事后提取数值替换旧分数。
4. 继续已启动的eICU跨医院实验，保留零目标病例和冻结版本。它是独立迁移测试，不能直接混入ATC主表。
5. 下一次登记改进要针对实测不足：规则收益小、尚未证明优于贪心／打乱证据、规则表达有限、witness并非嵌套隔离。加入强校准／条件规则对照和真正隔离的witness设计，再检验语言agent的额外贡献。更大机制必须在拟合前登记，最终结论预留未触碰确认集。
6. 持续同步现有英文LaTeX、中英文总览及版本报告；只有完成且核验的实验填分数，并确认编译和GitHub同步。

''')
        plan+=f'[Current actual results](CURRENT_RESULTS.{lang}.md) · [Rule study](../upgrade_v27/RESULTS.{lang}.md) · [FHIR repair](../upgrade_v28/RESULTS.{lang}.md)\n\n'
        plan+=('Earlier entries below are historical snapshots.\n' if lang=='en' else '下方较早条目是历史状态快照。\n')
        update(PAPER/('COMPLETION_PLAN.en.md' if lang=='en' else 'COMPLETION_PLAN.md'),plan)
    readme=f'''## Current execution snapshot

The rule-memory study completes **{complete}/6 five-round runs**; genuine author-model baselines complete **{nr}/15 full 50-epoch runs** ({epochs}/750 epochs saved). Independent development audits quantify the small memory increment against greedy/random/shuffled controls. A common test evaluator is implemented and stays closed until every selection and audit freezes.

The real-FHIR factorial executes fixed answer-contract/statistics repairs and frozen learned skills in all eight combinations. This is exploratory execution repair, not autonomous tool-code evolution. All completed audited cells, costs and limits are maintained in the reports.

[中文当前结果与方法对照](paper/CURRENT_RESULTS.zh.md) · [English current results](paper/CURRENT_RESULTS.en.md) · [Rule mechanism and rounds](upgrade_v27/RESULTS.en.md) · [FHIR repair](upgrade_v28/RESULTS.en.md)

Earlier paragraphs below describe retained study versions; this snapshot governs current execution status.
'''
    update(ROOT/'README.md',readme)
if __name__=='__main__':main()
