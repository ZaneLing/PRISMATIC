"""Build a separate retrospective visit-set panel from licensed local sources."""
import hashlib, json, sys
from collections import Counter
from pathlib import Path
import duckdb, joblib, pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = Path.home()/'Desktop/MedTreeBench/dataset/restricted'
PRIVATE = ROOT/'prismatic-v27'
SOURCE = ROOT/'mimiciv/3.1'
sys.path.insert(0, str(HERE.parent/'upgrade_v3'))
from build_atc4_cohort import ndc11, split_patient

def digest(value): return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,value): p.write_text(json.dumps(value,indent=2)+'\n')

def main():
    PRIVATE.mkdir(exist_ok=True); (HERE/'results').mkdir(exist_ok=True)
    protocol=json.loads((HERE/'protocol.json').read_text())
    lock={'protocol_sha256':sha(HERE/'protocol.json'),'builder_sha256':sha(Path(__file__)),
          'mapping_helper_sha256':sha(HERE.parent/'upgrade_v3/build_atc4_cohort.py')}
    lp=PRIVATE/'execution_lock.json'
    if lp.exists(): assert json.loads(lp.read_text())==lock
    else: save(lp,lock)
    mp=Path('/tmp/prismatic-safedrug/data/input/RXCUI2atc4.csv')
    assert sha(mp)=='162fefc5cc374ac545501dec0d3738cb7a362e1e08b46b64d1a779eaeda7888e'
    raw=pd.read_csv(mp,dtype=str,usecols=['NDC','ATC4']);raw['ndc']=raw.NDC.map(ndc11)
    raw=raw.dropna(subset=['ndc','ATC4']);raw=raw[raw.ATC4.str.fullmatch(r'[A-Z][0-9]{2}[A-Z]{2}')]
    n=raw.groupby('ndc').ATC4.nunique();mapping=raw[raw.ndc.isin(n[n==1].index)].drop_duplicates('ndc')[['ndc','ATC4']]
    con=duckdb.connect(str(PRIVATE/'cohort.duckdb'));con.execute('SET threads=2');con.execute("SET memory_limit='4GB'")
    con.execute('SET preserve_insertion_order=false');con.register('mapping',mapping)
    def exists(name): return name in {x[0] for x in con.execute('SHOW TABLES').fetchall()}
    if not exists('admissions'):
        con.execute('''CREATE TABLE admissions AS SELECT a.subject_id,a.hadm_id,TRY_CAST(a.admittime AS TIMESTAMP) AS admittime,
          TRY_CAST(a.dischtime AS TIMESTAMP) AS dischtime FROM read_csv(?,all_varchar=true) a
          JOIN read_csv(?,all_varchar=true) p USING(subject_id)
          WHERE TRY_CAST(p.anchor_age AS INTEGER)+YEAR(TRY_CAST(a.admittime AS TIMESTAMP))-TRY_CAST(p.anchor_year AS INTEGER)>=18
          AND a.hadm_id IN (SELECT DISTINCT hadm_id FROM read_csv(?,all_varchar=true))''',
          [str(SOURCE/'hosp/admissions.csv.gz'),str(SOURCE/'hosp/patients.csv.gz'),str(SOURCE/'icu/icustays.csv.gz')])
        assert con.execute('SELECT COUNT(*)-COUNT(DISTINCT hadm_id) FROM admissions').fetchone()[0]==0
    if not exists('rx'):
        con.execute('''CREATE TABLE rx AS SELECT p.subject_id,p.hadm_id,TRIM(p.ndc) AS ndc,m.ATC4 AS atc4
          FROM read_csv(?,all_varchar=true) p JOIN admissions a USING(subject_id,hadm_id)
          LEFT JOIN mapping m ON TRIM(p.ndc)=m.ndc''',[str(SOURCE/'hosp/prescriptions.csv.gz')])
        print('Whole-visit prescription mapping completed.',flush=True)
    for table,filename in [('diagnoses','diagnoses_icd.csv.gz'),('procedures','procedures_icd.csv.gz')]:
        if not exists(table):
            con.execute(f'''CREATE TABLE {table} AS SELECT d.subject_id,d.hadm_id,'ICD'||TRIM(d.icd_version)||':'||TRIM(d.icd_code) AS code
              FROM read_csv(?,all_varchar=true) d JOIN admissions a USING(subject_id,hadm_id)
              WHERE d.icd_code IS NOT NULL AND TRIM(d.icd_code)<>'' AND d.icd_version IN ('9','10')''',[str(SOURCE/'hosp'/filename)])
    flow={
      'adult_icu_admissions':con.execute('SELECT COUNT(*) FROM admissions').fetchone()[0],
      'source_prescription_rows':con.execute('SELECT COUNT(*) FROM rx').fetchone()[0],
      'unambiguous_mapped_rows':con.execute('SELECT COUNT(*) FROM rx WHERE atc4 IS NOT NULL').fetchone()[0]}
    visits=con.execute('''SELECT a.*,d.codes AS diagnoses,p.codes AS procedures,r.codes AS medications
      FROM admissions a JOIN (SELECT hadm_id,LIST_SORT(LIST_DISTINCT(LIST(code))) AS codes FROM diagnoses GROUP BY hadm_id) d USING(hadm_id)
      JOIN (SELECT hadm_id,LIST_SORT(LIST_DISTINCT(LIST(code))) AS codes FROM procedures GROUP BY hadm_id) p USING(hadm_id)
      JOIN (SELECT hadm_id,LIST_SORT(LIST_DISTINCT(LIST(atc4))) AS codes FROM rx WHERE atc4 IS NOT NULL GROUP BY hadm_id) r USING(hadm_id)
      ORDER BY subject_id,admittime,hadm_id''').fetchdf()
    flow['eligible_visits_before_repeat_patient_rule']=len(visits)
    repeat=visits.groupby('subject_id').size();visits=visits[visits.subject_id.isin(repeat[repeat>=2].index)].copy()
    flow.update(eligible_repeated_patients=int(visits.subject_id.nunique()),eligible_repeated_visits=len(visits))
    patients=visits[['subject_id']].drop_duplicates().copy();patients['part']=patients.subject_id.map(split_patient)
    val=patients.part.eq('val')
    patients.loc[val,'part']=patients.loc[val,'subject_id'].map(lambda s:'proposal' if int(digest(['v27-validation',s])[:8],16)%2==0 else 'guard')
    patients['sample_hash']=patients.subject_id.map(lambda s:digest(['v27-patient',s]))
    pieces=[]
    for part,cap in protocol['patient_caps'].items():pieces.append(patients[patients.part==part].sort_values('sample_hash').head(cap))
    patients=pd.concat(pieces);members=visits.merge(patients[['subject_id','part']],on='subject_id',validate='many_to_one')
    members.to_parquet(PRIVATE/'members.parquet',index=False)
    data={part:[] for part in protocol['patient_caps']}
    for subject,frame in members.groupby('subject_id',sort=True):
        part=frame.part.iloc[0];sequence=[]
        for row in frame.sort_values(['admittime','hadm_id']).to_dict('records'):
            sequence.append({'case_id':digest(['v27-visit',str(row['hadm_id'])]),'diagnoses':list(row['diagnoses']),
                             'procedures':list(row['procedures']),'medications':list(row['medications'])})
        data[part].append({'subject_hash':digest(str(subject)),'visits':sequence})
    for a in data:
        for b in data:
            if a!=b:assert not {p['subject_hash'] for p in data[a]}&{p['subject_hash'] for p in data[b]}
    vocab={field:sorted({c for p in data['train'] for v in p['visits'] for c in v[field]}) for field in ['diagnoses','procedures','medications']}
    assert all(len(p['visits'])>=2 for rows in data.values() for p in rows)
    joblib.dump({'data':data,'vocab':vocab},PRIVATE/'visits.joblib')
    selected_rx=con.execute('''SELECT COUNT(*),COUNT(*) FILTER(WHERE atc4 IS NOT NULL)
       FROM rx WHERE hadm_id IN (SELECT hadm_id FROM read_parquet(?))''',[str(PRIVATE/'members.parquet')]).fetchone()
    report={'status':'complete','execution_lock':lock,'flow':flow,'public_map_sha256':sha(mp),
      'unambiguous_public_ndc_count':len(mapping),'selected_source_rows':selected_rx[0],'selected_mapped_rows':selected_rx[1],
      'selected_row_mapping_fraction':selected_rx[1]/max(1,selected_rx[0]),
      'training_vocabulary':{k:len(v) for k,v in vocab.items()},'splits':{},'cross_split_patient_overlap':0,
      'bundle_sha256':sha(PRIVATE/'visits.joblib'),'membership_sha256':sha(PRIVATE/'members.parquet'),
      'test_predictions_generated':False,'task':protocol['task'],'test_status':protocol['test_status']}
    for part,rows in data.items():
        report['splits'][part]={'patients':len(rows),'visits':sum(len(p['visits']) for p in rows),
          'max_visits':max(len(p['visits']) for p in rows),'membership_digest':digest([p['subject_hash'] for p in rows]),
          'oov_occurrences':{field:sum(c not in set(vocab[field]) for p in rows for v in p['visits'] for c in v[field]) for field in vocab},
          'medication_targets':sum(len(v['medications']) for p in rows for v in p['visits'])}
    save(HERE/'results/cohort_manifest.json',report); print(json.dumps(report),flush=True);con.close()

if __name__=='__main__':main()
