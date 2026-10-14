"""Prepare local-only feedback, validation, and new-patient test for QLoRA."""
import json,sys
from pathlib import Path
import joblib,numpy as np,pandas as pd,duckdb
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'upgrade_v7'))
sys.path.insert(0,str(HERE.parent/'upgrade_v3'))
from rx_agent import hash_data,record_order,key,FIELDS
ROOT=Path.home()/'Desktop/MedTreeBench/dataset/restricted'
PRIVATE=ROOT/'prismatic-v9'

def run():
    PRIVATE.mkdir(exist_ok=True)
    b=joblib.load(ROOT/'prismatic-v7/data.joblib');v6=joblib.load(ROOT/'prismatic-v6/evaluation_bundle.joblib')
    agent=joblib.load(ROOT/'prismatic-v6/agent_8000.joblib')
    parts=b['parts'];base_patients=set(parts['train'].subject_id.iloc[:8000]);train=parts['train']
    blocks=[]
    for r in range(3):
        ix=[i for i,s in enumerate(train.subject_id) if s not in base_patients and int(hash_data(['v9-feedback-round',str(s)])[:8],16)%3==r]
        ix=sorted(ix,key=lambda i:hash_data(str(train.iloc[i].hadm_id)))[:600];assert len(ix)==600
        blocks.append(ix)
    seen=set(parts['test'].subject_id)|set(v6['parts']['test'].subject_id)
    cohort=pd.read_parquet(ROOT/'prismatic-v4/cohort.parquet');test=cohort[(cohort.split=='test')&~cohort.subject_id.isin(seen)].copy()
    test['pick']=test.hadm_id.map(lambda i:hash_data(['v9-new-test',str(i)]));test=test.sort_values('pick').head(500);assert len(test)==500
    con=duckdb.connect();con.register('members',test[['hadm_id']])
    rows=con.execute('select hadm_id,drug_key,route,dose_val_rx,dose_unit_rx,doses_per_24_hrs from read_parquet(?) join members using(hadm_id)',[str(ROOT/'prismatic-v4/mapped_orders.parquet')]).fetchdf();con.close();by={}
    for raw in rows.to_dict('records'):
        o=record_order(raw)
        if o['drug_name']:by.setdefault(str(raw['hadm_id']),{})[key(o,FIELDS)]=o
    def compile_case(row,gold):
        context=f"Chief complaint: {str(row.chiefcomplaint)[:250]}; acuity: {row.acuity}; home medicines: {str(row.home_meds)[:700]}"
        # Match the frozen policy's original feature serialization.
        text=f"chiefcomplaint: {row.chiefcomplaint} acuity: {row.acuity} home_meds: {row.home_meds}"
        # Use the exact shared helper for statistical candidate generation.
        from run_atc4_methods import text_features
        text=text_features(pd.DataFrame([row]))[0]
        p=agent['model'].predict_proba(agent['vectorizer'].transform([text]))[0]
        rank=np.argsort(-p,kind='stable')[:20];orders=agent['memory'].synthesize([agent['classes'][j] for j in rank],conditional=False)
        tools={f'O{i+1}':o for i,o in enumerate(orders)};names={o['drug_name'] for o in gold};target=[i for i,o in tools.items() if o['drug_name'] in names]
        catalogue='\n'.join(f"{i}: {o['drug_name'][:70]} | {o['route']} | {o['dose_value']} {o['dose_unit']}" for i,o in tools.items())
        messages=[{'role':'system','content':'You are an offline prescription research agent. Select the likely recorded orders from the provided tools using the patient context. Use only listed IDs. Return JSON only: {"order_ids":["O1"]}.'},
          {'role':'user','content':context+'\nCandidate order tools:\n'+catalogue}]
        return {'case_id':hash_data(str(row.hadm_id)),'subject_hash':hash_data(str(row.subject_id)),'messages':messages,'catalogue':tools,'gold':gold,'target':target}
    data={'blocks':[[compile_case(train.iloc[i],b['truth']['train'][i]) for i in ix] for ix in blocks],
      'validation':[compile_case(parts['proposal'].iloc[i],b['truth']['proposal'][i]) for i in range(100)],
      'guard':[compile_case(parts['guard'].iloc[i],b['truth']['guard'][i]) for i in range(200)],
      'test':[compile_case(row,list(by.get(str(row.hadm_id),{}).values())) for _,row in test.iterrows()]}
    (PRIVATE/'cases.json').write_text(json.dumps(data)+'\n')
    manifest={'block_cases':[len(x) for x in data['blocks']],'validation_cases':100,'guard_cases':200,'new_test_cases':500,
      'new_test_patients':test.subject_id.nunique(),'previous_v6_v7_test_patient_overlap':0,'initial_policy_feedback_patient_overlap':0,
      'membership_sha256':{s:hash_data([c['case_id'] for c in cases]) for s,cases in data.items() if s!='blocks'},
      'fixed_candidate_training_cases':8000,'candidate_tool_sha256':hash_data(agent['memory'].defaults)}
    (HERE/'results').mkdir(exist_ok=True);(HERE/'results/data_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest),flush=True)

if __name__=='__main__':run()
