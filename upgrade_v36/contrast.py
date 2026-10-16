"""A draft plus explicit factual-contradiction review, developed on MedQA only."""
import argparse,json,os,sys
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
from experiment import HERE,RUN,ROOT,LOCAL,MODEL,save,sha,digest,ledger_total,StudyAgent
from workflow import PLAN,ASSESS,FINAL,verify,routes
from common import json_object
P1=PLAN+'\nAlso supply independent_draft (one option letter) and decisive_claims (at most3 short factual statements). This independent attempt precedes label retrieval. Never infer findings from an image that was not provided.'
P2=ASSESS+'\nPerform an independent challenge of the preliminary draft. Decompose every compound option: all its clauses must be justified. Check direction of effects, required indication, patient qualifiers, dose, frequency, timing and duration separately. Identify any added patient fact (such as NEW symptom) absent from the original input. Do not equate absence from a selected product label with a clinical contraindication or lack of all indications. If a claim needs general medical knowledge outside a label, mark that provenance explicitly. Add JSON fields contradicted_claims:[{claim,reason,source_type}], and option_clause_checks:[{option,unsupported_clause}]. Challenge both the draft and its strongest alternative, rather than assuming the first answer is correct. Do not invent unseen image findings.'
P3=FINAL+'\nArbitrate the independent preliminary draft against the later evidence assessment. Resolve contradictory factual claims explicitly. An exact quotation can still concern the wrong indication, population, formulation, or treatment phase. A missing quotation is not a contradiction. For a compound answer, reject it if one required clause is unsupported; compare with the closest alternative. Answer the actual requested action, distinguishing initiation, continuation, adjustment, monitoring and discontinuation. Do not reinterpret an existing finding as new without textual support. If you change the preliminary draft, state which concrete premise caused the change. Do not infer unprovided images.'

class ContrastAgent(StudyAgent):
 def __init__(self):super().__init__('static_v35')
 def solve(self,c,arm='verified_evidence'):
  text=c['dialogue']+'\nOptions:\n'+'\n'.join(f'{chr(65+i)}. {o}' for i,o in enumerate(c['options']))
  r1=self.call(P1+'\nINPUT:\n'+text,'contrast_plan');plan=json_object(r1['raw']);plan=plan if isinstance(plan,dict) else {}
  plan['facts']=[f for f in plan.get('facts',[]) if isinstance(f,dict) and isinstance(f.get('input_quote'),str) and f['input_quote'] in text]
  es=plan.get('entities',[]);es=es if isinstance(es,list) else []
  for e in es:
   if not isinstance(e,dict):continue
   rq=e.get('route_quote','');rr=e.get('route','')
   if not isinstance(rq,str) or not rq or rq not in text or rr not in routes(rq):e['route']=''
  plan['entities']=es;ev=self.labels.query(c,plan)
  view='\nINPUT:\n'+text+'\nPRELIMINARY DRAFT AND FACTS (fallible):\n'+json.dumps(plan)+'\nLABEL EVIDENCE:\n'+json.dumps(ev)
  r2=self.call(P2+view,'contrast_assess');assessment=json_object(r2['raw']);assessment=assessment if isinstance(assessment,dict) else {};checked=verify(assessment,ev,text)
  r3=self.call(P3+view+'\nASSESSMENT:\n'+json.dumps(assessment)+'\nEXECUTED CHECKS:\n'+json.dumps(checked),'contrast_decide');parsed=json_object(r3['raw']);answer=parsed.get('final') if isinstance(parsed,dict) else None;answer=answer.strip().upper() if isinstance(answer,str) else None
  if answer not in [chr(65+i) for i in range(len(c['options']))]:answer=None
  return {'case_id':c['id'],'prediction':answer,'calls':[r1,r2,r3],'plan':plan,'evidence':ev,'assessment':assessment,'checks':checked,'final':parsed,'arm':'contrastive_review'}

def main():
 p=argparse.ArgumentParser();p.add_argument('--split',choices=['proposal','guard','rxqa'],required=True);a=p.parse_args();protocol=json.loads((HERE/'protocol.json').read_text());os.environ['RXRSI_PUBLIC_COST_CAP_USD']=str(protocol['ledger_start_usd']+10)
 proto=HERE/'contrast_protocol.json'
 if not proto.exists():
  assert a.split=='proposal';save(proto,{'created_utc':datetime.now(timezone.utc).isoformat(),'code_sha256':sha(__file__),'parent_sha256':sha(HERE/'experiment.py'),'design':'Independent draft; fact/option-clause contradiction review; arbitration. Same3x1536 calls and static verified source tool. Conditional on at least one option >6 words.','feedback':'After full-context proposal99/120 tied static99/120, inspected first8 static proposal errors. No RxQA per-item error inspection. Researcher-authored prompt revision, not autonomous tool/skill evolution.','gate':'Strict gain versus static99/120 proposal, then strict gain on untouched guard120 with no invalid increase. Freeze before RxQA.','additional_candidates':1})
 assert json.loads(proto.read_text())['code_sha256']==sha(__file__)
 if a.split=='rxqa':assert (HERE/'test_freeze.json').exists()
 cases=json.loads((LOCAL/'data.json').read_text())['transfer'] if a.split=='rxqa' else json.loads((RUN/'data.json').read_text())[a.split];folder=RUN/'contrastive_review'/a.split;folder.mkdir(parents=True,exist_ok=True);agent=ContrastAgent()
 def one(c):
  path=folder/(digest(c['id'])+'.json')
  if path.exists():return json.loads(path.read_text())
  if a.split=='rxqa' and all(len(o.split())<=6 for o in c['options']):r=json.loads((LOCAL.parent/'rxrsi-v35/verified_evidence/rxqa'/(digest(c['id'])+'.json')).read_text());r=dict(r,v36_route='reuse_frozen_short_option_branch')
  else:r=agent.solve({k:c[k] for k in ('id','dialogue','options')});r['v36_route']='long_option_contrastive_review'
  save(path,r);return r
 out={}
 with ThreadPoolExecutor(max_workers=20) as pool:
  for f in as_completed([pool.submit(one,c) for c in cases]):
   r=f.result();out[r['case_id']]=r
   if len(out)%30==0:print(json.dumps({'split':a.split,'done':len(out),'n':len(cases)}),flush=True)
 rows=[out[c['id']] for c in cases];calls=[x for r in rows for x in r['calls']];d={'status':'complete','arm':'contrastive_review','split':a.split,'n':len(cases),'correct':sum(r['prediction']==c['gold'] for r,c in zip(rows,cases)),'invalid':sum(r['prediction'] is None for r in rows),'calls':len(calls),'input_tokens':sum(r['input_tokens'] for r in calls),'output_tokens':sum(r['output_tokens'] for r in calls),'logical_cost_usd':sum(r['cost_usd'] or 0 for r in calls),'predictions_sha256':digest([r['prediction'] for r in rows]),'with_evidence':sum(bool(r['evidence']['excerpts']) for r in rows),'ledger_increment_usd':ledger_total()-protocol['ledger_start_usd']};d['accuracy']=d['correct']/d['n'];save(HERE/'results'/f'contrastive_review-{a.split}.json',d);print(json.dumps(d),flush=True)
if __name__=='__main__':main()
