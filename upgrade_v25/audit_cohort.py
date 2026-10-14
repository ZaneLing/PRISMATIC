"""Independently reconstruct exposed native-code orders and time-bounded inputs."""
import json,math
from collections import defaultdict
import pandas as pd,numpy as np,joblib,duckdb
from data_contract import HERE,PRIVATE,FIELDS,key,digest,sha,save

def clean(v):
    if v is None:return None
    value=' '.join(str(v).strip().lower().split());return value or None
def tuple_from_source(r):return ('hicl:'+str(int(r['hicl'])),clean(r['routeadmin']),clean(r['dosage']),clean(r['frequency']))

def main():
    manifest=json.loads((HERE/'results/cohort_manifest.json').read_text())
    for name,value in manifest['files_sha256'].items():assert sha(PRIVATE/name)==value
    cases=joblib.load(PRIVATE/'cases.joblib');members=pd.read_parquet(PRIVATE/'members.parquet')
    targets=pd.read_parquet(PRIVATE/'targets.parquet');prior=pd.read_parquet(PRIVATE/'prior.parquet');labs=pd.read_parquet(PRIVATE/'labs.parquet')
    assert len(members)==members.patientunitstayid.nunique()==sum(len(v) for v in cases.values())
    bad={'target_window':int((~targets.ordered_at.between(360,720,inclusive='left')).sum()),
      'target_code':int((targets.hicl.isna()|(targets.hicl<=0)).sum()),
      'prior_window':int((~prior.ordered_at.between(-1080,360,inclusive='left')).sum()),
      'lab_draw_window':int((~labs.drawn_at.between(-1080,360,inclusive='both')).sum()),
      'lab_revision':int((labs.revised_at.isna()|(labs.revised_at>360)).sum()),
      'lab_finite':int((~np.isfinite(labs.value)).sum()),
      'followup':int((pd.to_numeric(members.unitdischargeoffset)<720).sum())}
    assert not any(bad.values()),bad
    gold=defaultdict(set);history=defaultdict(list);measurements=defaultdict(list)
    for r in targets.to_dict('records'):gold[r['patientunitstayid']].add(tuple_from_source(r))
    for r in prior.to_dict('records'):
        h=r['hicl'];code='hicl:'+str(int(h)) if h is not None and not pd.isna(h) and h>0 else None
        history[r['patientunitstayid']].append((code,clean(r['drugname']),clean(r['routeadmin']),clean(r['dosage']),clean(r['frequency']),r['ordered_at']))
    for r in labs.to_dict('records'):measurements[r['patientunitstayid']].append((r['lab_key'],r['unit_key'],r['value'],r['drawn_at'],r['revised_at']))
    ids={digest(['eicu-v25',r.patientunitstayid]):r for r in members.itertuples()}
    patient_sets={s:{c['patient_hash'] for c in cs} for s,cs in cases.items()};hospital_sets={s:{c['hospital_hash'] for c in cs} for s,cs in cases.items()}
    for s in cases:
        for t in cases:
            if s!=t:assert not patient_sets[s]&patient_sets[t] and not hospital_sets[s]&hospital_sets[t]
    for s,cs in cases.items():
        for c in cs:
            m=ids[c['case_id']];h=m.patientunitstayid;assert m.split==s
            assert c['patient_hash']==digest(['eicu-patient',m.uniquepid]) and c['hospital_hash']==digest(['eicu-hospital',m.hospitalid])
            assert set(c['context'])=={'gender','age_decade','prior_orders','available_labs'}
            expected_age=90 if str(m.age).replace(' ','')=='>89' else int(float(m.age)//10)*10
            assert c['context']['gender']==clean(m.gender) and c['context']['age_decade']==expected_age
            assert {key(o) for o in c['gold']}==gold[h]
            p=c['context']['prior_orders'];l=c['context']['available_labs'];assert len(p)<=24 and len(l)<=32
            assert [tuple(o[k] for k in ['drug_code','drug_name','route','dosage','frequency','order_offset']) for o in p]==history[h]
            assert [tuple(o[k] for k in ['name','unit','value','draw_offset','revised_offset']) for o in l]==measurements[h]
            assert len({(o['name'],o['unit']) for o in l})==len(l)
    # Verify extraction against the source database, including zero-order cases.
    con=duckdb.connect(str(PRIVATE.parent/'prismatic-v24/audit.duckdb'),read_only=True);con.register('selected_members',members[['patientunitstayid','uniquepid','hospitalid','split']])
    assert con.execute('''SELECT COUNT(*) FROM selected_members m LEFT JOIN cohort c USING(patientunitstayid)
      WHERE c.patientunitstayid IS NULL OR m.uniquepid!=c.uniquepid OR m.hospitalid!=c.hospitalid OR m.split!=c.split''').fetchone()[0]==0
    n=con.execute('''SELECT COUNT(*) FROM medication t JOIN selected_members m USING(patientunitstayid)
      WHERE TRY_CAST(t.drugorderoffset AS DOUBLE)>=360 AND TRY_CAST(t.drugorderoffset AS DOUBLE)<720''').fetchone()[0]
    assert n==len(targets)
    assert con.execute('''SELECT COUNT(*) FROM targets t JOIN selected_members m USING(patientunitstayid)
      WHERE NOT COALESCE(TRY_CAST(t.drughiclseqno AS BIGINT)>0 AND TRY_CAST(t.drughiclseqno AS DOUBLE)=TRY_CAST(t.drughiclseqno AS BIGINT),false)''').fetchone()[0]==0
    con.register('saved_prior',prior[['medicationid']]);con.register('saved_labs',labs[['labid']])
    con.execute('''CREATE TEMP TABLE expected_prior AS SELECT medicationid FROM
      (SELECT t.medicationid,ROW_NUMBER() OVER(PARTITION BY t.patientunitstayid ORDER BY CAST(t.drugorderoffset AS DOUBLE) DESC,CAST(t.medicationid AS BIGINT) DESC) audit_rank
       FROM medication t JOIN selected_members m USING(patientunitstayid)
       WHERE TRY_CAST(t.drugorderoffset AS DOUBLE)>=-1080 AND TRY_CAST(t.drugorderoffset AS DOUBLE)<360) WHERE audit_rank<=24''')
    con.execute('''CREATE TEMP TABLE latest_pair AS SELECT l.patientunitstayid,
      arg_max(l.labid,struct_pack(draw:=CAST(l.labresultoffset AS DOUBLE),revision:=CAST(l.labresultrevisedoffset AS DOUBLE),id:=CAST(l.labid AS BIGINT))) AS labid
      FROM lab l JOIN selected_members m USING(patientunitstayid)
      WHERE TRY_CAST(l.labresultoffset AS DOUBLE)>=-1080 AND TRY_CAST(l.labresultoffset AS DOUBLE)<=360
        AND TRY_CAST(l.labresultrevisedoffset AS DOUBLE)<=360 AND ISFINITE(TRY_CAST(l.labresult AS DOUBLE)) AND NULLIF(TRIM(l.labname),'') IS NOT NULL
      GROUP BY l.patientunitstayid,LOWER(TRIM(l.labname)),LOWER(TRIM(COALESCE(NULLIF(TRIM(l.labmeasurenamesystem),''),NULLIF(TRIM(l.labmeasurenameinterface),''),'')))''')
    con.execute('''CREATE TEMP TABLE expected_labs AS SELECT labid FROM
      (SELECT l.labid,ROW_NUMBER() OVER(PARTITION BY l.patientunitstayid ORDER BY CAST(l.labresultoffset AS DOUBLE) DESC,CAST(l.labresultrevisedoffset AS DOUBLE) DESC,CAST(l.labid AS BIGINT) DESC) audit_rank
       FROM latest_pair p JOIN lab l USING(labid)) WHERE audit_rank<=32''')
    for a,b,column in [('expected_prior','saved_prior','medicationid'),('expected_labs','saved_labs','labid')]:
        assert con.execute(f'SELECT COUNT(*) FROM ((SELECT {column} FROM {a} EXCEPT SELECT {column} FROM {b}) UNION ALL (SELECT {column} FROM {b} EXCEPT SELECT {column} FROM {a}))').fetchone()[0]==0
    save(HERE/'results/cohort_audit.json',{'status':'passed','checks':bad,'all_targets_and_inputs_reconstructed':True,
      'source_target_count_matches':True,'source_latest_prior_and_lab_memberships_match':True,'native_identity_complete':True,'patient_hospital_overlap':0,
      'cases_sha256':sha(PRIVATE/'cases.joblib'),'counts':{s:len(v) for s,v in cases.items()},
      'limits':['Retrospective documentation and complete-target-identity selection.','No medication storage clock or full field versions; prospective availability unproven.','Native HICL/dosage/frequency task differs from MIMIC.']})
    print('All native-code, membership, reconstruction and declared clock checks passed.',flush=True)

if __name__=='__main__':main()
