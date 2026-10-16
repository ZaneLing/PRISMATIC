"""Frozen trajectory evaluation; no test score selects a state."""
import argparse,json,random,importlib.util
from datetime import datetime,timezone
from common37 import RUN,HERE,ROOT,configure,save,sha,digest
_s=importlib.util.spec_from_file_location('runner37',HERE/'run.py');_m=importlib.util.module_from_spec(_s);_s.loader.exec_module(_m)
batch,target=_m.batch,_m.target
BASE_HERE=HERE

def freeze():
 learn=json.loads((HERE/'results/learning.json').read_text());assert learn['status']=='frozen'
 assert len(learn['rounds'])==5
 impl=json.loads((BASE_HERE/'implementation.json').read_text());assert all(sha(BASE_HERE/k)==v for k,v in impl.items())
 payload={'created_utc':datetime.now(timezone.utc).isoformat(),'selection':'Last development-gated state; no test-based checkpoint selection','states':[{'round':s['round'],'cases_seen':s['cases_seen'],'state_sha256':digest(s['state'])} for s in learn['rounds']],'learning_sha256':sha(HERE/'results/learning.json'),'independent_protocol_sha256':sha(BASE_HERE/'independent_protocol.json'),'implementation':impl,'evaluator_sha256':sha(__file__),'learner_sha256':sha(HERE/'learn.py')}
 if HERE.name in ('upgrade_v40','upgrade_v41','upgrade_v42','upgrade_v43','upgrade_v44'):
  ext=json.loads((HERE/'implementation.json').read_text());assert all(sha(ROOT/k)==v for k,v in ext['actor'].items());payload['actor_extension']=ext
 p=HERE/'test_freeze.json'
 if p.exists():
  old=json.loads(p.read_text());assert all(old[k]==v for k,v in payload.items() if k!='created_utc')
 else:save(p,payload)
 return learn['rounds']

def detail(rows,cs):
 by={r['case_id']:r for r in rows};groups={}
 for family in sorted({c.get('family','unknown') for c in cs}):
  sub=[c for c in cs if c.get('family','unknown')==family];groups[family]={'correct':sum(by[c['id']]['prediction']==target(c) for c in sub),'n':len(sub)}
 ip=json.loads((BASE_HERE/'independent_protocol.json').read_text());valid=[p for p in ip['paired_ids'] if all(i in by for i in p)];gold={c['id']:target(c) for c in cs}
 return {'families':groups,'paired':{'n':len(valid),'both_correct':sum(all(by[i]['prediction']==gold[i] for i in p) for p in valid)},'prediction_hash':digest([(r['case_id'],r['prediction']) for r in rows])}

def main():
 global HERE,batch
 ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=['freeze','independent','main','shortcuts'],required=True);ap.add_argument('--split',choices=['test_rx','test_qa']);ap.add_argument('--experiment',choices=['37','38','39','40','41','42','43','44'],default='37');args=ap.parse_args();HERE=ROOT/('upgrade_v'+args.experiment);configure()
 if args.experiment in ('40','41','42','43','44'):
  import sys
  sys.path.insert(0,str(ROOT/'upgrade_v40'));spec=importlib.util.spec_from_file_location('runner40eval',ROOT/'upgrade_v40/run40.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);mod.RUN=RUN.parent/('rxrsi-v'+args.experiment);batch=mod.batch
  if args.experiment=='44':
   sys.path.insert(0,str(HERE));from actor44 import Agent44
   mod.Agent40=Agent44
 states=freeze();data=json.loads((RUN/'data.json').read_text())
 if args.mode=='freeze':print('Trajectory and evaluator frozen');return
 if args.mode=='independent':
  out=[]
  for s in states:
   rows,m=batch(data['test_independent'],s['state'],'test_independent');out.append(dict(round=s['round'],cases_seen=s['cases_seen'],state_sha256=digest(s['state']),cards=len(s['state']['cards']),metrics=m,detail=detail(rows,data['test_independent'])));save(HERE/'results/independent_progress.json',out)
  save(HERE/'results/independent.json',{'status':'complete','trajectory':out,'selection_feedback':False})
 elif args.mode=='main':
  assert args.split;out={}
  for label,s in [('initial',states[0]),('final',states[-1])]:
   rows,m=batch(data[args.split],s['state'],args.split);out[label]=dict(state_sha256=digest(s['state']),metrics=m)
  save(HERE/'results'/('main-'+args.split+'.json'),out)
 else:
  ip=json.loads((BASE_HERE/'independent_protocol.json').read_text());by={c['id']:c for c in data['test_independent']};cs=[by[i] for i in ip['shortcut_ids']];variants={'permuted':[],'no_patient':[]};maps={}
  for c in cs:
   p=list(range(len(c['options'])));random.Random(digest(['permutation',c['id']])).shuffle(p)
   if p==list(range(len(p))):p=p[1:]+p[:1]
   maps[c['id']]=p;variants['permuted'].append(dict(c,options=[c['options'][i] for i in p],gold=sorted(chr(65+p.index(ord(z)-65)) for z in target(c))));variants['no_patient'].append(dict(c,dialogue=c['question_only']))
  out={}
  for label,s in [('initial',states[0]),('final',states[-1])]:
   full,_=batch(cs,s['state'],'test_independent');base={r['case_id']:r['prediction'] for r in full};out[label]={'original':detail(full,cs),'original_correct':sum(r['prediction']==target(c) for r,c in zip(full,cs))}
   for mode,sub in variants.items():
    rows,m=batch(sub,s['state'],'test_shortcut_'+mode);extra={}
    if mode=='permuted':
     decoded={r['case_id']:sorted(chr(65+maps[r['case_id']][ord(z)-65]) for z in r['prediction']) if r['prediction'] is not None else None for r in rows};extra['same_prediction_after_remap']=sum(decoded[i]==base[i] for i in base)
    out[label][mode]={'metrics':m,'detail':detail(rows,sub),**extra}
  save(HERE/'results/shortcuts.json',{'status':'complete','n':len(cs),'result':out,'permutation_sha256':digest(maps),'note':'Diagnostic context dependence and option-position sensitivity; these do not rule out all parametric drug priors.'})
if __name__=='__main__':main()
