"""Audit historical start-time targets against actual order-entry timestamps."""
import json,time
from pathlib import Path
import duckdb
HERE=Path(__file__).resolve().parent
ROOT=Path.home()/'Desktop/MedTreeBench/dataset/restricted'
PRIVATE=ROOT/'prismatic-v20'

def main():
    PRIVATE.mkdir(exist_ok=True);(HERE/'results').mkdir(exist_ok=True)
    protocol={'purpose':'Resolve the known distinction between intended medication start and provider order authoring.',
        'cohort':'Existing v4 admission/starttime-in-next-6h targets, used only for audit, not a newly filtered performance cohort.',
        'join_keys':['prescriptions.poe_id -> poe.poe_id','prescriptions.pharmacy_id -> pharmacy.pharmacy_id'],
        'identity_checks':['subject_id','hadm_id'],'timestamps':['poe.ordertime','pharmacy.entertime','pharmacy.verifiedtime'],
        'privacy':'All row-level joins remain restricted/local; public outputs are aggregate counts.',
        'sources':['https://mimic.mit.edu/docs/iv/modules/hosp/poe.html','https://mimic.mit.edu/docs/iv/modules/hosp/pharmacy.html','https://mimic.mit.edu/docs/iv/modules/hosp/prescriptions.html']}
    (HERE/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    con=duckdb.connect(str(PRIVATE/'audit.duckdb'));con.execute("SET threads=2");con.execute("SET memory_limit='4GB'");con.execute("SET preserve_insertion_order=false")
    con.read_parquet(str(ROOT/'prismatic-v4/mapped_orders.parquet')).create_view('order_source')
    con.read_parquet(str(ROOT/'prismatic-v4/cohort.parquet')).create_view('cohort_source')
    con.execute('CREATE OR REPLACE TEMP VIEW targets AS SELECT m.*,c.decision_time FROM order_source m JOIN cohort_source c USING(subject_id,hadm_id)')
    existing={r[0] for r in con.execute('SHOW TABLES').fetchall()}
    if 'poe_linked' not in existing:
        con.execute('''CREATE TABLE poe_linked AS SELECT p.poe_id,p.subject_id,p.hadm_id,TRY_CAST(p.ordertime AS TIMESTAMP) AS ordertime,p.order_type,p.transaction_type
            FROM read_csv(?,all_varchar=true) p WHERE p.poe_id IN (SELECT DISTINCT poe_id FROM targets WHERE poe_id IS NOT NULL)''',
            [str(ROOT/'mimiciv/3.1/hosp/poe.csv.gz')]);print('Provider-order join prepared.',flush=True)
    if 'pharmacy_linked' not in existing:
        con.execute('''CREATE TABLE pharmacy_linked AS SELECT p.pharmacy_id,p.subject_id,p.hadm_id,TRY_CAST(p.entertime AS TIMESTAMP) AS entertime,
            TRY_CAST(p.verifiedtime AS TIMESTAMP) AS verifiedtime,p.frequency,p.duration,p.duration_interval,p.basal_rate,p.infusion_type
            FROM read_csv(?,all_varchar=true) p WHERE p.pharmacy_id IN (SELECT DISTINCT pharmacy_id FROM targets WHERE pharmacy_id IS NOT NULL)''',
            [str(ROOT/'mimiciv/3.1/hosp/pharmacy.csv.gz')]);print('Pharmacy-entry join prepared.',flush=True)
    duplicate_poe=con.execute('SELECT COUNT(*)-COUNT(DISTINCT poe_id) FROM poe_linked').fetchone()[0]
    duplicate_pharmacy=con.execute('SELECT COUNT(*)-COUNT(DISTINCT pharmacy_id) FROM pharmacy_linked').fetchone()[0]
    assert duplicate_poe==0 and duplicate_pharmacy==0,'Ambiguous joins need explicit resolution before counting'
    con.execute('''CREATE OR REPLACE TEMP VIEW joined AS SELECT t.*,
        CASE WHEN p.subject_id=t.subject_id AND p.hadm_id=t.hadm_id THEN p.ordertime END AS ordertime,
        p.order_type,p.transaction_type,
        CASE WHEN f.subject_id=t.subject_id AND f.hadm_id=t.hadm_id THEN f.entertime END AS entertime,
        CASE WHEN f.subject_id=t.subject_id AND f.hadm_id=t.hadm_id THEN f.verifiedtime END AS verifiedtime,
        f.frequency AS pharmacy_frequency,f.duration AS pharmacy_duration,f.duration_interval AS pharmacy_duration_unit,f.basal_rate,f.infusion_type,
        CASE WHEN p.poe_id IS NOT NULL THEN p.subject_id<>t.subject_id OR (p.hadm_id IS NOT NULL AND p.hadm_id<>t.hadm_id) ELSE false END AS poe_identity_mismatch,
        CASE WHEN f.pharmacy_id IS NOT NULL THEN f.subject_id<>t.subject_id OR f.hadm_id<>t.hadm_id ELSE false END AS pharmacy_identity_mismatch
        FROM targets t LEFT JOIN poe_linked p ON t.poe_id=p.poe_id LEFT JOIN pharmacy_linked f ON t.pharmacy_id=f.pharmacy_id''')
    columns=['target_rows','admissions','with_ordertime','with_entertime','with_verifiedtime','order_before_admission','order_in_next_6h','order_after_6h',
        'entered_before_admission','entered_in_next_6h','poe_identity_mismatch','pharmacy_identity_mismatch','frequency_present','duration_present','basal_rate_present']
    values=con.execute('''SELECT COUNT(*),COUNT(DISTINCT hadm_id),COUNT(ordertime),COUNT(entertime),COUNT(verifiedtime),
        COUNT(*) FILTER(WHERE ordertime<decision_time),COUNT(*) FILTER(WHERE ordertime>=decision_time AND ordertime<decision_time+INTERVAL 6 HOUR),
        COUNT(*) FILTER(WHERE ordertime>=decision_time+INTERVAL 6 HOUR),COUNT(*) FILTER(WHERE entertime<decision_time),
        COUNT(*) FILTER(WHERE entertime>=decision_time AND entertime<decision_time+INTERVAL 6 HOUR),
        COUNT(*) FILTER(WHERE poe_identity_mismatch),COUNT(*) FILTER(WHERE pharmacy_identity_mismatch),
        COUNT(NULLIF(TRIM(pharmacy_frequency),'')),COUNT(NULLIF(TRIM(pharmacy_duration),'')),COUNT(NULLIF(TRIM(basal_rate),'')) FROM joined''').fetchone()
    counts=dict(zip(columns,values))
    conflicts=con.execute('''SELECT COUNT(*) FILTER(WHERE p.subject_id<>t.subject_id) AS poe_subject_mismatch,
        COUNT(*) FILTER(WHERE p.hadm_id IS NOT NULL AND p.hadm_id<>t.hadm_id) AS poe_admission_mismatch,
        COUNT(*) FILTER(WHERE f.subject_id<>t.subject_id) AS pharmacy_subject_mismatch,
        COUNT(*) FILTER(WHERE f.hadm_id<>t.hadm_id) AS pharmacy_admission_mismatch
        FROM targets t LEFT JOIN poe_linked p ON t.poe_id=p.poe_id LEFT JOIN pharmacy_linked f ON t.pharmacy_id=f.pharmacy_id''').fetchdf().to_dict('records')[0]
    strata=con.execute('''SELECT split,COUNT(*) AS target_rows,COUNT(ordertime) AS with_ordertime,
        COUNT(*) FILTER(WHERE ordertime<decision_time) AS order_before_admission,
        COUNT(*) FILTER(WHERE ordertime>=decision_time AND ordertime<decision_time+INTERVAL 6 HOUR) AS order_in_next_6h FROM joined GROUP BY split ORDER BY split''').fetchdf().to_dict('records')
    lag=con.execute("SELECT quantile_cont(date_diff('second',ordertime,TRY_CAST(starttime AS TIMESTAMP))/3600.0,[0.01,0.5,0.99]) FROM joined WHERE ordertime IS NOT NULL").fetchone()[0]
    con.execute('COPY joined TO ? (FORMAT PARQUET,COMPRESSION ZSTD)',[str(PRIVATE/'entry_time_audit.parquet')])
    report={'status':'complete','counts':counts,'split_counts':strata,'start_minus_order_hours_quantiles_01_50_99':lag,
        'duplicate_link_keys':{'poe':duplicate_poe,'pharmacy':duplicate_pharmacy},'identity_conflict_detail':conflicts,
        'temporal_count_policy':'Only exact subject_id AND hadm_id matches supply timestamps. Conflicting or missing admission links remain unknown, and conflicts are explicitly counted.',
        'interpretation':'Orders scheduled to start after admission may already have been authored before admission. Existing scores remain historical start-window agreement, not proven prospective new-order prediction.',
        'next_protocol':'Build targets from provider ordertime, and inputs only from information recorded by the decision timestamp; do not merely filter old start-window targets, which would miss newly authored orders with different start times.'}
    (HERE/'results/order_entry_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True);con.close()

if __name__=='__main__':main()
