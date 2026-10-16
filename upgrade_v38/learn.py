"""Persistent trace-root ledger -> scoped edit -> intervention probe -> two gates."""
import json,re,random,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/"upgrade_v37"))
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
from common37 import ROOT,HERE,RUN,configure,save,sha,digest,call,json_object
import importlib.util
# Earlier experiment imports alter sys.path; bind this runner by its exact path.
_spec=importlib.util.spec_from_file_location('rx37_runner',HERE/'run.py')
_runner=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_runner)
batch,target=_runner.batch,_runner.target
BASE_HERE,BASE_RUN=HERE,RUN
HERE=ROOT/"upgrade_v38";RUN=BASE_RUN.parent/"rxrsi-v38";RUN.mkdir(exist_ok=True)
from evidence37 import FEATURES,BOUNDS,active_cards

ROOT_PROMPT='''Audit a failed TRAINING medication/medical decision. The reference is observed feedback, not infallible clinical truth. Trace the earliest observable mismatch among input interpretation, entity/product selection, missing evidence, rule applicability, quantitative check, and final option selection. Use actual retrieved spans and the recorded intermediate assessment, not a generic explanation. Distinguish a directly observed failure from a causal hypothesis. Do not rationalize an ambiguous reference into a hazardous clinical rule. Return JSON: {"earliest_stage":"...","root_hypothesis":"...","observed_gap":"reference versus predicted option, with decisive missing or contradicted condition","reference_status":"supported / ambiguous / inconsistent / insufficient_evidence","patient_quotes":["exact input substring"],"source_quotes":[{"evidence_id":"E1","quote":"exact excerpt substring"}],"minimal_process_change":"a generic procedure or retrieval change, never name-to-answer association","trigger_features":["allowed observable features"],"counterexample_requirement":"when that procedure must not apply or must not change a previously correct decision","confidence":"high/medium/low"}. A narrative root cause is a hypothesis until a controlled intervention actually improves held-out outcomes.'''
PROPOSE='''Propose ONE minimal persistent process-skill edit based on the root ledger and prior failed interventions. Return a new card, not a copy of the whole skill bank. It must address a recurring trace-level cause, preserve patient-conditioned applicability, and include counterexamples. Never encode drug identity frequency, reference letters, preferred drug names, isolated question answers, unsafe instructions, or a new medical rule unsupported by sources. Use general procedures for finding/checking evidence and distinguishing conditions. A skill is routed only when at least one trigger_any feature is true and no exclude_any feature is true. At least two support IDs must be observed errors in that triggered region; at least two counterexample IDs must be prior successes, including at least one inside the triggered region. Counterexamples must be explained, not merely listed. You may propose bounded retrieval settings affecting this region only. Do not preserve an unhelpful prior edit merely to make memory larger. Return JSON {"card":{"name":"short","trigger_any":["allowed feature"],"exclude_any":[],"exclude_reason":"specific boundary; unknown facts do not imply safety","procedure":"at most120 words, executable reasoning steps; no drug names or answer letters","retrieval_patch":{},"support_ids":["...","..."],"counterexample_ids":["...","..."],"counterexample_explanation":"why these successes must be preserved","root_ids":["..."]},"diagnosis":"how this differs from previous failed edits"}. Allowed retrieval keys and bounds are supplied. Empty card is allowed when no supported edit exists.'''

def metric_pair(old,new,cs):
 changes=[int(b['prediction']==target(c))-int(a['prediction']==target(c)) for a,b,c in zip(old,new,cs)]
 return {'fixes':sum(x==1 for x in changes),'regressions':sum(x==-1 for x in changes),'net':sum(changes),'changed':sum(a['prediction']!=b['prediction'] for a,b in zip(old,new))}
def trace_view(c,r):
 return {'id':c['id'],'question':c['dialogue'],'options':c['options'],'reference':target(c),'prediction':r['prediction'],'facts_and_plan':r['plan'],'products':r['evidence']['products'],'source_excerpts':r['evidence']['excerpts'],'assessment':r['assessment'],'checks':r['checks'],'decision':r['final'],'features':r['features'],'active_card_names':r['active_cards'],'retrieval_policy':r['retrieval_policy']}
def root_one(c,r,round_no):
 p=RUN/'roots'/f'r{round_no}'/(digest(c['id'])+'.json')
 prior=BASE_RUN/'roots'/f'r{round_no}'/(digest(c['id'])+'.json')
 if not p.exists() and prior.exists():
  old=json.loads(prior.read_text())
  if old['state_sha256']==r['state_sha256']:save(p,old)
 if p.exists():return json.loads(p.read_text())
 receipt=call(ROOT_PROMPT+'\nAllowed features:\n'+json.dumps(FEATURES)+'\nFULL TRAINING TRACE:\n'+json.dumps(trace_view(c,r)),'root_reflection',1600);obj=json_object(receipt['raw']);obj=obj if isinstance(obj,dict) else {};sources={e['evidence_id']:e['quote'] for e in r['evidence']['excerpts']};checks=[]
 for q in obj.get('patient_quotes',[]) if isinstance(obj.get('patient_quotes',[]),list) else []:checks.append(isinstance(q,str) and len(q)>=5 and q in c['dialogue'])
 for q in obj.get('source_quotes',[]) if isinstance(obj.get('source_quotes',[]),list) else []:checks.append(isinstance(q,dict) and isinstance(q.get('quote'),str) and len(q['quote'])>=8 and q['quote'] in sources.get(q.get('evidence_id'),'') )
 out={'case_id':c['id'],'round':round_no,'state_sha256':r['state_sha256'],'root':obj,'support_quotes_valid':bool(checks) and all(checks),'receipt':receipt,'status':'trace_based_hypothesis_not_proven_cause'};save(p,out);return out

def main():
 configure();protocol=HERE/'learning_protocol.json'
 if not protocol.exists():save(protocol,{'created_utc':datetime.now(timezone.utc).isoformat(),'code_sha256':sha(__file__),'prior_development_exposure':'Updater repaired after v37 training-feedback failures; same cohort reused, independent/main results not inspected. This is a second development experiment, not a fresh training sample.','repairs':['Separate explicit success/failure pools with input excerpts','Concrete invalid IDs plus legal replacement pool in schema repair','Only source-quote-valid roots with reference_status supported can sponsor skill proposals'],'rounds':4,'cases_per_round':100,'root_max_errors_per_round':24,'candidates_per_round':2,'probe_n_max':32,'same_inference_output_budget':4608,'root_source_checks':'Exact input/source quotation verification; hypotheses remain unproven until intervention.','gate':'At least2 net probe corrections; no loss on each proposal task with positive pooled delta; no loss on each guard task with positive pooled delta. No independent/test feedback.','shortcuts':'No numeric calibrator or raw training case retrieval in actor; no medication names allowed in skill procedure; no caseID or target letter in actor memory.','memory':'Rejected candidate diagnoses and observed regressions persist to inform later proposals. Successfully retained procedural cards and regional retrieval configurations are the learned state.'})
 assert json.loads(protocol.read_text())['code_sha256']==sha(__file__)
 data=json.loads((BASE_RUN/'data.json').read_text());train=data['train'];sf=RUN/'learning/states.json';hf=RUN/'learning/interventions.json';ff=RUN/'learning/feedback.json'
 if sf.exists():states=json.loads(sf.read_text());history=json.loads(hf.read_text());feedback=json.loads(ff.read_text())
 else:
  gates={}
  for split in ('proposal_rx','proposal_med','guard_rx','guard_med'):
   _,m=batch(data[split],{'cards':[]},split);gates[split]=m
  states=[{'round':0,'cases_seen':0,'state':{'cards':[]},'gates':gates,'accepted':False}];history=[];feedback=[];save(sf,states);save(hf,history);save(ff,feedback)
 # Only actual short source drug aliases are forbidden; ordinary medical concepts remain allowed.
 from evidence import LabelTool
 aliases=[k for k in LabelTool().by_alias if len(k)>=5 and len(k.split())<=5]
 for round_no in range(len(states),5):
  prev=states[-1];state=prev['state'];new=train[(round_no-1)*100:round_no*100];rows,tm=batch(new,state,'train');feedback+=rows;save(ff,feedback);seen=train[:round_no*100];by={r['case_id']:r for r in feedback};errors=[c for c in new if by[c['id']]['prediction']!=target(c)];errors.sort(key=lambda c:digest(['root',round_no,c['id']]));errors=errors[:24];roots=[]
  with ThreadPoolExecutor(max_workers=12) as pool:
   for f in as_completed([pool.submit(root_one,c,by[c['id']],round_no) for c in errors]):roots.append(f.result())
  roots.sort(key=lambda r:r['case_id']);eligible_roots=[r for r in roots if r['support_quotes_valid'] and r['root'].get('reference_status')=='supported'];all_errors=[c for c in seen if by[c['id']]['prediction']!=target(c)];success=[c for c in seen if by[c['id']]['prediction']==target(c)];support_pool={c['id'] for c in all_errors};counter_pool={c['id'] for c in success};root_ids={r['case_id'] for r in eligible_roots}
  # Accessible process card view omits labels, source case texts and IDs during inference.
  samples=[{'id':c['id'],'features':by[c['id']]['features'],'success':c['id'] in counter_pool,'question_summary':by[c['id']]['plan'].get('focus',''),'case_excerpt':c['dialogue'][:600]} for c in sorted(seen,key=lambda c:digest(['cards',round_no,c['id']]))]
  accepted=False;selected=state;selected_gates=prev['gates'];round_trials=[]
  for attempt in range(2):
   prompt=PROPOSE+'\nFEATURES:\n'+json.dumps(FEATURES)+'\nBOUNDS:\n'+json.dumps(BOUNDS)+'\nCURRENT STATE:\n'+json.dumps(selected)+'\nROOT LEDGER:\n'+json.dumps([{k:v for k,v in r.items() if k!='receipt'} for r in eligible_roots])+'\nALLOWED FAILURE SUPPORT CASES:\n'+json.dumps([x for x in samples if not x['success']])+'\nALLOWED SUCCESSFUL COUNTEREXAMPLES (only these IDs are allowed):\n'+json.dumps([x for x in samples if x['success']])+'\nPREVIOUS INTERVENTIONS:\n'+json.dumps(history[-6:])
   messages=prompt;card=None;receipts=[];schema_errors=[]
   for repair in range(2):
    receipt=call(messages,'skill_proposal',2200);receipts.append(receipt);obj=json_object(receipt['raw']);raw=obj.get('card') if isinstance(obj,dict) else None;why=[]
    if not isinstance(raw,dict):why=['missing_card']
    else:
     for k in ('name','exclude_reason','procedure','counterexample_explanation'):
      if not isinstance(raw.get(k),str) or not raw[k].strip():why.append('missing_'+k)
     trig=raw.get('trigger_any',[]);ex=raw.get('exclude_any',[]);pos=raw.get('support_ids',[]);neg=raw.get('counterexample_ids',[]);ri=raw.get('root_ids',[])
     if not isinstance(trig,list) or not trig or any(t not in FEATURES for t in trig):why.append('invalid_trigger')
     if not isinstance(ex,list) or any(t not in FEATURES for t in ex):why.append('invalid_exclusion')
     if not isinstance(pos,list) or len(set(pos))<2 or not set(pos)<=support_pool:why.append('support_ID_roles')
     if not isinstance(neg,list) or len(set(neg))<2 or not set(neg)<=counter_pool:why.append('counterexample_ID_roles')
     if not isinstance(ri,list) or not ri or not set(ri)<=root_ids:why.append('root_ID_roles')
     if not why:
      if not all(active_cards({'cards':[raw]},by[i]['features']) for i in pos):why.append('support_not_in_trigger_region')
      if not any(active_cards({'cards':[raw]},by[i]['features']) for i in neg):why.append('no_success_inside_trigger_region')
     patch=raw.get('retrieval_patch',{})
     if not isinstance(patch,dict) or any(k not in BOUNDS or type(v) not in (int,float) or not BOUNDS[k][0]<=v<=BOUNDS[k][1] for k,v in patch.items()):why.append('out_of_bounds_retrieval')
     s=' '+re.sub('[^a-z0-9]+',' ',raw.get('procedure','').lower())+' '
     if any(' '+alias+' ' in s for alias in aliases):why.append('medication_name_in_procedure')
     if len(raw.get('procedure','').split())>150:why.append('procedure_too_long')
    schema_errors.append(why)
    role_feedback={'invalid_counterexample_ids':[i for i in raw.get('counterexample_ids',[]) if i not in counter_pool] if isinstance(raw,dict) else [],'allowed_success_ids':sorted(counter_pool),'allowed_support_ids':sorted(support_pool),'allowed_root_ids':sorted(root_ids)}
    if not why:card=raw;break
    messages=prompt+'\nYour previous response:\n'+receipt['raw']+'\nRepair these concrete schema/role errors without adding unsupported medical claims:\n'+json.dumps(why)+'\nEXACT ROLE CORRECTION (do not repeat invalid IDs):\n'+json.dumps(role_feedback)
   trial={'round':round_no,'attempt':attempt+1,'schema_errors':schema_errors,'card':card,'accepted':False};save(RUN/'learning'/f'proposal-r{round_no}-a{attempt+1}.json',{'receipts':receipts,'trial':trial})
   if card is None:trial['rejection']='schema';history.append(trial);save(hf,history);round_trials.append(trial);continue
   candidate={'cards':[c for c in selected['cards'] if c['name']!=card['name']]+[card]};candidate['cards']=candidate['cards'][-8:]
   ids=set(card['support_ids']+card['counterexample_ids']);probe=[c for c in seen if c['id'] in ids]
   remaining=sorted([c for c in seen if c['id'] not in ids and active_cards(candidate,by[c['id']]['features'])],key=lambda c:digest(['probe',round_no,c['id']]))
   probe=(probe+remaining)[:32]
   before,bm=batch(probe,selected,'probe');after,am=batch(probe,candidate,'probe');delta=metric_pair(before,after,probe);trial['probe']={**delta,'n':len(probe),'before':bm['correct'],'after':am['correct'],'invalid_before':bm['invalid'],'invalid_after':am['invalid']}
   regress=[trace_view(c,b) for c,a,b in zip(probe,before,after) if a['prediction']==target(c) and b['prediction']!=target(c)];trial['observed_regression_summaries']=[{'id':x['id'],'focus':x['facts_and_plan'].get('focus'),'reference':x['reference'],'prediction':x['prediction'],'decision':x['decision']} for x in regress[:3]];save(RUN/'learning'/f'probe-regressions-r{round_no}-a{attempt+1}.json',regress)
   regression_roots=[]
   for c,a,b in [(c,a,b) for c,a,b in zip(probe,before,after) if a['prediction']==target(c) and b['prediction']!=target(c)][:3]:
    rr=root_one(c,b,str(round_no)+'-a'+str(attempt+1)+'-regression');regression_roots.append({'case_id':c['id'],'root':rr['root'],'support_quotes_valid':rr['support_quotes_valid']})
   trial['regression_root_hypotheses']=regression_roots
   gate=delta['net']>=2 and am['invalid']<=bm['invalid'];metrics={}
   if not gate:trial['rejection']='training_intervention'
   for stage in ('proposal','guard'):
    if not gate:break
    for task in ('rx','med'):
     split=stage+'_'+task;_,metrics[split]=batch(data[split],candidate,split)
    bases=selected_gates;gate=all(metrics[stage+'_'+t]['correct']>=bases[stage+'_'+t]['correct'] and metrics[stage+'_'+t]['invalid']<=bases[stage+'_'+t]['invalid'] for t in ('rx','med')) and sum(metrics[stage+'_'+t]['correct']-bases[stage+'_'+t]['correct'] for t in ('rx','med'))>0
    if not gate:trial['rejection']=stage
   trial['gates']=metrics;trial['accepted']=bool(gate)
   if gate:selected=candidate;selected_gates=metrics;accepted=True
   history.append(trial);round_trials.append(trial);save(hf,history);print(json.dumps({'round':round_no,'attempt':attempt+1,'accepted':gate,'probe':trial['probe'],'rejection':trial.get('rejection')}),flush=True)
   if gate:break
  states.append({'round':round_no,'cases_seen':round_no*100,'state':selected,'gates':selected_gates,'accepted':accepted,'new_batch':tm,'root_count':len(roots),'root_eligible':len(eligible_roots),'root_quote_valid':sum(r['support_quotes_valid'] for r in roots),'trials':round_trials});save(sf,states);save(HERE/'results/learning_progress.json',{'status':'running','rounds':states})
 save(HERE/'results/learning.json',{'status':'frozen','frozen_utc':datetime.now(timezone.utc).isoformat(),'rounds':states,'protocol_sha256':sha(protocol),'interventions_sha256':sha(hf)});print('Learning trajectory frozen.',flush=True)
if __name__=='__main__':main()
