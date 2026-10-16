import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/"upgrade_v37"))
from concurrent.futures import ThreadPoolExecutor,as_completed
from common37 import RUN,HERE,configure,digest,save,sha,ledger_total
from agent40 import Agent40
BASE_RUN=RUN
RUN=BASE_RUN.parent/"rxrsi-v40";RUN.mkdir(exist_ok=True)

def target(c):return sorted(c['gold']) if isinstance(c['gold'],list) else [c['gold']]
def batch(cases,state,split,workers=18):
 agent=Agent40(state);folder=RUN/'runs'/digest(state)/split;folder.mkdir(parents=True,exist_ok=True)
 def one(c):
  p=folder/(digest(c['id'])+'.json')
  if p.exists():return json.loads(p.read_text())
  prior=BASE_RUN/'runs'/digest(state)/split/(digest(c['id'])+'.json')
  if not state.get('cards') and prior.exists():
   r=json.loads(prior.read_text());save(p,r);return r
  r=agent.solve({k:c[k] for k in ['id','dialogue','options','multiple'] if k in c});save(p,r);return r
 out={}
 with ThreadPoolExecutor(max_workers=workers) as pool:
  for f in as_completed([pool.submit(one,c) for c in cases]):
   r=f.result();out[r['case_id']]=r
   if len(out)%40==0:print(json.dumps({'stage':split,'state':digest(state)[:8],'done':len(out),'n':len(cases)}),flush=True)
 rows=[out[c['id']] for c in cases];calls=[c for r in rows for c in r['calls']];m={'n':len(cases),'correct':sum(r['prediction']==target(c) for r,c in zip(rows,cases)),'invalid':sum(r['prediction'] is None for r in rows),'calls':len(calls),'input_tokens':sum(c['input_tokens'] for c in calls),'output_tokens':sum(c['output_tokens'] for c in calls),'logical_cost_usd':sum(c['cost_usd'] or 0 for c in calls),'active_cases':sum(bool(r['active_cards']) for r in rows),'predictions_sha256':digest([r['prediction'] for r in rows])};return rows,m

