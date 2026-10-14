"""Freeze new patient-disjoint proposal/guard/test subsets without reporting labels."""
import json,sys
from pathlib import Path
import joblib,duckdb,pandas as pd
from rx_agent import record_order,key,FIELDS,hash_data
HERE=Path(__file__).resolve().parent
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v7'
ROOT=PRIVATE.parent
sys.path.insert(0,str(HERE.parent/'upgrade_v3'))
from run_atc4_methods import take,text_features

def run():
    PRIVATE.mkdir(exist_ok=True)
    old=joblib.load(ROOT/'prismatic-v6/evaluation_bundle.joblib')
    f=pd.read_parquet(ROOT/'prismatic-v4/cohort.parquet')
    v=f[(f.split=='val')&~f.subject_id.isin(old['parts']['val'].subject_id)].copy()
    v['bucket']=v.subject_id.map(lambda s:int(hash_data('v7-guard-'+str(s))[:8],16)%2)
    t=f[(f.split=='test')&~f.subject_id.isin(old['parts']['test'].subject_id)].copy()
    parts={'train':old['parts']['train'],'proposal':take(v[v.bucket==0],'val',2000),
           'guard':take(v[v.bucket==1],'val',2000),'test':take(t,'test',4000)}
    for a in parts:
        for b in parts:
            if a!=b:assert not set(parts[a].subject_id)&set(parts[b].subject_id)
    con=duckdb.connect();members=pd.concat([p[['hadm_id']] for s,p in parts.items() if s!='train']);con.register('members',members)
    rows=con.execute('select hadm_id,drug_key,route,dose_val_rx,dose_unit_rx,doses_per_24_hrs from read_parquet(?) join members using(hadm_id)',[str(ROOT/'prismatic-v4/mapped_orders.parquet')]).fetchdf();con.close()
    by={}
    for row in rows.to_dict('records'):
        o=record_order(row)
        if o['drug_name']:by.setdefault(str(row['hadm_id']),{})[key(o,FIELDS)]=o
    truth={'train':old['truth']['train']}
    for s,p in parts.items():
        if s!='train':truth[s]=[list(by.get(str(h),{}).values()) for h in p.hadm_id]
    bundle={'parts':parts,'truth':truth,'text':{s:text_features(p) for s,p in parts.items()},'classes':old['classes']}
    joblib.dump(bundle,PRIVATE/'data.joblib')
    manifest={'samples':{s:len(p) for s,p in parts.items()},'patients':{s:p.subject_id.nunique() for s,p in parts.items()},
      'membership_sha256':{s:hash_data(sorted(p.hadm_id.astype(str))) for s,p in parts.items()},
      'cross_split_patient_overlap':0,'prior_v6_val_test_patient_overlap':0,
      'vocabulary_size':len(old['classes']),'vocabulary_provenance':'Frozen v6 initial 8k training names',
      'test_not_scored':True}
    (HERE/'results/data_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest),flush=True)

if __name__=='__main__':run()
