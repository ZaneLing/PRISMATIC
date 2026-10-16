import argparse,json
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
from common import HERE,RUN,LOCAL,configure,save,sha,digest,ledger_total
from active import ActiveAgent

def main():
 p=argparse.ArgumentParser();p.add_argument('--split',choices=['proposal','guard','test','rxqa'],required=True);a=p.parse_args();protocol=configure();data=json.loads((LOCAL/'data.json').read_text());cases=data['transfer'] if a.split=='rxqa' else data['parts'][a.split]
 f=HERE/'active_protocol.json';code={k:sha(HERE/k) for k in ('active.py','run_active.py','workflow.py','evidence.py')}
 if f.exists():assert json.loads(f.read_text())['code_sha256']==code
 else:save(f,{'created_utc':datetime.now(timezone.utc).isoformat(),'code_sha256':code,'design':'Same three1536-token calls; assessment proposes at most5 targeted searches, up to2 additional snippets/query, executed before final decision. No extra model call.','development_gate':'Must beat static verified_evidence on proposal190, then guard197 without invalid increase; fail means no promotion.','updates':'Researcher-authored retrieval orchestration intervention, not autonomous tool-code evolution.'})
 if a.split in ('test','rxqa'):assert (HERE/'test_freeze.json').exists()
 agent=ActiveAgent();folder=RUN/'active_evidence'/a.split;folder.mkdir(parents=True,exist_ok=True)
 def one(c):
  p=folder/(digest(c['id'])+'.json')
  if p.exists():return json.loads(p.read_text())
  r=agent.solve({k:c[k] for k in ('id','dialogue','options')});save(p,r);return r
 out={}
 with ThreadPoolExecutor(max_workers=24) as pool:
  for f in as_completed([pool.submit(one,c) for c in cases]):
   r=f.result();out[r['case_id']]=r
   if len(out)%50==0:print(json.dumps({'arm':'active_evidence','split':a.split,'done':len(out),'n':len(cases)}),flush=True)
 rows=[out[c['id']] for c in cases];calls=[x for r in rows for x in r['calls']]
 d={'status':'complete','arm':'active_evidence','split':a.split,'n':len(rows),'correct':sum(r['prediction']==c['gold'] for r,c in zip(rows,cases)),'invalid':sum(r['prediction'] is None for r in rows),'calls':len(calls),'input_tokens':sum(r['input_tokens'] for r in calls),'output_tokens':sum(r['output_tokens'] for r in calls),'logical_cost_usd':sum(r['cost_usd'] or 0 for r in calls),'with_followup':sum(bool(r['evidence']['followup_ids']) for r in rows),'code_sha256':code,'predictions_sha256':digest([r['prediction'] for r in rows]),'ledger_increment_usd':ledger_total()-protocol['ledger_start_usd']};d['accuracy']=d['correct']/d['n'];save(HERE/'results'/f'active_evidence-{a.split}.json',d);print(json.dumps(d),flush=True)
if __name__=='__main__':main()
