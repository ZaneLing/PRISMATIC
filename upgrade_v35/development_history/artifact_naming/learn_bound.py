"""Four rounds of error-driven procedural memory on the improved evidence agent.

Researcher source fixes are distinct from these autonomous language-card updates.
No test label enters proposals, acceptance or the selected state.
"""
import argparse,json,random,re
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from common import HERE,RUN,LOCAL,configure,save,sha,digest,request,json_object,MODEL
from workflow import Agent

class MemoryAgent(Agent):
 def __init__(self,cards):super().__init__();self.cards=cards
 def call(self,prompt,role):
  if self.cards and role in ('rx35_assess','rx35_decide'):
   view=[{k:c[k] for k in ('name','applies_when','exclude_when','procedure')} for c in self.cards]
   prompt+='\nTRAINING-DERIVED PROCEDURES: apply only when the stated positive conditions hold and no exclusion holds. They are fallible experience, never a source of medical facts; current input and applicable label evidence take priority. Do not follow a procedure just because a drug name is familiar.\n'+json.dumps(view)
  return super().call(prompt,role)

def batch(cases,cards,split):
 agent=MemoryAgent(cards);key=digest(cards);folder=RUN/'memory'/key/split;folder.mkdir(parents=True,exist_ok=True)
 def one(c):
  path=folder/(digest(c['id'])+'.json')
  # An empty memory has exactly the previously frozen base prompts.
  base=RUN/'verified_evidence'/split/(digest(c['id'])+'.json')
  if not cards and base.exists():return json.loads(base.read_text())
  if path.exists():return json.loads(path.read_text())
  r=agent.solve({k:c[k] for k in ('id','dialogue','options')},'verified_evidence');save(path,r);return r
 out={}
 with ThreadPoolExecutor(max_workers=24) as pool:
  for f in as_completed([pool.submit(one,c) for c in cases]):
   r=f.result();out[r['case_id']]=r
   if len(out)%50==0:print(json.dumps({'stage':split,'state':key[:8],'done':len(out),'n':len(cases)}),flush=True)
 rows=[out[c['id']] for c in cases]
 return rows,{'correct':sum(r['prediction']==c['gold'] for r,c in zip(rows,cases)),'n':len(cases),'invalid':sum(r['prediction'] is None for r in rows),'state_sha256':key}

def propose(seen,feedback,cards,round_no):
 by={r['case_id']:r for r in feedback};errors=[c for c in seen if by[c['id']]['prediction']!=c['gold']];success=[c for c in seen if by[c['id']]['prediction']==c['gold']]
 errors=sorted(errors,key=lambda c:digest(['v35-proposal',round_no,c['id']]))[:8]
 selected={c['id']:c for c in errors}
 if success:
  vec=TfidfVectorizer(stop_words='english');matrix=vec.fit_transform([c['dialogue']+' '+' '.join(c['options']) for c in success])
  for c in errors:
   sim=(matrix@vec.transform([c['dialogue']+' '+' '.join(c['options'])]).T).toarray()[:,0];close=success[int(np.argmax(sim))];selected[close['id']]=close
 items=[];support=[];counter=[]
 for c in selected.values():
  r=by[c['id']];bad=r['prediction']!=c['gold'];(support if bad else counter).append(c['id'])
  items.append({'id':c['id'],'role':'SUPPORT_ERROR' if bad else 'COUNTEREXAMPLE_SUCCESS','question':c['dialogue'],'options':c['options'],'reference':c['gold'],'prediction':r['prediction'],'decision_summary':r['final'],'source_products':r['evidence'].get('products',[]),'tool_flags':r['evidence'].get('flags',[])})
 prompt='''Learn at most TWO short procedural skills from the training feedback. Target causes of mistakes in interpreting applicable drug-label evidence, patient facts, indication, scope, route, dose or comparing options. Never memorize option positions, drug-specific answer mappings, synthetic-generation artifacts or unsupported drug facts. Reference labels may be ambiguous: do not create a clinically implausible rule merely to mimic a label. A useful skill explains when to apply AND when NOT to apply. Every card needs a SUPPORT_ERROR and a distinct COUNTEREXAMPLE_SUCCESS case; no other IDs. Preserve existing cards. Return JSON {"cards":[{"name":"...","applies_when":"observable condition","exclude_when":"specific contrary condition","procedure":"bounded steps grounded in sources","support_ids":["..."],"counterexample_ids":["..."]}],"diagnosis":"short"}.'''
 prompt+='\nExisting skills:\n'+json.dumps(cards)+'\nTraining feedback:\n'+json.dumps(items)
 prompt+='\nMissing warnings or indications in retrieved excerpts never prove safety or lack of efficacy. Skills should request missing evidence or preserve uncertainty rather than treat missing text as a negative clinical fact.\nAllowed support IDs: '+json.dumps(support)+'\nAllowed counterexample IDs: '+json.dumps(counter)
 messages=[{'role':'user','content':prompt}];attempts=[];valid=[]
 for attempt in range(2):
  r=request(messages,MODEL,2048,role='rx35_bound_skill_proposal')
  if r.get('error'):raise RuntimeError('Proposal transport incomplete')
  attempts.append(r);obj=json_object(r['raw']);raw=obj.get('cards',[]) if isinstance(obj,dict) else [];current=[];rejected=0
  for c in raw[:2] if isinstance(raw,list) else []:
   if not isinstance(c,dict) or not all(isinstance(c.get(k),str) and c[k].strip() for k in ('name','applies_when','exclude_when','procedure')):rejected+=1;continue
   pos=c.get('support_ids',[]);neg=c.get('counterexample_ids',[])
   if not isinstance(pos,list) or not isinstance(neg,list) or not pos or not neg:rejected+=1;continue
   if not all(i in support for i in pos) or not all(i in counter for i in neg):rejected+=1;continue
   current.append({k:c[k] for k in ('name','applies_when','exclude_when','procedure','support_ids','counterexample_ids')})
  if len(current)>=len(valid):valid=current
  if rejected==0:break
  messages += [{'role':'assistant','content':r['raw']},{'role':'user','content':'Schema repair only: support_ids must come from '+json.dumps(support)+'; counterexample_ids must come from '+json.dumps(counter)+'. Return complete cards respecting these roles. Do not change a clinical procedure merely to mimic an ambiguous label.'}]
 return (cards+valid)[-6:],{'attempts':attempts,'accepted_schema_cards':len(valid),'support_pool':support,'counterexample_pool':counter}


def main():
 p=argparse.ArgumentParser();p.add_argument('--stage',choices=['learn','test','rxqa'],default='learn');a=p.parse_args();configure();data=json.loads((LOCAL/'data.json').read_text());parts=data['parts'];folder=RUN/'learning_bound';folder.mkdir(exist_ok=True)
 proto=HERE/'learning_bound_protocol.json'
 if not proto.exists():save(proto,{'created_utc':datetime.now(timezone.utc).isoformat(),'code_sha256':sha(HERE/'learn_bound.py'),'seed':42,'cases_seen':[0,156,312,468,625],'changes':'procedural cards only; model, source-tool code, three-call allowance and verifier fixed','admission':'Strictly improve proposal190 with no extra invalids, then guard197 with no extra invalids against incumbent; otherwise retain incumbent','test':'Freeze whole trajectory before inference, use final retained state; no test-based selection','development_amendment':'Initial four-round trajectory rejected all updates; explicit allowed-role pools and one schema repair added before any new main-agent test inference. Initial trajectory retained.', 'limitation':'One training order; reused development and guard; added memory input tokens, same3x1536 output allowance.'})
 assert json.loads(proto.read_text())['code_sha256']==sha(HERE/'learn_bound.py')
 state_path=folder/'states.json';feedback_path=folder/'feedback.json'
 if a.stage!='learn':
  assert (HERE/'test_freeze.json').exists();states=json.loads(state_path.read_text());assert len(states)==5
  cases=parts['test'] if a.stage=='test' else data['transfer'];rows,m=batch(cases,states[-1]['cards'],a.stage);save(HERE/'results'/f'learned_bound-{a.stage}.json',{**m,'status':'complete','cards':states[-1]['cards'],'predictions_sha256':digest([r['prediction'] for r in rows])});print(json.dumps(m));return
 train=list(parts['train']);random.Random(42).shuffle(train)
 if state_path.exists():states=json.loads(state_path.read_text());feedback=json.loads(feedback_path.read_text())
 else:
  _,p0=batch(parts['proposal'],[],'proposal');_,g0=batch(parts['guard'],[],'guard');states=[{'round':0,'cases_seen':0,'cards':[],'proposal':p0,'guard':g0}];feedback=[];save(state_path,states);save(feedback_path,feedback)
 bounds=[0,156,312,468,625]
 for round_no in range(len(states),5):
  prev=states[-1];cases=train[bounds[round_no-1]:bounds[round_no]];rows,tm=batch(cases,prev['cards'],'train');feedback+=rows;save(feedback_path,feedback)
  candidate,receipt=propose(train[:bounds[round_no]],feedback,prev['cards'],round_no);save(folder/f'proposal-{round_no}.json',receipt)
  _,pm=batch(parts['proposal'],candidate,'proposal');gm=None
  gate1=pm['correct']>prev['proposal']['correct'] and pm['invalid']<=prev['proposal']['invalid']
  if gate1:_,gm=batch(parts['guard'],candidate,'guard')
  accepted=bool(gate1 and gm['correct']>prev['guard']['correct'] and gm['invalid']<=prev['guard']['invalid'])
  state={'round':round_no,'cases_seen':bounds[round_no],'cards':candidate if accepted else prev['cards'],'candidate_cards':candidate,'accepted':accepted,'train':tm,'candidate_proposal':pm,'candidate_guard':gm,'proposal':pm if accepted else prev['proposal'],'guard':gm if accepted else prev['guard']}
  states.append(state);save(state_path,states);save(HERE/'results/learning_progress.json',{'status':'running','rounds':states});print(json.dumps({'round':round_no,'accepted':accepted,'proposal':pm,'guard':gm}),flush=True)
 save(HERE/'results/learning.json',{'status':'frozen','frozen_utc':datetime.now(timezone.utc).isoformat(),'rounds':states,'protocol_sha256':sha(proto)})
if __name__=='__main__':main()
