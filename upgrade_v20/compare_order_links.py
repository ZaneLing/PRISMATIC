"""Check whether prescription and pharmacy rows point to the same provider order."""
import json
from pathlib import Path
import duckdb
HERE=Path(__file__).resolve().parent
ROOT=Path.home()/'Desktop/MedTreeBench/dataset/restricted'

def main():
    con=duckdb.connect(str(ROOT/'prismatic-v20/audit.duckdb'));con.execute('SET threads=2');con.execute("SET memory_limit='4GB'")
    con.read_parquet(str(ROOT/'prismatic-v4/mapped_orders.parquet')).create_view('targets')
    existing={r[0] for r in con.execute('SHOW TABLES').fetchall()}
    if 'pharmacy_poe' not in existing:
        con.execute('''CREATE TABLE pharmacy_poe AS SELECT p.pharmacy_id,p.poe_id AS pharmacy_poe_id FROM read_csv(?,all_varchar=true) p
            WHERE p.pharmacy_id IN (SELECT DISTINCT pharmacy_id FROM targets)''',[str(ROOT/'mimiciv/3.1/hosp/pharmacy.csv.gz')])
    keys=['rows','both_links_present','same_poe_id','different_poe_id','prescription_missing_poe','pharmacy_missing_poe']
    values=con.execute('''SELECT COUNT(*),COUNT(*) FILTER(WHERE t.poe_id IS NOT NULL AND f.pharmacy_poe_id IS NOT NULL),
        COUNT(*) FILTER(WHERE t.poe_id=f.pharmacy_poe_id),COUNT(*) FILTER(WHERE t.poe_id<>f.pharmacy_poe_id),
        COUNT(*) FILTER(WHERE t.poe_id IS NULL),COUNT(*) FILTER(WHERE f.pharmacy_poe_id IS NULL)
        FROM targets t LEFT JOIN pharmacy_poe f USING(pharmacy_id)''').fetchone()
    counts=dict(zip(keys,values))
    if 'pharmacy_provider_linked' not in existing:
        con.execute('''CREATE TABLE pharmacy_provider_linked AS SELECT p.poe_id,p.subject_id,p.hadm_id,TRY_CAST(p.ordertime AS TIMESTAMP) AS ordertime,p.transaction_type,p.order_type
            FROM read_csv(?,all_varchar=true) p WHERE p.poe_id IN (SELECT DISTINCT pharmacy_poe_id FROM pharmacy_poe)''',[str(ROOT/'mimiciv/3.1/hosp/poe.csv.gz')])
    con.read_parquet(str(ROOT/'prismatic-v4/cohort.parquet')).create_view('cohort')
    rows=con.execute('''SELECT COUNT(*) AS rows,COUNT(*) FILTER(WHERE p.subject_id=t.subject_id AND p.hadm_id=t.hadm_id) AS exact_identity,
        COUNT(*) FILTER(WHERE p.subject_id=t.subject_id AND p.hadm_id=t.hadm_id AND p.ordertime<c.decision_time) AS provider_before,
        COUNT(*) FILTER(WHERE p.subject_id=t.subject_id AND p.hadm_id=t.hadm_id AND p.ordertime>=c.decision_time AND p.ordertime<c.decision_time+INTERVAL 6 HOUR) AS provider_within,
        COUNT(*) FILTER(WHERE p.subject_id=t.subject_id AND p.hadm_id=t.hadm_id AND p.ordertime>=c.decision_time+INTERVAL 6 HOUR) AS provider_after
        FROM targets t JOIN cohort c USING(subject_id,hadm_id) LEFT JOIN pharmacy_poe f USING(pharmacy_id)
        LEFT JOIN pharmacy_provider_linked p ON f.pharmacy_poe_id=p.poe_id''').fetchdf().to_dict('records')[0]
    report={'status':'complete','prescription_vs_pharmacy_provider_links':counts,'pharmacy_provider_time_path':rows,
        'selection_note':'Audit both source linkage paths before declaring a new prospective cohort; this does not retroactively change old target scores.'}
    (HERE/'results/link_path_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)

if __name__=='__main__':main()
