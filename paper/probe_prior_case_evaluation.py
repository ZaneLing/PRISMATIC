"""Synthetic end-to-end scoring probe; never opens a real test prediction."""
import hashlib,json,tempfile
from pathlib import Path
import joblib,numpy as np
import evaluate_prior_case_subsets as evaluator
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,z):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(z)+'\n')
def main():
    with tempfile.TemporaryDirectory(prefix='rxrsi-synthetic-subset-') as temp:
        root=Path(temp);paper=root/'paper';private=root/'restricted';paper.mkdir();private.mkdir()
        for source,destination in [(HERE/'audit_exposure_registry.py',paper/'audit_exposure_registry.py'),(HERE.parent/'upgrade_v30/audit_program_tests.py',root/'upgrade_v30/audit_program_tests.py')]:
            destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(source.read_bytes())
        write(paper/'prior_case_exclusion_protocol.json',{'synthetic_fixture':True});write(paper/'exposure_registry.json',{'synthetic_fixture':True})
        ids=['synthetic-c1','synthetic-c2','synthetic-c3','synthetic-c4'];people=['synthetic-p1','synthetic-p1','synthetic-p2','synthetic-p3']
        assignments=[{'case_id':c,'subject_hash':p,'retained':i<3} for i,(c,p) in enumerate(zip(ids,people))]
        write(private/'prismatic-exposure/membership.json',{'protocol_sha256':sha(paper/'prior_case_exclusion_protocol.json'),'test_assignments':assignments})
        write(paper/'exposure_registry_audit.json',{'status':'passed','registry_sha256':sha(paper/'exposure_registry.json'),'auditor_sha256':sha(paper/'audit_exposure_registry.py'),'private_membership_sha256':sha(private/'prismatic-exposure/membership.json')})
        docs={27:{'panels':{}},30:{'panels':{}}};base=np.array([[1,0],[1,0],[0,0],[0,0]],dtype=bool);own=np.array([[1,0],[0,1],[0,0],[0,0]],dtype=bool)
        for panel in ('full','molecular'):
            gold=[['A'],['B'],['OOV'] if panel=='full' else [],[]];identity={'case_ids':ids,'people':people,'gold':gold,'medications':['A','B']};identity_hash=evaluator.digest(identity)
            write(private/f'prismatic-v30/common-test/{panel}-identity.json',identity)
            folder=private/'prismatic-v27';folder.mkdir(exist_ok=True);joblib.dump({'medications':['A','B'],'ddi':np.array([[0,1],[1,0]]),'ddi_covered_indices':[0,1]},folder/f'{panel}-models.joblib')
            target=private/f'prismatic-v27/evaluation/{panel}-static.npz';target.parent.mkdir(exist_ok=True);np.savez(target,prediction=base)
            docs[27]['panels'][panel]={'case_identity_sha256':identity_hash,'results':{'static':{'kind':'conventional','prediction_sha256':sha(target)}}}
            state={'case_identity_sha256':identity_hash,'records':{},'endpoint_prediction_names':{'selected':{}}}
            for method,pred in [('v29-own_error_program_agent',own),('v30-own_C1P1',base)]:
                names=[]
                for seed in (42,137,2026):
                    name=f'{method}-seed{seed}-round1';target=private/f'prismatic-v30/common-test/{panel}-{name}.npz';np.savez(target,prediction=pred);state['records'][name]={'prediction_sha256':sha(target)};names.append(name)
                state['endpoint_prediction_names']['selected'][method]=names
            docs[30]['panels'][panel]=state
        for v,report,audit in [(27,'test_summary.json','test_audit.json'),(30,'common_test_summary.json','common_test_audit.json')]:
            p=root/f'upgrade_v{v}/results'/report;write(p,docs[v]);z={'status':'passed','source_report_sha256':sha(p)}
            if v==30:z['auditor_sha256']=sha(root/'upgrade_v30/audit_program_tests.py')
            write(root/f'upgrade_v{v}/results'/audit,z)
        evaluator.HERE=paper;evaluator.ROOT=root;evaluator.PRIVATE=private;evaluator.main();result=json.loads((paper/'prior_case_subset_results.json').read_text())
        full=result['panels']['full']['prior_record_excluded'];mol=result['panels']['molecular']['prior_record_excluded'];excluded=result['panels']['full']['previously_recorded']
        assert full['visits']==3 and full['patients']==2 and excluded['visits']==1 and excluded['patients']==1
        assert full['methods']['v27-static']['metrics']['patient_f1']['mean']==.25
        assert full['methods']['v29-own_error_program_agent']['metrics']['patient_f1']['mean']==.5
        assert abs(full['methods']['v29-own_error_program_agent']['metrics']['micro_f1']['mean']-.8)<1e-12
        assert mol['methods']['v29-own_error_program_agent']['metrics']['patient_f1']['mean']==1.
        assert excluded['methods']['v27-static']['metrics']['patient_f1']['mean']==1.
        assert full['methods']['v29-own_error_program_agent']['runs']==3
        delta=full['paired_contrasts']['v29-own_error_program_agent']['v27-static']['patient_f1'];assert delta['difference']==.25 and delta['patient_ci95']==[0.,.5]
    proof={'status':'passed','synthetic_only':True,'real_test_predictions_read':False,'evaluator_sha256':sha(HERE/'evaluate_prior_case_subsets.py'),'probe_sha256':sha(Path(__file__)),'checks':['Complete patient visits retained across identity strata','Patient-average F1 differs correctly from visit average','Full-panel OOV gold remains in recall denominator','Molecular zero-target convention preserved','Frozen prediction hashes and case order checked','Three seeds and deterministic comparator aggregated','Hand-computed paired effect and exact two-patient interval reproduced']}
    (HERE/'exposure_evaluation_probe.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof))
if __name__=='__main__':main()
