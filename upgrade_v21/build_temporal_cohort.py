"""Rebuild a conservative order task from complete sources, never old targets."""
import hashlib,json,sys,time
from pathlib import Path
import duckdb,joblib,numpy as np,pandas as pd
HERE=Path(__file__).resolve().parent;ROOT=Path.home()/'Desktop/MedTreeBench/dataset/restricted';PRIVATE=ROOT/'prismatic-v21'
sys.path.insert(0,str(HERE.parent/'upgrade_v7'))
from rx_agent import hash_data,record_order,key,FIELDS

def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')

def main():
    PRIVATE.mkdir(exist_ok=True);(HERE/'results').mkdir(exist_ok=True)
    protocol=json.loads((HERE/'protocol.json').read_text());signature=hash_data(protocol)
    locked=PRIVATE/'protocol_signature.json'
    if locked.exists():assert json.loads(locked.read_text())['sha256']==signature
    else:save(locked,{'sha256':signature})
    con=duckdb.connect(str(PRIVATE/'cohort.duckdb'));con.execute('SET threads=2');con.execute("SET memory_limit='5GB'");con.execute('SET preserve_insertion_order=false')
    def exists(name):return name in {r[0] for r in con.execute('SHOW TABLES').fetchall()}
    hosp=ROOT/'mimiciv/3.1/hosp'
    if not exists('population'):
        con.execute('''CREATE TABLE population AS SELECT c.subject_id,c.hadm_id,c.split,
            TRY_CAST(a.admittime AS TIMESTAMP)+INTERVAL 6 HOUR AS decision_time,
            TRY_CAST(a.dischtime AS TIMESTAMP) AS discharge_time,p.gender,
            CAST(FLOOR((TRY_CAST(p.anchor_age AS DOUBLE)+YEAR(TRY_CAST(a.admittime AS TIMESTAMP))-TRY_CAST(p.anchor_year AS DOUBLE))/10) AS INTEGER)*10 AS age_decade
            FROM read_parquet(?) c JOIN read_csv(?,all_varchar=true) a ON c.subject_id=a.subject_id AND c.hadm_id=a.hadm_id
            JOIN read_csv(?,all_varchar=true) p ON c.subject_id=p.subject_id''',
            [str(ROOT/'prismatic-v4/cohort.parquet'),str(hosp/'admissions.csv.gz'),str(hosp/'patients.csv.gz')])
    if not exists('all_orders'):
        con.execute('''CREATE TABLE all_orders AS SELECT p.subject_id,p.hadm_id,p.pharmacy_id,p.poe_id,LOWER(TRIM(p.drug)) AS drug_key,
            p.route,p.dose_val_rx,p.dose_unit_rx,p.doses_per_24_hrs,p.ndc,p.gsn,p.drug_type
            FROM read_csv(?,all_varchar=true) p JOIN population c ON p.subject_id=c.subject_id AND p.hadm_id=c.hadm_id''',[str(hosp/'prescriptions.csv.gz')])
        print('Complete prescription rows prepared.',flush=True)
    if not exists('provider_orders'):
        con.execute('''CREATE TABLE provider_orders AS SELECT p.poe_id,p.subject_id,p.hadm_id,TRY_CAST(p.ordertime AS TIMESTAMP) AS ordertime,p.transaction_type
            FROM read_csv(?,all_varchar=true) p WHERE p.poe_id IN (SELECT DISTINCT poe_id FROM all_orders WHERE poe_id IS NOT NULL)''',[str(hosp/'poe.csv.gz')])
    if not exists('pharmacy_orders'):
        con.execute('''CREATE TABLE pharmacy_orders AS SELECT p.pharmacy_id,p.subject_id,p.hadm_id,p.poe_id AS pharmacy_poe_id,
            TRY_CAST(p.entertime AS TIMESTAMP) AS entertime,TRY_CAST(p.verifiedtime AS TIMESTAMP) AS verifiedtime
            FROM read_csv(?,all_varchar=true) p WHERE p.pharmacy_id IN (SELECT DISTINCT pharmacy_id FROM all_orders)''',[str(hosp/'pharmacy.csv.gz')])
    for table,column in [('provider_orders','poe_id'),('pharmacy_orders','pharmacy_id')]:
        assert con.execute(f'SELECT COUNT(*)-COUNT(DISTINCT {column}) FROM {table}').fetchone()[0]==0
    con.execute('''CREATE OR REPLACE TEMP VIEW joined AS SELECT o.*,c.decision_time,c.discharge_time,p.ordertime,p.transaction_type,f.entertime,f.verifiedtime,
        COALESCE(p.subject_id=o.subject_id AND p.hadm_id=o.hadm_id AND f.subject_id=o.subject_id AND f.hadm_id=o.hadm_id AND o.poe_id=f.pharmacy_poe_id,false) AS exact_identity,
        COALESCE((p.ordertime>=c.decision_time AND p.ordertime<c.decision_time+INTERVAL 6 HOUR) OR (f.entertime>=c.decision_time AND f.entertime<c.decision_time+INTERVAL 6 HOUR),false) AS potential,
        COALESCE(p.subject_id=o.subject_id AND p.hadm_id=o.hadm_id AND f.subject_id=o.subject_id AND f.hadm_id=o.hadm_id AND o.poe_id=f.pharmacy_poe_id
            AND p.ordertime>=c.decision_time AND p.ordertime<c.decision_time+INTERVAL 6 HOUR
            AND f.entertime>=c.decision_time AND f.entertime<c.decision_time+INTERVAL 6 HOUR
            AND f.verifiedtime IS NOT NULL AND f.verifiedtime<=c.decision_time+INTERVAL 6 HOUR
            AND p.transaction_type IN ('New','Change'),false) AS trusted
        FROM all_orders o JOIN population c USING(subject_id,hadm_id)
        LEFT JOIN provider_orders p ON o.poe_id=p.poe_id LEFT JOIN pharmacy_orders f ON o.pharmacy_id=f.pharmacy_id''')
    if not exists('eligibility'):
        con.execute('''CREATE TABLE eligibility AS SELECT subject_id,hadm_id,COUNT(*) FILTER(WHERE potential) AS potential_rows,
            COUNT(*) FILTER(WHERE trusted) AS trusted_rows,COUNT(*) FILTER(WHERE potential AND NOT trusted) AS ambiguous_rows
            FROM joined GROUP BY subject_id,hadm_id''')
    flow=con.execute('''SELECT COUNT(*) population,COUNT(*) FILTER(WHERE c.discharge_time>=c.decision_time+INTERVAL 6 HOUR) followup_complete,
        COUNT(*) FILTER(WHERE e.potential_rows>0) has_potential,COUNT(*) FILTER(WHERE e.ambiguous_rows>0) has_ambiguous,
        COUNT(*) FILTER(WHERE e.trusted_rows>0 AND e.ambiguous_rows=0 AND c.discharge_time>=c.decision_time+INTERVAL 6 HOUR) eligible
        FROM population c LEFT JOIN eligibility e USING(subject_id,hadm_id)''').fetchdf().to_dict('records')[0]
    eligible=con.execute('''SELECT c.* FROM population c JOIN eligibility e USING(subject_id,hadm_id)
        WHERE e.trusted_rows>0 AND e.ambiguous_rows=0 AND c.discharge_time>=c.decision_time+INTERVAL 6 HOUR''').fetchdf()
    old6=joblib.load(ROOT/'prismatic-v6/evaluation_bundle.joblib');old7=joblib.load(ROOT/'prismatic-v7/data.joblib')
    excluded=set(old6['parts']['test'].subject_id)|set(old7['parts']['test'].subject_id)
    old9=json.loads((ROOT/'prismatic-v9/cases.json').read_text());old9hash={c['subject_hash'] for c in old9['test']}
    excluded|={s for s in eligible.subject_id if hash_data(str(s)) in old9hash}
    del old6,old7,old9
    eligible['part']=eligible['split'];val=eligible.split.eq('val')
    eligible.loc[val,'part']=eligible.loc[val,'subject_id'].map(lambda s:'proposal' if int(hash_data(['v21-validation',str(s)])[:8],16)%2==0 else 'guard')
    removed_test=int((eligible.part.eq('test')&eligible.subject_id.isin(excluded)).sum())
    eligible=eligible[~(eligible.part.eq('test')&eligible.subject_id.isin(excluded))].copy()
    eligible['sample_hash']=eligible.hadm_id.map(lambda h:hash_data(['v21-case',str(h)]))
    parts={s:eligible[eligible.part==s].sort_values('sample_hash').head(cap).copy() for s,cap in protocol['sample_caps'].items()}
    for a in parts:
        for b in parts:
            if a!=b:assert not set(parts[a].subject_id)&set(parts[b].subject_id)
    assert len(parts['test'])>=300 and len(parts['train'])>=4000,'Cohort too small for the registered evaluation; inspect flow before revising protocol'
    members=pd.concat(parts.values());con.register('members',members[['subject_id','hadm_id']])
    targets=con.execute('SELECT j.* FROM joined j JOIN members m USING(subject_id,hadm_id) WHERE trusted').fetchdf()
    prior=con.execute('''SELECT j.*,GREATEST(ordertime,entertime,verifiedtime) AS available_at FROM joined j JOIN members m USING(subject_id,hadm_id)
        WHERE exact_identity AND ordertime IS NOT NULL AND entertime IS NOT NULL AND verifiedtime IS NOT NULL
        AND ordertime<decision_time AND entertime<decision_time AND verifiedtime<decision_time
        AND GREATEST(ordertime,entertime,verifiedtime)>=decision_time-INTERVAL 24 HOUR''').fetchdf()
    if not exists('latest_labs'):
        con.execute('''CREATE TEMP TABLE lab_items AS SELECT itemid,label,fluid FROM read_csv(?,all_varchar=true) WHERE fluid='Blood' ''',[str(hosp/'d_labitems.csv.gz')])
        con.execute('''CREATE TABLE latest_labs AS SELECT c.subject_id,c.hadm_id,c.decision_time,l.labevent_id,l.itemid,i.label,l.valueuom,
            TRY_CAST(l.charttime AS TIMESTAMP) AS charttime,TRY_CAST(l.storetime AS TIMESTAMP) AS storetime,TRY_CAST(l.valuenum AS DOUBLE) AS value
            FROM read_csv(?,all_varchar=true) l JOIN population c ON l.subject_id=c.subject_id AND l.hadm_id=c.hadm_id
            JOIN members m ON c.subject_id=m.subject_id AND c.hadm_id=m.hadm_id JOIN lab_items i ON l.itemid=i.itemid
            WHERE TRY_CAST(l.charttime AS TIMESTAMP)>=c.decision_time-INTERVAL 24 HOUR AND TRY_CAST(l.charttime AS TIMESTAMP)<=c.decision_time
                AND TRY_CAST(l.storetime AS TIMESTAMP)<=c.decision_time AND TRY_CAST(l.valuenum AS DOUBLE) IS NOT NULL
            QUALIFY ROW_NUMBER() OVER(PARTITION BY c.hadm_id,l.itemid ORDER BY TRY_CAST(l.charttime AS TIMESTAMP) DESC,TRY_CAST(l.storetime AS TIMESTAMP) DESC,TRY_CAST(l.labevent_id AS BIGINT) DESC)=1''',[str(hosp/'labevents.csv.gz')])
    labs=con.execute('SELECT * FROM latest_labs').fetchdf()
    assert not ((labs.charttime>labs.decision_time)|(labs.storetime>labs.decision_time)|labs.storetime.isna()).any()
    truth={};history={};lab_by={}
    for row in targets.to_dict('records'):
        o=record_order(row)
        if o['drug_name']:truth.setdefault(str(row['hadm_id']),{})[key(o,FIELDS)]=o
    for row in prior.sort_values('available_at',ascending=False).to_dict('records'):
        h=str(row['hadm_id']);o=record_order(row);index=history.setdefault(h,{})
        if o['drug_name'] and len(index)<24:index.setdefault(key(o,FIELDS),o)
    for row in labs.sort_values('storetime',ascending=False).to_dict('records'):
        values=lab_by.setdefault(str(row['hadm_id']),[])
        if len(values)<32:values.append({'itemid':row['itemid'],'name':row['label'],'value':float(row['value']),'unit':row['valueuom']})
    data={}
    for split,frame in parts.items():
        data[split]=[]
        for row in frame.to_dict('records'):
            h=str(row['hadm_id']);orders=list(truth.get(h,{}).values());assert orders
            view={'gender':row['gender'],'age_decade':int(row['age_decade']) if pd.notna(row['age_decade']) else None,
                'hours_since_admission':6,'recorded_prior_orders':list(history.get(h,{}).values()),'available_labs':lab_by.get(h,[])}
            data[split].append({'case_id':hash_data(['v21',h]),'subject_hash':hash_data(str(row['subject_id'])),'context':view,'gold':orders})
    save(PRIVATE/'cases.json',data);members.to_parquet(PRIVATE/'members.parquet',index=False)
    targets.to_parquet(PRIVATE/'target_orders.parquet',index=False);prior.to_parquet(PRIVATE/'prior_orders.parquet',index=False);labs.to_parquet(PRIVATE/'verified_labs.parquet',index=False)
    report={'status':'complete','protocol_sha256':signature,'flow':flow,'excluded_prior_test_admissions':removed_test,
        'samples':{s:len(v) for s,v in data.items()},'patients':{s:len({c['subject_hash'] for c in v}) for s,v in data.items()},
        'membership_sha256':{s:hash_data([c['case_id'] for c in v]) for s,v in data.items()},'cross_split_patient_overlap':0,'prior_test_patient_overlap':0,
        'cases_with_prior_orders':{s:sum(bool(c['context']['recorded_prior_orders']) for c in v) for s,v in data.items()},
        'cases_with_labs':{s:sum(bool(c['context']['available_labs']) for c in v) for s,v in data.items()},
        'postdecision_input_lab_violations':0,'test_predictions_generated':False,'privacy':'No API calls; restricted artifacts remain local.'}
    save(HERE/'results/data_manifest.json',report);print(json.dumps(report),flush=True);con.close()

if __name__=='__main__':main()
