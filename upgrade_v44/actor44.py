"""Source-applicability agent with routed procedural experience, no ranker."""
import json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/"upgrade_v37"))
from common37 import call,json_object,digest
from workflow import PLAN,ASSESS,FINAL,verify
from evidence37 import EvidenceTool,features,active_cards,config,routes
PLAN37=PLAN+'\nDistinguish a current medication, an option, a possible future recommendation and a suspected cause. For explicit dose/route/release-form information retain the exact quoted phrase; do not infer formulation from care setting. Never infer findings from unavailable images.'
ASSESS37=ASSESS+'''\nFor every decisive safety rule, check its patient-specific applicability: required conditions, excluded conditions, missing facts and treatment phase. Do not replace a risk warning by a blanket contraindication. Absence from an excerpt does not establish absence from the full label. When variants differ, identify which product the quotation describes. To check an explicit numeric threshold, add "applicability":[{"parameter":"age or egfr or crcl","patient_value":0,"patient_quote":"exact original span","operator":"lt/le/gt/ge","threshold":0,"evidence_id":"E1","rule_quote":"exact evidence span containing comparison phrase and threshold"}]. Only use this when the rule actually requires a numeric comparison; otherwise state unresolved applicability. Do not fabricate a threshold or patient value. Training-derived procedures are fallible process instructions, not medical authority.'''
FINAL37=FINAL+'''\nHonor executable applicability results: a rule whose condition is false cannot justify exclusion, and unknown inputs must not be treated as proof the rule applies. A condition check verifies only the extracted comparison, not the rule's overall clinical scope. Distinguish a source-supported contraindication, a precaution, monitoring advice and a lack of evidence. Interpret each complete answer statement, including dose, route, frequency and timing. Avoid changing an answer solely because one drug has a more familiar name.'''
PARS={'age':r'\b(\d+(?:\.\d+)?)\s*(?:-\s*)?(?:year|yr)s?\s*(?:-\s*)?old\b|\bage(?:d)?\s*(?:of\s*)?(\d+(?:\.\d+)?)','egfr':r'\b(?:egfr|glomerular filtration rate)\s*(?:is|of|=|:)?\s*(\d+(?:\.\d+)?)','crcl':r'\b(?:crcl|creatinine clearance)\s*(?:is|of|=|:)?\s*(\d+(?:\.\d+)?)'}
CMP={'lt':lambda x,y:x<y,'le':lambda x,y:x<=y,'gt':lambda x,y:x>y,'ge':lambda x,y:x>=y}
WORDS={'lt':r'(?:less than|below|under|<)\s*','le':r'(?:at most|no more than|less than or equal to|<=|≤)\s*','gt':r'(?:greater than|above|over|>)\s*','ge':r'(?:at least|greater than or equal to|>=|≥)\s*'}
def verify_applicability(a,ev,text):
 sources={z['evidence_id']:z['quote'] for z in ev['excerpts']};out=[]
 for entry in a.get('applicability',[])[:8] if isinstance(a.get('applicability',[]),list) else []:
  try:
   kind=entry['parameter'];pq=entry['patient_quote'];rq=entry['rule_quote'];op=entry['operator'];value=float(entry['patient_value']);threshold=float(entry['threshold']);assert kind in PARS and op in CMP;assert isinstance(pq,str) and pq and pq in text;assert isinstance(rq,str) and len(rq)>=8 and rq in sources.get(entry['evidence_id'],'')
   nums=[float(v) for match in re.finditer(PARS[kind],pq,re.I) for v in match.groups() if v is not None];assert value in nums
   thresholds=[float(m.group(1)) for m in re.finditer(WORDS[op]+r'(\d+(?:\.\d+)?)',rq,re.I)];assert threshold in thresholds
   if kind=='age':assert re.search(r'age|year|elderly|geriatric',rq,re.I)
   elif kind=='egfr':assert re.search(r'eGFR|glomerular filtration',rq,re.I)
   else:assert re.search(r'CrCl|creatinine clearance',rq,re.I)
   out.append({'parameter':kind,'patient_value':value,'operator':op,'threshold':threshold,'status':'source_bound_comparison','condition_satisfied':CMP[op](value,threshold),'evidence_id':entry['evidence_id'],'clinical_scope':'Other rule qualifiers, units and overall clinical applicability remain unverified'})
  except (AssertionError,KeyError,TypeError,ValueError):out.append({'status':'unverified_comparison','reason':'Unsupported source, parameter, comparator or patient value'})
 return out

def parse_answer(raw,n,multiple):
 obj=json_object(raw);x=obj.get('final') if isinstance(obj,dict) else None
 if isinstance(x,str):x=[x.strip().upper()]
 if not isinstance(x,list) or not x or any(not isinstance(z,str) for z in x):return None,obj
 x=[z.strip().upper() for z in x]
 if len(set(x))!=len(x) or any(z not in [chr(65+i) for i in range(n)] for z in x) or (not multiple and len(x)!=1):return None,obj
 return sorted(x),obj

def expanded_features(c,plan,state):
 fs=features(c,plan);text=' '.join(re.findall(r'[a-z]+',c['dialogue'].lower()))
 for card in state.get('cards',[]):
  for feature,terms in card.get('trigger_terms',{}).items():
   if any(' '+term.lower()+' ' in ' '+text+' ' for term in terms) and feature not in fs:fs.append(feature)
 return fs

class Agent44:
 def __init__(self,state=None):self.state=state or {'cards':[]};self.labels=EvidenceTool()
 def solve(self,c):
  multiple=c.get('multiple',False);task='Select ALL correct options. One or more may be correct. Return final as a JSON array of letters.' if multiple else 'Select exactly ONE best option. Return final as a JSON array containing one letter.'
  text=c['dialogue']+'\nOptions:\n'+'\n'.join(f'{chr(65+i)}. {o}' for i,o in enumerate(c['options']));r1=call(PLAN37+'\nTASK:\n'+task+'\nINPUT:\n'+text,'plan');plan=json_object(r1['raw']);plan=plan if isinstance(plan,dict) else {};plan['facts']=[f for f in plan.get('facts',[]) if isinstance(f,dict) and isinstance(f.get('input_quote'),str) and f['input_quote'] and f['input_quote'] in text];es=plan.get('entities',[]);es=es if isinstance(es,list) else []
  for e in es:
   if not isinstance(e,dict):continue
   rq=e.get('route_quote','');rr=e.get('route','')
   if not isinstance(rq,str) or not rq or rq not in text or rr not in routes(rq):e['route']=''
  plan['entities']=es;fs=expanded_features(c,plan,self.state);cards=active_cards(self.state,fs);policy=config(cards);ev=self.labels.query(c,plan,policy);view='\nTASK:\n'+task+'\nINPUT:\n'+text+'\nEXTRACTED FACTS (fallible):\n'+json.dumps(plan)+'\nLABEL EVIDENCE:\n'+json.dumps(ev)
  if cards:view+='\nAPPLICABLE PROCESS SKILLS:\n'+json.dumps([{k:s[k] for k in ('name','procedure','exclude_reason')} for s in cards])
  assessment_prompt=ASSESS37.replace('\"draft\":\"one option letter\"','\"draft\":[\"ALL correct option letters\"]') if multiple else ASSESS37
  r2=call(assessment_prompt+view,'assess');assessment=json_object(r2['raw']);assessment=assessment if isinstance(assessment,dict) else {};checked=verify(assessment,ev,text);checked['applicability']=verify_applicability(assessment,ev,text)
  final_prompt=FINAL37.replace('forced-choice','multi-select').replace('\"final\":\"one option letter\"','\"final\":[\"ALL correct option letters\"]') if multiple else FINAL37
  r3=call(final_prompt+view+'\nASSESSMENT:\n'+json.dumps(assessment)+'\nEXECUTED CHECKS:\n'+json.dumps(checked)+'\nOUTPUT CONTRACT:\n'+task,'decide');answer,parsed=parse_answer(r3['raw'],len(c['options']),multiple)
  return {'case_id':c['id'],'prediction':answer,'calls':[r1,r2,r3],'plan':plan,'evidence':ev,'assessment':assessment,'checks':checked,'final':parsed,'features':fs,'active_cards':[s['name'] for s in cards],'retrieval_policy':policy,'state_sha256':digest(self.state)}
