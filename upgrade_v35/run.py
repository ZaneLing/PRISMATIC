import argparse,json
from concurrent.futures import ThreadPoolExecutor,as_completed
from common import HERE,RUN,LOCAL,configure,save,sha,digest,ledger_total
from workflow import Agent

def main():
 p=argparse.ArgumentParser();p.add_argument('--split',choices=['proposal','guard','test','rxqa'],required=True);p.add_argument('--arm',choices=['no_evidence','old_evidence','verified_evidence'],required=True);p.add_argument('--limit',type=int);p.add_argument('--workers',type=int,default=20);a=p.parse_args()
 protocol=configure();data=json.loads((LOCAL/'data.json').read_text());cases=data['transfer'] if a.split=='rxqa' else data['parts'][a.split]
 if a.limit:cases=sorted(cases,key=lambda c:digest(['v35-pilot',c['id']]))[:a.limit]
 if a.split in ('test','rxqa'):assert (HERE/'test_freeze.json').exists(),'Freeze after development gate first'
 code={f:sha(HERE/f) for f in ('workflow.py','evidence.py','run.py')};freeze=HERE/'implementation.json'
 if freeze.exists():assert json.loads(freeze.read_text())==code
 else:save(freeze,code)
 folder=RUN/a.arm/a.split;folder.mkdir(parents=True,exist_ok=True);agent=Agent()
 def one(c):
  path=folder/(digest(c['id'])+'.json')
  if path.exists():return json.loads(path.read_text())
  r=agent.solve({k:c[k] for k in ('id','dialogue','options')},a.arm);save(path,r);return r
 rows={}
 with ThreadPoolExecutor(max_workers=a.workers) as pool:
  for f in as_completed([pool.submit(one,c) for c in cases]):
   r=f.result();rows[r['case_id']]=r
   if len(rows)%25==0:print(json.dumps({'arm':a.arm,'split':a.split,'done':len(rows),'n':len(cases)}),flush=True)
 ordered=[rows[c['id']] for c in cases];calls=[x for r in ordered for x in r['calls']]
 result={'status':'complete','arm':a.arm,'split':a.split,'n':len(cases),'correct':sum(r['prediction']==c['gold'] for r,c in zip(ordered,cases)),
  'invalid':sum(r['prediction'] is None for r in ordered),'calls':len(calls),'input_tokens':sum(r['input_tokens'] for r in calls),'output_tokens':sum(r['output_tokens'] for r in calls),'logical_cost_usd':sum(r['cost_usd'] or 0 for r in calls),
  'case_membership_sha256':digest([c['id'] for c in cases]),'predictions_sha256':digest([r['prediction'] for r in ordered]),'source_code_sha256':code,
  'with_evidence':sum(bool(r['evidence']['excerpts']) for r in ordered),'invalid_verification_checks':sum(r['checks']['invalid_checks'] for r in ordered),
  'ledger_increment_usd':ledger_total()-protocol['ledger_start_usd']}
 result['accuracy']=result['correct']/result['n'];tag='-pilot'+str(a.limit) if a.limit else '';save(HERE/'results'/f'{a.arm}-{a.split}{tag}.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':main()
