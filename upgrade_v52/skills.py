"""Bounded executable repair language. No target labels are visible to execution."""
from common52 import *
OPS=['recover_consensus','prune_unsupported','contextual_order','reconcile_prior']
DESCRIPTION={
 'recover_consensus':'Retrieve omitted drugs supported by at least5 of8 diagnosis-overlapping training neighbors; add at most2 complete joint templates, each supported by at least3 neighbors.',
 'prune_unsupported':'Remove at most2 selected drugs absent from retrieved targets and prior orders when the frozen predictor also assigns probability below0.1.',
 'contextual_order':'For selected identities, replace a non-consensus joint tuple by a complete tuple supported by at least3 neighbors and a strict majority of the drug-supporting neighbors.',
 'reconcile_prior':'Remove unchanged prior tuples only when fewer than2 diagnosis-overlapping neighbors contain that drug as a new target; same-field renewal can make this heuristic wrong.'}
def tags(c):
 x=c['context'];out={'multi' if len(x['categories'])>=2 else 'single','prior_present' if x['prior_orders'] else 'prior_missing','labs_present' if x['available_labs'] else 'labs_missing'}
 return out|{'dx:'+z for z in x['categories']}
def applies(c,card,unscoped=False):return unscoped or card['when'] in tags(c) and not set(card['unless'])&tags(c)
def operate(c,orders,op):
 # Access only precomputed training evidence, observed context and the current prediction.
 ev=c['evidence'];ds=ev['drug_support'];os=ev['order_support'];cat=c['catalogue'];p=ev['probabilities'];prior=c['context']['prior_orders'];bycode={}
 for oid,o in cat.items():
  if not all(o.get(f) for f in FIELDS):continue
  old=bycode.get(o['drug_code'])
  if old is None or (os[oid],oid)>(os[old],old):bycode[o['drug_code']]=oid
 result=list(orders);selected={o['drug_code'] for o in result}
 if op=='recover_consensus':
  eligible=[n for n in bycode if n not in selected and ds.get(n,0)>=5 and os[bycode[n]]>=3]
  for n in sorted(eligible,key=lambda n:(-ds[n],n))[:2]:result.append(cat[bycode[n]])
 elif op=='prune_unsupported':
  priorcodes={o['drug_code'] for o in prior};drop={n for n in sorted(selected,key=lambda n:(p.get(n,0),n)) if ds.get(n,0)==0 and n not in priorcodes and p.get(n,0)<.1}
  drop=set(sorted(drop,key=lambda n:(p.get(n,0),n))[:2]);result=[o for o in result if o['drug_code'] not in drop]
 elif op=='contextual_order':
  out=[]
  for o in result:
   n=o['drug_code'];oid=bycode.get(n);best=cat[oid] if oid else o
   if oid and os[oid]>=3 and os[oid]>ds.get(n,0)/2 and key(best)!=key(o):out.append(best)
   else:out.append(o)
  result=out
 elif op=='reconcile_prior':
  priorjoint={key(o) for o in prior};result=[o for o in result if not(key(o) in priorjoint and ds.get(o['drug_code'],0)<2)]
 else:raise ValueError('Unknown operator')
 return uniq(result)
def execute(c,orders,state,unscoped=False):
 for card in state:
  if applies(c,card,unscoped):orders=operate(c,orders,card['operator'])
 return orders
def predict(cases,base,state,unscoped=False):return [execute(c,p,state,unscoped) for c,p in zip(cases,base)]
