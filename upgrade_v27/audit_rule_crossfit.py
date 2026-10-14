"""Reproduce cross-fitted probabilities from raw visits and independent fits.

Original fold probabilities were saved; original fold model weights were not.
These are explicitly new deterministic reproductions, never relabeled originals.
"""
import argparse,hashlib,json,time,warnings
from pathlib import Path
import joblib,numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.exceptions import ConvergenceWarning
from audit_controls import reconstruct
HERE=Path(__file__).resolve().parent;PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v27'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def integer(s):return int(hashlib.sha256(s.encode()).hexdigest(),16)
def save(p,x):
    tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(x,indent=2)+'\n');tmp.replace(p)
def main(panel,seed):
    folder=PRIVATE/f'{panel}-rsi-seed{seed}';lock=json.loads((folder/'lock.json').read_text())
    assert all(sha(HERE/f)==h for f,h in lock['sources'].items())
    source=joblib.load(PRIVATE/'visits.joblib');b=joblib.load(PRIVATE/(panel+'-models.joblib'));meds=b['medications']
    x,gold,_,people,_=reconstruct(source['data']['train'],source['vocab'],meds)
    y=np.array([[m in g for m in meds] for g in gold],dtype=np.float32)
    ranks=sorted(set(people),key=lambda p:integer(str(seed)+'|order|'+p));folds=np.array([integer(str(seed)+'|fold|'+p)%3 for p in people])
    audit=folder/'crossfit_reproduction';audit.mkdir(exist_ok=True);rows=[]
    for round_number in range(1,6):
        part=folder/f'round{round_number}'
        if not (part/'fits_complete.json').exists():break
        fit=json.loads((part/'fits_complete.json').read_text());ix=np.load(part/'members.npy');selected=set(ranks[:int(np.ceil(len(ranks)*round_number/5))])
        assert np.array_equal(ix,np.flatnonzero(np.isin(people,list(selected))))
        original=np.load(part/'oof.npy');assert np.isfinite(original).all()
        for fold in range(3):
            receipt=audit/f'round{round_number}-fold{fold}.json';model_path=audit/f'round{round_number}-fold{fold}.joblib'
            if receipt.exists():
                row=json.loads(receipt.read_text());assert row['source_oof_sha256']==sha(part/'oof.npy') and row['reproduced_model_sha256']==sha(model_path);rows.append(row);continue
            start=time.perf_counter();train=ix[folds[ix]!=fold];held=np.flatnonzero(folds[ix]==fold)
            assert set(people[train]).isdisjoint(people[ix[held]])
            models=[];prediction=[]
            for j in range(len(meds)):
                target=y[train,j]
                if np.unique(target).size==1:models.append(float(target[0]));prediction.append(np.full(len(held),target[0]));continue
                model=LogisticRegression(C=fit['selection']['C'],solver='liblinear',max_iter=1000,tol=.0001,random_state=42)
                with warnings.catch_warnings():
                    warnings.simplefilter('error',ConvergenceWarning);model.fit(x[train],target)
                models.append(model);prediction.append(model.predict_proba(x[ix[held]])[:,1])
            prob=np.column_stack(prediction);saved=original[held]
            np.testing.assert_allclose(prob,saved,atol=1e-12,rtol=1e-12)
            t=fit['selection']['threshold']
            for boundary in [t-.15,t,t+.15]:assert np.array_equal(prob>=boundary,saved>=boundary)
            joblib.dump(models,model_path)
            row={'round':round_number,'fold':fold,'train_visits':len(train),'held_out_visits':len(held),'patient_overlap':0,
              'source_oof_sha256':sha(part/'oof.npy'),'reproduced_model_sha256':sha(model_path),'max_abs_probability_delta':float(np.max(np.abs(prob-saved))),
              'all_decision_boundaries_identical':True,'seconds':time.perf_counter()-start,'status':'passed'}
            save(receipt,row);rows.append(row);print(json.dumps({'panel':panel,'seed':seed,**row}),flush=True)
    result={'status':'complete' if len(rows)==15 else 'partial','panel':panel,'seed':seed,'folds':rows,
      'scope':'Independent raw-visit feature construction and fresh deterministic model fits reproduce saved cross-fit probabilities. These audit weights are reconstructed, not original fit artifacts. No guard/test inference.'}
    save(HERE/f'results/{panel}-rsi-crossfit-audit-seed{seed}.json',result)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('panel',choices=['full','molecular']);p.add_argument('seed',type=int);a=p.parse_args();main(a.panel,a.seed)
