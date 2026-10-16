"""Source-bound, candidate-balanced label retrieval. No answer-label access."""
import json,re,threading,time,urllib.request,urllib.parse,urllib.error
from datetime import datetime,timezone
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from common import LOCAL,RUN,digest,save,sha
FIELDS=('indications_and_usage','dosage_and_administration','contraindications','drug_interactions','use_in_specific_populations','boxed_warning','warnings_and_cautions','warnings')
LOCK=threading.RLock();NEXT=[0.];LABEL_LOCKS={}
ROUTES={'oral':('oral','by mouth','tablet','capsule'),'nasal':('nasal','intranasal','nose spray'),'intravenous':('intravenous','iv infusion','iv injection'),'intramuscular':('intramuscular',),'subcutaneous':('subcutaneous',),'topical':('topical','cream','ointment'),'ophthalmic':('ophthalmic','eye drops'),'otic':('otic','ear drops'),'inhalation':('inhaled','inhalation','inhaler')}
def norm(s):return ' '.join(re.findall(r'[a-z0-9]+',str(s).lower()))
def routes(text):
 t=' '+norm(text)+' ';return [k for k,vs in ROUTES.items() if any(' '+v+' ' in t for v in vs)]
def aliases(l):return [norm(x) for field in ('generic_name','brand_name','substance_name') for x in (l.get('openfda') or {}).get(field,[])]
def matches(name,l):
 ts=set(norm(name).split());return bool(ts) and any(norm(name)==a or ts<=set(a.split()) for a in aliases(l))
def fetch(name):
 p=RUN/'label_requests'/(digest(name)+'.json')
 with LOCK:lock=LABEL_LOCKS.setdefault(name,threading.Lock())
 with lock:
  if p.exists():return json.loads(p.read_text())
  query='openfda.generic_name:"'+name+'" OR openfda.brand_name:"'+name+'"'
  url='https://api.fda.gov/drug/label.json?'+urllib.parse.urlencode({'search':query,'limit':12,'sort':'effective_time:desc'})
  out={'query_name':name,'url':url,'fetched_utc':datetime.now(timezone.utc).isoformat(),'status':'unavailable','labels':[]}
  for attempt in range(3):
   with LOCK:wait=max(0,NEXT[0]-time.monotonic());NEXT[0]=max(NEXT[0],time.monotonic())+.32
   if wait:time.sleep(wait)
   try:
    req=urllib.request.Request(url,headers={'User-Agent':'RxRSIAgent-public-label-research'})
    with urllib.request.urlopen(req,timeout=25) as r:raw=r.read()
    data=json.loads(raw)
    labels=[{k:l.get(k) for k in ('id','set_id','effective_time','openfda')+FIELDS} for l in data.get('results',[]) if matches(name,l) and l.get('effective_time','')<='20261016']
    out.update(status='matched' if labels else 'no_verified_name_match',labels=labels,response_sha256=__import__('hashlib').sha256(raw).hexdigest());break
   except urllib.error.HTTPError as e:
    out['status']='not_found' if e.code==404 else 'http_'+str(e.code)
    if e.code!=429:break
   except (OSError,ValueError) as e:out['status']=type(e).__name__
   time.sleep(2*(attempt+1))
  save(p,out);return out

class LabelTool:
 def __init__(self):
  p=LOCAL.parent/'rxrsi-v11/labels.json';self.snapshot=sha(p);self.old=json.loads(p.read_text());self.by_alias={};self.cache={};self.lock=threading.RLock()
  for name,r in self.old.items():
   l=r.get('label')
   if not l:continue
   for a in set([norm(name)]+aliases(l)):self.by_alias.setdefault(a,{})[l['id']]=l
 def products(self,name,route):
  found=dict(self.by_alias.get(norm(name),{}));rr=norm(route)
  compatible=[l for l in found.values() if not rr or rr in routes(' '.join((l.get('openfda') or {}).get('route',[])))]
  if not compatible:
   record=fetch(norm(name));found.update({l['id']:l for l in record['labels']})
  return list(found.values())
 def chunks(self,l):
  key=l['id']
  with self.lock:
   if key in self.cache:return self.cache[key]
   chunks=[]
   for field in FIELDS:
    values=l.get(field) or [];values=[values] if isinstance(values,str) else values
    for pi,v in enumerate(values):
     for offset in range(0,len(v),750):
      quote=v[offset:offset+1000]
      if len(quote.strip())<30:continue
      chunks.append({'label_id':key,'set_id':l.get('set_id'),'date':l.get('effective_time'),'section':field,'paragraph':pi,'offset':offset,'quote':quote})
   if not chunks:self.cache[key]=(chunks,None,None);return self.cache[key]
   v=TfidfVectorizer(stop_words='english',ngram_range=(1,2),max_features=20000);x=v.fit_transform([c['quote'] for c in chunks]);self.cache[key]=(chunks,v,x)
   return self.cache[key]
 def query(self,c,plan):
  text=c['dialogue']+'\n'+'\n'.join(c['options']);entities=[]
  # Every short medication option gets an equal retrieval opportunity.
  for i,o in enumerate(c['options']):
   if len(o.split())<=6 and norm(o) in self.by_alias:entities.append({'name':norm(o),'quote':o,'route':'','option':chr(65+i)})
  for e in plan.get('entities',[])[:10]:
   if not isinstance(e,dict):continue
   name=norm(e.get('name',''));quote=e.get('input_quote','')
   if not name or len(name)>90 or not isinstance(quote,str) or quote not in text:continue
   if not set(name.split())<=set(norm(quote).split()):continue
   entities.append({'name':name,'quote':quote,'route':norm(e.get('route','')),'option':str(e.get('option','context'))})
  merged={}
  for e in entities:
   if e['name'] not in merged or e['route']:merged[e['name']]=e
  products=[];excerpts=[];flags=[]
  query=' '.join(str(plan.get(k,'')) for k in ('focus','facts','question_type'))+'\n'+text
  for e in list(merged.values())[:10]:
   labs=self.products(e['name'],e['route']);rr=e['route'];ranked=[]
   for l in labs:
    lr=routes(' '.join((l.get('openfda') or {}).get('route',[])))
    conflict=bool(rr and lr and rr not in lr)
    ranked.append((conflict, -(sum(len(str(l.get(f,''))) for f in FIELDS)),l['id'],l,lr))
   ranked.sort(key=lambda z:z[:3])
   if not ranked:flags.append({'name':e['name'],'status':'label_unavailable'});continue
   chosen=ranked[0];conflict,_,_,l,lr=chosen;of=l.get('openfda') or {}
   product={'name':e['name'],'option':e['option'],'label_id':l['id'],'set_id':l.get('set_id'),'generic':of.get('generic_name',[]),'substances':of.get('substance_name',[]),'unii':of.get('unii',[]),'routes':lr,'requested_route':rr,'route_status':'conflict' if conflict else 'matched' if rr and lr else 'unknown'};products.append(product)
   if conflict:flags.append({'name':e['name'],'status':'route_conflict_excluded','label_id':l['id']});continue
   chunks,vec,x=self.chunks(l)
   if not chunks:continue
   scores=(x@vec.transform([query]).T).toarray()[:,0];selected=[]
   # Reserve indication, dose and safety evidence for each candidate instead of global top-k.
   for group in [('indications_and_usage',),('dosage_and_administration',),('contraindications','drug_interactions','use_in_specific_populations','boxed_warning','warnings_and_cautions','warnings')]:
    ix=[i for i,z in enumerate(chunks) if z['section'] in group]
    if ix:selected.append(max(ix,key=lambda i:(scores[i],-i)))
   for i in selected:
    z=dict(chunks[i],name=e['name'],option=e['option'],product_route_status=product['route_status']);z['evidence_id']='E'+str(len(excerpts)+1);excerpts.append(z)
  for i,a in enumerate(products):
   for b in products[i+1:]:
    if a['option']!=b['option'] and a['unii'] and set(a['unii'])==set(b['unii']):flags.append({'status':'same_ingredient_identifiers','options':[a['option'],b['option']],'names':[a['name'],b['name']]})
  return {'products':products,'excerpts':excerpts[:24],'flags':flags,'scope':'Exact identity/route/source checks only; no comprehensive clinical safety clearance.'}
