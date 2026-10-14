"""Build v4 development labels with a 40k-only fallback mapper; audit orders.

All row-level derivatives remain under the restricted root. No clinical-purpose,
infusion-rate or indication label is inferred from a medication name.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
import duckdb
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'upgrade_v3'))
from build_atc4_cohort import ndc11, ROOT
from run_atc4_methods import take

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()

def run(root, public_map, out):
    started = time.time()
    out.mkdir(parents=True, exist_ok=True)
    source = root/'prismatic-v3/cohort_atc4_6h.parquet'
    frame = pd.read_parquet(source)
    train = take(frame, 'train', 40000)[['hadm_id']]
    rawmap = pd.read_csv(public_map, dtype=str, usecols=['NDC','ATC4'])
    rawmap['ndc11'] = rawmap.NDC.map(ndc11)
    rawmap = rawmap.dropna(subset=['ndc11','ATC4'])
    rawmap = rawmap[rawmap.ATC4.str.fullmatch(r'[A-Z][0-9]{2}[A-Z]{2}')]
    counts = rawmap.groupby('ndc11').ATC4.nunique()
    public = rawmap[rawmap.ndc11.isin(counts[counts.eq(1)].index)].drop_duplicates('ndc11')[['ndc11','ATC4']]
    con = duckdb.connect()
    con.execute('SET threads=4')
    con.register('frame',frame); con.register('train_sample',train); con.register('public_map',public)
    con.execute('''CREATE TEMP TABLE raw AS
      SELECT b.subject_id,b.hadm_id,b.split,p.* EXCLUDE(subject_id,hadm_id),
        CASE WHEN t.hadm_id IS NOT NULL THEN true ELSE false END AS mapping_train
      FROM read_csv(?,all_varchar=true) p JOIN frame b
        ON p.hadm_id=b.hadm_id AND p.subject_id=b.subject_id
      LEFT JOIN train_sample t ON b.hadm_id=t.hadm_id
      WHERE TRY_CAST(p.starttime AS TIMESTAMP)>=b.decision_time
        AND TRY_CAST(p.starttime AS TIMESTAMP)<b.decision_time+INTERVAL 6 HOUR''',
      [str(root/'mimiciv/3.1/hosp/prescriptions.csv.gz')])
    ndcs=con.execute('SELECT DISTINCT ndc FROM raw').fetchdf()
    ndcs['normalized']=ndcs.ndc.map(ndc11)
    con.register('ndcs',ndcs)
    con.execute('''CREATE TEMP TABLE direct AS SELECT r.*,TRIM(r.gsn) AS gsn_key,
      LOWER(TRIM(r.drug)) AS drug_key,m.ATC4 AS direct_atc4
      FROM raw r LEFT JOIN ndcs n ON r.ndc=n.ndc
      LEFT JOIN public_map m ON n.normalized=m.ndc11''')
    for key in ['gsn','drug']:
        con.execute(f'''CREATE TEMP TABLE {key}_map AS
          WITH counts AS (SELECT {key}_key, direct_atc4 AS atc4,COUNT(*) AS n
            FROM direct WHERE mapping_train AND direct_atc4 IS NOT NULL
              AND {key}_key IS NOT NULL AND {key}_key<>'' GROUP BY 1,2),
          ranked AS (SELECT *,SUM(n) OVER(PARTITION BY {key}_key) AS total,
            ROW_NUMBER() OVER(PARTITION BY {key}_key ORDER BY n DESC,atc4) AS rk FROM counts)
          SELECT {key}_key,atc4,total,n*1.0/total AS purity FROM ranked
            WHERE rk=1 AND total>=10 AND n*1.0/total>=0.98''')
    con.execute('''CREATE TEMP TABLE mapped AS SELECT d.*,
      COALESCE(d.direct_atc4,g.atc4,n.atc4) AS atc4,
      CASE WHEN d.direct_atc4 IS NOT NULL THEN 'public_ndc'
        WHEN g.atc4 IS NOT NULL THEN 'train40k_gsn'
        WHEN n.atc4 IS NOT NULL THEN 'train40k_name' ELSE 'unmapped' END AS map_source
      FROM direct d LEFT JOIN gsn_map g USING(gsn_key) LEFT JOIN drug_map n USING(drug_key)''')
    con.execute('COPY mapped TO ? (FORMAT PARQUET,COMPRESSION ZSTD)',[str(out/'mapped_orders.parquet')])
    con.execute('''COPY (SELECT b.* EXCLUDE(atc4_codes),
      COALESCE(l.codes,[]::VARCHAR[]) AS atc4_codes,COALESCE(l.raw_orders,0) AS raw_orders,
      COALESCE(l.mapped_orders,0) AS mapped_orders FROM frame b LEFT JOIN (
        SELECT hadm_id,LIST_SORT(LIST_DISTINCT(LIST(atc4) FILTER(WHERE atc4 IS NOT NULL))) AS codes,
          COUNT(*) AS raw_orders,COUNT(atc4) AS mapped_orders FROM mapped GROUP BY hadm_id
      ) l USING(hadm_id)) TO ? (FORMAT PARQUET,COMPRESSION ZSTD)''',[str(out/'cohort.parquet')])
    con.execute('COPY (SELECT * FROM gsn_map) TO ? (FORMAT PARQUET)',[str(out/'gsn_map.parquet')])
    con.execute('COPY (SELECT * FROM drug_map) TO ? (FORMAT PARQUET)',[str(out/'drug_map.parquet')])
    route=con.execute('''SELECT COALESCE(NULLIF(TRIM(route),''),'UNKNOWN') AS route,
        COUNT(*) AS orders,COUNT(atc4) AS mapped FROM mapped GROUP BY 1''').fetchdf()
    rare=route.orders<100
    rows=route[~rare].to_dict('records')
    if rare.any(): rows.append({'route':'OTHER_SMALL_GROUPS','orders':int(route.loc[rare,'orders'].sum()),'mapped':int(route.loc[rare,'mapped'].sum())})
    rows=sorted(rows,key=lambda x:-x['orders'])
    for r in rows:r['mapped_fraction']=round(r['mapped']/r['orders'],6)
    fluid=con.execute('''SELECT COUNT(*) AS rows,COUNT(atc4) AS mapped,
       COUNT(*) FILTER(WHERE TRY_CAST(dose_val_rx AS DOUBLE) IS NOT NULL) AS numeric_dose,
       COUNT(*) FILTER(WHERE LOWER(TRIM(dose_unit_rx))='ml') AS dose_unit_ml,
       COUNT(*) FILTER(WHERE LOWER(drug) LIKE '%flush%') AS name_contains_flush
       FROM mapped WHERE REGEXP_MATCHES(LOWER(drug),'saline|sodium chloride|(^|[^a-z])nacl([^a-z]|$)|(^|[^a-z])ns([^a-z]|$)')''').fetchdf().iloc[0]
    completeness=con.execute('''SELECT COUNT(*) AS raw_orders,COUNT(atc4) AS mapped,
      COUNT(*) FILTER(WHERE NULLIF(TRIM(route),'') IS NOT NULL) AS route_present,
      COUNT(*) FILTER(WHERE NULLIF(TRIM(dose_val_rx),'') IS NOT NULL) AS dose_string_present,
      COUNT(*) FILTER(WHERE TRY_CAST(dose_val_rx AS DOUBLE) IS NOT NULL) AS scalar_numeric_dose,
      COUNT(*) FILTER(WHERE NULLIF(TRIM(dose_unit_rx),'') IS NOT NULL) AS dose_unit_present,
      COUNT(*) FILTER(WHERE TRY_CAST(doses_per_24_hrs AS DOUBLE) IS NOT NULL) AS numeric_doses_per_24h
      FROM mapped''').fetchdf().iloc[0]
    split_counts=con.execute('''SELECT split,COUNT(*) AS orders,COUNT(direct_atc4) AS public_mapped,
        COUNT(atc4) AS mapped FROM mapped GROUP BY split ORDER BY split''').fetchdf().to_dict('records')
    con.close()
    report={'run_id':'P02-map-train40k-v1','source_cohort_sha256':sha(source),
      'public_map_sha256':sha(public_map),'output_cohort_sha256':sha(out/'cohort.parquet'),
      'mapping_training_admissions':len(train),'fallback_minimum_support':10,'fallback_purity':0.98,
      'raw_ndc_normalized':True,'mapping_by_split':split_counts,'route_coverage':rows,
      'order_field_counts':{k:int(v) for k,v in completeness.items()},
      'saline_name_proxy':{k:int(v) for k,v in fluid.items()},
      'missing_from_prescriptions_schema':['indication','fluid_purpose','infusion_rate','weight','renal_adjustment_rationale'],
      'limits':['Saline name matching is an audit proxy, not an indication or fluid-purpose label.',
        'The raw prescription dose can be a range/text; scalar parsing does not preserve all valid doses.',
        'ATC-L4 classes are not ingredient-level RxNorm identifiers.',
        'The 40k mapping pool is fixed for this comparison, not valid for smaller case-growth checkpoints.'],
      'elapsed_seconds':round(time.time()-started,2)}
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--restricted',type=Path,default=ROOT)
    p.add_argument('--public-map',type=Path,default=Path('/tmp/prismatic-safedrug/data/input/RXCUI2atc4.csv'))
    p.add_argument('--private-out',type=Path,default=ROOT/'prismatic-v4')
    a=p.parse_args(); r=run(a.restricted,a.public_map,a.private_out)
    path=Path(__file__).parent/'results/mapping_protocol_audit.json'
    path.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
