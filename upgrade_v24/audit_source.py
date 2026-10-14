"""Audit external task feasibility without fitting or scoring any model."""
import hashlib,json,time
from pathlib import Path
import duckdb
HERE=Path(__file__).resolve().parent
ROOT=Path.home()/'Desktop/MedTreeBench/dataset/restricted'
SOURCE=ROOT/'eicu-crd-v2.0';PRIVATE=ROOT/'prismatic-v24'

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for part in iter(lambda:f.read(4*1024*1024),b''):h.update(part)
    return h.hexdigest()

def main():
    begin=time.time();PRIVATE.mkdir(exist_ok=True);(HERE/'results').mkdir(exist_ok=True)
    protocol=json.loads((HERE/'protocol.json').read_text());lock=PRIVATE/'protocol_lock.json';signature=sha(HERE/'protocol.json')
    if lock.exists():assert json.loads(lock.read_text())['sha256']==signature
    else:lock.write_text(json.dumps({'sha256':signature})+'\n')
    con=duckdb.connect(str(PRIVATE/'audit.duckdb'));con.execute('SET threads=1');con.execute("SET memory_limit='2GB'")
    for name in ['patient','medication','lab']:
        exists=con.execute('SELECT count(*) FROM information_schema.tables WHERE table_name=?',[name]).fetchone()[0]
        if not exists:con.execute(f'CREATE TABLE {name} AS SELECT * FROM read_csv(?,all_varchar=true)',[str(SOURCE/(name+'.csv.gz'))])
        print(json.dumps({'loaded_table':name,'rows':con.execute(f'SELECT count(*) FROM {name}').fetchone()[0]}),flush=True)
    hospitals=[x[0] for x in con.execute("SELECT DISTINCT hospitalid FROM patient WHERE hospitalid IS NOT NULL").fetchall()]
    con.execute('CREATE OR REPLACE TABLE hospital_partition(hospitalid VARCHAR,split VARCHAR,priority INTEGER)')
    assignments=[]
    for h in hospitals:
        bucket=int(hashlib.sha256(('rxrsi-eicu-v24:'+h).encode()).hexdigest()[:16],16)%10
        split={0:'test',1:'guard',2:'proposal'}.get(bucket,'train');rank={'test':3,'guard':2,'proposal':1,'train':0}[split]
        assignments.append((h,split,rank))
    con.executemany('INSERT INTO hospital_partition VALUES(?,?,?)',assignments)
    con.execute('''CREATE OR REPLACE TABLE eligible AS SELECT p.patientunitstayid,p.uniquepid,p.hospitalid,h.split,h.priority
      FROM patient p JOIN hospital_partition h USING(hospitalid)
      WHERE (TRY_CAST(p.age AS DOUBLE)>=18 OR REPLACE(p.age,' ','')='>89')
      AND TRY_CAST(p.unitdischargeoffset AS DOUBLE)>=720 AND NULLIF(TRIM(p.uniquepid),'') IS NOT NULL
      AND EXISTS(SELECT 1 FROM medication m WHERE m.patientunitstayid=p.patientunitstayid)''')
    con.execute('''CREATE OR REPLACE TABLE cohort AS SELECT patientunitstayid,uniquepid,hospitalid,split FROM
      (SELECT *,MAX(priority) OVER(PARTITION BY uniquepid) AS highest FROM eligible) WHERE priority=highest''')
    con.execute('''CREATE OR REPLACE TABLE targets AS SELECT m.*,c.split FROM medication m JOIN cohort c USING(patientunitstayid)
      WHERE TRY_CAST(drugorderoffset AS DOUBLE)>=360 AND TRY_CAST(drugorderoffset AS DOUBLE)<720''')
    membership=PRIVATE/'cohort.parquet';con.execute('COPY (SELECT * FROM cohort ORDER BY split,patientunitstayid) TO ? (FORMAT PARQUET)',[str(membership)])
    totals={n:con.execute(f'SELECT COUNT(*) FROM {n}').fetchone()[0] for n in ['patient','medication','lab','eligible','cohort','targets']}
    assert totals['cohort']==con.execute('SELECT COUNT(DISTINCT patientunitstayid) FROM cohort').fetchone()[0]
    overlap={key:con.execute(f'SELECT COUNT(*) FROM (SELECT {key} FROM cohort GROUP BY {key} HAVING COUNT(DISTINCT split)>1)').fetchone()[0] for key in ['uniquepid','hospitalid']}
    assert all(x==0 for x in overlap.values())
    split_rows={}
    for split in ['train','proposal','guard','test']:
        base=con.execute('SELECT COUNT(*),COUNT(DISTINCT uniquepid),COUNT(DISTINCT hospitalid) FROM cohort WHERE split=?',[split]).fetchone()
        target=con.execute('''SELECT COUNT(*),COUNT(DISTINCT patientunitstayid),COUNT(*) FILTER(WHERE NULLIF(TRIM(drugname),'') IS NULL),
          COUNT(*) FILTER(WHERE NULLIF(TRIM(drughiclseqno),'') IS NULL OR drughiclseqno='0'),
          COUNT(*) FILTER(WHERE NULLIF(TRIM(dosage),'') IS NULL),COUNT(*) FILTER(WHERE NULLIF(TRIM(routeadmin),'') IS NULL),
          COUNT(*) FILTER(WHERE NULLIF(TRIM(frequency),'') IS NULL),COUNT(*) FILTER(WHERE LOWER(drugordercancelled)='yes')
          FROM targets WHERE split=?''',[split]).fetchone()
        split_rows[split]=dict(zip(['stays','patients','hospitals'],base))
        split_rows[split].update(dict(zip(['target_rows','stays_with_target_rows','target_missing_name','target_missing_hicl','target_missing_dosage','target_missing_route','target_missing_frequency','target_final_cancelled'],target)))
        split_rows[split]['zero_target_stays']=base[0]-target[1]
    lab=con.execute('''SELECT COUNT(*),COUNT(*) FILTER(WHERE TRY_CAST(labresultrevisedoffset AS DOUBLE)<=360),
        COUNT(*) FILTER(WHERE TRY_CAST(labresultrevisedoffset AS DOUBLE)>360),
        COUNT(*) FILTER(WHERE TRY_CAST(labresultrevisedoffset AS DOUBLE) IS NULL)
        FROM lab l JOIN cohort c USING(patientunitstayid) WHERE TRY_CAST(labresultoffset AS DOUBLE)<=360
        AND ISFINITE(TRY_CAST(labresult AS DOUBLE))''').fetchone()
    order_time=con.execute('''SELECT COUNT(*) FILTER(WHERE TRY_CAST(drugorderoffset AS DOUBLE) IS NULL),
        COUNT(*) FILTER(WHERE TRY_CAST(drugorderoffset AS DOUBLE)<360),
        COUNT(*) FILTER(WHERE TRY_CAST(drugstartoffset AS DOUBLE)>=360 AND TRY_CAST(drugstartoffset AS DOUBLE)<720
          AND NOT(TRY_CAST(drugorderoffset AS DOUBLE)>=360 AND TRY_CAST(drugorderoffset AS DOUBLE)<720))
        FROM medication m JOIN cohort c USING(patientunitstayid)''').fetchone()
    result={'status':'complete','protocol_sha256':signature,'source_rows':totals,'splits':split_rows,'cross_split_overlap':overlap,
       'dropped_cross_partition_patient_stays':totals['eligible']-totals['cohort'],
       'labs':dict(zip(['finite_drawn_by_decision','also_revised_by_decision','revised_after_decision','missing_revision_offset'],lab)),
       'orders':dict(zip(['missing_order_offset','prior_order_rows','start_in_target_but_ordered_elsewhere'],order_time)),
       'private_membership_sha256':sha(membership),'source_sha256':{n:sha(SOURCE/(n+'.csv.gz')) for n in ['patient','medication','lab']},
       'no_model_fitted':True,'no_model_scores':True,'claim_boundary':protocol['claim_boundary'],'seconds':time.time()-begin}
    (HERE/'results/source_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)

if __name__=='__main__':main()
