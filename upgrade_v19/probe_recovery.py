"""Synthetic real-state rollback probe; no language-model/benchmark score."""
import json,sys,types,uuid
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'upgrade_v14'))
from probe_fhir_state import request,total,BASE
from fhir_executor import run_case

def main():
    before={r:total(r) for r in ['Patient','MedicationRequest','Observation','ServiceRequest']}
    code,p=request('POST','Patient',{'resourceType':'Patient','identifier':[{'system':'urn:prismatic:probe','value':uuid.uuid4().hex}]});assert code==201
    patient='Patient/'+p['id']
    try:
        payload={'resourceType':'MedicationRequest','status':'draft','intent':'proposal','subject':{'reference':patient},
            'medicationCodeableConcept':{'text':'Synthetic rollback probe; no administration'},'dosageInstruction':[{'route':'IV'}]}
        actions=iter(['POST '+BASE+'MedicationRequest\n'+json.dumps(payload),'FINISH([])'])
        seen=[]
        def actor(history):seen.append(history[-1]['content']);return {'raw':next(actions)}
        case={'id':'task1_synthetic_rollback','instruction':'Exercise the research rollback path.','context':'Synthetic integration test.'}
        grader=types.SimpleNamespace(task1=lambda case,result,base:result.result=='[]')
        row=run_case(case,'verified_state_harness',grader,actor=actor,compile_payloads=False,repair_protocol=True)
        assert row['write_checks']==[False] and row['writes']==0 and row['model_calls']==2
        audit=row['write_audits'][0]
        assert audit['create_status']==201 and audit['readback_status']==200
        assert not audit['persisted'] and audit['rolled_back'] and audit['rollback_status'] in (200,204)
        assert audit['canonical_payload']==payload and audit['readback'].get('dosageInstruction')!=payload['dosageInstruction']
        assert len([t for t in row['tools'] if t.get('rollback')])==1
        assert row['active_post_checks']==[] and row['cleanup_checks']==[]
        assert 'rolled back' in seen[1]
        assert total('MedicationRequest')==before['MedicationRequest']
    finally:
        code,_=request('DELETE',patient);assert code in (200,204)
    after={r:total(r) for r in before};assert before==after
    report={'kind':'synthetic engineering integration, not agent benchmark','language_model_calls':0,'scripted_action_steps':2,
        'lossy_write_detected':True,'owned_resource_rolled_back':True,'repair_feedback_observed':True,'receipts_and_rollback_records_verified':True,'counts_before':before,'counts_after':after}
    (HERE/'results/recovery_probe.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

if __name__=='__main__':main()
