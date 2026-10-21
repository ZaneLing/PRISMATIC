"""Failure-guided conditional program induction; no audit loader in this module."""
import argparse,random,copy
from common52 import *
from skills import *
def errors(pred,cases):return [sum(counts(p,c['gold'])[j] for p,c in zip(pred,cases)) for j in range(3)]
def delta(after,before):return [a-b for a,b in zip(after,before)]
def pareto(d):return max(d)<=0 and sum(d)<0
def candidate(cases,current,op,scope,unless):
 card={'operator':op,'when':scope,'unless':unless}
 out=predict(cases,current,[card]);ds=[delta(counts(a,c['gold'])[:3],counts(b,c['gold'])[:3]) for c,a,b in zip(cases,out,current)]
 active=[i for i,c in enumerate(cases) if applies(c,card)];negative=[i for i,c in enumerate(cases) if not applies(c,card)]
 if len(active)<4 or len(negative)<2:return None
 d=delta(errors(out,cases),errors(current,cases))
 if not pareto(d):return None
 return {'card':card,'training_delta':d,'active_training':len(active),'negative_training':len(negative),'helpful_training':sum(sum(ds[i])<0 for i in active),'harmful_training':sum(sum(ds[i])>0 for i in active)}
def propose(cases,current,state):
 scopes=sorted(set().union(*(tags(c) for c in cases)));out=[];existing={(x['operator'],x['when'],tuple(x['unless'])) for x in state}
 roots=errors(current,cases)
 allowed=[op for op in OPS if roots[0 if op=='recover_consensus' else 2 if op=='contextual_order' else 1]>0]
 for op in allowed:
  changed=[operate(c,p,op) for c,p in zip(cases,current)]
  ds=[delta(counts(a,c['gold'])[:3],counts(b,c['gold'])[:3]) for c,a,b in zip(cases,changed,current)]
  for scope in scopes:
   raw_harm=[i for i,c in enumerate(cases) if scope in tags(c) and sum(ds[i])>0]
   exceptions=[None]+[tag for tag in scopes if tag!=scope and sum(tag in tags(cases[i]) for i in raw_harm)>=2]
   variants=[]
   for exception in exceptions:
    exc=[exception] if exception else []
    if (op,scope,tuple(exc)) in existing:continue
    item=candidate(cases,current,op,scope,exc)
    if not item:continue
    protected=[i for i in raw_harm if exception and exception in tags(cases[i])]
    item['empirical_harmful_exceptions']=len(protected)
    item['counterexample_case_ids']=[cases[i]['case_id'] for i in protected]
    item['scope_negative_case_ids']=[c['case_id'] for c in cases if scope not in tags(c)][:4]
    item['root_hypothesis']={'recover_consensus':'missed identities supported by retrieved future-order records','prune_unsupported':'extra identities without retrieval, prior or predictor support','contextual_order':'selected identity has a weaker joint tuple than contextual retrieved consensus','reconcile_prior':'an unchanged historical tuple may have been copied into a new-order prediction'}[op]
    variants.append(item)
   if variants:
    # Infer exception on training only. Prefer simpler rule at equal training loss.
    variants.sort(key=lambda x:(sum(x['training_delta']),len(x['card']['unless']),digest(x['card'])))
    out.append(variants[0])
 return out
def public_history(hist):
 return [{k:v for k,v in row.items() if k not in ['seen_case_ids']} for row in hist]
def learn(seed,shuffle=False,backbone='qwen'):
 split={s:json.loads((PRIVATE/(s+'.json')).read_text()) for s in ['reflection','proposal','guard']}
 base={s:[r['orders'] for r in json.loads((PRIVATE/(backbone+'-'+s+'.json')).read_text())] if backbone!='tool' else [[c['catalogue'][i] for i in c['frozen_draft']] for c in cs] for s,cs in split.items()}
 for s in split:assert len(split[s])==len(base[s])
 rng=random.Random(seed);indices=list(range(len(split['reflection'])));rng.shuffle(indices)
 if shuffle:
  perm=list(range(len(indices)));random.Random(7252).shuffle(perm);truth=[c['gold'] for c in split['reflection']];split=copy.deepcopy(split)
  for i,c in enumerate(split['reflection']):c['gold']=truth[perm[i]]
 state=[];states=[[]];history=[]
 for roundno in range(1,7):
  ids=indices[:roundno*32];seen=[split['reflection'][i] for i in ids];bb=[base['reflection'][i] for i in ids];cur=predict(seen,bb,state)
  proposals=propose(seen,cur,state)
  pp=predict(split['proposal'],base['proposal'],state);gg=predict(split['guard'],base['guard'],state);pe=errors(pp,split['proposal']);ge=errors(gg,split['guard'])
  passing=[]
  for item in proposals:
   pd=delta(errors(predict(split['proposal'],pp,[item['card']]),split['proposal']),pe);item['proposal_delta']=pd
   if pareto(pd):passing.append(item)
  passing.sort(key=lambda x:(sum(x['proposal_delta']),sum(x['training_delta']),digest(x['card'])))
  accepted=None;attempts=[]
  for item in passing[:3]:
   gd=delta(errors(predict(split['guard'],gg,[item['card']]),split['guard']),ge);item['guard_delta']=gd
   attempts.append({k:v for k,v in item.items() if not k.endswith('case_ids')})
   if pareto(gd):accepted=item;break
  if accepted:
   card={**accepted['card'],'procedure':DESCRIPTION[accepted['card']['operator']],'root_hypothesis':accepted['root_hypothesis'],'round':roundno,'training_cases_seen':len(seen),'empirical_harmful_exceptions':accepted['empirical_harmful_exceptions'],'support_training':accepted['active_training'],'negative_training':accepted['negative_training']}
   state=state+[card]
   save(PRIVATE/(f'{backbone}-{seed}-'+('shuffle-' if shuffle else '')+f'accepted-{roundno}.json'),accepted)
  states.append(copy.deepcopy(state))
  row={'round':roundno,'seen':len(seen),'skills':len(state),'training_qualified_candidates':len(proposals),'proposal_pass':len(passing),'guard_attempts':attempts,'accepted':state[-1] if accepted else None,'training_errors':errors(predict(seen,bb,state),seen),'proposal_errors':errors(predict(split['proposal'],base['proposal'],state),split['proposal']),'guard_errors':errors(predict(split['guard'],base['guard'],state),split['guard']),'seen_case_ids':[c['case_id'] for c in seen]}
  history.append(row);print(json.dumps({k:row[k] for k in ['round','seen','skills','training_qualified_candidates','proposal_pass']}),flush=True)
 name=f'{backbone}-{seed}'+('-shuffle' if shuffle else '')
 save(PRIVATE/(name+'-states.json'),states);save(PRIVATE/(name+'-learning.json'),history)
 save(HERE/'results'/(name+'-learning.json'),{'seed':seed,'shuffled_feedback':shuffle,'backbone':backbone,'states':states,'history':public_history(history),'states_sha256':sha(PRIVATE/(name+'-states.json')),'audit_used_for_selection':False})
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--seed',type=int,default=52);p.add_argument('--shuffle',action='store_true');p.add_argument('--backbone',default='qwen');a=p.parse_args();learn(a.seed,a.shuffle,a.backbone)
