"""Train-only vocabulary construction and development coverage; no test vocabulary tuning."""
import json
from pathlib import Path
import duckdb
HERE=Path(__file__).resolve().parent
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v24'

def main():
    con=duckdb.connect(str(PRIVATE/'audit.duckdb'),read_only=True);con.execute('SET threads=1')
    con.execute('''CREATE TEMP VIEW coded AS SELECT *,TRY_CAST(drughiclseqno AS BIGINT) AS hicl,
      NULLIF(LOWER(TRIM(drugname)),'') AS name FROM targets''')
    valid='hicl>0'
    coverage={}
    for split in ['train','proposal','guard','test']:
        vals=con.execute(f'''SELECT COUNT(*),COUNT(*) FILTER(WHERE {valid}),
          COUNT(*) FILTER(WHERE name IS NULL AND {valid}),
          COUNT(*) FILTER(WHERE name IS NOT NULL AND NOT COALESCE({valid},false)),
          COUNT(*) FILTER(WHERE name IS NULL AND NOT COALESCE({valid},false))
          FROM coded WHERE split=?''',[split]).fetchone()
        coverage[split]=dict(zip(['rows','valid_hicl','missing_name_with_hicl','name_only_without_valid_hicl','neither_name_nor_valid_hicl'],vals))
        assert sum(vals[1:2])+vals[3]+vals[4]==vals[0]
    # Count patients/stays rather than repeated rows when defining popular codes.
    con.execute(f'''CREATE TEMP VIEW train_rank AS SELECT hicl,COUNT(DISTINCT patientunitstayid) AS stays,
      ROW_NUMBER() OVER(ORDER BY COUNT(DISTINCT patientunitstayid) DESC,hicl) AS rank
      FROM coded WHERE split='train' AND {valid} GROUP BY hicl''')
    capacities=[]
    for n in [64,128,256,512]:
        values={}
        for split in ['train','proposal','guard']:
            row=con.execute('''SELECT COUNT(*),COUNT(*) FILTER(WHERE r.rank<=?) FROM
              (SELECT DISTINCT patientunitstayid,hicl FROM coded WHERE split=? AND hicl>0) t
              LEFT JOIN train_rank r USING(hicl)''',[n,split]).fetchone()
            values[split]={'coded_stay_drug_pairs':row[0],'covered_pairs':row[1],'coverage':row[1]/row[0] if row[0] else None}
        capacities.append({'top_train_codes':n,'development_coverage':values})
    names=con.execute('''SELECT COUNT(*),COUNT(*) FILTER(WHERE names>1) FROM
      (SELECT hicl,COUNT(DISTINCT name) AS names FROM coded WHERE split='train' AND hicl>0 GROUP BY hicl)''').fetchone()
    result={'status':'complete','row_identity_coverage':coverage,'development_vocabulary_capacity':capacities,
      'train_distinct_hicl':names[0],'train_codes_with_multiple_raw_names':names[1],
      'no_test_vocabulary_capacity_computed':True,'no_prediction_score':True,
      'interpretation':'Native HICL is an available label identity, not an asserted ingredient/RxNorm equivalence. Missing names cannot justify dropping coded orders. A final label/missing-target policy and model budget must be frozen before evaluation.'}
    (HERE/'results/native_code_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)

if __name__=='__main__':main()
