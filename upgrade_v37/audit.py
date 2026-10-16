"""Recount public results and bind checks to saved source/response artifacts."""
import argparse,collections,json,importlib.util,random
import numpy as np
from common37 import RUN,HERE,ROOT,LOCAL,save,sha,digest,ledger_total
from agent37 import parse_answer,verify_applicability
from workflow import verify
_s=importlib.util.spec_from_file_location('runner37',HERE/'run.py');_m=importlib.util.module_from_spec(_s);_s.loader.exec_module(_m)
target=_m.target
BASE_HERE=HERE

def paired(old,new,cs):
 dif=np.array([int(b['prediction']==target(c))-int(a['prediction']==target(c)) for a,b,c in zip(old,new,cs)]);groups=collections.defaultdict(list)
 for i,c in enumerate(cs):groups[c.get('group_id',c['id'])].append(i)
 sums=np.array([dif[g].sum() for g in groups.values()]);sizes=np.array([len(g) for g in groups.values()]);rng=np.random.default_rng(37);draw=[]
 for _ in range(4000):
  ix=rng.integers(0,len(sums),len(sums));draw.append(sums[ix].sum()/sizes[ix].sum())
 return {'difference':float(dif.mean()),'ci95':np.quantile(draw,[.025,.975]).tolist(),'fixes':int((dif==1).sum()),'regressions':int((dif==-1).sum())}

def main():
 global RUN
 ap=argparse.ArgumentParser();ap.add_argument('--experiment',choices=['37','38','39','40','41','42','43','44'],default='38');a=ap.parse_args();here=ROOT/('upgrade_v'+a.experiment);learn=json.loads((here/'results/learning.json').read_text());freeze=json.loads((here/'test_freeze.json').read_text());assert freeze['learning_sha256']==sha(here/'results/learning.json');assert freeze['learner_sha256']==sha(here/'learn.py');assert all(sha(BASE_HERE/k)==v for k,v in freeze['implementation'].items());data=json.loads((RUN/'data.json').read_text());protocol=json.loads((BASE_HERE/'protocol.json').read_text());assert sha(RUN/'data.json')==protocol['data_sha256'];assert sha(RUN/'medpic_source.json')==protocol['independent']['sha256'];labels={}
 for x in json.loads((LOCAL.parent/'rxrsi-v11/labels.json').read_text()).values():
  if x.get('label'):labels[x['label']['id']]=x['label']
 if a.experiment in ('40','41','42','43','44'):assert all(sha(ROOT/k)==v for k,v in freeze['actor_extension']['actor'].items())
 sources=list((LOCAL.parent/'rxrsi-v35/label_requests').glob('*.json'))+list((RUN/'label_requests').glob('*.json'))
 for p in sources:
  for l in json.loads(p.read_text()).get('labels',[]):labels[l['id']]=l
 result={'status':'complete','experiment':a.experiment,'audit_code_sha256':sha(__file__),'states':[],'methods':{},'comparisons':{},'source_spans_checked':0,'source_queries':len(sources),'source_statuses':dict(collections.Counter(json.loads(p.read_text())['status'] for p in (RUN/'label_requests').glob('*.json'))),'source_manifest_sha256':digest([(str(p.relative_to(LOCAL.parent)),sha(p)) for p in sources]),'applicability_statuses':{},'root_hypotheses':{},'interval_note':'4000 exploratory paired bootstrap draws, source-scenario clusters for RxSafe; item resampling otherwise. Repeated research and multiple comparisons unadjusted.'};allchecks=collections.Counter();seenpaths=set()
 if a.experiment in ('40','41','42','43','44'):RUN=LOCAL.parent/('rxrsi-v'+a.experiment)
 def rows(cs,state,split):
  out=[]
  for c in cs:
   p=RUN/'runs'/digest(state)/split/(digest(c['id'])+'.json');r=json.loads(p.read_text());assert r['case_id']==c['id'];assert r['state_sha256']==digest(state);assert len(r['calls'])==3;assert sum(x['output_tokens'] for x in r['calls'])<=4608;assert parse_answer(r['calls'][-1]['raw'],len(c['options']),c.get('multiple',False))[0]==r['prediction']
   if p not in seenpaths:
    seenpaths.add(p);text=c['dialogue']+'\nOptions:\n'+'\n'.join(f'{chr(65+i)}. {o}' for i,o in enumerate(c['options']));checked=verify(r['assessment'],r['evidence'],text);checked['applicability']=verify_applicability(r['assessment'],r['evidence'],text);assert checked==r['checks']
    for z in r['evidence']['excerpts']:
     vals=labels[z['label_id']][z['section']];vals=[vals] if isinstance(vals,str) else vals;assert vals[z['paragraph']][z['offset']:z['offset']+len(z['quote'])]==z['quote'];result['source_spans_checked']+=1
    allchecks.update(x['status'] for x in checked['applicability'])
    for rr in r['calls']:
     assert not rr.get('error') and rr.get('model_returned');cached=json.loads((LOCAL/'cache'/(rr['request_sha256']+'.json')).read_text());assert rr['raw']==cached['raw']
   out.append(r)
  return out
 def metrics(rs,cs):
  calls=[q for r in rs for q in r['calls']];return {'n':len(cs),'correct':sum(r['prediction']==target(c) for r,c in zip(rs,cs)),'invalid':sum(r['prediction'] is None for r in rs),'calls':len(calls),'input_tokens':sum(x['input_tokens'] for x in calls),'output_tokens':sum(x['output_tokens'] for x in calls),'logical_cost_usd':sum(x['cost_usd'] or 0 for x in calls),'active_cases':sum(bool(r['active_cards']) for r in rs),'prediction_sha256':digest([r['prediction'] for r in rs])}
 states=learn['rounds'];assert len(states)==5
 for idx,s in enumerate(states):
  prev=states[max(0,idx-1)];accepted=[t for t in s.get('trials',[]) if t['accepted']]
  assert bool(accepted)==s['accepted']
  for t in accepted:
   assert t['probe']['net']>=2 and t['probe']['invalid_after']<=t['probe']['invalid_before']
   for stage in ['proposal','guard']:
    assert (a.experiment in ('40','41','42','43','44') and stage=='guard') or sum(t['gates'][stage+'_'+task]['correct']-prev['gates'][stage+'_'+task]['correct'] for task in ['rx','med'])>0
    for task in ['rx','med']:
     k=stage+'_'+task;assert t['gates'][k]['correct']>=prev['gates'][k]['correct'];assert t['gates'][k]['invalid']<=prev['gates'][k]['invalid']
  cs=data['test_independent'];rs=rows(cs,s['state'],'test_independent');m=metrics(rs,cs);expected=json.loads((here/'results/independent.json').read_text())['trajectory'][idx]['metrics'];assert m['correct']==expected['correct'] and m['n']==expected['n'];result['states'].append({'round':s['round'],'cases_seen':s['cases_seen'],'cards':len(s['state']['cards']),'state_sha256':digest(s['state']),'independent':m})
 for split in ['test_rx','test_qa']:
  cs=data[split];initial=rows(cs,states[0]['state'],split);final=rows(cs,states[-1]['state'],split);result['methods'][split]={'initial':metrics(initial,cs),'final':metrics(final,cs)};result['comparisons']['initial_to_final_'+split]=paired(initial,final,cs);oldsplit='test' if split=='test_rx' else 'rxqa'
  for method in ['medagents','mdagents','grasp']:
   base=[]
   for c in cs:
    rr=json.loads((LOCAL.parent/'rxrsi-v35'/method/oldsplit/(digest(c['id'])+'.json')).read_text());base.append({'prediction':[rr['prediction']] if rr['prediction'] else None})
   result['comparisons'][method+'_to_final_'+split]=paired(base,final,cs)
  if split=='test_qa':
   base=[]
   for c in cs:
    rr=json.loads((LOCAL.parent/'rxrsi-v34/medagents'/oldsplit/(digest(c['id'])+'.json')).read_text());base.append({'prediction':[rr['prediction']] if rr['prediction'] else None})
   result['comparisons']['native_medagents_to_final_'+split]=paired(base,final,cs)
 ip=json.loads((BASE_HERE/'independent_protocol.json').read_text());bycase={c['id']:c for c in data['test_independent']};sub=[bycase[i] for i in ip['shortcut_ids']];reported=json.loads((here/'results/shortcuts.json').read_text());shortcut_audit={}
 for label,s0 in [('initial',states[0]),('final',states[-1])]:
  orig=rows(sub,s0['state'],'test_independent');base={r['case_id']:r['prediction'] for r in orig};shortcut_audit[label]={}
  for mode in ['permuted','no_patient']:
   cs=[];maps={}
   for c in sub:
    if mode=='no_patient':cs.append(dict(c,dialogue=c['question_only']));continue
    ix=list(range(len(c['options'])));random.Random(digest(['permutation',c['id']])).shuffle(ix)
    if ix==list(range(len(ix))):ix=ix[1:]+ix[:1]
    maps[c['id']]=ix;cs.append(dict(c,options=[c['options'][j] for j in ix],gold=sorted(chr(65+ix.index(ord(z)-65)) for z in target(c))))
   rr=rows(cs,s0['state'],'test_shortcut_'+mode);mm=metrics(rr,cs);assert mm['correct']==reported['result'][label][mode]['metrics']['correct'];shortcut_audit[label][mode]=mm
   if mode=='permuted':
    decoded={r['case_id']:sorted(chr(65+maps[r['case_id']][ord(z)-65]) for z in r['prediction']) if r['prediction'] is not None else None for r in rr};assert sum(decoded[i]==base[i] for i in base)==reported['result'][label][mode]['same_prediction_after_remap']
 result['shortcut_audit']=shortcut_audit
 if a.experiment=='44':
  amendment=json.loads((here/'runtime_amendment.json').read_text());assert sha(here/'runtime.py')==amendment['runtime_code_sha256'];assert sha(here/'resume.py')==amendment['resume_code_sha256'];assert sha(here/'test_freeze.json')==amendment['original_test_freeze_sha256'];folder=RUN/'runs'/digest(states[-1]['state'])/'test_rx'
  for filename,value in amendment['completed_file_hashes'].items():assert sha(folder/filename)==value
  result['runtime_amendment']={'completed_unchanged':amendment['completed_before'],'missing_completed':len(amendment['missing_case_ids']),'amendment_sha256':sha(here/'runtime_amendment.json'),'scope':'Deterministic focus-list normalization only; no completed prediction replaced.'}
 roots=[json.loads(p.read_text()) for p in (LOCAL.parent/('rxrsi-v'+a.experiment)/'roots').glob('*/*.json')];result['root_hypotheses']={'n':len(roots),'quote_valid':sum(r['support_quotes_valid'] for r in roots),'reference_status':dict(collections.Counter(r['root'].get('reference_status','missing') for r in roots)),'stages':dict(collections.Counter(r['root'].get('earliest_stage','missing') for r in roots)),'note':'Model-generated diagnoses; quote verification is provenance, not clinical adjudication or causal proof.'};result['applicability_statuses']=dict(allchecks);result['unique_evaluated_rows_audited']=len(seenpaths);result['ledger_increment_usd_shared_37_38']=ledger_total()-json.loads((BASE_HERE/'protocol.json').read_text())['ledger_start_usd'];save(here/'results/audit.json',result);print(json.dumps({k:result[k] for k in ['status','source_spans_checked','unique_evaluated_rows_audited','ledger_increment_usd_shared_37_38','methods']}))
if __name__=='__main__':main()
