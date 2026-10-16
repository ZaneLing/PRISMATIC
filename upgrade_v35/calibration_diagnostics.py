"""Post-selection attribution, never a new test-selected agent configuration."""
import json,pickle
import numpy as np
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from common import HERE,RUN,LOCAL,save,sha,digest
from rank_probe import features,load

def main():
 data=json.loads((LOCAL/'data.json').read_text());train=data['parts']['train'];tr=load(train,'train');f=HERE/'calibration_diagnostics_protocol.json'
 if not f.exists():save(f,{'code_sha256':sha(__file__),'purpose':'Post-selection attribution, after aggregate primary results known. Fixed C=10 and margin=.2; never select a new model from diagnostic test results.','arms':['identity_only','identity_and_draft','context_only','context_and_draft'],'test_adaptation':False})
 assert json.loads(f.read_text())['code_sha256']==sha(__file__)
 result={'status':'complete','post_selection_diagnostic':True,'selected_primary_unchanged':True,'arms':{}}
 def filt(fs,arm):
  return [{k:v for k,v in d.items() if (k.startswith('name=') and arm.startswith('identity')) or (k.startswith('drug=') and arm.startswith('context')) or (k=='draft' and arm.endswith('draft'))} for d in fs]
 x0=[z for c,r in zip(train,tr) for z in features(c,r)];y=[int(chr(65+j)==c['gold']) for c in train for j in range(len(c['options']))];seen={o.lower().strip() for c in train for o in c['options']}
 for arm in json.loads(f.read_text())['arms']:
  v=DictVectorizer();x=v.fit_transform(filt(x0,arm));m=LogisticRegression(C=10,max_iter=1000,solver='liblinear',random_state=35).fit(x,y);stats={}
  for split in ('proposal','guard','test','rxqa'):
   cs=data['transfer'] if split=='rxqa' else data['parts'][split];rs=load(cs,split);p=m.predict_proba(v.transform(filt([z for c,r in zip(cs,rs) for z in features(c,r)],arm)))[:,1];out=[];offset=0;applied=0
   for c,r in zip(cs,rs):
    s=p[offset:offset+len(c['options'])];offset+=len(c['options']);order=sorted(range(len(s)),key=lambda j:(-s[j],digest(c['options'][j])));eligible=all(len(o.split())<=6 and o.lower().strip() in seen for o in c['options']);use=eligible and s[order[0]]-s[order[1]]>=.2;applied+=use;out.append(chr(65+order[0]) if use else r['prediction'])
   stats[split]={'n':len(cs),'correct':sum(a==c['gold'] for a,c in zip(out,cs)),'applied':int(applied),'predictions_sha256':digest(out)}
  result['arms'][arm]={'features':len(v.feature_names_),'splits':stats}
 save(HERE/'results/calibration_diagnostics.json',result);print(json.dumps(result))
if __name__=='__main__':main()
