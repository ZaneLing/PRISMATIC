"""Evaluate frozen states once; never write training decisions from audit feedback."""
import numpy as np
from common52 import *
from skills import *
def bootstrap(base,after,cases):
 a=np.array([counts(p,c['gold']) for p,c in zip(base,cases)]);b=np.array([counts(p,c['gold']) for p,c in zip(after,cases)]);rng=np.random.default_rng(5252);vals=[]
 for _ in range(2000):
  ix=rng.integers(len(cases),size=len(cases));aa=a[ix].sum(0);bb=b[ix].sum(0)
  vals.append([(bb[j]-aa[j])/len(cases) for j in range(3)]+[100*(2*bb[3]/max(1,bb[4]+bb[5])-2*aa[3]/max(1,aa[4]+aa[5])),100*(2*bb[6]/max(1,bb[7]+bb[8])-2*aa[6]/max(1,aa[7]+aa[8]))])
 return dict(zip(['missed_drugs_per_patient','extra_drugs_per_patient','joint_errors_per_patient','drug_f1_pp','joint_f1_pp'],np.quantile(vals,[.025,.975],axis=0).T.tolist()))
def load_actor(name,split,cases):
 rows=json.loads((PRIVATE/(name+'-'+split+'.json')).read_text());assert [r['case_id'] for r in rows]==[c['case_id'] for c in cases];return rows
def summarize(pred,cases,base=None):
 out={'all':metrics(pred,cases),'strata':{}}
 for name,flag in [('single',False),('multi',True),('zero_target',None),('nonzero_target','nonzero')]:
  ix=[i for i,c in enumerate(cases) if ((len(c['context']['categories'])>=2)==flag if isinstance(flag,bool) else (not c['gold'] if flag is None else bool(c['gold'])))]
  if ix:out['strata'][name]=metrics([pred[i] for i in ix],[cases[i] for i in ix])
 if base is not None:
  out['paired95']=bootstrap(base,pred,cases);out['changed_patients']=sum({key(o) for o in a}!={key(o) for o in b} for a,b in zip(base,pred))
  changes=[sum(counts(a,c['gold'])[:3])-sum(counts(b,c['gold'])[:3]) for a,b,c in zip(pred,base,cases)]
  out['helped_patients']=sum(x<0 for x in changes);out['harmed_patients']=sum(x>0 for x in changes)
  components=[[counts(a,c['gold'])[j]-counts(b,c['gold'])[j] for j in range(3)] for a,b,c in zip(pred,base,cases)]
  out['any_primary_worsened_patients']=sum(max(x)>0 for x in components)
  out['omission_worsened_patients']=sum(x[0]>0 for x in components)
  out['pareto_improved_patients']=sum(max(x)<=0 and sum(x)<0 for x in components)
  out['patient_count_semantics']='helped/harmed mean summed reference discrepancy only, not clinical harm; inspect componentwise worsened counts'
 return out
def main():
 lock=json.loads((PRIVATE/'selection_lock.json').read_text())
 for name,h in lock['states'].items():assert sha(PRIVATE/(name+'-states.json'))==h
 cases=json.loads((PRIVATE/'audit.json').read_text());qr=load_actor('qwen','audit',cases);qb=[r['orders'] for r in qr]
 tool=[[c['catalogue'][i] for i in c['frozen_draft']] for c in cases]
 arms={'frozen_predictor':summarize(tool,cases),'fixed_qwen':summarize(qb,cases)};saved={'fixed_qwen':qb,'frozen_predictor':tool};curves={}
 for name in ['qwen-52','qwen-152','qwen-52-shuffle','tool-52']:
  states=json.loads((PRIVATE/(name+'-states.json')).read_text());base=tool if name.startswith('tool') else qb;curves[name]=[]
  for r,state in enumerate(states):
   pred=predict(cases,base,state);curves[name].append({'round':r,'seen':32*r,'skills':len(state),'metrics':metrics(pred,cases),'operator_counts':{op:sum(c['operator']==op for c in state) for op in OPS},'exception_clauses':sum(len(c['unless']) for c in state)})
  arms[name]=summarize(pred,cases,base);saved[name]=pred
 state=json.loads((PRIVATE/'qwen-52-states.json').read_text())[-1]
 no=predict(cases,qb,state,True);arms['qwen_unscoped']=summarize(no,cases,qb);saved['qwen_unscoped']=no
 static=qb
 for op in OPS:static=[operate(c,p,op) for c,p in zip(cases,static)]
 arms['static_all_repairs']=summarize(static,cases,qb);saved['static_all_repairs']=static
 transfer=cases[:128];lr=load_actor('llama','audit',transfer);lb=[r['orders'] for r in lr];lp=predict(transfer,lb,state)
 arms['llama_fixed_128']=summarize(lb,transfer);arms['llama_transfer_128']=summarize(lp,transfer,lb)
 activations=[]
 for card in state:
  active=[i for i,c in enumerate(cases) if applies(c,card)];exc=[i for i,c in enumerate(cases) if card['when'] in tags(c) and not applies(c,card)]
  effects=[]
  for i in exc:
   before=qb[i];after=operate(cases[i],before,card['operator']);effects.append(sum(counts(after,cases[i]['gold'])[:3])-sum(counts(before,cases[i]['gold'])[:3]))
  activations.append({'card':card,'active_patients':len(active),'exception_patients':len(exc),'exception_would_harm':sum(x>0 for x in effects),'exception_would_help':sum(x<0 for x in effects)})
 target=sum(len({o['drug_code'] for o in c['gold']}) for c in cases);covered=sum(len({o['drug_code'] for o in c['gold']}&{o['drug_code'] for o in c['catalogue'].values()}) for c in cases)
 complete=sum(all(o.get(f) for f in FIELDS) for c in cases for o in c['gold']);jointcovered=sum(len({key(o) for o in c['gold'] if all(o.get(f) for f in FIELDS)}&{key(o) for o in c['catalogue'].values()}) for c in cases)
 result={'status':'completed_frozen_new_patient_audit','selection_lock_sha256':sha(PRIVATE/'selection_lock.json'),'protocol_sha256':sha(HERE/'protocol.json'),'arms':arms,'curves':curves,'activations':activations,'candidate_drug_coverage':covered/max(1,target),'candidate_complete_joint_coverage':jointcovered/max(1,complete),'invalid_outputs':{'qwen':sum(r['invalid'] for r in qr),'llama':sum(r['invalid'] for r in lr)},'new_api_cost_usd':0,'patient_records_sent_to_cloud':0,'qwen_audit_tokens':{k:sum(r['receipt'][k] for r in qr) for k in ['input_tokens','output_tokens']}}
 save(HERE/'results/evaluation.json',result);save(PRIVATE/'audit_predictions.json',saved)
 # Restricted examples include failures as well as improvements; never published in Git.
 examples=[]
 for label,predicate in [('pareto_improved',lambda ds:max(ds)<=0 and sum(ds)<0),('component_tradeoff_or_worsened',lambda ds:max(ds)>0),('unchanged_failure',lambda ds:all(x==0 for x in ds))]:
  candidates=[]
  for i,(c,a,b) in enumerate(zip(cases,qb,saved['qwen-52'])):
   ds=[counts(b,c['gold'])[j]-counts(a,c['gold'])[j] for j in range(3)];d=sum(ds)
   if predicate(ds) and sum(counts(b,c['gold'])[:3])>0:candidates.append((i,d))
  for i,d in sorted(candidates,key=lambda z:(-abs(z[1]),z[0]))[:3]:
   c=cases[i];examples.append(dict(type=label,error_delta=d,case=c,before=qb[i],after=saved['qwen-52'][i],active_skills=[x for x in state if applies(c,x)]))
 save(PRIVATE/'case_studies.json',examples)
 print(json.dumps({k:{m:round(v['all'][m],4) for m in ['drug_f1','joint_f1','missed_drugs_per_patient','extra_drugs_per_patient','joint_errors_per_patient']} for k,v in arms.items()},indent=2),flush=True)
if __name__=='__main__':main()
