"""Factorial updater audit: original predictions and original study remain unchanged."""
from common52 import *
from skills import *
from evaluate import summarize
def main():
 lock=json.loads((HERE/'results/refined_freeze.json').read_text());assert sha(HERE/'learn_refined.py')==lock['source_sha256']
 cases=json.loads((PRIVATE/'audit.json').read_text());qr=json.loads((PRIVATE/'qwen-audit.json').read_text());base=[r['orders'] for r in qr];out={}
 for name,h in lock['states'].items():
  path=PRIVATE/(name+'-states.json');assert sha(path)==h;states=json.loads(path.read_text());curve=[]
  for i,state in enumerate(states):
   pp=predict(cases,base,state);curve.append({'round':i,'seen':i*32,'skills':len(state),'exception_clauses':sum(len(s['unless']) for s in state),'metrics':metrics(pp,cases)})
  out[name]={'final':summarize(pp,cases,base),'curve':curve,'state':states[-1]}
 save(HERE/'results/refined_evaluation.json',{'status':'completed_exploratory_amendment','original_primary_replaced':False,'audit_used_for_selection':False,'variants':out})
 print(json.dumps({n:{'rules':len(v['state']),'drug_f1':v['final']['all']['drug_f1'],'joint_f1':v['final']['all']['joint_f1']} for n,v in out.items()},indent=2),flush=True)
if __name__=='__main__':main()
