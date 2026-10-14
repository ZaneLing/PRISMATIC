"""Regrade immutable common-test predictions on preregistered identity strata."""
import hashlib,json,sys
from collections import defaultdict
from pathlib import Path
import joblib,numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;sys.path.insert(0,str(ROOT))
from upgrade_v27.evaluation_metrics import score,paired
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(z):return hashlib.sha256(json.dumps(z,sort_keys=True).encode()).hexdigest()
def main():
    registry=HERE/'exposure_registry.json';registry_audit=HERE/'exposure_registry_audit.json';a=json.loads(registry_audit.read_text())
    assert a['status']=='passed' and a['registry_sha256']==sha(registry) and a['auditor_sha256']==sha(HERE/'audit_exposure_registry.py')
    path=PRIVATE/'prismatic-exposure/membership.json';frozen=json.loads(path.read_text());assert sha(path)==a['private_membership_sha256']
    assert frozen['protocol_sha256']==sha(HERE/'prior_case_exclusion_protocol.json')
    documents={};audits={}
    for v,report,audit in [(27,'test_summary.json','test_audit.json'),(30,'common_test_summary.json','common_test_audit.json')]:
        p=ROOT/f'upgrade_v{v}/results'/report;q=ROOT/f'upgrade_v{v}/results'/audit
        z=json.loads(q.read_text());assert z['status']=='passed' and z['source_report_sha256']==sha(p)
        if v==30:assert z['auditor_sha256']==sha(ROOT/'upgrade_v30/audit_program_tests.py')
        documents[v]=json.loads(p.read_text());audits[f'v{v}']={'report_sha256':sha(p),'audit_sha256':sha(q)}
    assignments={c['case_id']:c for c in frozen['test_assignments']}
    result={'status':'complete','source_sha256':sha(Path(__file__)),'protocol_sha256':frozen['protocol_sha256'],'registry_audit_sha256':sha(registry_audit),'parent_audits':audits,'new_model_inference':False,'new_fitting':False,'panels':{},'scope':'Identity-only subgroup frozen and independently audited before current test predictions. Regrade exact audited parent predictions; distinct source populations are never pooled. Registry covers named histories, not all possible external use. Intervals condition on observed seeds and have no multiplicity correction.'}
    for panel in ('full','molecular'):
        identity=json.loads((PRIVATE/f'prismatic-v30/common-test/{panel}-identity.json').read_text())
        assert digest(identity)==documents[27]['panels'][panel]['case_identity_sha256']==documents[30]['panels'][panel]['case_identity_sha256']
        assert set(identity['case_ids'])==set(assignments)
        assert all(assignments[c]['subject_hash']==p for c,p in zip(identity['case_ids'],identity['people']))
        b=joblib.load(PRIVATE/f'prismatic-v27/{panel}-models.joblib');meds=b['medications'];assert meds==identity['medications']
        keep=np.array([assignments[c]['retained'] for c in identity['case_ids']],dtype=bool);gold=[set(g) for g in identity['gold']];people=np.array(identity['people'])
        plans={}
        for name,row in documents[27]['panels'][panel]['results'].items():
            if row['kind']!='raw_round':plans['v27-'+name]=(PRIVATE/f'prismatic-v27/evaluation/{panel}-{name}.npz',row['prediction_sha256'],'v27-'+name.rsplit('-seed',1)[0])
        z=documents[30]['panels'][panel]
        for method,names in z['endpoint_prediction_names']['selected'].items():
            for name in names:plans[name]=(PRIVATE/f'prismatic-v30/common-test/{panel}-{name}.npz',z['records'][name]['prediction_sha256'],method)
        result['panels'][panel]={}
        for stratum,mask in [('prior_record_excluded',keep),('previously_recorded',~keep)]:
            indices=np.flatnonzero(mask);truth=[gold[i] for i in indices];patients=people[indices];rows={};values={};groups={};patient_keys=None
            if not len(indices):result['panels'][panel][stratum]={'visits':0,'patients':0,'methods':{},'reason':'No eligible patients; no replacement cohort searched.'};continue
            for name,(p,h,method) in plans.items():
                assert sha(p)==h;saved=np.load(p);prediction=saved['prediction'][indices]
                m,vector,keys=score(prediction,truth,patients,meds,b['ddi'],b['ddi_covered_indices'])
                # A separate set loop checks subgroup assignment and primary scores.
                patient=defaultdict(list);hit=chosen_n=gold_n=0
                for row,g,person in zip(prediction,truth,patients):
                    selected={meds[j] for j in np.flatnonzero(row)};tp=len(selected&g);pn=len(selected);gn=len(g);union=len(selected|g)
                    patient[person].append((2*tp/(pn+gn) if pn+gn else 1.,tp/union if union else 1.));hit+=tp;chosen_n+=pn;gold_n+=gn
                independent=np.array([np.mean(patient[k],axis=0) for k in sorted(patient)])
                assert sorted(patient)==keys;np.testing.assert_allclose(independent,vector,atol=1e-15,rtol=1e-15)
                assert abs(m['micro_f1']-2*hit/max(1,chosen_n+gold_n))<1e-12
                if patient_keys is None:patient_keys=keys
                else:assert patient_keys==keys
                rows[name]=m;values[name]=vector;groups.setdefault(method,[]).append(name)
            methods={method:{'runs':len(names),'metrics':{k:{'mean':float(np.mean([rows[n][k] for n in names])),'seed_sd':float(np.std([rows[n][k] for n in names],ddof=1)) if len(names)>1 else None} for k in rows[names[0]] if isinstance(rows[names[0]][k],(float,int))}} for method,names in groups.items()}
            contrasts={}
            for own in ('v29-own_error_program_agent','v30-own_C1P1'):
                x=np.array([values[n] for n in groups[own]])
                contrasts[own]={method:paired(x,np.array([values[n] for n in names])) for method,names in groups.items() if method!=own}
            result['panels'][panel][stratum]={'visits':len(indices),'patients':len(patient_keys),'methods':methods,'paired_contrasts':contrasts,'all_prediction_hashes_match_parent':True,'independent_patient_set_metric_recount':'passed'}
            print(json.dumps({'panel':panel,'stratum':stratum,'visits':len(indices),'patients':len(patient_keys),'methods':len(methods)}),flush=True)
    (HERE/'prior_case_subset_results.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
