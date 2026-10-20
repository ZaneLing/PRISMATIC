"""Update durable indexes after completed reports; retain full-cohort scores."""
import json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent

def main():
 c=json.loads((HERE/'results/cloud/controls_transfer.json').read_text());l=json.loads((HERE/'results/cloud/learning.json').read_text());local=json.loads((HERE/'results/trajectory.json').read_text());cost=json.loads((HERE/'results/cost.json').read_text());assert c['complete'] and l['complete'] and local['complete']
 decoder=json.loads((HERE/'results/decoder_replay.json').read_text());q=c['methods']['qwen'];fmt=lambda x:f'{100*x:.2f}';spent=cost['api_cost_usd']
 for lang in ['zh','en']:
  zh=lang=='zh';p=ROOT/f'paper/CURRENT_RESULTS.{lang}.md';old=p.read_text()
  marker='<!-- REPAIR_PILOT_END -->'
  if marker in old:old=old.split(marker,1)[1].lstrip()
  title='## 最新修复试验：2026-10-20' if zh else '## Latest repair pilot: 2026-10-20'
  lines=[title,
   '候选覆盖缺口已分解：18.87% 的 GT 药物实例被 128 词表排除，29.51% 在词表内但被前24截断排除。已接入候选检索扩展、明确执行的适用/排除条件、根因—操作检查、无效修改检测和累计反思。' if zh else 'Candidate loss is decomposed: 18.87% of GT drug instances are outside the 128-name vocabulary and 29.51% are inside it but pruned by top24. Repairs add executable candidate/evidence actions, explicit conditions and exceptions, root/action compatibility, no-op checks and cumulative reflection.',
   f'72 个反思病例，三轮各24；提案24、守门32；冻结后审计48。较强汇总反思器保留 {l["rounds"][-1]["retained"]} 个技能，审计药物 F1 {fmt(q["initial"]["drug_micro_f1"])}% → {fmt(q["selected"]["drug_micro_f1"])}%；四字段 F1 {fmt(q["initial"]["core_order_micro_f1"])}% → {fmt(q["selected"]["core_order_micro_f1"])}%。' if zh else f'Three rounds reuse 72 reflection admissions; proposal24, guard32, post-freeze audit48. The stronger aggregate proposer retains {l["rounds"][-1]["retained"]} skills. Audit drug F1: {fmt(q["initial"]["drug_micro_f1"])}% → {fmt(q["selected"]["drug_micro_f1"])}%; Core4: {fmt(q["initial"]["core_order_micro_f1"])}% → {fmt(q["selected"]["core_order_micro_f1"])}%.',
   (f'统一完整数组解码重放后，最终药物F1为 {fmt(decoder["methods"]["qwen_retained"]["replayed"]["drug_micro_f1"])}%；恢复的5份输出均没有新增GT命中。该工程修复与原始学习结果分开披露，未重新选择技能状态。' if zh else f'After uniform complete-array decoding replay, final drug F1 is {fmt(decoder["methods"]["qwen_retained"]["replayed"]["drug_micro_f1"])}%. Five restored outputs add no GT hits. This engineering repair is separate from the original learning result; states are not reselected.'),
   f'本地反思器保留 {local["trajectory"][-1]["retained"]} 个技能；固定工程组合和 Llama 迁移对照均已完成。小样本审计复用历史测试病例，不替代下方1,082例主表，不证明单调进化或临床有效。累计错误记忆不等于能力提升。' if zh else f'The local-proposer control retains {local["trajectory"][-1]["retained"]} skills. Static-tool and Llama-transfer controls are complete. This small historically exposed audit does not replace the 1,082-admission main table below or prove monotonic/clinical improvement. Growing error memory is not itself capability growth.',
   f'本轮新增 API 花费 USD {spent:.6f} / 10；仅汇总统计发送给提案模型，患者记录保留本地。' if zh else f'New API cost: USD {spent:.6f} / 10. Only aggregate statistics reach the proposer; patient records remain local.',
   f'[完整修复结果 / Repair results](../upgrade_v51/RESULTS.{lang}.md) · [逐轮记录 / Trajectory](../upgrade_v51/results/cloud/trajectory.json) · [代码与复现 / Code](../upgrade_v51/README.md)',
   '---',marker]
  p.write_text('\n\n'.join(lines)+'\n\n'+old)
  report=(HERE/f'RESULTS.{lang}.md').read_text()
  report=re.sub(r'\]\((?!https?://|/|#)([^)]+)\)',lambda m:'](../../upgrade_v51/'+m.group(1)+')',report)
  (ROOT/f'paper/versions/v0.51-2026-10-20.{lang}.md').write_text(report)
 p=ROOT/'README.md';s=p.read_text();head='## Current repair pilot — 2026-10-20\n\n'+f'Candidate coverage loss is attributed to the 128-name vocabulary and top-24 truncation. The repaired updater now changes candidate recall, evidence tools and conditional procedural memory. Three-round studies compare local and aggregate-only stronger proposers on the same 72 training admissions, with a separate 48-admission exploratory audit. New paid API spend: USD {spent:.6f} / USD 10. These pilot scores do not replace the full 1,082-admission table.\n\n'+ '- [中文修复结果](upgrade_v51/RESULTS.zh.md) · [English repair results](upgrade_v51/RESULTS.en.md) · [Code and protocol](upgrade_v51/README.md).\n\n'
 if '## Current repair pilot' not in s:s=s.replace('## Current evidence — 2026-10-17',head+'## Complete-cohort evidence — 2026-10-17')
 s=s.replace('**Incremental paid API spend: USD 0 / USD 10 authorized.**','**The complete-cohort local experiment incurred USD 0 in API charges; the new repair pilot cost is reported above.**');p.write_text(s)
 p=ROOT/'paper/README.md';s=p.read_text().replace('Updated 2026-10-17','Updated 2026-10-20');s=s if '## Latest updater repair' in s else s.replace('## Read first','## Latest updater repair\n\n[Chinese results](../upgrade_v51/RESULTS.zh.md) · [English results](../upgrade_v51/RESULTS.en.md) · [Frozen round trajectory](../upgrade_v51/results/cloud/trajectory.json). The 48-case exploratory pilot is separate from the full-cohort table; it includes a local-proposer control, static repair bundle and cross-model transfer.\n\n## Read first');s=s.replace('USD 0 new paid API spend;',f'USD {spent:.6f} new proposer API spend;');p.write_text(s)
 for lang in ['zh','en']:
  p=ROOT/f'paper/TOTAL_COST.{lang}.md';s=p.read_text();marker='<!-- UPDATER_REPAIR_COST -->'
  if marker in s:s=s.split(marker,1)[0].rstrip()
  paragraph=(f'本轮新增提案 API 账单 USD {spent:.6f}，在授权 USD 10 内；与此前已定位约 USD 89.53 的账单分开计量。本地 Qwen/Llama 计算时间未计价。费用证据为 `upgrade_v51/results/cost.json`；提案请求只发送汇总统计，没有患者记录。' if lang=='zh' else f'Provider-reported proposer receipts: USD {spent:.6f}, within the USD 10 authorization. This increment is additional to the earlier approximately USD 89.53 located receipts. Local Qwen/Llama compute is unpriced. Aggregate-only requests are audited in `upgrade_v51/results/cost.json`; no patient records were sent.')
  s+='\n\n'+marker+'\n\n## 2026-10-20 updater repair increment\n\n'+paragraph+'\n';p.write_text(s)
 print('Durable indexes and versioned bilingual results updated.')
if __name__=='__main__':main()
