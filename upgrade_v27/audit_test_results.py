"""Recount all frozen test outputs against raw-source labels and identities."""
import hashlib,json
from pathlib import Path
import joblib,numpy as np
from evaluation_metrics import score,compare,paired
from test_gate import check
HERE=Path(__file__).resolve().parent;PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v27'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()
def main():
    report=json.loads((HERE/'results/test_summary.json').read_text());assert report['status']=='executed_pending_independent_prediction_audit'
    lock=report['lock'];assert check()==lock['gate'] and all(sha(HERE/f)==h for f,h in lock['source_sha256'].items())
    source=joblib.load(PRIVATE/'visits.joblib');out={'status':'passed','source_report_sha256':sha(HERE/'results/test_summary.json'),'panels':{},'test_predictions_recomputed':False}
    for panel,panel_report in report['panels'].items():
        b=joblib.load(PRIVATE/(panel+'-models.joblib'));identity=json.loads((PRIVATE/'evaluation'/(panel+'-case-identity.json')).read_text())
        assert digest(identity)==panel_report['case_identity_sha256'] and identity['medications']==b['medications']
        gold=[];people=[];case_ids=[]
        for person in source['data']['test']:
            for visit in person['visits']:
                truth=set(visit['medications'])
                if panel=='molecular':truth&=set(b['medications'])
                gold.append(truth);people.append(person['subject_hash']);case_ids.append(visit['case_id'])
        assert case_ids==identity['case_ids'] and people==identity['people'] and [sorted(g) for g in gold]==identity['gold']
        expected={'prevalence','last_visit','cosine_knn','structured_logistic'}
        arms=json.loads((HERE/'rsi_addendum.json').read_text())['arms']
        for seed in [42,137,2026]:
            expected.update(f'{method}-seed{seed}' for method in (['ARMR','GAMENet'] if panel=='full' else ['ARMR','GAMENet','SafeDrug']))
            expected.update(f'{arm}-seed{seed}' for arm in arms)
            expected.update(f'{arm}-seed{seed}-round{r}' for arm in arms for r in range(1,6))
            expected.update(f'{name}-seed{seed}' for name in ['own_remove_memory','own_first_memory','own_first_policy'])
        assert set(panel_report['results'])==expected
        values={};grouped={};maximum=0.
        for name,row in panel_report['results'].items():
            path=PRIVATE/'evaluation'/(panel+'-'+name+'.npz');assert sha(path)==row['prediction_sha256'];z=np.load(path)
            metrics,patients,keys=score(z['prediction'],gold,people,b['medications'],b['ddi'],b['ddi_covered_indices']);compare(row['metrics'],metrics)
            assert metrics['strata']==row['metrics']['strata'];np.testing.assert_allclose(patients,z['patient_scores'],atol=1e-15,rtol=1e-15);assert keys==z['patient_keys'].tolist()
            values[name]=patients
            if row['kind']!='raw_round':grouped.setdefault(name.rsplit('-seed',1)[0],[]).append(name)
            maximum=max(maximum,abs(metrics['patient_f1']-row['metrics']['patient_f1']))
        own=np.array([values[f'own_error_rule_agent-seed{s}'] for s in [42,137,2026]])
        for name,names in grouped.items():
            if name!='own_error_rule_agent':assert paired(own,np.array([values[n] for n in names]))==panel_report['own_agent_minus_comparator'][name]
        out['panels'][panel]={'prediction_sets':len(expected),'visits':len(gold),'patients':len(set(people)),'maximum_metric_delta':maximum,'source_identity_label_and_paired_recount':'passed'}
    out['scope']='Rebuild case identities and target sets from the source; verify immutable predictions, independently implemented class-set metrics (also cross-checked against training scorer at execution), strata and paired patient intervals. This audit does not retrain models or independently rerun test inference.'
    (HERE/'results/test_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out),flush=True)
if __name__=='__main__':main()
