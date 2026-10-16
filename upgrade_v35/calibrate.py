"""Train-only option calibration with development-frozen routing.

Ordinary supervised learning is credited as such. Numeric state evolves with
case exposure; no claim that the optimizer autonomously rewrites itself.
"""
import argparse,json,pickle,random
from datetime import datetime,timezone
import numpy as np
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from common import HERE,RUN,LOCAL,digest,save,sha
from rank_probe import features,load


def fit(cases,rows,C):
 x=[z for c,r in zip(cases,rows) for z in features(c,r)];y=[int(chr(65+j)==c['gold']) for c in cases for j in range(len(c['options']))]
 v=DictVectorizer();xx=v.fit_transform(x);model=LogisticRegression(C=C,max_iter=1000,solver='liblinear',random_state=35).fit(xx,y)
 assert np.isfinite(model.coef_).all() and np.isfinite(model.intercept_).all()
 assert int(model.n_iter_[0])<1000
 return {'vectorizer':v,'model':model,'seen_names':{o.lower().strip() for c in cases for o in c['options']},'C':C,'n_train':len(cases)}

def predict(bundle,cases,rows,margin):
 matrix=bundle['vectorizer'].transform([z for c,r in zip(cases,rows) for z in features(c,r)]);scores=bundle['model'].predict_proba(matrix)[:,1];assert np.isfinite(scores).all()
 out=[];offset=0
 for c,r in zip(cases,rows):
  p=scores[offset:offset+len(c['options'])];offset+=len(c['options']);order=sorted(range(len(p)),key=lambda j:(-p[j],digest(c['options'][j])))
  # Do not impose medication-name priors on full treatment-statement options.
  eligible=all(len(o.split())<=6 and o.lower().strip() in bundle['seen_names'] for o in c['options'])
  gap=float(p[order[0]]-p[order[1]]);apply=eligible and gap>=margin
  out.append({'case_id':c['id'],'prediction':chr(65+order[0]) if apply else r['prediction'],'raw_agent_prediction':r['prediction'],'rank_prediction':chr(65+order[0]),'eligible':eligible,'applied':apply,'margin':gap,'scores':p.tolist()})
 return out

def metric(rows,cases):return {'n':len(cases),'correct':sum(r['prediction']==c['gold'] for r,c in zip(rows,cases)),'applied':sum(r['applied'] for r in rows),'invalid':sum(r['prediction'] is None for r in rows)}

def main():
 p=argparse.ArgumentParser();p.add_argument('--stage',choices=['develop','test','rxqa'],default='develop');a=p.parse_args();data=json.loads((LOCAL/'data.json').read_text());parts=data['parts'];folder=RUN/'calibration';folder.mkdir(exist_ok=True)
 proto=HERE/'calibration_protocol.json'
 if not proto.exists():
  assert a.stage=='develop'
  save(proto,{'created_utc':datetime.now(timezone.utc).isoformat(),'code_sha256':sha(HERE/'calibrate.py'),'feature_code_sha256':sha(HERE/'rank_probe.py'),
   'design':'Ordinary supervised option calibration after source-verifying agent; no extra model call. Base output kept unless all options are short names observed in training and rank margin exceeds development-chosen threshold.',
   'features':'Second-call draft; exact medication-name indicators; medication/UNII crossed with extracted focus words. No answer-position or case-ID features.',
   'grid':{'C':[.1,1,10],'margin':[0,.05,.1,.2,.3]},
   'selection':'Highest proposal190 correct; ties prefer fewer overrides, then stronger regularization. Freeze candidate before guard. Guard must beat source agent102/197 with no invalid increase. Failure blocks promotion.',
   'risk':'Medication identity priors may exploit benchmark construction; gains do not establish clinical correctness. Ordinary supervised ranker is a required component comparator, not renamed RSI.',
   'curves':'Post hoc fixed-hyperparameter training-prefix curves; selected hyperparameters used full625 training/development feedback, so early prefixes are not a prospective online study.'})
 d=json.loads(proto.read_text());assert d['code_sha256']==sha(HERE/'calibrate.py') and d['feature_code_sha256']==sha(HERE/'rank_probe.py')
 if a.stage!='develop':
  freeze=json.loads((HERE/'test_freeze.json').read_text());selection=json.loads((HERE/'results/calibration_selection.json').read_text());assert selection['guard_pass']
  with (folder/'selected.pkl').open('rb') as f:b=pickle.load(f)
  assert sha(folder/'selected.pkl')==selection['model_sha256'];cases=parts['test'] if a.stage=='test' else data['transfer'];rows=load(cases,a.stage);out=predict(b,cases,rows,selection['margin']);save(folder/f'{a.stage}.json',out);m=metric(out,cases);save(HERE/'results'/f'calibrated-{a.stage}.json',dict(m,status='complete',model_sha256=sha(folder/'selected.pkl')));print(json.dumps(m));return
 tr=load(parts['train'],'train');dr=load(parts['proposal'],'proposal');grid=[];bundles={}
 for C in d['grid']['C']:
  b=fit(parts['train'],tr,C);bundles[C]=b
  for margin in d['grid']['margin']:
   rows=predict(b,parts['proposal'],dr,margin);grid.append(dict(metric(rows,parts['proposal']),C=C,margin=margin))
 grid.sort(key=lambda x:(-x['correct'],x['applied'],x['C'],x['margin']));best=grid[0];save(HERE/'results/calibration_proposal.json',{'status':'complete','grid':grid,'selected_before_guard':best})
 b=bundles[best['C']]
 with (folder/'selected.pkl').open('wb') as f:pickle.dump(b,f)
 # Selection is persisted before loading guard output/labels for this calibration stage.
 save(folder/'proposal_selection.json',dict(best,model_sha256=sha(folder/'selected.pkl')))
 gr=load(parts['guard'],'guard');out=predict(b,parts['guard'],gr,best['margin']);save(folder/'guard.json',out);gm=metric(out,parts['guard']);base=sum(r['prediction']==c['gold'] for r,c in zip(gr,parts['guard']));passed=gm['correct']>base and gm['invalid']<=sum(r['prediction'] is None for r in gr)
 selection=dict(best,guard=gm,guard_base_correct=base,guard_pass=passed,model_sha256=sha(folder/'selected.pkl'));save(HERE/'results/calibration_selection.json',selection)
 # Report all training-prefix states with fixed chosen hyperparameters, without changing selection.
 train=list(parts['train']);random.Random(42).shuffle(train);by={r['case_id']:r for r in tr};curve=[]
 for n in (156,312,468,625):
  cb=fit(train[:n],[by[c['id']] for c in train[:n]],best['C']);pr=predict(cb,parts['proposal'],dr,best['margin']);g=predict(cb,parts['guard'],gr,best['margin']);curve.append({'cases':n,'features':len(cb['vectorizer'].feature_names_),'nonzero_weights':int(np.count_nonzero(cb['model'].coef_)),'proposal':metric(pr,parts['proposal']),'guard':metric(g,parts['guard'])})
 save(HERE/'results/calibration_curve.json',{'status':'complete','post_hoc_fixed_hyperparameters':True,'curve':curve});print(json.dumps({'best':selection,'curve':curve}),flush=True)
if __name__=='__main__':main()
