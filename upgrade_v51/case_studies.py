"""Readable private examples; only aggregate/hashes leave the restricted directory."""
import json
from common import *
def fmt(os):
 return '\n'.join('- '+o['drug_name']+' | '+str(o.get('route'))+' | '+str(o.get('dose_value'))+' '+str(o.get('dose_unit'))+' | frequency/day '+str(o.get('frequency_per_24h')) for o in os) or '- (empty / 空)'
def main():
 old=json.loads((PRIVATE/'selected-historical-training-cases.json').read_text());notes=[
 ('候选库外漏药 / Candidate exclusion','GT 的药物未进入候选集合，后续推理无权选中。修复方向是扩展候选召回，并分别测候选覆盖和最终选择。 / The target is unavailable to the actor; repair recall before expecting downstream reasoning to select it.'),
 ('库内漏选 / Candidate present but omitted','目标已在候选中，模型却选择其他药；不能用扩容解释这类错误。输入缺乏症状、诊断等信息，额外抗菌药选择相对于记录不符，但不能仅凭 GT 宣判临床不适宜。 / Selection fails despite available candidates; missing indications remain unresolved.'),
 ('药物正确但订单字段错误 / Correct drug, wrong joint fields','同名药物被选中但剂量模板与 GT 不同，药名 F1 会掩盖此差距。现有试验仍冻结联合订单模板，尚未实现自主剂量工具更新。 / Name agreement hides a joint-order error; joint templates remain frozen in the current bounded repair pilot.')]
 lines=['# 真实失败病例 / Real failure cases','仅限本地受限目录；按失败类型挑选，不能估计总体发生率。以下是历史训练病例，非新测试集调参案例。记录处方作为行为 GT，不等于唯一正确治疗。 / Restricted local training illustrations, deliberately selected by failure type; not clinical advice or a random sample.']
 for i,(c,(title,note)) in enumerate(zip(old,notes),1):
  ctx=c['available_context'];lines += [f'## {i}. {title}',f'本地案例标识 / local key: `{c["case_id"]}`',
   '### 当时可见信息 / Available inputs',f'已有订单 {len(ctx["recorded_prior_orders"])} 条，可用检验 {len(ctx["available_labs"])} 条；没有已验证的实时诊断字段。 / Prior orders and recorded laboratory values only; no verified contemporaneous diagnosis field.',
   '### GT / Recorded target',fmt(c['reference']),'### Agent prediction / 实际输出',fmt(c['before']),
   '### 根因与修复 / Root cause and repair',note,'### 原始输入供核对 / Input for local verification','```json\n'+json.dumps(ctx,ensure_ascii=False,indent=2)+'\n```']
 # New training interventions: first gain/loss within retained and rejected edits; no checkpoint selection.
 examples=[]
 learning_path=PRIVATE/'learning.json'
 if learning_path.exists():
  learning=json.loads(learning_path.read_text());data=load_cases();examples=[]
  for r in learning['rounds'][1:]:
   cs=data['train'][(r['round']-1)*24:r['round']*24];before=json.loads((PRIVATE/f'train-{r["round"]}-before.json').read_text())['rows']
   for j,t in enumerate(r['trials']):
    p=PRIVATE/f'train-{r["round"]}-trial-{j}.json'
    if not p.exists():continue
    after=json.loads(p.read_text())['rows']
    for c,a,z in zip(cs,before,after):
     da=score([a['orders']],[c['gold']])['drug_micro_f1'];dz=score([z['orders']],[c['gold']])['drug_micro_f1'];direction='improvement' if dz>da else 'regression' if dz<da else 'equal'
     if direction!='equal' and (direction,t['accepted']) not in [(e['direction'],e['accepted']) for e in examples]:examples.append({'direction':direction,'case':c,'before':a,'after':z,'round':r['round'],'operator':t['card']['operator'],'accepted':t['accepted'],'before_f1':da,'after_f1':dz})
    if t['accepted']:before=after
  for e in examples:
   lines += ['## New training '+('retained ' if e['accepted'] else 'rejected ')+e['direction']+' / 新训练干预案例',f'Round {e["round"]}; operator {e["operator"]}; globally retained {e["accepted"]}; F1 {100*e["before_f1"]:.2f}% → {100*e["after_f1"]:.2f}%.',
    '### Observed input',e['case']['input'],'### GT',fmt(e['case']['gold']),'### Before',fmt(e['before']['orders']),'### After',fmt(e['after']['orders']),
    '个例改善不证明技能泛化；个例退步也保留供审计。 / Per-case gain does not establish generalization; regressions are retained.']
 path=PRIVATE/'CASE_STUDIES.bilingual.md';path.write_text('\n\n'.join(lines)+'\n');save(HERE/'results/case_manifest.json',{'historical_illustrations':3,'intervention_illustrations':len(examples),'selection':'first improvement/regression in each of retained/rejected training intervention strata; nonrandom illustrations','sha256':sha(path),'restricted_path':str(path),'patient_content_published':False})
if __name__=='__main__':main()
