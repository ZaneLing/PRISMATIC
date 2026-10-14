"""Repeat the frozen static-ensemble configuration; no new hyperparameter search."""
import json,time
import numpy as np
import pandas as pd
import joblib
from sklearn.linear_model import SGDClassifier
from sklearn.multiclass import OneVsRestClassifier
from run_rankers import HERE,ROOT,PRIVATE,take,text_features,top,score

def run():
    start=time.time()
    anchor=joblib.load(PRIVATE/'selected_anchor.joblib')
    selection=json.loads((HERE/'results/ranker_selection.json').read_text())
    protocol={'seeds':[17,42,73],'selection_sha256':__import__('hashlib').sha256((HERE/'results/ranker_selection.json').read_bytes()).hexdigest(),
              'policy':'Freeze seed-42 validation-selected architecture/alphas; report every seed; no test selection'}
    (HERE/'results/seed_protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    frame=pd.read_parquet(ROOT/'prismatic-v4/cohort.parquet')
    parts={s:take(frame,s,40000 if s=='train' else 4000) for s in ['train','test']}
    classes=anchor['classes']; gold=[set(x) for x in parts['test'].atc4_codes]
    y=np.array([[c in row for c in classes] for row in parts['train'].atc4_codes],dtype=np.float32)
    x={v:{s:vec.transform(text_features(p)) for s,p in parts.items()} for v,vec in anchor['vectors'].items()}
    results={}
    for seed in protocol['seeds']:
        if seed==42:pred=top(np.load(PRIVATE/'anchor_test_scores.npy'))
        else:
            probabilities={}
            for view in ['word','char']:
                alpha=float(selection['selected'][view].split('-',1)[1])
                model=OneVsRestClassifier(SGDClassifier(loss='log_loss',alpha=alpha,max_iter=50,tol=1e-3,random_state=seed),n_jobs=1)
                model.fit(x[view]['train'],y)
                probabilities[view]=model.predict_proba(x[view]['test'])
            w=anchor['word_weight'];pred=top(w*probabilities['word']+(1-w)*probabilities['char'])
        results[str(seed)]=score(gold,pred,classes)
        np.save(PRIVATE/f'static_ensemble_seed{seed}.npy',pred)
        print(json.dumps({'seed':seed,'test':results[str(seed)]}),flush=True)
    f=[r['micro_f1_at_5'] for r in results.values()]
    report={'protocol':protocol,'metrics':results,'f1_mean':float(np.mean(f)),'f1_sample_sd':float(np.std(f,ddof=1)),
            'elapsed_seconds':time.time()-start}
    (HERE/'results/seed_robustness.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':run()
