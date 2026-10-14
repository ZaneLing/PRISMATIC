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
        if (PAPER/'execution_status.json').exists() and json.loads((PAPER/'execution_status.json').read_text())['api']['status']=='waiting_for_credit':
            block+=('**Execution notice:** new OpenRouter requests returned HTTP402 after the previous recharge. Unfinished API branches retain checkpoints and await credit; completed results and independent local training/audits continue. Missing requests are never scored as model errors.\n\n' if lang=='en' else '**执行状态：** 上次充值后，新OpenRouter请求再次返回HTTP402。未完成的API分支已保存断点，等待补充额度；已完成结果及独立本地训练／审计继续。缺失请求不计作模型错误。\n\n')
        elif (PAPER/'execution_status.json').exists() and json.loads((PAPER/'execution_status.json').read_text())['api']['status']=='restored_actual_completion_verified':
            block+=('**Execution notice:** a real OpenRouter completion verified restored access after recharge. Interrupted studies resume from saved receipts under their original protocols and budgets; missing requests are not model errors.\n\n' if lang=='en' else '**执行状态：** 充值后已用真实OpenRouter响应验证访问恢复。中断实验从原回执继续，保持原协议和预算；缺失请求不计作模型错误。\n\n')
        block+=(f'**Actual training:** {complete}/6 rule runs finish five rounds; {nr}/15 author-model runs finish their full 50 epochs, with {epochs}/750 completed epochs overall. Training/audit queues continue. The final common ATC-L4 test table opens only after all registered choices and audits freeze.\n\n' if lang=='en' else f'**实际运行：** {complete}/6组规则实验完成五轮；作者神经方法{nr}/15组完成各自50轮，总计已完成{epochs}/750轮。训练与审计队列继续，正式ATC-L4测试主表等待全部已登记版本和核验完成后统一运行。\n\n')
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
            block+=('v0.31 runs four arms across three seeds and three rounds: ranked uniform, permuted uniform, permuted own-error and permuted shuffled-error updates. Each round uses the same 400-example/100-step budget. Original retrieval ranks and candidate order fields remain visible. This tests whether weight updates learn drug decisions beyond display position, and whether own errors add value over ordinary training. Candidate tools and order templates stay fixed.\n\n' if lang=='en' else 'v0.31已运行四种方法、三个种子、三轮：原排序普通更新、随机位置普通更新、随机位置自身错误优先、随机位置打乱错误权重。每轮均为400样本／100步，保留原检索排名和候选订单字段。它检验参数更新能否摆脱展示位置依赖，以及自身错误是否比普通学习更有价值。候选工具和订单模板固定。\n\n')
            block+=(f"Completed optimizer runs: **{progress['optimizer_runs_with_complete_receipts']}/36**; fully audited seeds: **{len(progress['seeds_fully_audited'])}/3**. Old test cases are excluded. Proposal selects checkpoints; the reused 200-case guard is exploratory development evidence, not an untouched test.\n\n" if lang=='en' else f"已完成训练回执：**{progress['optimizer_runs_with_complete_receipts']}/36**；完整核验种子：**{len(progress['seeds_fully_audited'])}/3**。排除旧测试病例。proposal选择检查点；复用的200例guard属于探索性开发证据，不是未触碰测试。\n\n")
            p=ROOT/'upgrade_v31/results/audit-seed42.json'
            if p.exists():
                base=json.loads(p.read_text())['base_proposal']
                block+='| State on 100 proposal cases | Ranked drug/order F1 | Permuted drug/order F1 |\n|---|---:|---:|\n'
                block+=f"| Frozen base | {base['ranked']['drug_micro_f1']:.5f}/{base['ranked']['core_order_micro_f1']:.5f} | {base['permuted']['drug_micro_f1']:.5f}/{base['permuted']['core_order_micro_f1']:.5f} |\n\n"
            block+=f'[Actual parameter updates, audit and results](../upgrade_v31/RESULTS.{lang}.md)\n\n'
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
if __name__=='__main__':main()
