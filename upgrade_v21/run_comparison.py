"""Run the frozen v7 method family on independently audited v21 temporal data."""
import json,sys,hashlib,os,subprocess,time
from collections import Counter
from pathlib import Path
os.environ.setdefault('OPENBLAS_NUM_THREADS','1');os.environ.setdefault('OMP_NUM_THREADS','1');os.environ.setdefault('VECLIB_MAXIMUM_THREADS','1')
import pandas as pd,joblib
HERE=Path(__file__).resolve().parent;PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v21'
sys.path.insert(0,str(HERE.parent/'upgrade_v7'))
from rx_agent import score,hash_data,OrderMemory
from run_rounds import run as rounds
from run_strong_baselines import run as strong

def text_view(c):
    v=c['context'];out=[f"gender {v['gender']} age_decade {v['age_decade']}"]
    for o in v['recorded_prior_orders']:
        out.append('prior_order '+' '.join(f'{k} {val}' for k,val in o.items() if val is not None))
    for l in v['available_labs']:
        out.append(f"blood_lab {l['name']} value {l['value']:.4g} unit {l['unit']}")
    return ' ; '.join(out)

def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')

def main():
    assert json.loads((HERE/'results/independent_cohort_audit.json').read_text())['status']=='passed'
    protocol=json.loads((HERE/'evaluation_protocol.json').read_text());sig=hash_data(protocol)
    lock=PRIVATE/'evaluation_protocol_lock.json'
    if lock.exists():assert json.loads(lock.read_text())['sha256']==sig
    else:save(lock,{'sha256':sig,'test_predictions_generated':False})
    data=json.loads((PRIVATE/'cases.json').read_text());truth={s:[c['gold'] for c in rows] for s,rows in data.items()}
    counts=Counter(n for row in truth['train'][:8000] for n in {o['drug_name'] for o in row})
    classes=[n for n,count in sorted(counts.items(),key=lambda x:(-x[1],x[0]))[:128]]
    parts={s:pd.DataFrame({'hadm_id':[c['case_id'] for c in rows],'subject_id':[c['subject_hash'] for c in rows]}) for s,rows in data.items()}
    bundle={'parts':parts,'truth':truth,'text':{s:[text_view(c) for c in rows] for s,rows in data.items()},'classes':classes}
    joblib.dump(bundle,PRIVATE/'data.joblib')
    manifest={'status':'running','protocol_sha256':sig,'class_count':len(classes),'class_sha256':hash_data(classes),
      'split_counts':{s:len(v) for s,v in data.items()},'input_function_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
      'reused_method_code_sha256':{n:hashlib.sha256((HERE.parent/'upgrade_v7'/n).read_bytes()).hexdigest() for n in ['rx_agent.py','order_tools.py','run_rounds.py','run_strong_baselines.py']},
      'frozen_before_training':True,'no_test_based_selection':True}
    save(HERE/'results/execution_manifest.json',manifest)
    # Entire suite and selection rules are fixed before the first test score.
    for seed in protocol['seeds']:
        if not (HERE/f'results/round_results_seed_{seed}.json').exists():rounds(seed,HERE,PRIVATE)
        if not (HERE/f'results/strong_results_seed_{seed}.json').exists():strong(seed,HERE,PRIVATE)
    memory=OrderMemory(truth['train']);freq=Counter(n for row in truth['train'] for n in {o['drug_name'] for o in row})
    ranked=sorted(classes,key=lambda n:(-freq[n],n));chosen={};predictions={}
    def predict(method,split,k):
        if method=='prevalence':return [memory.synthesize(ranked[:k],conditional=False) for _ in data[split]]
        output=[]
        for c in data[split]:
            row=[];seen=set()
            for o in c['context']['recorded_prior_orders']:
                n=o['drug_name']
                if n in classes and n not in seen:row.append(o);seen.add(n)
                if len(row)==k:break
            output.append(row)
        return output
    for method in ['prevalence','reuse_prior_orders']:
        options=[(score(predict(method,'proposal',k),truth['proposal'])['promotion_score'],k) for k in [1,3,5,8,12,20]]
        value,k=max(options,key=lambda x:x[0]);chosen[method]={'k':k,'proposal_composite':value}
    save(HERE/'results/simple_control_selection.json',chosen)
    for method,choice in chosen.items():predictions[method]=predict(method,'test',choice['k'])
    joblib.dump(predictions,PRIVATE/'simple_controls.joblib');save(HERE/'results/simple_control_results.json',{n:score(p,truth['test']) for n,p in predictions.items()})
    manifest['status']='complete';save(HERE/'results/execution_manifest.json',manifest)

if __name__=='__main__':main()
