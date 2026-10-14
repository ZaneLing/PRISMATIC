"""Execute all frozen program states on the already registered common test."""
import hashlib,json,sys,time
from pathlib import Path
import joblib,numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;sys.path[:0]=[str(ROOT),str(ROOT/'upgrade_v27')]
from upgrade_v30.common_test_gate import check
from upgrade_v27.control_features import features
from upgrade_v27.method_runtime import flatten
from upgrade_v27.evaluation_metrics import score,paired
from upgrade_v29.programs import apply
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted';OUTPUT=PRIVATE/'prismatic-v30/common-test'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()
def save(p,x):
    t=p.with_suffix('.tmp');t.write_text(json.dumps(x,indent=2)+'\n');t.replace(p)
def probability(models,x):return np.column_stack([np.full(x.shape[0],m) if isinstance(m,float) else m.predict_proba(x)[:,1] for m in models])
def arm_names(version):
    if version==29:return json.loads((ROOT/'upgrade_v29/protocol.json').read_text())['arms']
    return ['raw_policy','calibrated_policy']+[f'{m}_C{c}P{p}' for m in ('greedy','own','shuffled') for c in (0,1) for p in (0,1)]
def visit_f1(pred,gold,meds):
    out=[]
    for p,g in zip(pred,gold):
        chosen={meds[i] for i in np.flatnonzero(p)};n=len(chosen)+len(g);out.append(2*len(chosen&g)/n if n else 1.)
    return np.array(out)
def mean_rows(rows):
    return {k:{'mean':float(np.mean([r[k] for r in rows])),'seed_sd':float(np.std([r[k] for r in rows],ddof=1)) if len(rows)>1 else None} for k in rows[0] if isinstance(rows[0][k],(float,int))}
def transitions(a,b):
    d=a-b;return {'improved':int((d>1e-12).sum()),'regressed':int((d< -1e-12).sum()),'unchanged':int((abs(d)<=1e-12).sum()),'visits':len(d)}
def main():
    gate=check()
    if gate['status']!='open':raise RuntimeError(f"Common extension remains closed: {len(gate['pending'])} prerequisites.")
    OUTPUT.mkdir(exist_ok=True)
    paths=['upgrade_v30/evaluate_program_tests.py','upgrade_v30/common_test_gate.py','upgrade_v29/programs.py','upgrade_v27/evaluation_metrics.py','upgrade_v27/control_features.py','upgrade_v27/method_runtime.py']
    lock={'gate':gate,'addendum_sha256':sha(HERE/'common_test_addendum.json'),'sources':{p:sha(ROOT/p) for p in paths}}
    if (OUTPUT/'lock.json').exists():assert json.loads((OUTPUT/'lock.json').read_text())==lock
    else:save(OUTPUT/'lock.json',lock)
    out={'status':'running','lock':lock,'panels':{},'api_calls':0,'new_training':False};path=HERE/'results/common_test_summary.json'
    if path.exists():
        previous=json.loads(path.read_text());assert previous['lock']==lock
        if previous['status']=='executed_pending_independent_prediction_audit':return
    original=json.loads((ROOT/'upgrade_v27/results/test_summary.json').read_text())
    for panel in ('full','molecular'):
        b=joblib.load(PRIVATE/f'prismatic-v27/{panel}-models.joblib');cases=flatten(b['data']['test']);x=features(cases,b['sizes']);meds=b['medications'];gold=[set(c['gold']) for c in cases];people=[c['subject_hash'] for c in cases]
        identity={'case_ids':[c['case_id'] for c in cases],'people':people,'gold':[sorted(g) for g in gold],'medications':meds}
        assert identity==json.loads((PRIVATE/f'prismatic-v27/evaluation/{panel}-case-identity.json').read_text())
        assert digest(identity)==original['panels'][panel]['case_identity_sha256'];save(OUTPUT/f'{panel}-identity.json',identity)
        records={};values={};visits={};states={};row_keys=None
        out['panels'][panel]={'status':'running','case_identity_sha256':digest(identity),'records':records};save(path,out)
        for seed in (42,137,2026):
            for v in (29,30):states[v,seed]=json.loads((ROOT/f'upgrade_v{v}/results/{panel}-seed{seed}.json').read_text())
            assert all(sha(PRIVATE/f'prismatic-v27/{panel}-models.joblib')==states[v,seed]['lock']['bundle_sha256'] for v in (29,30))
            for r in range(1,6):
                src=PRIVATE/f'prismatic-v29/{panel}-seed{seed}/round{r}';fits=json.loads((src/'fits.json').read_text());assert all(sha(src/f)==h for f,h in fits['model_sha256'].items())
                frozen=states[29,seed]['rounds'][r-1];assert fits['model_sha256']==frozen['model_sha256'] and sha(src/'thresholds.npy')==frozen['thresholds_sha256']
                start=time.perf_counter();prob=probability(joblib.load(src/fits['base_file']),x);elapsed=time.perf_counter()-start
                thresholds=np.load(src/'thresholds.npy');raw=np.full(len(meds),fits['selection']['threshold'])
                for version in (29,30):
                    part=PRIVATE/f'prismatic-v{version}/{panel}-seed{seed}/round{r}';memories=json.loads((part/'memories.json').read_text());assert set(memories)==set(arm_names(version))
                    complete=json.loads((part/'complete.json').read_text())
                    for arm,memory in memories.items():
                        assert digest(memory)==complete['arms'][arm]['memory_sha256']
                        name=f'v{version}-{arm}-seed{seed}-round{r}';target=OUTPUT/f'{panel}-{name}.npz';pred=apply(memory,x,prob,raw if arm=='raw_policy' else thresholds)
                        m,a,keys=score(pred,gold,people,meds,b['ddi'],b['ddi_covered_indices']);vf=visit_f1(pred,gold,meds)
                        if row_keys is None:row_keys=keys
                        else:assert keys==row_keys
                        if target.exists():
                            existing=np.load(target);np.testing.assert_array_equal(existing['prediction'],pred);np.testing.assert_array_equal(existing['patient_scores'],a);np.testing.assert_array_equal(existing['visit_f1'],vf)
                        else:np.savez_compressed(target,prediction=pred,patient_scores=a,patient_keys=np.array(keys),visit_f1=vf)
                        records[name]={'version':version,'arm':arm,'seed':seed,'round':r,'metrics':m,'memory_sha256':digest(memory),'model_sha256':fits['model_sha256'][fits['base_file']],'prediction_sha256':sha(target),'shared_probability_seconds':elapsed,'memory_size':len(memory)}
                        values[name]=a;visits[name]=vf
                save(path,out);print(json.dumps({'panel':panel,'seed':seed,'round':r,'program_predictions_completed':len(records)}),flush=True)
        endpoints={};curves={};changes={};selected_names={}
        def state_name(version,arm,seed,r):return f'v{version}-{arm}-seed{seed}-round{r}'
        for endpoint in ('selected','final'):
            groups={};arrays={};selected_names[endpoint]={}
            for version in (29,30):
                for arm in arm_names(version):
                    method=f'v{version}-{arm}';names=[state_name(version,arm,s,states[version,s]['selections'][arm]['round'] if endpoint=='selected' else 5) for s in (42,137,2026)]
                    selected_names[endpoint][method]=names;groups[method]=mean_rows([records[n]['metrics'] for n in names]);arrays[method]=np.array([values[n] for n in names])
            contrasts={}
            for version,own in [(29,'own_error_program_agent'),(30,'own_C1P1')]:
                for arm in arm_names(version):
                    if arm!=own:contrasts[f'v{version}-{own}_minus_{arm}']=paired(arrays[f'v{version}-{own}'],arrays[f'v{version}-{arm}'])
            for method in ('greedy','own','shuffled'):
                a,bv,c,d=[arrays[f'v30-{method}_C{i}P{j}'] for i,j in [(0,0),(0,1),(1,0),(1,1)]]
                contrasts[method+'_compatibility_main']=paired((c+d)/2,(a+bv)/2)
                contrasts[method+'_confirmation_main']=paired((bv+d)/2,(a+c)/2)
                contrasts[method+'_interaction']=paired(d-c,bv-a)
            endpoints[endpoint]={'methods':groups,'within_program_contrasts':contrasts}
            if endpoint=='selected':
                old_arrays={}
                for name,row in original['panels'][panel]['results'].items():
                    if row['kind']=='raw_round':continue
                    f=PRIVATE/f'prismatic-v27/evaluation/{panel}-{name}.npz';assert sha(f)==row['prediction_sha256'];z=np.load(f);assert z['patient_keys'].tolist()==row_keys
                    old_arrays.setdefault(name.rsplit('-seed',1)[0],[]).append(z['patient_scores'])
                endpoints[endpoint]['v27_methods']=original['panels'][panel]['methods']
                endpoints[endpoint]['versus_v27']={own:{m:paired(arrays[own],np.array(a)) for m,a in old_arrays.items()} for own in ('v29-own_error_program_agent','v30-own_C1P1')}
        for version in (29,30):
            for arm in arm_names(version):
                method=f'v{version}-{arm}';curves[method]={};changes[method]={}
                for kind in ('raw','accepted'):
                    names_by_round=[]
                    for r in range(1,6):
                        names=[]
                        for seed in (42,137,2026):
                            chosen=r if kind=='raw' else states[version,seed]['rounds'][r-1]['arms'][arm]['best_round']
                            names.append(state_name(version,arm,seed,chosen))
                        names_by_round.append(names)
                    curves[method][kind]=[mean_rows([records[n]['metrics'] for n in names]) for names in names_by_round]
                    changes[method][kind]={str(seed):[transitions(visits[names_by_round[r][i]],visits[names_by_round[r-1][i]]) for r in range(1,5)] for i,seed in enumerate((42,137,2026))}
        out['panels'][panel].update(status='complete',endpoints=endpoints,endpoint_prediction_names=selected_names,curves=curves,fix_regress=changes)
        save(path,out)
    out['status']='executed_pending_independent_prediction_audit';save(path,out)
if __name__=='__main__':main()
