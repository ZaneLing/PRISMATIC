"""Uniform decoder replay plus newly gated trajectories; no additional inference."""
from common52 import *
from skills import *
from decoder_development import replay
from evaluate import summarize
def main():
 lock=json.loads((HERE/'results/decoder_freeze.json').read_text());assert sha(HERE/'runtime_decoder.py')==lock['decoder_sha256']
 changed={'qwen':replay('qwen','audit'),'llama':replay('llama','audit')};cases=json.loads((PRIVATE/'audit.json').read_text());q=json.loads((PRIVATE/'qwen-compatible-audit.json').read_text());base=[r['orders'] for r in q];curves={};arms={'fixed_qwen_compatible':summarize(base,cases)}
 for name,h in lock['states'].items():
  path=PRIVATE/(name+'-states.json');assert sha(path)==h;states=json.loads(path.read_text());curve=[]
  for i,s in enumerate(states):
   pp=predict(cases,base,s);curve.append(dict(round=i,seen=32*i,skills=len(s),metrics=metrics(pp,cases)))
  arms[name]=summarize(pp,cases,base);curves[name]=curve
 state=json.loads((PRIVATE/'qwen-compatible-52-states.json').read_text())[-1]
 static=base
 for op in OPS:static=[operate(c,p,op) for c,p in zip(cases,static)]
 arms['compatible_static_all_repairs']=summarize(static,cases,base)
 lr=json.loads((PRIVATE/'llama-compatible-audit.json').read_text());lc=cases[:len(lr)];lb=[r['orders'] for r in lr]
 arms['fixed_llama_compatible']=summarize(lb,lc);arms['llama_compatible_transfer']=summarize(predict(lc,lb,state),lc,lb)
 save(HERE/'results/decoder_evaluation.json',dict(status='completed_uniform_runtime_repair_and_regated_learning',original_primary_replaced=False,changed_rows=changed,arms=arms,curves=curves,new_llm_calls=0))
 print(json.dumps({n:{'drug_f1':x['all']['drug_f1'],'joint_f1':x['all']['joint_f1']} for n,x in arms.items()},indent=2),flush=True)
if __name__=='__main__':main()
