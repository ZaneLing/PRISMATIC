"""Publish negative checkpoints, paired contrasts and the feedback receipt limit."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parent

def main():
    summary=json.loads((HERE/'results/summary.json').read_text());raw=json.loads((HERE/'results/parameter_results.json').read_text())
    audit=json.loads((HERE/'results/learning_audit.json').read_text());assert summary['status']=='complete'
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for j,k in enumerate(['drug_micro_f1','core_order_micro_f1']):
        for arm,label in [('uniform_sft','Uniform'),('error_prioritized_sft','Error priority')]:
            accepted=[r['scores'][j] for r in summary['accepted_state_curves'][arm]]
            candidates=[raw['base'][k]]+[r['metrics'][k] for r in raw['arms'][arm]['raw_checkpoint_curve']]
            line=axes[j].plot(range(4),accepted,marker='o',label=label+' accepted')[0]
            axes[j].plot(range(4),candidates,marker='x',ls=':',color=line.get_color(),label=label+' raw')
        tool=summary['methods']['guard_selected_top_k_tools'][['drug_f1','core_order_f1'][j]]
        axes[j].axhline(tool,color='gray',ls='--',label='Direct top-8 tool')
        axes[j].set(xlabel='Round',ylabel=['Drug F1','Core-order F1'][j],xticks=range(4),ylim=(0,None));axes[j].grid(alpha=.2)
    axes[1].legend(fontsize=7);fig.tight_layout();fig.savefig(HERE/'raw_checkpoint_curves.png',dpi=180);plt.close(fig)
    table='| Contrast | Drug Δ (95% CI) | Order Δ (95% CI) |\n|---|---:|---:|\n'
    for key in ['error_prioritized_sft__minus__uniform_sft','error_prioritized_sft__minus__guard_selected_top_k_tools']:
        v=summary['paired'][key];ci=v['patient_cluster_ci95'];delta=v['drug_order_difference']
        table+=f'| {key} | {delta[0]:+.5f} [{ci[0][0]:+.5f}, {ci[1][0]:+.5f}] | {delta[1]:+.5f} [{ci[0][1]:+.5f}, {ci[1][1]:+.5f}] |\n'
    for lang in ['en','zh']:
        header='## Completed findings and failure diagnosis' if lang=='en' else '## 完整结论与失败诊断'
        text='''
Both arms select round 2 before testing. Error prioritization improves over uniform updating by 0.05098 drug F1 and 0.04257 order F1, with positive descriptive patient-cluster intervals. It still trails direct top-8 tools by 0.01977/0.01410, with negative intervals. This is one learning seed, not a robust superiority result. Equal sample/step budgets do not equal target-token budgets across the ID and binary representations.

The raw priority checkpoint in round 1 emits either all-zero or all-one masks (70.8%/29.2%). Round 2 has 16 distinct masks, with 99% consisting of an initial run of ones followed only by zeros; only 34% of GT masks have that pattern. Round 3 emits all zeros on both guard and test and is rejected on guard. Its zero is valid parsed model output, not a transport or parser failure. The accepted curve is flat after round 2 because selection protects it; the underlying model has not improved monotonically. Candidate-order/cardinality bias is a post-hoc diagnosis, not an isolated causal explanation.

Independent auditing confirms six actual adapter hashes, all six 100-step logs, the 400 selected training rows per round, target masks, selection decisions and all saved test predictions. However, 10 of 3,600 pre-update feedback records cannot be reconstructed exactly from the current input-keyed cache: duplicate-input generations could overwrite each other. The original recorded weights and resulting sampled memberships are preserved and verified; the missing individual feedback generations are not invented. This limits complete training-trace reproducibility, without changing the independently recounted test scores. Fresh runs must deduplicate identical generation requests and preserve immutable case-bound feedback receipts.

''' if lang=='en' else '''
两臂均在测试前选择第 2 轮。错误优先较普通更新提高药物 F1 0.05098、订单 F1 0.04257，患者聚类描述性区间均为正；仍比直接 top-8 工具低 0.01977/0.01410，区间均为负。这里只有一个学习种子，不能宣称稳健最优。ID 与二元表示的样本/步数相同，但目标 token 预算不同。

错误优先第 1 轮仅输出全零或全一，比例 70.8%/29.2%；第 2 轮有 16 种掩码，99% 都是“前若干候选全选、后面不选”，GT 仅 34% 有这种形状。第 3 轮在 guard 和 test 都全零，被 guard 拒绝。零输出是有效解析后的模型选择，不是 API 或解析失败。接纳曲线第 2 轮后保持不变来自版本选择保护，底层模型并非单调进步。候选顺序/数量偏差只是事后诊断，尚未隔离因果原因。

独立核验了 6 个实际适配器哈希、6 次 100 步日志、每轮 400 条实际训练输入/标签、选择决策和全部保存的测试预测。但 3,600 条更新前反馈中有 10 条无法从现有输入缓存精确恢复：重复输入曾分别生成，缓存可能覆盖了先前结果。原始权重和对应采样成员保留且可核对，不补造缺失的逐例原始输出。这限制完整训练轨迹复现，不改变已独立重算的测试成绩。新实验必须去重生成请求并保存逐例不可变反馈回执。

'''
        p=HERE/f'RESULTS.{lang}.md';prior=p.read_text().split('\n'+header)[0]
        p.write_text(prior+'\n'+header+'\n'+text+table+'\n![Raw candidates versus accepted versions](raw_checkpoint_curves.png)\n\n'+('Audit: `results/learning_audit.json`. No test-based checkpoint reselection was performed.\n' if lang=='en' else '审计见 `results/learning_audit.json`。没有根据测试结果重选检查点。\n'))

if __name__=='__main__':main()
