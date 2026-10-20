"""Cumulative root-cause reflection, executable skills, effect checks and guarded updates."""
import collections,json,time,re
import common
common.PRIVATE=common.PRIVATE/"cloud"
from common import *
from cloud_proposer import propose
from actor import run,view
from policy import *
from local_backend import Backend

def execute(b,cases,state,tag):
 sig=digest([b.model_hash,state,cases, {n:sha(HERE/n) for n in ['actor.py','policy.py','evidence_tool.py','local_backend.py']}]);path=PRIVATE/(tag+'.json')
 if path.exists():
  d=json.loads(path.read_text())
  if d['signature']==sig:return d['rows']
 rows=run(b,cases,'rxrsi',state,tag);save(path,{'signature':sig,'rows':rows});return rows

def evaluated(rows,cases):return metrics(rows,[{**c,'catalogue':r['catalogue']} for c,r in zip(cases,rows)])
def error(c,r):
 g={o['drug_name'] for o in c['gold']};p={o['drug_name'] for o in r['orders']};cat={o['drug_name'] for o in r['catalogue'].values()}
 from route_evidence import route_status
 return {'candidate_omission':len(g-cat),'selection_omission':len((g&cat)-p),'extra_drugs':len(p-g),
  'joint_field_mismatch':sum(not any(key(a)==key(o) for a in r['orders']) for o in c['gold'] if o['drug_name'] in p and all(o.get(f) is not None for f in CORE)),
  'unattributed_route_excerpt':sum(route_status(r['catalogue'][s['order_id']].get('route'),s.get('source_route'))=='no_declared_overlap' for s in r['evidence']['spans']),
  'unchecked_facts':max(0,len(c['input'].split(' ; '))-len(set(r['checks']['verified_input_quotes'])))}
def reflection_packet(records):
 total=collections.Counter();by_scope=collections.defaultdict(collections.Counter);entries=[]
 for c,r in records:
  e=error(c,r);total.update(e)
  for domain in scopes(c):by_scope[domain].update({'cases':1,**e})
  entries.append((c,r,e))
 # Six distinct demonstrations, stratified by actual error stage rather than lab presence alone.
 examples=[];seen=set()
 for root in ['candidate_omission','selection_omission','extra_drugs','joint_field_mismatch','unattributed_route_excerpt','unchecked_facts']:
  pool=[x for x in entries if x[0]['case_id'] not in seen and x[2][root]>0]
  if not pool:continue
  c,r,e=max(pool,key=lambda x:x[2][root]);seen.add(c['case_id'])
  examples.append({'focus':root,'observed_input':c['input'],'scopes':sorted(scopes(c)),'predicted_orders':r['orders'],'recorded_training_orders':c['gold'],
   'candidate_names':[o['drug_name'] for o in r['catalogue'].values()],'stage_errors':e,'checked_facts':r['checks']['verified_input_quotes'],
   'assessment':r['assessment'],'evidence':r['evidence']})
 return {'cases':len(records),'all_case_root_counts':{k:v for k,v in total.items() if k in REPAIRABLE},'process_observations_not_causal_errors':{k:v for k,v in total.items() if k not in REPAIRABLE},'by_observable_context':{k:dict(v) for k,v in by_scope.items()},'examples':examples,
  'interpretation':'Reference discrepancies locate measurable pipeline errors; they do not alone establish clinical indications or uniquely correct treatment.'}
def public_card(c):return {k:c[k] for k in ['operator','when','unless']}|{'sha256':digest(c)}
def public_trials(t):
 d={k:v for k,v in t.items() if k not in ['card','probe']};d['card']=public_card(t['card']) if t.get('card') and all(k in t['card'] for k in ['operator','when','unless']) else {'invalid':True}
 if 'probe' in t:d['probe']={k:v for k,v in t['probe'].items() if k!='changes'}
 return d

def save_learning(rounds,state,ledger,complete):
 full={'complete':complete,'rounds':rounds,'state':state,'rejection_ledger':ledger};save(PRIVATE/'learning.json',full)
 public=json.loads(json.dumps(full));public['state']={'cards':[public_card(c) for c in state['cards']]};public.pop('rejection_ledger')
 for r in public['rounds']:
  r['state']={'cards':[public_card(c) for c in r['state']['cards']]};r['trials']=[public_trials(t) for t in r.get('trials',[])]
 save(HERE/'results/cloud/learning.json',public)

def main():
 data=load_cases();b=Backend();state={'cards':[]};records=[];ledger=[]
 pm=evaluated(execute(b,data['proposal'],state,'proposal-initial'),data['proposal']);gm=evaluated(execute(b,data['guard'],state,'guard-initial'),data['guard'])
 rounds=[{'round':0,'cases_seen':0,'state':state,'proposal':pm,'guard':gm,'trials':[],'retained':0,'root_memory_cases':0}]
 save_learning(rounds,state,ledger,False)
 for rd in range(1,4):
  cs=data['train'][(rd-1)*24:rd*24];before=execute(b,cs,state,f'train-{rd}-before');records.extend(zip(cs,before));packet=reflection_packet(records)
  save(PRIVATE/f'root-memory-{rd}.json',packet)
  save(HERE/f'results/cloud/root-counts-{rd}.json',{k:v for k,v in packet.items() if k!='examples'})
  prompt='''You are the local RxRSIAgent updater. Read cumulative discrepancies from ALL seen training cases and stage-stratified examples. Diagnose the earliest repairable failure, distinguish absent candidates from selection errors, and propose up to TWO different executable process skills. These are observed context groups, not diagnoses. Never infer a disease from a medicine. Reference orders are training feedback; do not condition runtime actions on reference membership or copy a drug action. You can change candidate recall, evidence routing/diversity, fact checking, or temporal reconciliation. These operators are already implemented; do not claim to invent code or change weights.
Important causal constraints: candidate_omission can ONLY be repaired by candidate_wide48 or candidate_retrieval48. Checking more facts CANNOT add a candidate. All original input is ALREADY visible to the LLM, so fact_all only repeats input at the checker. Unchecked-fact counts are process measurements, NOT evidence of prescribing error. joint_field_mismatch cannot be repaired by this fixed-template interface; record it as unresolved. Temporal reconciliation must permit repeated identical-field orders and frequency changes; do not require every target to differ in dose/route. The ranked_draft operator exposes the existing fixed classifier's top-eight prediction as a tool input; it does not train a calibrator.
For the FIRST proposal, address candidate_omission if it is nonzero; for the SECOND, address selection_omission or extra_drugs. Use the typed root/operator mapping. Repair the earliest stage before rephrasing later-stage instructions.
Return strict JSON: {"proposals":[{"root_cause":"mechanistic hypothesis","cluster":"error category","operator":"one listed operator","when":"one listed scope","unless":["zero or more listed executable exception scopes"],"instruction":"general procedure under 90 words, no drug/dose commands","counterexample":"general runtime exception or limitation; observed numeric values are allowed here"}]}. Do not refer to T1/T2 or case IDs in counterexamples. Choose applicable scopes supported by multiple examples. Do not repeat previously ineffective operator/scope pairs. You may propose fewer if unsupported, but explain an empty result in a reason field. All proposed interventions are measured for execution and output changes before the development gate. No special credit is given for writing a card.
'''
  prompt+='\nROOT/OPERATOR CONTRACT: '+json.dumps({k:sorted(v) for k,v in REPAIRABLE.items()})+'\nOPERATORS: '+json.dumps(PROCEDURES)+'\nSCOPES: '+json.dumps(sorted(SCOPES|set(packet['by_observable_context'])))+'\nCURRENT STATE: '+json.dumps(state)+'\nCOMPLETE REJECTION/ACCEPTANCE LEDGER: '+json.dumps(ledger)+'\nCUMULATIVE OBSERVATIONS: '+json.dumps(packet)
  msgs=[{'role':'system','content':'Propose testable, scoped changes in executable JSON; no hidden GT predicates.'},{'role':'user','content':prompt}]
  rec=propose(packet,state,ledger,f'reflect-{rd}');save(PRIVATE/f'reflect-{rd}.json',rec);obj=parse(rec['raw']);proposals=obj.get('proposals',[]);trials=[]
  if not isinstance(proposals,list):proposals=[]
  for attempt,card in enumerate(proposals[:2]):
   trial={'card':card,'accepted':False};reason=validate(card,[c for c,r in records]);
   if not reason and attempt==0 and packet['all_case_root_counts'].get('candidate_omission',0)>0 and card['cluster']!='candidate_omission':reason='first_proposal_must_address_earliest_candidate_omission'
   trial['rejection']=reason
   if reason:
    repairmsgs=msgs+[{'role':'assistant','content':rec['raw']},{'role':'user','content':'Repair this proposal once: '+json.dumps(card)+'\nExact error: '+reason+'. Return one JSON object with the proposal fields only. Numeric counterexamples are allowed; operational conditions must use listed observable scopes.'}]
    fix=propose(packet,state,ledger,f'repair-{rd}-{attempt}',repair={'proposal':card,'error':reason});save(PRIVATE/f'repair-{rd}-{attempt}.json',fix);card=normalize_card(parse(fix['raw']));trial.update(card=card,rejection=validate(card,[c for c,r in records]));reason=trial['rejection']
   if not reason:
    # Reject exact already retained instructions or redundant operator settings through measured effect.
    candidate={'cards':state['cards']+[card]};current=before
    probe=effect_probe(cs,current,state,candidate);trial['probe']=probe
    if probe['effective_cases']==0:trial['rejection']='no_executable_effect_on_current_batch'
    else:
     after=execute(b,cs,candidate,f'train-{rd}-trial-{attempt}');changes=sum({key(o,FIELDS) for o in a['orders']}!={key(o,FIELDS) for o in z['orders']} for a,z in zip(current,after))
     trial.update(training_before=evaluated(current,cs),training_after=evaluated(after,cs),changed_training_outputs=changes)
     if changes==0:trial['rejection']='no_semantic_output_change'
     elif trial['training_after']['promotion_score']<=trial['training_before']['promotion_score']:trial['rejection']='no_training_agreement_gain'
     else:
      p=evaluated(execute(b,data['proposal'],candidate,f'proposal-{rd}-{attempt}'),data['proposal']);g=evaluated(execute(b,data['guard'],candidate,f'guard-{rd}-{attempt}'),data['guard'])
      ok=p['promotion_score']>pm['promotion_score'] and g['drug_micro_f1']>=gm['drug_micro_f1'] and g['core_order_micro_f1']>=gm['core_order_micro_f1']
      trial.update(proposal_before=pm,guard_before=gm,candidate_proposal=p,candidate_guard=g,accepted=ok,rejection=None if ok else 'development_gate')
      if ok:state=candidate;pm=p;gm=g;before=after
   trials.append(trial)
   ledger.append({'round':rd,'operator':card.get('operator') if isinstance(card,dict) else None,'scope':card.get('when') if isinstance(card,dict) else None,'rejection':trial['rejection'],'accepted':trial['accepted'],
    'applicable_cases':trial.get('probe',{}).get('applicable_cases',0),'effect_cases':trial.get('probe',{}).get('effective_cases',0),'changed_outputs':trial.get('changed_training_outputs',0),
    'training_delta':trial.get('training_after',{}).get('promotion_score',0)-trial.get('training_before',{}).get('promotion_score',0) if 'training_after' in trial else None,
    'proposal_delta':trial.get('candidate_proposal',{}).get('promotion_score',0)-trial.get('proposal_before',{}).get('promotion_score',0) if 'candidate_proposal' in trial else None})
   save(PRIVATE/'rejection-ledger.json',ledger);print(json.dumps({'round':rd,'trial':attempt,'accepted':trial['accepted'],'rejection':trial['rejection']}),flush=True)
  rounds.append({'round':rd,'cases_seen':len(records),'state':state,'proposal':pm,'guard':gm,'trials':trials,'retained':len(state['cards']),'root_memory_cases':len(records),
    'root_clusters':sum(v>0 for v in packet['all_case_root_counts'].values()),'context_groups_observed':sum(k in GROUPS for k in packet['by_observable_context'])})
  save_learning(rounds,state,ledger,False)
 save_learning(rounds,state,ledger,True)
 save(PRIVATE/'freeze.json',{'time':time.time(),'states':[r['state'] for r in rounds],'state_sha256':[digest(r['state']) for r in rounds],'audit_evaluated':False,'selection_used_audit':False})
 print('Learning finished; all states frozen before audit.',flush=True)
 # Evaluate UNIQUE retained states after selection; same hash -> same cached audit prediction.
 seen={};curve=[]
 for r in rounds:
  h=digest(r['state'])
  if h not in seen:seen[h]=execute(b,data['audit'],r['state'],f'audit-round-{r["round"]}')
  curve.append({'round':r['round'],'cases_seen':r['cases_seen'],'retained':r['retained'],'state_sha256':h,'metrics':evaluated(seen[h],data['audit'])})
 save(HERE/'results/cloud/trajectory.json',{'complete':True,'trajectory':curve,'unique_states':len(seen),'audit_used_for_selection':False,'audit_cases':len(data['audit']),'historically_exposed':True})
 print('Audit completed.',flush=True)
if __name__=='__main__':main()
