"""Fit all conventional controls and freeze development choices; no testing."""
import copy, hashlib, json, time, warnings
from pathlib import Path
import joblib, numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from control_features import features, neighbor_probabilities
from method_runtime import flatten, truths, select, metrics
HERE=Path(__file__).resolve().parent
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v27'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
    tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(x,indent=2)+'\n');tmp.replace(p)
def logistic_probabilities(models, x):
    return np.column_stack([np.full(x.shape[0], m, dtype=np.float32) if isinstance(m,float) else m.predict_proba(x)[:,1] for m in models])
def main():
    resources=json.loads((HERE/'results/model_resource_manifest.json').read_text())
    for panel in ['full','molecular']:
        folder=PRIVATE/f'{panel}-controls';folder.mkdir(exist_ok=True)
        out=HERE/f'results/{panel}-controls.json'
        bundle_path=PRIVATE/(panel+'-models.joblib');assert sha(bundle_path)==resources['panels'][panel]['bundle_sha256']
        lock={'bundle_sha256':sha(bundle_path),'sources':{f:sha(HERE/f) for f in ['train_controls.py','control_features.py','method_runtime.py']},
              'training_addendum_sha256':sha(HERE/'training_addendum.json'),'implementation_notes_sha256':sha(HERE/'implementation_notes.json')}
        if out.exists():
            old=json.loads(out.read_text());assert old['lock']==lock
            if old['status']=='selection_frozen':continue
        b=joblib.load(bundle_path);parts={s:flatten(b['data'][s]) for s in ['train','proposal','guard']}
        target=truths(parts['train'],b['medications']);start=time.perf_counter()
        x={s:features(c,b['sizes']) for s,c in parts.items()}
        # Verify current-target masking on actual training input without printing it.
        mutated=copy.deepcopy(parts['train'][0]);mutated['source'][mutated['visit']]['codes'][2]=list(range(b['sizes'][2]))
        assert (features([mutated],b['sizes'])!=x['train'][:1]).nnz==0
        results={};report={'status':'training','lock':lock,'methods':results,'test_inference':False,'current_target_masking':'passed','feature_seconds':time.perf_counter()-start}
        save(out,report)
        def freeze(name, choice, guard, seconds, config):
            np.save(folder/(name+'-guard.npy'),guard)
            results[name]={'selection':choice,'guard':metrics(guard,parts['guard'],b,choice['threshold']),'seconds':seconds,'configuration':config}
            save(out,report);print(json.dumps({'panel':panel,'method':name,**results[name]}),flush=True)
        prevalence=target.mean(0)
        choice=select(np.repeat(prevalence[None,:],len(parts['proposal']),axis=0),parts['proposal'],b)
        freeze('prevalence',choice,np.repeat(prevalence[None,:],len(parts['guard']),axis=0),0.,{})
        joblib.dump(prevalence,folder/'prevalence.joblib')
        def last(cases):
            values=np.zeros((len(cases),b['sizes'][2]),dtype=np.float32)
            for i,c in enumerate(cases):
                if c['visit']>0:values[i,c['source'][c['visit']-1]['codes'][2]]=1
            return values
        choice=select(last(parts['proposal']),parts['proposal'],b)
        freeze('last_visit',choice,last(parts['guard']),0.,{})
        start=time.perf_counter()
        options=neighbor_probabilities(x['proposal'],x['train'],parts['proposal'],parts['train'],target)
        choices=[{'k':k,**select(prob,parts['proposal'],b)} for k,prob in options.items()]
        chosen=max(choices,key=lambda z:z['metrics']['patient_jaccard']);k=chosen['k']
        guard=neighbor_probabilities(x['guard'],x['train'],parts['guard'],parts['train'],target,ks=(k,))[k]
        freeze('cosine_knn',chosen,guard,time.perf_counter()-start,{'trials':choices})
        trials=[];best=-1;selected=None;selected_model=None;start=time.perf_counter()
        for c in [.1,1.,10.]:
            models=[];iterations=[]
            for label in range(target.shape[1]):
                y=target[:,label]
                if y.min()==y.max():models.append(float(y.mean()));iterations.append(0);continue
                model=LogisticRegression(C=c,solver='liblinear',max_iter=1000,tol=.0001,random_state=42)
                with warnings.catch_warnings():
                    warnings.simplefilter('error',ConvergenceWarning);model.fit(x['train'],y)
                models.append(model);iterations.append(int(model.n_iter_.max()))
                if (label+1)%50==0:print(json.dumps({'panel':panel,'C':c,'classes_fit':label+1}),flush=True)
            choice={'C':c,**select(logistic_probabilities(models,x['proposal']),parts['proposal'],b),'max_class_iterations':max(iterations)}
            trials.append(choice)
            if choice['metrics']['patient_jaccard']>best:
                best=choice['metrics']['patient_jaccard'];selected=choice;selected_model=models
            save(folder/'logistic_trials.json',trials)
        guard=logistic_probabilities(selected_model,x['guard'])
        freeze('structured_logistic',selected,guard,time.perf_counter()-start,{'trials':trials,'convergence_warnings':0})
        joblib.dump(selected_model,folder/'logistic.joblib')
        report['status']='selection_frozen';save(out,report)

if __name__=='__main__':main()
