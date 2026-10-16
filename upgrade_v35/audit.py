"""Independent recount of completed runs, source spans, checks and learning gates."""
import json,collections,random,sys
import numpy as np
from common import HERE,RUN,LOCAL,ROOT,sha,digest,save
from workflow import verify
sys.path.insert(0,str(ROOT/'upgrade_v34'))
from medical_agents import parse_answer

def paired(a,b,cases):
 diff=np.array([int(y['prediction']==c['gold'])-int(x['prediction']==c['gold']) for x,y,c in zip(a,b,cases)])
 groups=collections.defaultdict(list)
 for i,c in enumerate(cases):groups[c.get('group_id',c['id'])].append(i)
 sums=np.array([diff[ix].sum() for ix in groups.values()]);sizes=np.array([len(ix) for ix in groups.values()]);rng=np.random.default_rng(35);draw=[]
 for _ in range(4000):
  sample=rng.integers(0,len(sums),len(sums));draw.append(sums[sample].sum()/sizes[sample].sum())
 return {'difference':float(diff.mean()),'ci95':np.quantile(draw,[.025,.975]).tolist(),'fixes':int((diff==1).sum()),'regressions':int((diff==-1).sum())}

def load_rows(cases,method,split,cards=None):
 rows=[]
 for c in cases:
  p=RUN/method/split/(digest(c['id'])+'.json') if cards is None else RUN/'memory'/digest(cards)/split/(digest(c['id'])+'.json')
  if cards==[] and not p.exists():p=RUN/'verified_evidence'/split/(digest(c['id'])+'.json')
  rows.append(json.loads(p.read_text()))
 assert [r['case_id'] for r in rows]==[c['id'] for c in cases]
 return rows

def main():
 data=json.loads((LOCAL/'data.json').read_text());impl=json.loads((HERE/'implementation.json').read_text());assert all(sha(HERE/f)==v for f,v in impl.items())
 labels={}
 old=json.loads((LOCAL.parent/'rxrsi-v11/labels.json').read_text())
 for r in old.values():
  if r.get('label'):labels[r['label']['id']]=r['label']
 sourcefiles=list((RUN/'label_requests').glob('*.json'))
 for p in sourcefiles:
  for l in json.loads(p.read_text()).get('labels',[]):labels[l['id']]=l
 result={'status':'audited_available','audit_sha256':sha(HERE/'audit.py'),'methods':{},'paired':{},'learning':[],
  'source_queries':len(sourcefiles),'distinct_labels':len(labels),'label_snapshot_sha256':digest(sorted((k,digest(v)) for k,v in labels.items())),
  'source_request_manifest':{p.name:sha(p) for p in sourcefiles},'source_spans_checked':0,'raw_cache_variants':0,
  'interval_note':'Exploratory paired bootstrap4000; scenario clusters for RxSafe and items for RxQA; no multiplicity correction.'}
 cache={};allrows={}
 def audit_rows(rows,cases,source=False):
  for r,c in zip(rows,cases):
   calls=r['calls'];assert sum(x['output_tokens'] for x in calls)<=4608
   assert len(calls)<=80
   for call in calls:
    key=call['request_sha256']
    if key not in cache:cache[key]=json.loads((LOCAL/'cache'/(key+'.json')).read_text())
    # Concurrent identical public requests may have separate valid raw receipts.
    # Preserve each row's actual response, count any difference from latest cache.
    if cache[key]['raw']!=call['raw']:result['raw_cache_variants']+=1
    assert not call.get('error') and call.get('model_returned')
   if source:
    answer=r.get('final',{}).get('final');answer=answer.strip().upper() if isinstance(answer,str) else None
    if answer not in [chr(65+i) for i in range(len(c['options']))]:answer=None
    assert answer==r['prediction']
    text=c['dialogue']+'\nOptions:\n'+'\n'.join(f'{chr(65+i)}. {o}' for i,o in enumerate(c['options']))
    assert verify(r['assessment'],r['evidence'],text)==r['checks']
    for z in r['evidence']['excerpts']:
     l=labels[z['label_id']];values=l[z['section']];values=[values] if isinstance(values,str) else values
     if 'offset' in z:assert values[z['paragraph']][z['offset']:z['offset']+len(z['quote'])]==z['quote']
     else:assert any(z['quote'] in v for v in values)
     result['source_spans_checked']+=1
  calls=[x for r in rows for x in r['calls']]
  return {'n':len(cases),'correct':sum(r['prediction']==c['gold'] for r,c in zip(rows,cases)),'invalid':sum(r['prediction'] is None for r in rows),
   'calls':len(calls),'mean_calls':len(calls)/len(rows),'input_tokens':sum(c['input_tokens'] for c in calls),'output_tokens':sum(c['output_tokens'] for c in calls),'logical_cost_usd':sum(c['cost_usd'] or 0 for c in calls)}
 for method in ('no_evidence','old_evidence','verified_evidence','active_evidence','grasp','medagents','mdagents'):
  result['methods'][method]={}
  for split in ('proposal','guard','test','rxqa'):
   p=HERE/'results'/f'{method}-{split}.json'
   if not p.exists():continue
   d=json.loads(p.read_text());cases=data['transfer'] if split=='rxqa' else data['parts'][split];rows=load_rows(cases,method,split)
   stats=audit_rows(rows,cases,method not in ('grasp','medagents','mdagents'));assert stats['correct']==d['correct'] and stats['n']==d['n']
   result['methods'][method][split]=dict(stats,accuracy=stats['correct']/stats['n'],statuses=d.get('statuses',{}));allrows[(method,split)]=rows
 learning=HERE/'results/learning.json'
 if learning.exists():
  states=json.loads(learning.read_text())['rounds'];feedback=json.loads((RUN/'learning/feedback.json').read_text());by={r['case_id']:r for r in feedback}
  train=list(data['parts']['train']);random.Random(42).shuffle(train);gold={c['id']:c['gold'] for c in train};assert len(by)==625
  for state in states:
   seen={c['id'] for c in train[:state['cases_seen']]}
   for card in state['cards']:
    assert set(card['support_ids']+card['counterexample_ids'])<=seen
    assert all(by[i]['prediction']!=gold[i] for i in card['support_ids'])
    assert all(by[i]['prediction']==gold[i] for i in card['counterexample_ids'])
   if state['round']:
    prev=states[state['round']-1];pm=state['candidate_proposal'];gm=state['candidate_guard'];accepted=pm['correct']>prev['proposal']['correct'] and pm['invalid']<=prev['proposal']['invalid'] and gm is not None and gm['correct']>prev['guard']['correct'] and gm['invalid']<=prev['guard']['invalid']
    assert state['accepted']==accepted
   result['learning'].append({'round':state['round'],'cases_seen':state['cases_seen'],'skills':len(state['cards']),'accepted':state.get('accepted',False),'proposal':state['proposal'],'guard':state['guard']})
  result['methods']['learned']={}
  for split in ('test','rxqa'):
   p=HERE/'results'/f'learned-{split}.json'
   if not p.exists():continue
   cases=data['transfer'] if split=='rxqa' else data['parts']['test'];rows=load_rows(cases,'learned',split,states[-1]['cards']);d=json.loads(p.read_text());stats=audit_rows(rows,cases,True);assert stats['correct']==d['correct'];result['methods']['learned'][split]=dict(stats,accuracy=stats['correct']/stats['n']);allrows[('learned',split)]=rows
 # Calibrated results reuse the exact underlying verified-agent calls.
 calibration=HERE/'results/calibration_selection.json'
 if calibration.exists():
  import pickle
  from calibrate import predict
  selected=json.loads(calibration.read_text());assert selected['guard_pass']
  assert sha(RUN/'calibration/selected.pkl')==selected['model_sha256']
  with (RUN/'calibration/selected.pkl').open('rb') as f:bundle=pickle.load(f)
  result['methods']['calibrated']={}
  for split in ('test','rxqa'):
   p=HERE/'results'/f'calibrated-{split}.json'
   if not p.exists():continue
   cases=data['transfer'] if split=='rxqa' else data['parts']['test'];base=allrows[('verified_evidence',split)]
   rows=json.loads((RUN/'calibration'/f'{split}.json').read_text());recomputed=predict(bundle,cases,base,selected['margin']);assert rows==recomputed
   d=json.loads(p.read_text());correct=sum(r['prediction']==c['gold'] for r,c in zip(rows,cases));assert correct==d['correct']
   stats=dict(result['methods']['verified_evidence'][split],correct=correct,accuracy=correct/len(cases),applied=sum(r['applied'] for r in rows))
   result['methods']['calibrated'][split]=stats;allrows[('calibrated',split)]=rows
   for method in ('medagents','mdagents'):
    native=[json.loads((LOCAL.parent/'rxrsi-v34'/method/split/(digest(c['id'])+'.json')).read_text()) for c in cases]
    result['paired'][method+'_native__calibrated__'+split]=paired(native,rows,cases)
   ds='rxsafebench' if split=='test' else 'rxqa'
   prior=json.loads((LOCAL/'grounded-grasp-v17-seed-42'/f'evolving_grounded-{ds}.json').read_text())
   result['paired']['prior_agent__calibrated__'+split]=paired(prior,rows,cases)
 bound=HERE/'results/learning_bound.json'
 if bound.exists():
  states=json.loads(bound.read_text())['rounds'];feedback=json.loads((RUN/'learning_bound/feedback.json').read_text());by={r['case_id']:r for r in feedback};gold={c['id']:c['gold'] for c in data['parts']['train']}
  assert len(by)==625
  for s0 in states:
   for card in s0['cards']:
    assert all(by[i]['prediction']!=gold[i] for i in card['support_ids']) and all(by[i]['prediction']==gold[i] for i in card['counterexample_ids'])
  result['learning_bound']=[{'round':x['round'],'cases_seen':x['cases_seen'],'accepted':x.get('accepted',False),'skills':len(x['cards']),'proposal':x['proposal'],'guard':x['guard']} for x in states]
 for split in ('proposal','guard','test','rxqa'):
  cases=data['transfer'] if split=='rxqa' else data['parts'][split]
  for before,after in [('no_evidence','verified_evidence'),('old_evidence','verified_evidence'),('verified_evidence','calibrated'),('medagents','calibrated'),('mdagents','calibrated'),('grasp','calibrated')]:
   if (before,split) in allrows and (after,split) in allrows:result['paired'][before+'__'+after+'__'+split]=paired(allrows[(before,split)],allrows[(after,split)],cases)
 if all(s in result['methods'].get(m,{}) for m in ('no_evidence','old_evidence','verified_evidence','medagents','mdagents','grasp','calibrated') for s in ('test','rxqa')):result['status']='passed_complete'
 save(HERE/'results/audit.json',result);print(json.dumps({'status':result['status'],'source_spans':result['source_spans_checked'],'cache_variants':result['raw_cache_variants'],'methods':{m:list(v) for m,v in result['methods'].items()}}))
if __name__=='__main__':main()
