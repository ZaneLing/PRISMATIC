"""Recount private predictions, membership and runtime; export aggregates only."""
import json,sys
from common53 import *
from programs import predict
from runtime import run_case
def main():
    import pandas as pd
    members=pd.read_parquet(PRIVATE/'members.parquet');pids=set(members.uniquepid)
    assert len(pids)==len(members)==256
    for path in [SOURCE/'members.parquet',DEV/'members.parquet']:assert not pids&set(pd.read_parquet(path).uniquepid)
    cs=json.loads((PRIVATE/'audit.json').read_text());outputs=json.loads((PRIVATE/'audit_outputs.json').read_text());r=json.loads((HERE/'results/audit.json').read_text())
    lock=json.loads((PRIVATE/'learning_lock.json').read_text());am=json.loads((PRIVATE/'library_lock.json').read_text())
    for name,h in lock['states'].items():assert sha(PRIVATE/name)==h
    for name,h in am['states'].items():assert sha(PRIVATE/'library'/name)==h
    runtime_rows=0
    for model in ['qwen','llama']:
        for name,pp in outputs[model].items():
            expected=r['metrics'][model][name]['metrics']
            actual=metrics(pp,cs)
            assert all(expected[k]==v for k,v in actual.items())
        state=json.loads((PRIVATE/'library/53-states.json').read_text())[-1]
        for c,b,p in zip(cs,outputs[model]['fixed'],outputs[model]['rxrsi_library_53']):
            stripped={k:v for k,v in c.items() if k!='gold'}
            result=run_case(stripped,b,state)
            assert result['orders']==p and result['clinical_appropriateness']=='not_assessed';runtime_rows+=1
    # Ensure public JSON contains no private records or learned medication rules.
    forbidden={'case_id','patient_hash','hospital_hash','uniquepid','patientunitstayid','gold','prior_orders','available_labs','raw','drug_name','drug_code','support_cases','counterexample_cases'}
    def scan(obj):
        if isinstance(obj,dict):
            assert not forbidden&set(obj)
            for value in obj.values():scan(value)
        elif isinstance(obj,list):
            for value in obj:scan(value)
    for p in list((HERE/'results').glob('*.json'))+list((HERE/'library/results').glob('*.json')):scan(json.loads(p.read_text()))
    save(HERE/'results/verification.json',dict(patient_disjoint=True,new_patients=256,metrics_recounted=True,frozen_states_unchanged=True,gold_stripped_runtime_rows_verified=runtime_rows,public_aggregate_scan=True,clinical_reviews_completed=0,default_memory_promoted=False,api_spend_usd=0))
    print('Verified256 new patients, both backbones, all aggregate recounts and512 target-blind runtime executions.')
if __name__=='__main__':main()
