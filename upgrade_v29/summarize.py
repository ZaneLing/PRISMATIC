"""Aggregate only independently audited development outputs, never test scores."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'upgrade_v27'))
from evaluation_metrics import paired
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v29'
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
        methods={};curves={}
        for arm in audits[0]['guard']:
            methods[arm]={k:{'mean':float(np.mean([a['guard'][arm][k] for a in audits])),
              'seed_sd':float(np.std([a['guard'][arm][k] for a in audits],ddof=1)) if len(audits)>1 else None} for k in audits[0]['guard'][arm] if isinstance(audits[0]['guard'][arm][k],(int,float))}
            curves[arm]=[{'round':r+1,'fit_patients':[a['rounds'][r]['fit_patient_count'] for a in audits],
              'fresh_witness_patients':[a['rounds'][r]['fresh_witness_patients'] for a in audits],
              'proposal_f1':[a['rounds'][r]['arms'][arm]['proposal']['patient_f1'] for a in audits],
              'proposal_jaccard':[a['rounds'][r]['arms'][arm]['proposal']['patient_jaccard'] for a in audits],
              'memory_size':[a['rounds'][r]['arms'][arm]['memory_size'] for a in audits],
              'retained_conjunctions':[a['rounds'][r]['arms'][arm]['retained_conjunctions'] for a in audits]} for r in range(5)]
        own=np.array([z['own_error_program_agent'] for z in arrays]);pairs={arm:paired(own,np.array([z[arm] for z in arrays])) for arm in methods if arm!='own_error_program_agent'}
        costs={arm:{'logical_model_calls':sum(r['arms'][arm]['proposer_calls'] for z in states for r in z['rounds']),
          'logical_response_cost_usd':sum(r['arms'][arm]['proposer_cost_usd'] or 0 for z in states for r in z['rounds']),
          'proposal_seconds':sum(r['arms'][arm]['proposal_seconds'] for z in states for r in z['rounds']),
          'enumerated_programs':sum(r['arms'][arm]['search'].get('evaluated_programs',0) for z in states for r in z['rounds'])} for arm in methods}
        out['panels'][panel]={'seeds':seeds,'methods':methods,'own_agent_minus_control':pairs,'proposal_curves':curves,'proposal_costs':costs,'patients':len(arrays[0]['people']),'visits':audits[0]['guard']['raw_policy']['visits']}
    if len(out['panels'])==2 and all(len(p['seeds'])==3 for p in out['panels'].values()):out['status']='complete'
    out['scope']='Development-only intervention. Frozen v27 vocabularies precede witness assignment; coefficients/candidate statistics never use witness labels. Fresh witnesses are adaptively reused for up to four edits within their single round. Patient intervals condition on observed seeds; no multiplicity correction. Ordinary calibration is a control, not LLM evolution.'
    (HERE/'results/summary.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'status':out['status'],'audited_seeds':{p:z['seeds'] for p,z in out['panels'].items()}}),flush=True)
if __name__=='__main__':main()
