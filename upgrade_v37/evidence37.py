"""Product variants and request-specific evidence; no learned identity prior."""
import json,re,time,urllib.request,urllib.parse,urllib.error,fcntl,threading
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from common37 import RUN,LOCAL,digest,save
from evidence import LabelTool,norm,routes,FIELDS
EXTRA=('dosage_forms_and_strengths','how_supplied','spl_product_data_elements')
RATE=threading.Lock();NEXT=[0.]
DEFAULT={'variants':2,'window':1600,'char_budget':18000,'dose_weight':1.5,'safety_weight':1.5,'indication_weight':1.0}
BOUNDS={'variants':(1,3),'window':(800,2600),'char_budget':(8000,26000),'dose_weight':(.5,3.),'safety_weight':(.5,3.),'indication_weight':(.5,3.)}
FEATURES=('dose_question','interaction_question','renal_context','hepatic_context','age_context','pregnancy_context','explicit_route','statement_options','short_drug_options','multiple_medications','conditional_question')
def features(c,plan):
 s=c['dialogue'].lower();opt=c['options'];es=plan.get('entities',[])
 checks={'dose_question':r'\b(dos(?:e|age|ing)|mg|mcg|frequency|daily|weekly|titration|titrate)\b','interaction_question':r'\b(interact\w*|coadminist\w*|concomitant|combination)\b','renal_context':r'\b(renal|kidney|creatinine|egfr|crcl|dialysis)\b','hepatic_context':r'\b(hepatic|liver|cirrhosis)\b','age_context':r'\b(\d{1,3}[- ]year[- ]old|elderly|geriatric|pediatric|infant|child)\b','pregnancy_context':r'\b(pregnan\w*|lactat\w*|breastfeed\w*)\b','conditional_question':r'\b(avoid|contraindicat\w*|except|unless|not recommended|appropriate|best next)\b'}
 found={k:bool(re.search(p,s)) for k,p in checks.items()};found['explicit_route']=bool(routes(s));found['statement_options']=any(len(o.split())>6 for o in opt);found['short_drug_options']=all(len(o.split())<=6 for o in opt);found['multiple_medications']=len({norm(e.get('name','')) for e in es if isinstance(e,dict) and isinstance(e.get('input_quote'),str) and e['input_quote'] in c['dialogue']})>=2
 return [k for k,v in found.items() if v]
def active_cards(state,feats):
 s=set(feats);return [c for c in state.get('cards',[]) if set(c['trigger_any'])&s and not set(c['exclude_any'])&s]
def config(cards):
 d=dict(DEFAULT)
 for c in cards:
  for k,v in c.get('retrieval_patch',{}).items():
   lo,hi=BOUNDS[k];assert type(v) in (int,float) and lo<=v<=hi;d[k]=v
 for k in ('variants','window','char_budget'):d[k]=int(d[k])
 return d

def enhanced_fetch(name,route):
 folder=RUN/'label_requests';folder.mkdir(exist_ok=True);key=digest([name,route]);p=folder/(key+'.json')
 with (folder/(key+'.lock')).open('a') as f:
  fcntl.flock(f,fcntl.LOCK_EX)
  if p.exists():return json.loads(p.read_text())
  if len(list(folder.glob('*.json')))>=600:return {'status':'source_query_limit','labels':[]}
  query='(openfda.generic_name:"'+name+'" OR openfda.brand_name:"'+name+'")'
  if route:query+=' AND openfda.route:"'+route.upper()+'"'
  url='https://api.fda.gov/drug/label.json?'+urllib.parse.urlencode({'search':query,'limit':30,'sort':'effective_time:desc'});out={'url':url,'name':name,'route':route,'status':'unavailable','labels':[]}
  with RATE:
   delay=max(0,NEXT[0]-time.monotonic());NEXT[0]=max(NEXT[0],time.monotonic())+.4
  if delay:time.sleep(delay)
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'RxRSIAgent-public-source-audit'}),timeout=20) as r:raw=r.read()
   d=json.loads(raw);ls=[{k:l.get(k) for k in ('id','set_id','effective_time','openfda')+FIELDS+EXTRA} for l in d.get('results',[]) if l.get('effective_time','')<='20261016'];out.update(status='retrieved',labels=ls,response_sha256=__import__('hashlib').sha256(raw).hexdigest())
  except urllib.error.HTTPError as e:out['status']='http_'+str(e.code)
  except (OSError,ValueError) as e:out['status']=type(e).__name__
  save(p,out);return out

def forms(l):
 text=' '.join((l.get('openfda') or {}).get('brand_name',[]))+' '+' '.join(l.get('dosage_forms_and_strengths') or [])
 return [v for v,p in [('extended_release',r'extended.release|sustained.release|controlled.release'),('delayed_release',r'delayed.release|enteric.coated'),('immediate_release',r'immediate.release')] if re.search(p,text,re.I)]

class EvidenceTool(LabelTool):
 def __init__(self):super().__init__();self.ext_cache={}
 def products(self,name,route):
  old=super().products(name,route);new=enhanced_fetch(norm(name),norm(route));merged={l['id']:l for l in old}
  for l in new['labels']:
   if self.identity_ok(name,l):merged[l['id']]=l
  return list(merged.values())
 def query(self,c,plan,policy=None):
  policy=policy or DEFAULT;initial=super().query(c,plan);products=[];ev=[];pending=[];flags=list(initial['flags']);remaining=policy['char_budget'];query=plan.get('focus','')+' '+c['dialogue'];query_words=set(norm(plan.get('focus','')).split())
  for product in initial['products']:
   rr=product.get('requested_route','');labs=self.products(product['name'],rr);rank=[]
   for l in labs:
    route=routes(' '.join((l.get('openfda') or {}).get('route',[])));conflict=bool(rr and route and rr not in route);inds=' '.join(l.get('indications_and_usage') or []);score=len(query_words&set(norm(inds).split()));rank.append((conflict,-score,l['id'],l,route))
   rank.sort(key=lambda x:x[:3]);picked=[];signatures=set()
   for conflict,score,lid,l,route in rank:
    if conflict:continue
    signature=(tuple(route),tuple(forms(l)))
    if signature in signatures:continue
    signatures.add(signature);picked.append((l,route))
    if len(picked)>=policy['variants']:break
   if not picked:flags.append({'name':product['name'],'status':'no_route_compatible_product'});continue
   for l,route in picked:
    of=l.get('openfda') or {};prod=dict(product,label_id=l['id'],set_id=l.get('set_id'),routes=route,route_status='matched' if rr and route else 'unknown',release_forms=forms(l),formulation_status='source_described' if l.get('dosage_forms_and_strengths') else 'unknown');products.append(prod)
    chunks=[]
    for field in FIELDS+('dosage_forms_and_strengths',):
     vals=l.get(field) or [];vals=[vals] if isinstance(vals,str) else vals
     for pi,v in enumerate(vals):
      for offset in range(0,len(v),max(400,policy['window']//2)):
       quote=v[offset:offset+policy['window']]
       if len(quote.strip())>=30:chunks.append({'label_id':l['id'],'set_id':l.get('set_id'),'date':l.get('effective_time'),'section':field,'paragraph':pi,'offset':offset,'quote':quote,'name':product['name'],'option':product['option'],'product_route_status':prod['route_status']})
    if not chunks:continue
    vec=TfidfVectorizer(stop_words='english',ngram_range=(1,2),sublinear_tf=True,max_features=20000);x=vec.fit_transform([z['quote'] for z in chunks]);scores=(x@vec.transform([query]).T).toarray()[:,0];chosen=[]
    groups=[('indication_weight',('indications_and_usage',)),('dose_weight',('dosage_and_administration','dosage_forms_and_strengths')),('safety_weight',('contraindications','drug_interactions','use_in_specific_populations','boxed_warning','warnings_and_cautions','warnings'))]
    # Each product receives one excerpt per clinical group; additional slots follow request relevance.
    for weight,fields in groups:
     ids=[i for i,z in enumerate(chunks) if z['section'] in fields]
     if ids:chosen.append(max(ids,key=lambda i:(scores[i]*policy[weight],-i)))
    weighted=[scores[i]*(policy['dose_weight'] if z['section']=='dosage_and_administration' else policy['indication_weight'] if z['section']=='indications_and_usage' else policy['safety_weight']) for i,z in enumerate(chunks)]
    for i in sorted(range(len(chunks)),key=lambda i:(-weighted[i],i)):
     if i not in chosen and len(chosen)<4:chosen.append(i)
    pending.append([chunks[i] for i in chosen])
  per_span=max(200,min(policy['window'],policy['char_budget']//max(1,len(pending)*3)))
  for slot in range(4):
   for spans in pending:
    if slot>=len(spans) or remaining<100:continue
    z=dict(spans[slot]);z['quote']=z['quote'][:min(per_span,remaining)];ev.append(dict(z,evidence_id='E'+str(len(ev)+1)));remaining-=len(z['quote'])
  return {'products':products,'excerpts':ev,'flags':flags,'char_budget':policy['char_budget'],'chars_used':policy['char_budget']-remaining,'scope':'Product variants and exact source excerpts. Missing form/strength is unknown. No comprehensive clinical clearance.'}
