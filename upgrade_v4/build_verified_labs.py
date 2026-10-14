"""Audit and retain only labs with both event and store time before admission."""
from __future__ import annotations
import json,time
from pathlib import Path
import duckdb
from build_protocol_data import ROOT,sha

def run():
    t=time.time();private=ROOT/'prismatic-v4';con=duckdb.connect();con.execute('SET threads=4')
    con.execute('CREATE TEMP TABLE cohort AS SELECT subject_id,hadm_id,decision_time FROM read_parquet(?)',[str(private/'cohort.parquet')])
    con.execute('''CREATE TEMP TABLE items AS SELECT itemid,label FROM read_csv(?,all_varchar=true)
      WHERE fluid='Blood' AND label IN ('Creatinine','Sodium','Potassium','Glucose','Urea Nitrogen')''',
      [str(ROOT/'mimiciv/3.1/hosp/d_labitems.csv.gz')])
    con.execute('''CREATE TEMP TABLE candidate AS SELECT c.subject_id,c.hadm_id,c.decision_time,
      l.labevent_id,i.label,TRY_CAST(l.charttime AS TIMESTAMP) AS charttime,
      TRY_CAST(l.storetime AS TIMESTAMP) AS storetime,TRY_CAST(l.valuenum AS DOUBLE) AS value,l.valueuom
      FROM read_csv(?,all_varchar=true) l JOIN cohort c ON l.subject_id=c.subject_id AND l.hadm_id=c.hadm_id
      JOIN items i ON l.itemid=i.itemid
      WHERE TRY_CAST(l.charttime AS TIMESTAMP) BETWEEN c.decision_time-INTERVAL 24 HOUR AND c.decision_time''',
      [str(ROOT/'mimiciv/3.1/hosp/labevents.csv.gz')])
    audit=con.execute('''SELECT COUNT(*) AS event_time_eligible_rows,
      COUNT(*) FILTER(WHERE storetime>decision_time) AS stored_after_decision,
      COUNT(*) FILTER(WHERE storetime IS NULL) AS missing_storetime,
      COUNT(*) FILTER(WHERE storetime<=decision_time AND value IS NOT NULL) AS eligible_numeric_rows,
      COUNT(DISTINCT hadm_id) FILTER(WHERE storetime<=decision_time AND value IS NOT NULL) AS admissions_with_verified_lab
      FROM candidate''').fetchdf().iloc[0]
    con.execute('''CREATE TEMP TABLE latest AS SELECT * FROM candidate
      WHERE storetime<=decision_time AND value IS NOT NULL
      QUALIFY ROW_NUMBER() OVER(PARTITION BY hadm_id,label ORDER BY charttime DESC,storetime DESC,labevent_id DESC)=1''')
    con.execute('COPY latest TO ? (FORMAT PARQUET,COMPRESSION ZSTD)',[str(private/'verified_labs.parquet')])
    by_item=con.execute('SELECT label,COUNT(*) AS admissions FROM latest GROUP BY label ORDER BY label').fetchdf().to_dict('records')
    violations=con.execute('SELECT COUNT(*) FROM latest WHERE storetime>decision_time OR charttime>decision_time OR storetime IS NULL').fetchone()[0]
    assert violations==0
    r={'run_id':'P01b-verified-labs-v1','protocol':'same-hadm blood labs within 24h before admission; both timestamps<=decision; latest per label',
      'counts':{k:int(v) for k,v in audit.items()},'latest_by_label':by_item,'postfilter_violations':violations,
      'output_sha256':sha(private/'verified_labs.parquet'),'elapsed_seconds':round(time.time()-t,2),
      'limitations':['Labs with null hadm_id are excluded even if potentially from the same ED visit.',
        'Storetime is the available database proxy for recorded availability, not proof of clinician viewing.',
        'These labs are not inputs to E01-v4 baselines or the registered 50-case LLM comparison.',
        'Creatinine alone is not a validated renal-adjustment recommendation.']}
    con.close();(Path(__file__).parent/'results/verified_labs_audit.json').write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps(r,indent=2))

if __name__=='__main__':run()
