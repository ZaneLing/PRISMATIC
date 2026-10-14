"""Report every audited factorial cell and registered development contrast."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'upgrade_v27'))
from evaluation_metrics import paired
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v30'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    out={'status':'partial','split':'guard','test_inference':False,'panels':{}}
    for panel in ['full','molecular']:
        audits=[];states=[];arrays=[];seeds=[]
        for seed in [42,137,2026]:
            path=HERE/f'results/{panel}-audit-seed{seed}.json'
            if not path.exists():continue
            a=json.loads(path.read_text());report=HERE/f'results/{panel}-seed{seed}.json';assert a['status']=='passed' and a['source_report_sha256']==sha(report) and a['auditor_sha256']==sha(HERE/'audit.py')
            audits.append(a);states.append(json.loads(report.read_text()));seeds.append(seed);z=np.load(PRIVATE/f'{panel}-seed{seed}/audited-guard-patient-scores.npz')
            if arrays:np.testing.assert_array_equal(z['people'],arrays[0]['people'])
            arrays.append({k:z[k] for k in z.files})
        if not audits:continue
        endpoints={}
        for endpoint in ['selected','final']:
            methods={}
            for arm,base in audits[0]['guard'][endpoint].items():
                methods[arm]={k:{'mean':float(np.mean([a['guard'][endpoint][arm][k] for a in audits])),'seed_sd':float(np.std([a['guard'][endpoint][arm][k] for a in audits],ddof=1)) if len(audits)>1 else None} for k in base if isinstance(base[k],(int,float))}
            def arr(arm):return np.array([z[endpoint+'__'+arm] for z in arrays])
            contrasts={}
            for method in ['greedy','own','shuffled']:
                a,b,c,d=[arr(f'{method}_C{x}P{y}') for x,y in [(0,0),(0,1),(1,0),(1,1)]]
                contrasts[method+'_compatibility_main']=paired((c+d)/2,(a+b)/2)
                contrasts[method+'_confirmation_main']=paired((b+d)/2,(a+c)/2)
                contrasts[method+'_interaction']=paired(d-b,c-a)
                contrasts[method+'_full_gates_minus_no_gates']=paired(d,a)
            for c in [0,1]:
                for p in [0,1]:
                    for control in ['greedy','shuffled']:contrasts[f'own_minus_{control}_C{c}P{p}']=paired(arr(f'own_C{c}P{p}'),arr(f'{control}_C{c}P{p}'))
            contrasts['own_full_gates_minus_calibration']=paired(arr('own_C1P1'),arr('calibrated_policy'))
            endpoints[endpoint]={'methods':methods,'contrasts':contrasts}
        curves={};costs={};unique={}
        for arm in audits[0]['guard']['selected']:
            curves[arm]=[{'round':r+1,'proposal_f1':[a['rounds'][r]['arms'][arm]['proposal']['patient_f1'] for a in audits],'memory_size':[a['rounds'][r]['arms'][arm]['memory_size'] for a in audits],'compatibility_resets':[a['rounds'][r]['arms'][arm]['compatibility_reset'] for a in audits],'confirmation_resets':[a['rounds'][r]['arms'][arm]['confirmation_reset'] for a in audits]} for r in range(5)]
            rows=[r['arms'][arm] for z in states for r in z['rounds']]
            costs[arm]={'logical_model_calls':sum(z['proposer_calls'] for z in rows),'logical_response_usd':sum(z['proposer_cost_usd'] or 0 for z in rows),'actual_context_programs':sum(z['search'].get('evaluated_programs',0) for z in rows if not z['context_reused']),'seconds':sum(z['seconds'] for z in rows),'compatibility_resets':sum(z['compatibility_reset'] for z in rows),'confirmation_resets':sum(z['confirmation_reset'] for z in rows),'accepted_edits_before_confirmation':sum(z['accepted_edits_before_confirmation'] for z in rows)}
            for z in rows:
                if z['request_sha256']:unique[z['request_sha256']]=z['proposer_cost_usd'] or 0
        out['panels'][panel]={'seeds':seeds,'endpoints':endpoints,'proposal_curves':curves,'costs':costs,'unique_request_count':len(unique),'unique_response_usd':sum(unique.values()),'patients':len(arrays[0]['people']),'visits':audits[0]['guard']['selected']['raw_policy']['visits']}
    if len(out['panels'])==2 and all(len(p['seeds'])==3 for p in out['panels'].values()):out['status']='complete'
    out['scope']='Exploratory reused development cohort. C/P are fixed gate policies; rule memory is generated. All conditions use identical A/B partitions; C0P0 is not identical to v29 full-batch editing. Selected and raw round5 guard endpoints are separate. Intervals condition on observed seeds and do not correct multiplicity. Unique response cost includes exact reused responses, not fresh physical spend.'
    temp=HERE/'results/summary.tmp';temp.write_text(json.dumps(out,indent=2)+'\n');temp.replace(HERE/'results/summary.json');print(json.dumps({'status':out['status'],'audited_seeds':{p:z['seeds'] for p,z in out['panels'].items()}}),flush=True)
if __name__=='__main__':main()
