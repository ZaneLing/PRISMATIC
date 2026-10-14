"""Build native-code tasks; no model fitting or test predictions."""
import json,math
from collections import defaultdict
import duckdb,joblib,pandas as pd
from data_contract import HERE,PRIVATE,FIELDS,norm,order,key,sha,digest,save

def main():
    PRIVATE.mkdir(exist_ok=True);(HERE/'results').mkdir(exist_ok=True)
    protocol=json.loads((HERE/'protocol.json').read_text());lock=PRIVATE/'protocol_lock.json'
    if lock.exists():assert json.loads(lock.read_text())['sha256']==sha(HERE/'protocol.json')
    else:save(lock,{'sha256':sha(HERE/'protocol.json')})
    source=PRIVATE.parent/'prismatic-v24';audit=json.loads((HERE.parent/'upgrade_v24/results/source_audit.json').read_text())
    assert sha(source/'cohort.parquet')==audit['private_membership_sha256']
    con=duckdb.connect(str(source/'audit.duckdb'),read_only=True);con.execute('SET threads=1');con.execute("SET memory_limit='3GB'")
    con.execute('''CREATE TEMP TABLE valid_stays AS SELECT c.* FROM cohort c WHERE NOT EXISTS
      (SELECT 1 FROM targets t WHERE t.patientunitstayid=c.patientunitstayid
       AND NOT COALESCE(TRY_CAST(t.drughiclseqno AS BIGINT)>0 AND TRY_CAST(t.drughiclseqno AS DOUBLE)=TRY_CAST(t.drughiclseqno AS BIGINT),false))''')
    con.execute('''CREATE TEMP TABLE members AS SELECT * EXCLUDE(rn) FROM
      (SELECT *,ROW_NUMBER() OVER(PARTITION BY split ORDER BY sha256('rxrsi-eicu-v25:'||patientunitstayid),patientunitstayid) rn FROM valid_stays)
      WHERE (split='train' AND rn<=40000) OR (split IN ('proposal','guard') AND rn<=2000) OR split='test' ''')
    con.execute('''CREATE TEMP VIEW member_details AS SELECT m.*,p.gender,p.age,p.unitdischargeoffset,
      CASE WHEN REPLACE(p.age,' ','')='>89' THEN 90 ELSE FLOOR(TRY_CAST(p.age AS DOUBLE)/10)*10 END AS age_decade
      FROM members m JOIN patient p USING(patientunitstayid)''')
    con.execute('''CREATE TEMP TABLE selected_prior AS SELECT * EXCLUDE(rn) FROM
      (SELECT m.*,TRY_CAST(m.drughiclseqno AS BIGINT) AS hicl,TRY_CAST(m.drugorderoffset AS DOUBLE) AS ordered_at,
        ROW_NUMBER() OVER(PARTITION BY m.patientunitstayid ORDER BY TRY_CAST(m.drugorderoffset AS DOUBLE) DESC,TRY_CAST(m.medicationid AS BIGINT) DESC) rn
       FROM medication m JOIN members c USING(patientunitstayid)
       WHERE TRY_CAST(m.drugorderoffset AS DOUBLE)>=-1080 AND TRY_CAST(m.drugorderoffset AS DOUBLE)<360) WHERE rn<=24''')
    con.execute('''CREATE TEMP TABLE selected_labs AS SELECT * EXCLUDE(rn) FROM
      (SELECT *,ROW_NUMBER() OVER(PARTITION BY patientunitstayid ORDER BY drawn_at DESC,revised_at DESC,TRY_CAST(labid AS BIGINT) DESC) rn FROM
        (SELECT l.*,LOWER(TRIM(l.labname)) AS lab_key,
          LOWER(TRIM(COALESCE(NULLIF(TRIM(l.labmeasurenamesystem),''),NULLIF(TRIM(l.labmeasurenameinterface),''),''))) AS unit_key,
          TRY_CAST(l.labresultoffset AS DOUBLE) AS drawn_at,TRY_CAST(l.labresultrevisedoffset AS DOUBLE) AS revised_at,TRY_CAST(l.labresult AS DOUBLE) AS value,
          ROW_NUMBER() OVER(PARTITION BY l.patientunitstayid,LOWER(TRIM(l.labname)),
            LOWER(TRIM(COALESCE(NULLIF(TRIM(l.labmeasurenamesystem),''),NULLIF(TRIM(l.labmeasurenameinterface),''),'')))
            ORDER BY TRY_CAST(l.labresultoffset AS DOUBLE) DESC,TRY_CAST(l.labresultrevisedoffset AS DOUBLE) DESC,TRY_CAST(l.labid AS BIGINT) DESC) pair_rank
         FROM lab l JOIN members c USING(patientunitstayid)
         WHERE TRY_CAST(l.labresultoffset AS DOUBLE) BETWEEN -1080 AND 360 AND TRY_CAST(l.labresultrevisedoffset AS DOUBLE)<=360
           AND ISFINITE(TRY_CAST(l.labresult AS DOUBLE)) AND NULLIF(TRIM(l.labname),'') IS NOT NULL)
       WHERE pair_rank=1) WHERE rn<=32''')
    queries={'members':'SELECT * FROM member_details ORDER BY split,sha256(\'rxrsi-eicu-v25:\'||patientunitstayid),patientunitstayid',
      'targets':'''SELECT t.*,TRY_CAST(t.drughiclseqno AS BIGINT) AS hicl,TRY_CAST(t.drugorderoffset AS DOUBLE) AS ordered_at
        FROM targets t JOIN members m USING(patientunitstayid) ORDER BY t.patientunitstayid,TRY_CAST(t.medicationid AS BIGINT)''',
      'prior':'SELECT * FROM selected_prior ORDER BY patientunitstayid,ordered_at DESC,TRY_CAST(medicationid AS BIGINT) DESC',
      'labs':'SELECT * FROM selected_labs ORDER BY patientunitstayid,drawn_at DESC,revised_at DESC,TRY_CAST(labid AS BIGINT) DESC'}
    for name,query in queries.items():con.execute(f'COPY ({query}) TO ? (FORMAT PARQUET)',[str(PRIVATE/(name+'.parquet'))])
    members=pd.read_parquet(PRIVATE/'members.parquet');gold=defaultdict(dict);prior=defaultdict(list);labs=defaultdict(list)
    for row in pd.read_parquet(PRIVATE/'targets.parquet').to_dict('records'):
        o=order(row);gold[row['patientunitstayid']][key(o)]=o
    for r in pd.read_parquet(PRIVATE/'prior.parquet').to_dict('records'):
        h=r['hicl'];valid=h is not None and not pd.isna(h) and h>0
        prior[r['patientunitstayid']].append({'drug_code':'hicl:'+str(int(h)) if valid else None,'drug_name':norm(r['drugname']),
          'route':norm(r['routeadmin']),'dosage':norm(r['dosage']),'frequency':norm(r['frequency']),'order_offset':r['ordered_at']})
    for r in pd.read_parquet(PRIVATE/'labs.parquet').to_dict('records'):
        labs[r['patientunitstayid']].append({'name':r['lab_key'],'unit':r['unit_key'],'value':r['value'],'draw_offset':r['drawn_at'],'revised_offset':r['revised_at']})
    cases={s:[] for s in ['train','proposal','guard','test']}
    for r in members.to_dict('records'):
        h=r['patientunitstayid'];cases[r['split']].append({'case_id':digest(['eicu-v25',h]),'patient_hash':digest(['eicu-patient',r['uniquepid']]),
          'hospital_hash':digest(['eicu-hospital',r['hospitalid']]),'context':{'gender':norm(r['gender']),'age_decade':int(r['age_decade']),
            'prior_orders':prior[h],'available_labs':labs[h]},'gold':list(gold[h].values())})
    assert len(cases['train'])==40000 and len(cases['proposal'])==len(cases['guard'])==2000
    joblib.dump(cases,PRIVATE/'cases.joblib')
    result={'status':'cohort_built','protocol_sha256':sha(HERE/'protocol.json'),
      'label_complete_population':con.execute('SELECT COUNT(*) FROM valid_stays').fetchone()[0],
      'excluded_incomplete_identity_stays':con.execute('SELECT COUNT(*) FROM cohort').fetchone()[0]-con.execute('SELECT COUNT(*) FROM valid_stays').fetchone()[0],
      'splits':{s:{'stays':len(cs),'patients':len({c['patient_hash'] for c in cs}),'hospitals':len({c['hospital_hash'] for c in cs}),
        'zero_target_stays':sum(not c['gold'] for c in cs),'unique_drug_targets':sum(len({o['drug_code'] for o in c['gold']}) for c in cs),
        'all_joint_targets':sum(len(c['gold']) for c in cs),'complete_joint_targets':sum(all(o[f] is not None for f in FIELDS) for c in cs for o in c['gold'])} for s,cs in cases.items()},
      'source_rows':{n:con.execute(f'SELECT COUNT(*) FROM ({q})').fetchone()[0] for n,q in queries.items()},
      'files_sha256':{p.name:sha(p) for p in [PRIVATE/'cases.joblib']+[PRIVATE/(x+'.parquet') for x in queries]},'no_model_scores':True}
    save(HERE/'results/cohort_manifest.json',result);print(json.dumps(result),flush=True)

if __name__=='__main__':main()
