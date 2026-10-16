"""Development candidate: targeted second retrieval within the same three calls."""
import json,re
import numpy as np
from common import json_object
from workflow import Agent,PLAN,ASSESS,FINAL,verify
from evidence import routes,norm

class ActiveAgent(Agent):
 def targeted(self,ev,queries):
  out=json.loads(json.dumps(ev));added=[]
  byname={p['name']:p for p in ev.get('products',[])}
  existing={z['quote'] for z in ev['excerpts']}
  for q in queries[:5] if isinstance(queries,list) else []:
   if not isinstance(q,dict):continue
   name=norm(q.get('name',''));focus=q.get('focus','')
   if name not in byname or not isinstance(focus,str) or not focus.strip():continue
   product=byname[name]
   if product['route_status']=='conflict':continue
   labs=self.labels.products(name,product.get('requested_route',''));ranked=[]
   for l in labs:
    if product.get('requested_route') and product['requested_route'] not in routes(' '.join((l.get('openfda') or {}).get('route',[]))):continue
    chunks,vec,x=self.labels.chunks(l)
    if not chunks:continue
    scores=(x@vec.transform([focus]).T).toarray()[:,0]
    for i in np.argsort(-scores,kind='stable')[:2]:ranked.append((float(scores[i]),chunks[int(i)],l))
   ranked.sort(key=lambda x:(-x[0],x[1]['label_id'],x[1]['section'],x[1]['offset']))
   count=0
   for score,z,l in ranked:
    if score<=0 or z['quote'] in existing:continue
    # A follow-up may use another formulation, explicitly identify its own route.
    z=dict(z,name=name,option=product['option'],evidence_id='E'+str(len(out['excerpts'])+1),retrieval_stage='targeted_followup',query=focus,source_routes=routes(' '.join((l.get('openfda') or {}).get('route',[]))))
    out['excerpts'].append(z);existing.add(z['quote']);added.append(z['evidence_id']);count+=1
    if count>=2:break
  out['followup_ids']=added;return out
 def solve(self,c,arm='active_evidence'):
  text=c['dialogue']+'\nOptions:\n'+'\n'.join(f'{chr(65+i)}. {o}' for i,o in enumerate(c['options']))
  r1=self.call(PLAN+'\nINPUT:\n'+text,'rx35_plan');plan=json_object(r1['raw']);plan=plan if isinstance(plan,dict) else {}
  facts=plan.get('facts',[]);plan['facts']=[f for f in facts if isinstance(f,dict) and isinstance(f.get('input_quote'),str) and f['input_quote'] in text] if isinstance(facts,list) else []
  entities=plan.get('entities',[]);entities=entities if isinstance(entities,list) else []
  for e in entities:
   if not isinstance(e,dict):continue
   rq=e.get('route_quote','');rr=e.get('route','')
   if not isinstance(rq,str) or not rq or rq not in text or rr not in routes(rq):e['route']=''
  plan['entities']=entities;ev=self.labels.query(c,plan)
  def view(evidence):return '\nINPUT:\n'+text+'\nEXTRACTED FACTS (fallible):\n'+json.dumps(plan)+'\nLABEL EVIDENCE:\n'+json.dumps(evidence)
  instruction=ASSESS+'''\nAlso return "followup_queries":[{"name":"EXACT product name in the supplied product list","focus":"precise missing fact: dose interval, route, named co-medication AND its pharmacologic class, contraindication or population"}]. Request up to5 targeted label searches for facts that could change the choice. This second search is actually executed before final decision. Do not merely repeat the diagnosis; use specific concepts missing from initial excerpts. Do not infer an undocumented patient condition. Do not treat a product's label excerpt as exhaustive.'''
  r2=self.call(instruction+view(ev),'rx35_active_assess');assessment=json_object(r2['raw']);assessment=assessment if isinstance(assessment,dict) else {}
  expanded=self.targeted(ev,assessment.get('followup_queries',[]));checked=verify(assessment,expanded,text)
  r3=self.call(FINAL+view(expanded)+'\nASSESSMENT:\n'+json.dumps(assessment)+'\nEXECUTED CHECKS:\n'+json.dumps(checked)+'\nThe targeted follow-up evidence may correct the draft. Each excerpt is scoped to its stated product and source route; do not generalize a route-specific warning to all formulations.','rx35_active_decide')
  parsed=json_object(r3['raw']);answer=parsed.get('final') if isinstance(parsed,dict) else None;answer=answer.strip().upper() if isinstance(answer,str) else None
  if answer not in [chr(65+i) for i in range(len(c['options']))]:answer=None
  return {'case_id':c['id'],'prediction':answer,'calls':[r1,r2,r3],'plan':plan,'evidence':expanded,'assessment':assessment,'checks':checked,'final':parsed,'arm':'active_evidence'}
