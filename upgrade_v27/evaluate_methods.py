"""Gated, resumable common test evaluation of every registered method and round."""
import hashlib,json,time
from pathlib import Path
import joblib,numpy as np,torch
from test_gate import check
from method_runtime import flatten,truths,make_model,predict as neural_predict,metrics as training_metrics
from control_features import features,neighbor_probabilities
from rule_memory import apply
from audit_rule_learning import predict as logistic_predict
from audit_controls import reconstruct
from evaluation_metrics import score,compare,paired
HERE=Path(__file__).resolve().parent;PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v27'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()
def save(p,x):
    tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(x,indent=2)+'\n');tmp.replace(p)

def main():
    gate=check()
    if gate['status']!='open':raise RuntimeError(f"Test remains closed: {len(gate['pending'])} selection/audit prerequisites remain.")
    lock={'gate':gate,'evaluation_addendum_sha256':sha(HERE/'evaluation_addendum.json'),
      'source_sha256':{f:sha(HERE/f) for f in ['evaluate_methods.py','evaluation_metrics.py','test_gate.py','method_runtime.py','rule_memory.py','control_features.py','audit_controls.py','audit_rule_learning.py']}}
    outdir=PRIVATE/'evaluation';outdir.mkdir(exist_ok=True)
    if (outdir/'lock.json').exists():assert json.loads((outdir/'lock.json').read_text())==lock
    else:save(outdir/'lock.json',lock)
    public=HERE/'results/test_summary.json';report={'status':'running','lock':lock,'panels':{}}
    source=joblib.load(PRIVATE/'visits.joblib');torch.set_num_threads(1)
    assert sha(PRIVATE/'visits.joblib')==json.loads((HERE/'results/cohort_manifest.json').read_text())['bundle_sha256']
    for panel in ['full','molecular']:
        b=joblib.load(PRIVATE/(panel+'-models.joblib'));cases=flatten(b['data']['test']);train=flatten(b['data']['train']);meds=b['medications']
        x,gold,_,people,_=reconstruct(source['data']['test'],source['vocab'],meds)
        if panel=='molecular':gold=[g&set(meds) for g in gold]
        assert all(set(c['gold'])==g and c['subject_hash']==p for c,g,p in zip(cases,gold,people))
        assert (x!=features(cases,b['sizes'])).nnz==0
        identity={'case_ids':[c['case_id'] for c in cases],'people':people.tolist(),'gold':[sorted(g) for g in gold],'medications':meds}
        save(outdir/(panel+'-case-identity.json'),identity);ident=digest(identity);rows={};patient_values={};keys=None
        report['panels'][panel]={'status':'running','case_identity_sha256':ident,'results':rows};save(public,report)
        def record(name,prob,threshold,selection,kind,seed=None,round_number=None):
            nonlocal keys
            path=outdir/(panel+'-'+name+'.npz');pred=np.asarray(prob)>=threshold
            result,values,pk=score(pred,gold,people,meds,b['ddi'],b['ddi_covered_indices'])
            compare(training_metrics(pred.astype(np.float32),cases,b,.5),result)
            if keys is None:keys=pk
            else:assert keys==pk
            np.savez(path,prediction=pred,patient_scores=values,patient_keys=np.array(pk))
            rows[name]={'kind':kind,'seed':seed,'round':round_number,'selection':selection,'metrics':result,'prediction_sha256':sha(path)}
            patient_values[name]=values;save(public,report)
            print(json.dumps({'panel':panel,'name':name,'patient_f1':result['patient_f1']}),flush=True)
        controls=json.loads((HERE/f'results/{panel}-controls.json').read_text());folder=PRIVATE/(panel+'-controls')
        train_x=features(train,b['sizes']);y=truths(train,meds)
        prevalence=joblib.load(folder/'prevalence.joblib');prob=np.tile(prevalence,(len(cases),1))
        record('prevalence',prob,controls['methods']['prevalence']['selection']['threshold'],controls['methods']['prevalence']['selection'],'conventional')
        prob=np.zeros((len(cases),len(meds)),dtype=np.float32)
        for i,c in enumerate(cases):
            if c['visit']>0:prob[i,c['source'][c['visit']-1]['codes'][2]]=1
        record('last_visit',prob,controls['methods']['last_visit']['selection']['threshold'],controls['methods']['last_visit']['selection'],'conventional')
        selection=controls['methods']['cosine_knn']['selection'];k=selection['k'];prob=neighbor_probabilities(x,train_x,cases,train,y,ks=(k,))[k]
        record('cosine_knn',prob,selection['threshold'],selection,'conventional')
        prob=logistic_predict(joblib.load(folder/'logistic.joblib'),x);selection=controls['methods']['structured_logistic']['selection']
        record('structured_logistic',prob,selection['threshold'],selection,'conventional')
        for method in (['ARMR','GAMENet'] if panel=='full' else ['ARMR','GAMENet','SafeDrug']):
            for seed in [42,137,2026]:
                z=json.loads((HERE/f'results/{panel}-{method}-seed{seed}.json').read_text());folder=PRIVATE/f'{panel}-{method}-seed{seed}'
                assert sha(folder/'best.pt')==z['best_model_sha256'];device=torch.device(z['lock']['device']);model=make_model(method,b,device)
                state=torch.load(folder/'best.pt',map_location=device,weights_only=False);model.load_state_dict(state['model'])
                start=time.perf_counter();prob=neural_predict(model,method,cases,b,device)
                record(f'{method}-seed{seed}',prob,z['selection']['threshold'],z['selection'],'author',seed)
                rows[f'{method}-seed{seed}']['test_inference_seconds']=time.perf_counter()-start
                del model,state
        for seed in [42,137,2026]:
            z=json.loads((HERE/f'results/{panel}-rsi-seed{seed}.json').read_text());folder=PRIVATE/f'{panel}-rsi-seed{seed}';rounds={}
            for row in z['rounds']:
                r=row['round'];part=folder/f'round{r}';assert sha(part/'base.joblib')==row['base_model_sha256']
                prob=logistic_predict(joblib.load(part/'base.joblib'),x);memories=json.loads((part/'memories.json').read_text());threshold=row['shared_policy_selection']['threshold'];rounds[r]=(prob,memories,threshold)
                for arm,memory in memories.items():
                    pred=apply(memory,x,prob,threshold);record(f'{arm}-seed{seed}-round{r}',pred,.5,{'training_patients':row['training_patients'],'memory_sha256':row['arms'][arm]['memory_sha256'],'memory_size':len(memory)},'raw_round',seed,r)
            for arm,selection in z['selections'].items():
                r=selection['round'];prob,memories,threshold=rounds[r];pred=apply(memories[arm],x,prob,threshold)
                record(f'{arm}-seed{seed}',pred,.5,selection,'rule_selected',seed,r)
            selected=z['selections']['own_error_rule_agent'];r=selected['round'];prob,memories,t=rounds[r];first_prob,first_memories,first_t=rounds[1]
            variants={'own_remove_memory':apply([],x,prob,t),'own_first_memory':apply(first_memories['own_error_rule_agent'],x,prob,t),
              'own_first_policy':apply(memories['own_error_rule_agent'],x,first_prob,first_t)}
            for name,pred in variants.items():record(f'{name}-seed{seed}',pred,.5,{'own_selected_round':r,'no_retuning':True},'intervention',seed)
        grouped={}
        for name,row in rows.items():
            if row['kind']=='raw_round':continue
            key=name.rsplit('-seed',1)[0];grouped.setdefault(key,[]).append(name)
        aggregates={}
        for method,names in grouped.items():
            aggregates[method]={'runs':len(names),'metrics':{metric:{'mean':float(np.mean([rows[n]['metrics'][metric] for n in names])),
              'seed_sd':float(np.std([rows[n]['metrics'][metric] for n in names],ddof=1)) if len(names)>1 else None} for metric in rows[names[0]]['metrics'] if isinstance(rows[names[0]]['metrics'][metric],(int,float))}}
        own=np.array([patient_values[f'own_error_rule_agent-seed{s}'] for s in [42,137,2026]])
        contrasts={method:paired(own,np.array([patient_values[n] for n in names])) for method,names in grouped.items() if method!='own_error_rule_agent'}
        report['panels'][panel].update(status='complete',methods=aggregates,own_agent_minus_comparator=contrasts)
        save(public,report)
    report['status']='executed_pending_independent_prediction_audit';save(public,report)
if __name__=='__main__':main()
