"""Author workflows under the same total generated-token allowance.

The allowance is equal; the adaptive numbers of calls and input tokens are not.
Never equate this with exact compute matching. Native full-budget results remain
reported alongside budget exhaustion instead of disappearing from the table.
"""
import argparse,json,sys
from concurrent.futures import ThreadPoolExecutor,as_completed
from common import HERE,RUN,LOCAL,configure,save,sha,digest,ledger_total,ROOT
sys.path.insert(0,str(ROOT/'upgrade_v34'))
from medical_agents import run

def main():
 p=argparse.ArgumentParser();p.add_argument('--method',choices=['medagents','mdagents'],required=True);p.add_argument('--split',choices=['proposal','guard','test','rxqa'],required=True);p.add_argument('--workers',type=int,default=24);a=p.parse_args()
 protocol=configure();data=json.loads((LOCAL/'data.json').read_text());cases=data['transfer'] if a.split=='rxqa' else data['parts'][a.split]
 folder=RUN/a.method/a.split;folder.mkdir(parents=True,exist_ok=True)
 def one(c):
  path=folder/(digest(c['id'])+'.json')
  if path.exists():return json.loads(path.read_text())
  r=run(a.method,c,80,4608);save(path,r);return r
 out={}
 with ThreadPoolExecutor(max_workers=a.workers) as pool:
  for f in as_completed([pool.submit(one,c) for c in cases]):
   r=f.result();out[r['case_id']]=r
   if len(out)%100==0:print(json.dumps({'method':a.method,'split':a.split,'done':len(out),'n':len(cases)}),flush=True)
 rows=[out[c['id']] for c in cases];calls=[x for r in rows for x in r['calls']]
 d={'status':'complete','method':a.method,'split':a.split,'n':len(cases),'correct':sum(r['prediction']==c['gold'] for r,c in zip(rows,cases)),
  'invalid':sum(r['prediction'] is None for r in rows),'statuses':{k:sum(r['status']==k for r in rows) for k in set(r['status'] for r in rows)},
  'model_calls':len(calls),'mean_calls':len(calls)/len(cases),'input_tokens':sum(x['input_tokens'] for x in calls),'output_tokens':sum(x['output_tokens'] for x in calls),'logical_cost_usd':sum(x['cost_usd'] or 0 for x in calls),'total_output_token_ceiling':4608,'maximum_calls':80,
  'adapter_sha256':sha(ROOT/'upgrade_v34/medical_agents.py'),'case_membership_sha256':digest([c['id'] for c in cases]),'predictions_sha256':digest([r['prediction'] for r in rows]),'ledger_increment_usd':ledger_total()-protocol['ledger_start_usd']}
 d['accuracy']=d['correct']/d['n'];save(HERE/'results'/f'{a.method}-{a.split}.json',d);print(json.dumps(d),flush=True)
if __name__=='__main__':main()
