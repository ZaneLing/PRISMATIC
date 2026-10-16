import argparse,json
from concurrent.futures import ThreadPoolExecutor,as_completed
from common37 import RUN,HERE,configure,digest,save,sha,ledger_total
from agent37 import Agent37

def target(c):return sorted(c['gold']) if isinstance(c['gold'],list) else [c['gold']]
def batch(cases,state,split,workers=18):
 agent=Agent37(state);folder=RUN/'runs'/digest(state)/split;folder.mkdir(parents=True,exist_ok=True)
 def one(c):
  p=folder/(digest(c['id'])+'.json')
  if p.exists():return json.loads(p.read_text())
  r=agent.solve({k:c[k] for k in ['id','dialogue','options','multiple'] if k in c});save(p,r);return r
 out={}
 with ThreadPoolExecutor(max_workers=workers) as pool:
  for f in as_completed([pool.submit(one,c) for c in cases]):
   r=f.result();out[r['case_id']]=r
   if len(out)%40==0:print(json.dumps({'stage':split,'state':digest(state)[:8],'done':len(out),'n':len(cases)}),flush=True)
 rows=[out[c['id']] for c in cases];calls=[c for r in rows for c in r['calls']];m={'n':len(cases),'correct':sum(r['prediction']==target(c) for r,c in zip(rows,cases)),'invalid':sum(r['prediction'] is None for r in rows),'calls':len(calls),'input_tokens':sum(c['input_tokens'] for c in calls),'output_tokens':sum(c['output_tokens'] for c in calls),'logical_cost_usd':sum(c['cost_usd'] or 0 for c in calls),'active_cases':sum(bool(r['active_cards']) for r in rows),'predictions_sha256':digest([r['prediction'] for r in rows])};return rows,m

def main():
 p=argparse.ArgumentParser();p.add_argument('--split',required=True);a=p.parse_args();configure();data=json.loads((RUN/'data.json').read_text());f=HERE/'implementation.json';code={k:sha(HERE/k) for k in ['common37.py','evidence37.py','agent37.py','run.py']}
 if f.exists():assert json.loads(f.read_text())==code
 else:save(f,code)
 if a.split.startswith('test'):assert (HERE/'test_freeze.json').exists()
 _,m=batch(data[a.split],{'cards':[]},a.split);save(HERE/'results'/f'initial-{a.split}.json',dict(m,status='complete'));print(json.dumps(m),flush=True)
if __name__=='__main__':main()
