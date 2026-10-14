"""Independently audit saved temporal inputs/targets; publish aggregates only."""
import json,sys,hashlib
from pathlib import Path
import numpy as np,pandas as pd,joblib,duckdb
HERE=Path(__file__).resolve().parent
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v21'
sys.path.insert(0,str(HERE.parent/'upgrade_v7'))
from rx_agent import hash_data,record_order,key,FIELDS

def main():
    data=json.loads((PRIVATE/'cases.json').read_text());members=pd.read_parquet(PRIVATE/'members.parquet')
    targets=pd.read_parquet(PRIVATE/'target_orders.parquet');prior=pd.read_parquet(PRIVATE/'prior_orders.parquet');labs=pd.read_parquet(PRIVATE/'verified_labs.parquet')
    assert len(members)==members.hadm_id.nunique()
    assert len(members)==sum(map(len,data.values()))
    assert not members.subject_id.isna().any()
    end=targets.decision_time+pd.Timedelta(hours=6)
    failures={
      'target_identity':int((~targets.exact_identity).sum()),
      'target_provider_window':int((~((targets.ordertime>=targets.decision_time)&(targets.ordertime<end))).sum()),
      'target_pharmacy_window':int((~((targets.entertime>=targets.decision_time)&(targets.entertime<end))).sum()),
      'target_verification':int((targets.verifiedtime.isna()|(targets.verifiedtime>end)).sum()),
      'target_transaction':int((~targets.transaction_type.isin(['New','Change'])).sum()),
      'target_followup':int((targets.discharge_time<end).sum()),
      'prior_identity':int((~prior.exact_identity).sum()),
      'prior_clock':int(sum((prior[c].isna()|(prior[c]>=prior.decision_time)).sum() for c in ['ordertime','entertime','verifiedtime'])),
      'prior_lookback':int((prior.available_at<prior.decision_time-pd.Timedelta(hours=24)).sum()),
      'lab_clock':int((labs.charttime.isna()|labs.storetime.isna()|(labs.charttime>labs.decision_time)|(labs.storetime>labs.decision_time)).sum()),
      'lab_lookback':int((labs.charttime<labs.decision_time-pd.Timedelta(hours=24)).sum()),
      'nonfinite_lab':int((~np.isfinite(labs.value)).sum())}
    assert not any(failures.values()),failures
    con=duckdb.connect(str(PRIVATE/'cohort.duckdb'),read_only=True)
    con.register('members_check',members[['subject_id','hadm_id']])
    assert con.execute('SELECT COUNT(*) FROM population').fetchone()[0]==201750
    assert con.execute('SELECT COUNT(*)-COUNT(DISTINCT hadm_id) FROM population').fetchone()[0]==0
    assert con.execute('''SELECT COUNT(*) FROM eligibility e JOIN members_check m USING(subject_id,hadm_id)
        WHERE ambiguous_rows>0 OR trusted_rows=0''').fetchone()[0]==0
    con.close()
    # Reconstruct every exposed order tuple directly from the saved source join.
    source={};history={}
    for row in targets.to_dict('records'):
        o=record_order(row);source.setdefault(str(row['hadm_id']),set()).add(key(o,FIELDS))
    for row in prior.to_dict('records'):
        o=record_order(row);history.setdefault(str(row['hadm_id']),set()).add(key(o,FIELDS))
    ids={hash_data(['v21',str(r.hadm_id)]):str(r.hadm_id) for r in members.itertuples()}
    subjects={s:{c['subject_hash'] for c in cases} for s,cases in data.items()}
    for s in subjects:
        for t in subjects:
            if s!=t:assert not subjects[s]&subjects[t]
    for cases in data.values():
        for c in cases:
            h=ids[c['case_id']]
            assert {key(o,FIELDS) for o in c['gold']}==source[h]
            assert {key(o,FIELDS) for o in c['context']['recorded_prior_orders']}<=history.get(h,set())
            assert len(c['context']['recorded_prior_orders'])<=24 and len(c['context']['available_labs'])<=32
            assert set(c['context'])=={'gender','age_decade','hours_since_admission','recorded_prior_orders','available_labs'}
    excluded=set()
    for version,file in [('v6','evaluation_bundle.joblib'),('v7','data.joblib')]:
        old=joblib.load(PRIVATE.parent/f'prismatic-{version}'/file)
        excluded|={hash_data(str(s)) for s in old['parts']['test'].subject_id}
    excluded|={c['subject_hash'] for c in json.loads((PRIVATE.parent/'prismatic-v9/cases.json').read_text())['test']}
    assert not subjects['test']&excluded
    report={'status':'passed','independent_checks':failures,'source_target_rows':len(targets),'source_prior_rows':len(prior),'source_lab_rows':len(labs),
      'all_case_order_reconstructions':'passed','cross_split_patient_overlap':0,'prior_test_patient_overlap':0,
      'test_members':len(data['test']),'test_patients':len(subjects['test']),
      'private_cases_sha256':hashlib.sha256((PRIVATE/'cases.json').read_bytes()).hexdigest(),
      'limits':['Input order availability follows recorded timestamps; released data lack full field-version history.',
      'Only coherent-time, nonempty future-order cases are selected; no claim of general all-admission performance.']}
    (HERE/'results/independent_cohort_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)

if __name__=='__main__':main()
