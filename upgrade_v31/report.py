"""Maintain bilingual local-training progress and audited development results."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v31'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    data=json.loads((HERE/'results/data_audit.json').read_text());audits={};states={};trained=sorted(PRIVATE.glob('seed*/*-round*/training_complete.json'));completed=sorted(PRIVATE.glob('seed*/*-round*/complete.json'));raws=list((PRIVATE/'inference-v2/raw').glob('*.json'))
    for seed in [42,137,2026]:
        p=HERE/f'results/audit-seed{seed}.json'
        if p.exists():
            z=json.loads(p.read_text());assert z['auditor_sha256']==sha(HERE/'audit_learning.py');audits[seed]=z
        p=HERE/f'results/seed{seed}.json'
        if p.exists():states[seed]=json.loads(p.read_text())
    progress={'optimizer_runs_with_complete_receipts':len(trained),'updates_with_completed_proposal_scoring':len(completed),'unique_model_responses_saved':len(raws),'seeds_fully_audited':[s for s,z in audits.items() if z['status']=='passed'],'api_calls':0,'test_inference':False}
    (HERE/'results/progress.json').write_text(json.dumps(progress,indent=2)+'\n')
    for lang in ['en','zh']:
        text=('''# v0.31 — Parameter evolution with randomized candidate positions

## 1. Motivation and implemented comparison

The prior v0.26 diagnostic found near-universal display-prefix selection in the trained adapters. This local experiment keeps original retrieval ranks, candidate identities and order fields visible while randomizing display positions during supervision. It separates a representation repair from error-specific learning using four arms: ranked uniform, permuted uniform, permuted own-error priority and permuted shuffled-error priority.

Each of three seeds receives three600-case patient blocks in a declared order. Every round samples400 accumulated admissions without replacement and performs100 QLoRA steps, batch4, updating the last eight layers of the same Qwen3-4B backbone. A model predicts each new block before those outputs generate sampling priorities. Earlier priorities retain their original pre-update errors; the study does not rescore every earlier case. Fixed candidate tools and recorded order templates do not evolve.

Checkpoint selection uses100 proposal admissions under ranked and permuted views, including base as an option. Training continues from each latest raw adapter. Only after all four arms freeze three rounds does a seed evaluate all raw checkpoints on the200-case report-only guard under ranked, permuted and reversed views. The500 old test admissions are excluded; these are exploratory development results on the legacy admission-proxy task, with incomplete entry-time provenance and no novel dose generation.

## 2. Execution and data integrity

''' if lang=='en' else '''# v0.31：随机候选位置下的参数进化

## 1. 动机与已实现对照

v0.26发现训练后的适配器几乎总是选择展示在前面的连续一段。本次本地实验保留原检索排名、候选药物身份和完整订单字段，只在监督训练时随机化展示位置。四种方法区分表示修复与错误反馈的作用：原排序普通训练、随机位置普通训练、随机位置自身错误优先、随机位置打乱错误权重。

三个种子各按已登记顺序接收三批600例患者互不交叉的反馈病例。每轮从累积病例中不放回抽取400次住院，进行100步、批量4的QLoRA更新，使用相同Qwen3-4B骨干的最后八层。模型先预测新病例，再根据这些输出计算抽样优先级；早期病例保留当时的更新前错误，不冒充每轮重新评估全部旧病例。候选工具和记录订单模板不进化。

用100例proposal在原排序及打乱排序两个视图上选择检查点，基础模型也是候选；训练始终从最新原始适配器继续。每个种子的四种方法均完成三轮并冻结后，才对200例报告用guard运行全部原始检查点，比较原排序、随机排序、倒序。原500例测试病例不再纳入。本版属于既往入院代理任务上的探索性开发实验，仍有录入时间证据不完整的局限，不生成新剂量。

## 2. 真实执行与数据完整性

''')
        text+=f"- Completed optimizer runs / 已完成训练回执：**{len(trained)}/36**\n- Updates with completed proposal evaluation / 已完成proposal评价的更新：**{len(completed)}/36**\n- Unique local model responses saved / 已保存本地唯一模型响应：**{len(raws)}**\n- Audited complete seeds / 已完整核验种子：**{len(progress['seeds_fully_audited'])}/3**\n\n"
        text+=(f"The data audit checks{data['views_checked']:,} transformed views with zero patient-role overlap, unchanged candidate sets/GT and no target truncation. The longest complete sequence has{data['max_sequence_tokens']} tokens against a1,536-token limit; each target has69 tokens. Eleven synthetic execution checks cover target transport, prompt blindness, shuffled-weight identity and loss masking. These are integrity checks, not performance gains.\n\n" if lang=='en' else f"数据核验覆盖{data['views_checked']:,}个展示版本：患者角色无交叉、候选集合和真值保持一致、目标未截断。最长完整序列{data['max_sequence_tokens']}个token，低于1,536上限；每个目标69个token。十一项合成执行检查覆盖标签重排、提示不含真值、打乱权重分布和损失掩码；这些是完整性检查，不是性能提升。\n\n")
        text+=('Before any generation/fitting, a synthetic probe confirmed that the installed trainer included one trailing padded target per sequence. All four arms use the same strict completion-only loss excluding that position, via a wrapper that leaves the installed library unchanged. This does not identify the cause of the historical collapse; the new ranked-uniform control shares the correction.\n\n' if lang=='en' else '在生成／拟合前，合成探针证实已安装训练器每个序列会额外监督一个末尾填充目标。四臂统一采用排除该位置的完整回答损失，通过包装器传入，不修改已安装库。该发现不证明它导致了历史训练崩溃；本版原排序普通训练对照也采用相同修正。\n\n')
        if audits:
            text+=('## 3. Independently recounted proposal results\n\nProposal scores select checkpoints and are not test results.\n\n' if lang=='en' else '## 3. 独立复算的proposal结果\n\nproposal用于选择检查点，不是测试成绩。\n\n')
            text+='| Seed | Arm | Raw round | Ranked drug/order F1 | Permuted drug/order F1 | Accepted round so far |\n|---:|---|---:|---:|---:|---:|\n'
            for seed,a in audits.items():
                v=a['base_proposal'];text+=f"| {seed} | base | 0 | {v['ranked']['drug_micro_f1']:.5f}/{v['ranked']['core_order_micro_f1']:.5f} | {v['permuted']['drug_micro_f1']:.5f}/{v['permuted']['core_order_micro_f1']:.5f} | 0 |\n"
                for arm,rows in a['arms'].items():
                    for r in rows:
                        v=r['proposal'];text+=f"| {seed} | {arm} | {r['round']} | {v['ranked']['drug_micro_f1']:.5f}/{v['ranked']['core_order_micro_f1']:.5f} | {v['permuted']['drug_micro_f1']:.5f}/{v['permuted']['core_order_micro_f1']:.5f} | {r['active_round']} |\n"
        finished={s:z for s,z in audits.items() if z['status']=='passed'}
        if finished:
            text+='\n## 4. Audited selected-state guard results\n\n| Seed | Method | Selected round | View | Drug/order F1 | Empty (%) | Nontrivial display-prefix (%) |\n|---:|---|---:|---|---:|---:|---:|\n'
            for seed,a in finished.items():
                for arm,chosen in a['frozen_selection']['arms'].items():
                    name='base' if chosen['round']==0 else f'{arm}-round{chosen["round"]}'
                    for condition,z in a['guard'][name].items():
                        fraction=z['display_prefix_fraction'];pf='NA (no nontrivial mask)' if fraction is None else f'{100*fraction:.1f}'
                        text+=f"| {seed} | {arm} | {chosen['round']} | {condition} | {z['drug_micro_f1']:.5f}/{z['core_order_micro_f1']:.5f} | {100*z['empty_fraction']:.1f} | {pf} |\n"
                for name,z in a['direct_controls'].items():text+=f"| {seed} | {name} | fixed | all views | {z['drug_micro_f1']:.5f}/{z['core_order_micro_f1']:.5f} | {100*z['empty_fraction']:.1f} | NA |\n"
        text+=('\nUnfinished guard cells and pooled patient intervals remain pending completion/audit; no best-method claim is made from running jobs. For each completed update, audits check source receipts, sampled examples, finite changed adapter tensors and 100-step logs. The floating-point optimizer trajectory is not independently refit.\n' if lang=='en' else '\n未完成guard单元与汇总患者区间等待完成与核验；不根据运行中的任务宣称最优。对每次完成的更新，逐项核验源回执、抽样样本、变化且有限的适配器张量与100步日志；不声称独立重跑浮点优化轨迹。\n')
        text+='\n## Artifacts / 交付\n\n- [Frozen protocol](protocol.json)\n- [Actual data audit](results/data_audit.json)\n- [Synthetic runtime checks](results/runtime_probe.json)\n- [Execution progress](results/progress.json)\n- [Earlier position diagnosis](../upgrade_v26/RESULTS.en.md)\n'
        (HERE/f'RESULTS.{lang}.md').write_text(text)
if __name__=='__main__':main()
