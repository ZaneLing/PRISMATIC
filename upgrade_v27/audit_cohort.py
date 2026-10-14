"""Independently reconstruct selected source labels/inputs and resource coverage."""
import csv,hashlib,json,re
from collections import defaultdict
from pathlib import Path
import duckdb,joblib,numpy as np,pandas as pd

HERE=Path(__file__).resolve().parent;ROOT=Path.home()/'Desktop/MedTreeBench/dataset/restricted'
PRIVATE=ROOT/'prismatic-v27';SOURCE=ROOT/'mimiciv/3.1'
RESOURCE=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/resources'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()
def normalize_ndc(value):
    value=value.strip();pieces=value.split('-')
    if len(pieces)==1:return value if value.isdecimal() and len(value)==11 else None
    if tuple(map(len,pieces)) not in [(4,4,2),(5,3,2),(5,4,1),(5,4,2)] or not all(x.isdecimal() for x in pieces):return None
    return ''.join(x.zfill(width) for x,width in zip(pieces,[5,4,2]))

def main():
    bundle=joblib.load(PRIVATE/'visits.joblib');data=bundle['data'];vocab=bundle['vocab'];members=pd.read_parquet(PRIVATE/'members.parquet')
    con=duckdb.connect();con.execute('SET threads=2');con.execute("SET memory_limit='3GB'");con.register('members',members[['subject_id','hadm_id']])
    mapping=defaultdict(set)
    with Path('/tmp/prismatic-safedrug/data/input/RXCUI2atc4.csv').open() as f:
        for row in csv.DictReader(f):
            code=row['ATC4'];ndc=normalize_ndc(row['NDC'])
            if ndc and re.fullmatch(r'[A-Z]\d{2}[A-Z]{2}',code):mapping[ndc].add(code)
    pairs=pd.DataFrame([(n,next(iter(c))) for n,c in mapping.items() if len(c)==1],columns=['ndc','code']);con.register('map',pairs)
    raw=con.execute('''SELECT p.hadm_id,m.code FROM read_csv(?,all_varchar=true) p JOIN members b USING(subject_id,hadm_id)
       JOIN map m ON TRIM(p.ndc)=m.ndc''',[str(SOURCE/'hosp/prescriptions.csv.gz')]).fetchall()
    med=defaultdict(set)
    for hadm,code in raw:med[hadm].add(code)
    sources={'medications':med}
    for field,filename in [('diagnoses','diagnoses_icd.csv.gz'),('procedures','procedures_icd.csv.gz')]:
        rows=con.execute('''SELECT p.hadm_id,p.icd_version,p.icd_code FROM read_csv(?,all_varchar=true) p
          JOIN members b USING(subject_id,hadm_id)''',[str(SOURCE/'hosp'/filename)]).fetchall();codes=defaultdict(set)
        for hadm,version,code in rows:
            if version in ['9','10'] and code and code.strip():codes[hadm].add('ICD'+version+':'+code.strip())
        sources[field]=codes
    for row in members.to_dict('records'):
        for field,values in sources.items():assert set(row[field])==values[row['hadm_id']]
    population=con.execute('''SELECT a.subject_id,a.hadm_id,CAST(a.admittime AS TIMESTAMP) AS admittime
      FROM read_csv(?,all_varchar=true) a JOIN read_csv(?,all_varchar=true) p USING(subject_id)
      WHERE TRY_CAST(p.anchor_age AS INTEGER)+YEAR(TRY_CAST(a.admittime AS TIMESTAMP))-TRY_CAST(p.anchor_year AS INTEGER)>=18
      AND a.hadm_id IN (SELECT hadm_id FROM read_csv(?,all_varchar=true))''',
      [str(SOURCE/'hosp/admissions.csv.gz'),str(SOURCE/'hosp/patients.csv.gz'),str(SOURCE/'icu/icustays.csv.gz')]).fetchdf()
    assert set(members.hadm_id)<=set(population.hadm_id)
    source_times=population.set_index('hadm_id').admittime
    assert all(row.admittime==source_times[row.hadm_id] for row in members.itertuples())
    by_hash={digest(str(s)):f.sort_values(['admittime','hadm_id']) for s,f in members.groupby('subject_id')}
    for part,patients in data.items():
        for patient in patients:
            frame=by_hash[patient['subject_hash']];subject=str(frame.subject_id.iloc[0])
            bucket=int.from_bytes(hashlib.blake2b(('patient-split-2026:'+subject).encode(),digest_size=8).digest(),'big')%10
            expected='test' if bucket==0 else ('proposal' if int(digest(['v27-validation',subject])[:8],16)%2==0 else 'guard') if bucket==1 else 'train'
            assert expected==part and len(frame)>=2
            assert [digest(['v27-visit',str(h)]) for h in frame.hadm_id]==[v['case_id'] for v in patient['visits']]
            for row,visit in zip(frame.to_dict('records'),patient['visits']):
                for field in vocab:assert set(visit[field])==sources[field][row['hadm_id']]
    for field,values in vocab.items():assert values==sorted({c for p in data['train'] for v in p['visits'] for c in v[field]})
    training=set(vocab['medications']);molecules=json.loads((RESOURCE/'v27-molecules/atc4_molecules.json').read_text());covered=training&set(molecules)
    coverage={}
    for part,patients in data.items():
        labels=[c for p in patients for v in p['visits'] for c in v['medications']]
        coverage[part]={'targets':len(labels),'outside_training_vocabulary':sum(c not in training for c in labels),
          'with_training_class_molecules':sum(c in covered for c in labels)}
    # Earlier observed cohorts: report intersections, do not silently call them fresh.
    previous={}
    for name,filename in [('v9',ROOT/'prismatic-v9/cases.json'),('v21',ROOT/'prismatic-v21/cases.json')]:
        if filename.exists():previous[name]={c['subject_hash'] for c in json.loads(filename.read_text())['test']}
    test={p['subject_hash'] for p in data['test']}
    report={'status':'passed','selected_visits_reconstructed':len(members),'mapped_source_rows_reconstructed':len(raw),
      'fields_reconstructed':['diagnoses','procedures','medications','admission_order','adult_ICU_membership','patient_partition','training_only_vocabularies'],
      'bundle_sha256':sha(PRIVATE/'visits.joblib'),'member_sha256':sha(PRIVATE/'members.parquet'),
      'molecular_coverage':{'training_classes':len(training),'classes_with_molecules':len(covered),'classes_without_molecules':sorted(training-covered),'by_split':coverage},
      'prior_observed_test_patient_overlap':{k:len(test&v) for k,v in previous.items()},
      'fresh_confirmation_claim':False,
      'limit':'Independently checks every selected visit and split; full population eligibility/sampling flow is produced by the builder, not independently rescanned here.',
      'test_predictions_generated':False}
    (HERE/'results/cohort_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True);con.close()

if __name__=='__main__':main()
