"""Recalculate saved predictions without using the experiment scoring function."""
import hashlib,json,sys
from pathlib import Path
import joblib
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v6'

def counts(pred,gold):
    fields=('drug_name','route','dose_value','dose_unit')
    def core(rows):
        return {tuple(o.get(f) for f in fields) for o in rows if all(o.get(f) is not None for f in fields)}
    p={o['drug_name'] for o in pred};g={o['drug_name'] for o in gold}
    a,b=core(pred),core(gold)
    return [len(p&g),len(p),len(g),len(a&b),len(a),len(b)]

def f1(c):
    return np.array([2*c[0]/max(1,c[1]+c[2]),2*c[3]/max(1,c[4]+c[5])])

def verify(pred,gold,reported):
    assert len(pred)==len(gold)
    matrix=np.array([counts(p,g) for p,g in zip(pred,gold)])
    assert np.allclose(f1(matrix.sum(0)),[reported['drug_micro_f1'],reported['core_order_micro_f1']],rtol=0,atol=1e-12)
    return matrix

def run():
    b=joblib.load(PRIVATE/'evaluation_bundle.joblib')
    e=json.loads((HERE/'results/order_evolution_results.json').read_text())
    r=json.loads((HERE/'results/error_replay_results.json').read_text())
    a=json.loads((HERE/'results/local_agent_results.json').read_text())
    matrices={}
    for row in e['growth']:
        n=row['training_cases'];matrices[n]=verify(b['predictions'][n],b['truth']['test'],row['test'])
    final=verify(joblib.load(PRIVATE/'r2_test_predictions.joblib'),b['truth']['test'],r['test'])
    patients={s:set(p.subject_id) for s,p in b['parts'].items()}
    assert not (patients['train']&patients['val'] or patients['train']&patients['test'] or patients['val']&patients['test'])
    for split in ['val','test']:
        inputs=[json.loads(x) for x in (PRIVATE/f'{split}_inputs.jsonl').read_text().splitlines()]
        labels=[json.loads(x)['orders'] for x in (PRIVATE/f'{split}_labels.jsonl').read_text().splitlines()]
        rows={x['case_id']:x for x in map(json.loads,(PRIVATE/f'{split}_agent_trace.jsonl').read_text().splitlines())}
        for arm in ['catalogue_planner','experience_planner','learned_policy']:
            verify([rows[c['case_id']]['arms'][arm]['orders'] for c in inputs],labels,a[split]['metrics'][arm])
    # Patient-cluster paired bootstrap: admissions from the same patient stay together.
    _,idx=np.unique(b['parts']['test'].subject_id.to_numpy(),return_inverse=True)
    n=int(idx.max()+1);initial=np.zeros((n,6));current=np.zeros((n,6))
    np.add.at(initial,idx,matrices[8000]);np.add.at(current,idx,final)
    rng=np.random.default_rng(42);diff=[]
    for _ in range(2000):
        sample=rng.integers(0,n,n)
        diff.append(f1(current[sample].sum(0))-f1(initial[sample].sum(0)))
    bounds=np.quantile(diff,[.025,.975],axis=0)
    report={'independent_set_count_verification':'passed',
        'verified_growth_checkpoints':[8000,16000,32000,40000],
        'verified_r2_test_cases':len(final),'verified_llm_cases_per_split':20,
        'patient_split_disjoint':True,'test_patients':n,
        'paired_patient_bootstrap':{'replicates':2000,'seed':42,'comparison':'r2 selected versus initial 8k',
          'drug_f1_difference':float(f1(final.sum(0))[0]-f1(matrices[8000].sum(0))[0]),
          'drug_f1_difference_ci95':bounds[:,0].tolist(),
          'core_f1_difference':float(f1(final.sum(0))[1]-f1(matrices[8000].sum(0))[1]),
          'core_f1_difference_ci95':bounds[:,1].tolist(),
          'interpretation':'Developmental data-growth comparison; not a unique mechanism effect or external-baseline superiority.'}}
    (HERE/'results/verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':run()
