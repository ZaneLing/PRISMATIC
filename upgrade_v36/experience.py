"""Train-only medical-example retrieval; no evaluation answers enter memory."""
import argparse,json,os,sys,re
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor,as_completed
import pyarrow.parquet as pq
from sklearn.feature_extraction.text import TfidfVectorizer
from experiment import HERE,RUN,ROOT,LOCAL,save,sha,digest,ledger_total,StudyAgent
from workflow import PLAN,ASSESS,FINAL,verify,routes
from common import json_object
MEMORY_RULE='''Training examples below are fallible task demonstrations, not drug-label evidence or facts about this patient. Use only a transferable mechanism whose indication and patient conditions match the current question. Explicitly reject differences in population, treatment phase or question intent. Do not copy an answer by medication name or letter. Resolve the present options using the present patient facts. Never cite a training answer as authoritative product labeling.'''

def norm(s):return ' '.join(re.findall(r'[a-z0-9]+',s.lower()))
class ExperienceAgent(StudyAgent):
 def __init__(self):
  super().__init__('static_v35');d=json.loads((RUN/'data.json').read_text());p=json.loads((LOCAL/'data.json').read_text());exclude={norm(c['dialogue']) for cs in [*d.values(),*p['parts'].values(),p['transfer']] for c in cs};prior=LOCAL.parent/'rxrsi-v34/medqa200.json'
  if prior.exists():
   old=json.loads(prior.read_text());old=old['cases'] if isinstance(old,dict) else old;exclude.update(norm(c.get('dialogue','')) for c in old)
  self.memory=[];seen=set()
  for rr in pq.read_table(RUN/'medqa_train.parquet').to_pylist():
   row=rr['data'];q=row['Question'];n=norm(q)
   if n in exclude or n in seen:continue
   seen.add(n);self.memory.append({'question':q,'options':row['Options'],'reference':row['Correct Option']})
  self.memory.sort(key=lambda x:digest(x['question']));self.vector=TfidfVectorizer(stop_words='english',ngram_range=(1,2),sublinear_tf=True,max_features=120000);self.matrix=self.vector.fit_transform([x['question']+' '+ ' '.join(x['options'].values()) for x in self.memory]);self.manifest={'n':len(self.memory),'sha256':digest(self.memory),'retriever':'TF-IDF word1-2gram,sublinear,max_features120000;top3 by input-only similarity;no benchmark answer lookup'}
 def solve(self,c,arm='verified_evidence'):
  text=c['dialogue']+'\nOptions:\n'+'\n'.join(f'{chr(65+i)}. {o}' for i,o in enumerate(c['options']))
  r1=self.call(PLAN+'\nINPUT:\n'+text,'rx35_plan');plan=json_object(r1['raw']);plan=plan if isinstance(plan,dict) else {};plan['facts']=[f for f in plan.get('facts',[]) if isinstance(f,dict) and isinstance(f.get('input_quote'),str) and f['input_quote'] in text];es=plan.get('entities',[]);es=es if isinstance(es,list) else []
  for e in es:
   if not isinstance(e,dict):continue
   rq=e.get('route_quote','');rr=e.get('route','')
   if not isinstance(rq,str) or not rq or rq not in text or rr not in routes(rq):e['route']=''
  plan['entities']=es;ev=self.labels.query(c,plan);scores=(self.matrix@self.vector.transform([c['dialogue']+' '+ ' '.join(c['options'])]).T).toarray()[:,0];ix=sorted(range(len(scores)),key=lambda i:(-scores[i],i))[:3];memory=[dict(self.memory[i],similarity=float(scores[i]),id=digest(self.memory[i]['question'])) for i in ix]
  view='\nINPUT:\n'+text+'\nEXTRACTED FACTS (fallible):\n'+json.dumps(plan)+'\nLABEL EVIDENCE:\n'+json.dumps(ev)+'\nTRAINING EXAMPLES:\n'+json.dumps(memory)+'\n'+MEMORY_RULE
  r2=self.call(ASSESS+view,'memory_assess');assessment=json_object(r2['raw']);assessment=assessment if isinstance(assessment,dict) else {};checked=verify(assessment,ev,text);r3=self.call(FINAL+view+'\nASSESSMENT:\n'+json.dumps(assessment)+'\nEXECUTED CHECKS:\n'+json.dumps(checked),'memory_decide');parsed=json_object(r3['raw']);answer=parsed.get('final') if isinstance(parsed,dict) else None;answer=answer.strip().upper() if isinstance(answer,str) else None
  if answer not in [chr(65+i) for i in range(len(c['options']))]:answer=None
  return {'case_id':c['id'],'prediction':answer,'calls':[r1,r2,r3],'plan':plan,'evidence':ev,'memory':memory,'assessment':assessment,'checks':checked,'final':parsed,'arm':'training_memory'}

def main():
 p=argparse.ArgumentParser();p.add_argument('--split',choices=['proposal','guard','rxqa'],required=True);a=p.parse_args();protocol=json.loads((HERE/'protocol.json').read_text());os.environ['RXRSI_PUBLIC_COST_CAP_USD']=str(protocol['ledger_start_usd']+10);proto=HERE/'experience_protocol.json'
 if not proto.exists():
  assert a.split=='proposal';save(proto,{'created_utc':datetime.now(timezone.utc).isoformat(),'code_sha256':sha(__file__),'design':'TF-IDF retrieval of3 prior MedQA training examples, excluding evaluation/development texts. Static source workflow and3x1536output. No extra LLM call. Only long-option inputs.','gate':'Strictly beat static99/120 proposal then static guard120, no invalid increase. No RxQA test if fail.','training_budget_difference':'Uses additional external training examples; this is not an equal-training-data comparison with named agents.','motivation':'Generic medical factual confusions persisted after full-context and contrastive-review candidates each tied99/120. No RxQA per-item errors used.','candidate_count_including_this':3})
 assert json.loads(proto.read_text())['code_sha256']==sha(__file__)
 if a.split=='rxqa':assert (HERE/'test_freeze.json').exists()
 agent=ExperienceAgent();mp=HERE/'memory_manifest.json'
 if mp.exists():assert json.loads(mp.read_text())==agent.manifest
 else:save(mp,agent.manifest)
 cases=json.loads((LOCAL/'data.json').read_text())['transfer'] if a.split=='rxqa' else json.loads((RUN/'data.json').read_text())[a.split];folder=RUN/'training_memory'/a.split;folder.mkdir(parents=True,exist_ok=True)
 def one(c):
  path=folder/(digest(c['id'])+'.json')
  if path.exists():return json.loads(path.read_text())
  if a.split=='rxqa' and all(len(o.split())<=6 for o in c['options']):r=json.loads((LOCAL.parent/'rxrsi-v35/verified_evidence/rxqa'/(digest(c['id'])+'.json')).read_text());r=dict(r,v36_route='reuse_frozen_short_option_branch')
  else:r=agent.solve({k:c[k] for k in ('id','dialogue','options')});r['v36_route']='long_option_training_memory'
  save(path,r);return r
 out={}
 with ThreadPoolExecutor(max_workers=20) as pool:
  for f in as_completed([pool.submit(one,c) for c in cases]):
   r=f.result();out[r['case_id']]=r
   if len(out)%30==0:print(json.dumps({'split':a.split,'done':len(out),'n':len(cases)}),flush=True)
 rows=[out[c['id']] for c in cases];calls=[x for r in rows for x in r['calls']];d={'status':'complete','arm':'training_memory','split':a.split,'n':len(cases),'correct':sum(r['prediction']==c['gold'] for r,c in zip(rows,cases)),'invalid':sum(r['prediction'] is None for r in rows),'calls':len(calls),'input_tokens':sum(r['input_tokens'] for r in calls),'output_tokens':sum(r['output_tokens'] for r in calls),'logical_cost_usd':sum(r['cost_usd'] or 0 for r in calls),'predictions_sha256':digest([r['prediction'] for r in rows]),'with_evidence':sum(bool(r['evidence']['excerpts']) for r in rows),'ledger_increment_usd':ledger_total()-protocol['ledger_start_usd']};d['accuracy']=d['correct']/d['n'];save(HERE/'results'/f'training_memory-{a.split}.json',d);print(json.dumps(d),flush=True)
if __name__=='__main__':main()
