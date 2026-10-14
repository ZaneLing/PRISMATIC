"""Reexecute frozen rule programs on raw-source test features and regrade outputs."""
import hashlib,json,sys
from pathlib import Path
import joblib,numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;sys.path.insert(0,str(ROOT))
from upgrade_v30.common_test_gate import check
from upgrade_v29.audit import execute,probabilities
from upgrade_v27.audit_controls import reconstruct
from upgrade_v27.evaluation_metrics import score,compare,paired
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted';OUTPUT=PRIVATE/'prismatic-v30/common-test'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(z):return hashlib.sha256(json.dumps(z,sort_keys=True).encode()).hexdigest()
def mean_rows(rows):
    return {k:{'mean':float(np.mean([r[k] for r in rows])),'seed_sd':float(np.std([r[k] for r in rows],ddof=1)) if len(rows)>1 else None} for k in rows[0] if isinstance(rows[0][k],(float,int))}
def main():
    path=HERE/'results/common_test_summary.json';report=json.loads(path.read_text());assert report['status']=='executed_pending_independent_prediction_audit'
    assert report['lock']['gate']==check() and report['lock']['addendum_sha256']==sha(HERE/'common_test_addendum.json')
    assert all(sha(ROOT/p)==h for p,h in report['lock']['sources'].items())
    source=joblib.load(PRIVATE/'prismatic-v27/visits.joblib');manifest=json.loads((ROOT/'upgrade_v27/results/cohort_manifest.json').read_text());assert sha(PRIVATE/'prismatic-v27/visits.joblib')==manifest['bundle_sha256']
    arms={29:json.loads((ROOT/'upgrade_v29/protocol.json').read_text())['arms'],30:['raw_policy','calibrated_policy']+[f'{m}_C{c}P{p}' for m in ('greedy','own','shuffled') for c in (0,1) for p in (0,1)]}
    result={'status':'passed','source_report_sha256':sha(path),'auditor_sha256':sha(Path(__file__)),'panels':{},'new_training':False}
    old=json.loads((ROOT/'upgrade_v27/results/test_summary.json').read_text())
    for panel,panel_report in report['panels'].items():
        b=joblib.load(PRIVATE/f'prismatic-v27/{panel}-models.joblib');meds=b['medications'];x,gold,_,people,_=reconstruct(source['data']['test'],source['vocab'],meds)
        if panel=='molecular':gold=[g&set(meds) for g in gold]
        ids=[v['case_id'] for person in source['data']['test'] for v in person['visits']]
        identity={'case_ids':ids,'people':people.tolist(),'gold':[sorted(g) for g in gold],'medications':meds}
        assert digest(identity)==panel_report['case_identity_sha256']==old['panels'][panel]['case_identity_sha256']
        assert identity==json.loads((OUTPUT/f'{panel}-identity.json').read_text())
        expected={f'v{v}-{arm}-seed{s}-round{r}' for v in (29,30) for arm in arms[v] for s in (42,137,2026) for r in range(1,6)}
        assert set(panel_report['records'])==expected and len(expected)==315
        metrics={};values={};visits={};states={}
        for seed in (42,137,2026):
            for version in (29,30):states[version,seed]=json.loads((ROOT/f'upgrade_v{version}/results/{panel}-seed{seed}.json').read_text())
            assert all(sha(PRIVATE/f'prismatic-v27/{panel}-models.joblib')==states[v,seed]['lock']['bundle_sha256'] for v in (29,30))
            for r in range(1,6):
                src=PRIVATE/f'prismatic-v29/{panel}-seed{seed}/round{r}';fits=json.loads((src/'fits.json').read_text());assert all(sha(src/f)==h for f,h in fits['model_sha256'].items())
                frozen=states[29,seed]['rounds'][r-1];assert fits['model_sha256']==frozen['model_sha256'] and sha(src/'thresholds.npy')==frozen['thresholds_sha256']
                prob=probabilities(joblib.load(src/fits['base_file']),x);thresholds=np.load(src/'thresholds.npy');raw=np.full(len(meds),fits['selection']['threshold'])
                for version in (29,30):
                    memories=json.loads((PRIVATE/f'prismatic-v{version}/{panel}-seed{seed}/round{r}/memories.json').read_text())
                    for arm in arms[version]:
                        name=f'v{version}-{arm}-seed{seed}-round{r}';record=panel_report['records'][name];f=OUTPUT/f'{panel}-{name}.npz';assert sha(f)==record['prediction_sha256']
                        assert digest(memories[arm])==record['memory_sha256'] and record['model_sha256']==fits['model_sha256'][fits['base_file']]
                        z=np.load(f);actual=execute(memories[arm],x,prob,raw if arm=='raw_policy' else thresholds);np.testing.assert_array_equal(actual,z['prediction'])
                        m,a,keys=score(actual,gold,people,meds,b['ddi'],b['ddi_covered_indices']);compare(record['metrics'],m);assert m['strata']==record['metrics']['strata']
                        np.testing.assert_allclose(a,z['patient_scores'],atol=1e-15,rtol=1e-15);assert keys==z['patient_keys'].tolist()
                        vf=[]
                        for p,g in zip(actual,gold):
                            chosen={meds[i] for i in np.flatnonzero(p)};n=len(chosen)+len(g);vf.append(2*len(chosen&g)/n if n else 1.)
                        np.testing.assert_array_equal(vf,z['visit_f1']);metrics[name]=m;values[name]=a;visits[name]=np.array(vf)
                print(json.dumps({'audit_panel':panel,'seed':seed,'round':r,'predictions_reexecuted':len(metrics)}),flush=True)
        for endpoint,z in panel_report['endpoints'].items():
            selected={};chosen_arrays={}
            for version in (29,30):
                for arm in arms[version]:
                    method=f'v{version}-{arm}';names=[]
                    for seed in (42,137,2026):
                        r=states[version,seed]['selections'][arm]['round'] if endpoint=='selected' else 5;names.append(f'v{version}-{arm}-seed{seed}-round{r}')
                    selected[method]=names;assert mean_rows([metrics[n] for n in names])==z['methods'][method];chosen_arrays[method]=np.array([values[n] for n in names])
            assert selected==panel_report['endpoint_prediction_names'][endpoint]
            contrasts={}
            for version,own in [(29,'own_error_program_agent'),(30,'own_C1P1')]:
                for arm in arms[version]:
                    if arm!=own:contrasts[f'v{version}-{own}_minus_{arm}']=paired(chosen_arrays[f'v{version}-{own}'],chosen_arrays[f'v{version}-{arm}'])
            for method in ('greedy','own','shuffled'):
                a,b0,c,d=[chosen_arrays[f'v30-{method}_C{i}P{j}'] for i,j in [(0,0),(0,1),(1,0),(1,1)]]
                contrasts[method+'_compatibility_main']=paired((c+d)/2,(a+b0)/2);contrasts[method+'_confirmation_main']=paired((b0+d)/2,(a+c)/2);contrasts[method+'_interaction']=paired(d-c,b0-a)
            assert contrasts==z['within_program_contrasts']
            if endpoint=='selected':
                old_arrays={}
                for name,row in old['panels'][panel]['results'].items():
                    if row['kind']=='raw_round':continue
                    f=PRIVATE/f'prismatic-v27/evaluation/{panel}-{name}.npz';assert sha(f)==row['prediction_sha256'];saved=np.load(f);assert saved['patient_keys'].tolist()==keys
                    old_arrays.setdefault(name.rsplit('-seed',1)[0],[]).append(saved['patient_scores'])
                expected_contrasts={own:{m:paired(chosen_arrays[own],np.array(a)) for m,a in old_arrays.items()} for own in ('v29-own_error_program_agent','v30-own_C1P1')}
                assert expected_contrasts==z['versus_v27'] and z['v27_methods']==old['panels'][panel]['methods']
        for version in (29,30):
            for arm in arms[version]:
                method=f'v{version}-{arm}'
                for kind in ('raw','accepted'):
                    names=[]
                    for r in range(1,6):
                        group=[]
                        for seed in (42,137,2026):
                            row=states[version,seed]['rounds'][r-1];number=r if kind=='raw' else row['arms'][arm]['best_round'];group.append(f'v{version}-{arm}-seed{seed}-round{number}')
                        names.append(group)
                    assert [mean_rows([metrics[n] for n in group]) for group in names]==panel_report['curves'][method][kind]
                    for i,seed in enumerate((42,137,2026)):
                        counts=[]
                        for r in range(1,5):
                            delta=visits[names[r][i]]-visits[names[r-1][i]];counts.append({'improved':int((delta>1e-12).sum()),'regressed':int((delta< -1e-12).sum()),'unchanged':int((abs(delta)<=1e-12).sum()),'visits':len(delta)})
                        assert counts==panel_report['fix_regress'][method][kind][str(seed)]
        result['panels'][panel]={'visits':len(gold),'patients':len(set(people)),'reexecuted_prediction_sets':len(expected),'binary_prediction_disagreements':0,'all_endpoints_curves_transitions_and_intervals_recounted':True}
    result['scope']='Raw-source identities/features/labels and all program predictions reexecuted using independent conditional-rule logic and original model files; set scorer shared with the established independently implemented v27 evaluation. All selected states, trajectories and paired contrasts recounted. No model refitting; v27 author inference relies on its separate audit.'
    (HERE/'results/common_test_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
