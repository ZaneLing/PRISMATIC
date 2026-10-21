"""Declared development-driven amendment: componentwise counterexamples and rejection memory.

The original learner remains immutable. This variant is frozen before any audit
metrics are calculated; audit actor generation has already begun independently.
"""
import copy,random,datetime
from common52 import *
from skills import *
from learn import errors,delta,pareto,candidate,propose
def propose_refined(cases,current,state):
 scopes=sorted(set().union(*(tags(c) for c in cases)));out=[];existing={(x['operator'],x['when'],tuple(x['unless'])) for x in state}
 roots=errors(current,cases)
 for op in OPS:
  if not roots[0 if op=='recover_consensus' else 2 if op=='contextual_order' else 1]:continue
  ds=[delta(counts(operate(c,p,op),c['gold'])[:3],counts(p,c['gold'])[:3]) for c,p in zip(cases,current)]
  for scope in scopes:
   # A lost correct drug is a counterexample even if deleting other extras reduces total loss.
   harm=[i for i,c in enumerate(cases) if scope in tags(c) and max(ds[i])>0]
   exceptions=[None]+[tag for tag in scopes if tag!=scope and sum(tag in tags(cases[i]) for i in harm)>=2]
   variants=[]
   for ex in exceptions:
    unless=[ex] if ex else []
    if (op,scope,tuple(unless)) in existing:continue
    item=candidate(cases,current,op,scope,unless)
    if not item:continue
    protected=[i for i in harm if ex and ex in tags(cases[i])]
    item['empirical_harmful_exceptions']=len(protected);item['counterexample_case_ids']=[cases[i]['case_id'] for i in protected]
    item['root_hypothesis']='componentwise reference discrepancy; repair must not trade an omission increase for fewer extras'
    variants.append(item)
   if variants:
    variants.sort(key=lambda x:(sum(x['training_delta']),len(x['card']['unless']),digest(x['card'])));out.append(variants[0])
 return out
def run(seed,component=True,rejection=True):
 name=f'qwen-refined-{seed}' if component and rejection else f'qwen-counterexample-only-{seed}' if component else f'qwen-rejection-only-{seed}'
 split={s:json.loads((PRIVATE/(s+'.json')).read_text()) for s in ['reflection','proposal','guard']}
 base={s:[r['orders'] for r in json.loads((PRIVATE/('qwen-'+s+'.json')).read_text())] for s in split}
 ix=list(range(192));random.Random(seed).shuffle(ix);state=[];states=[[]];history=[];rejections={}
 for roundno in range(1,7):
  ids=ix[:32*roundno];seen=[split['reflection'][i] for i in ids];bb=[base['reflection'][i] for i in ids];cur=predict(seen,bb,state)
  candidates=(propose_refined if component else propose)(seen,cur,state);pp=predict(split['proposal'],base['proposal'],state);gg=predict(split['guard'],base['guard'],state);pe=errors(pp,split['proposal']);ge=errors(gg,split['guard']);passing=[]
  for item in candidates:
   pd=delta(errors(predict(split['proposal'],pp,[item['card']]),split['proposal']),pe);item['proposal_delta']=pd
   if pareto(pd):passing.append(item)
  passing.sort(key=lambda x:(sum(x['proposal_delta']),sum(x['training_delta']),digest(x['card'])))
  attempts=[];skipped=0;accepted=None
  for item in passing:
   signature=digest([state,item['card']])
   if rejection and signature in rejections:skipped+=1;continue
   if len(attempts)>=3:break
   gd=delta(errors(predict(split['guard'],gg,[item['card']]),split['guard']),ge);item['guard_delta']=gd
   attempts.append({k:v for k,v in item.items() if not k.endswith('case_ids')})
   if pareto(gd):accepted=item;break
   rejections[signature]={'card':item['card'],'guard_delta':gd,'round':roundno}
  if accepted:
   card={**accepted['card'],'procedure':DESCRIPTION[accepted['card']['operator']],'root_hypothesis':accepted['root_hypothesis'],'round':roundno,'training_cases_seen':len(seen),'empirical_harmful_exceptions':accepted['empirical_harmful_exceptions'],'support_training':accepted['active_training'],'negative_training':accepted['negative_training']}
   state=state+[card];save(PRIVATE/f'{name}-accepted-{roundno}.json',accepted)
  states.append(copy.deepcopy(state));history.append(dict(round=roundno,seen=len(seen),skills=len(state),training_qualified_candidates=len(candidates),proposal_pass=len(passing),guard_attempts=attempts,cached_rejections_skipped=skipped,rejected_memory_entries=len(rejections),accepted=state[-1] if accepted else None))
  print(json.dumps(history[-1]),flush=True)
 save(PRIVATE/(name+'-states.json'),states);save(HERE/'results'/(name+'-learning.json'),{'seed':seed,'componentwise_counterexamples':component,'rejection_memory':rejection,'states':states,'history':history,'states_sha256':sha(PRIVATE/(name+'-states.json')),'audit_used_for_selection':False})
if __name__=='__main__':
 assert not (HERE/'results/evaluation.json').exists(),'Cannot claim pre-audit-metric amendment after seeing audit scores'
 amendment={'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'development_driven_amendment_before_audit_metrics; audit actor generation already started','reason':'Original counterexamples used total loss while acceptance constrains each component; repeated rejected rules also consume guard slots.','changes':['Any component increase qualifies as harmful counterexample.','Cache guard-rejected state/program pairs; do not repeat identical failed proposals.'],'unchanged':['patient splits','source tools','actor responses','minimum2 harmful examples per exception','candidate scope support','componentwise gates','max3 new guard checks per round','six rounds and two streams'],'interpretation':'Exploratory updater variant; not the original prespecified primary. Original results remain visible.','source_sha256':sha(Path(__file__))}
 save(HERE/'results/learning_amendment.json',amendment)
 for seed in [52,152]:run(seed)
 run(52,rejection=False);run(52,component=False)
 names=['qwen-refined-52','qwen-refined-152','qwen-counterexample-only-52','qwen-rejection-only-52']
 save(HERE/'results/refined_freeze.json',{'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_sha256':sha(Path(__file__)),'states':{n:sha(PRIVATE/(n+'-states.json')) for n in names},'audit_metrics_observed':False,'audit_predictions_used':False,'factorial_controls':['original','component-counterexample only','rejection-memory only','both changes']})
