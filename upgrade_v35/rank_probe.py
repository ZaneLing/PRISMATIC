"""Development-only ordinary supervised comparator; no automatic agent promotion."""
import json,re,random
import numpy as np
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
from sklearn.linear_model import LogisticRegression
from common import LOCAL,RUN,HERE,digest,save

def features(c,r):
 focus=r['plan'].get('focus','');words=sorted(set(re.findall('[a-z]{3,}',focus.lower()))-ENGLISH_STOP_WORDS)
 draft=r.get('assessment',{}).get('draft');products=r['evidence'].get('products',[]);rows=[]
 for j,o in enumerate(c['options']):
  name=' '.join(re.findall('[a-z0-9]+',o.lower()));ids=sorted({u for p in products if p.get('option')==chr(65+j) for u in p.get('unii',[])})
  d={'draft':float(draft==chr(65+j)),'name='+name:1.}
  for identity in [name]+ids:
   for w in words:d['drug='+identity+'|context='+w]=1.
  rows.append(d)
 return rows

def load(cs,split):
 out=[]
 for c in cs:
  p=RUN/'verified_evidence'/split/(digest(c['id'])+'.json')
  if not p.exists():p=RUN/'memory'/digest([])/split/(digest(c['id'])+'.json')
  out.append(json.loads(p.read_text()))
 return out

def main():
 data=json.loads((LOCAL/'data.json').read_text());train=data['parts']['train'];dev=data['parts']['proposal'];tr=load(train,'train');dr=load(dev,'proposal')
 x=[z for c,r in zip(train,tr) for z in features(c,r)];y=[int(chr(65+j)==c['gold']) for c in train for j in range(len(c['options']))];v=DictVectorizer();x=v.fit_transform(x);xd=v.transform([z for c,r in zip(dev,dr) for z in features(c,r)])
 scores=[]
 for C in (.1,1,10):
  model=LogisticRegression(C=C,max_iter=300,random_state=35).fit(x,y);p=model.predict_proba(xd)[:,1];pred=[];offset=0
  for c in dev:
   arr=p[offset:offset+len(c['options'])];offset+=len(c['options']);best=max(range(len(arr)),key=lambda j:(arr[j],digest(c['options'][j])));pred.append(chr(65+best))
  scores.append({'C':C,'n':len(dev),'correct':sum(a==c['gold'] for a,c in zip(pred,dev))})
 save(HERE/'results/rank_probe.json',{'status':'development_only','ordinary_supervised_comparator':True,'notes':'Uses draft and medication/context interactions. Drug-frequency shortcuts are possible. No test scores or automatic promotion.','scores':scores});print(json.dumps(scores))
if __name__=='__main__':main()
