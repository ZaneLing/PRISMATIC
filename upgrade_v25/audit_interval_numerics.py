"""Check the observed floating-matmul warning with integer cluster resampling.

This recount changes no prediction, threshold, model, test membership or interval
definition. It independently reconstructs final-method counts and repeats the
registered 2,000 draws with integer accumulation rather than floating BLAS.
"""
import os
for name in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:
    os.environ.setdefault(name,'1')
import json,math
from pathlib import Path
import joblib
import numpy as np
from data_contract import HERE,PRIVATE,FIELDS,sha,save


def read(path):return json.loads(path.read_text())


def matrix(predictions,truth):
    out=[]
    assert len(predictions)==len(truth)
    for pred,gold in zip(predictions,truth):
        p=set(o['drug_code'] for o in pred);g=set(o['drug_code'] for o in gold)
        pt=set(tuple(o[k] for k in FIELDS) for o in pred if all(o.get(k) is not None for k in FIELDS))
        gt=set(tuple(o[k] for k in FIELDS) for o in gold if all(o.get(k) is not None for k in FIELDS))
        out.append([len(p & g),len(p),len(g),len(pt & gt),len(pt),len(gt)])
    return np.asarray(out,dtype=np.int64)


def endpoints(sums):
    return np.stack([2*sums[...,0]/np.maximum(1,sums[...,1]+sums[...,2]),
                     2*sums[...,3]/np.maximum(1,sums[...,4]+sums[...,5])],axis=-1)


def resample(matrices,groups):
    _,ix=np.unique(groups,return_inverse=True);n=int(ix.max()+1);names=list(matrices);blocks=[]
    for name in names:
        grouped=np.zeros((n,6),dtype=np.int64)
        np.add.at(grouped,ix,matrices[name]);blocks.append(grouped)
    stacked=np.concatenate(blocks,axis=1)
    rng=np.random.default_rng(42)
    weights=np.asarray([np.bincount(rng.integers(0,n,n),minlength=n) for _ in range(2000)],dtype=np.int64)
    assert (weights.sum(axis=1)==n).all() and (stacked>=0).all()
    upper=int(n)*int(stacked.max())
    assert upper<np.iinfo(np.int64).max//2
    sums=(weights@stacked).reshape(2000,len(names),6)
    assert sums.dtype==np.int64 and (sums>=0).all() and (sums<=upper).all()
    values=endpoints(sums)
    assert np.isfinite(values).all() and ((values>=0)&(values<=1)).all()
    return {name:values[:,j,:] for j,name in enumerate(names)},upper


def main():
    np.seterr(all='raise')
    path=HERE/'results/summary.json';summary=read(path);assert summary['status']=='complete'
    manifest=read(HERE/'results/feature_manifest.json');assert sha(PRIVATE/'sealed_evaluation.joblib')==manifest['sealed_evaluation_sha256']
    test=joblib.load(PRIVATE/'sealed_evaluation.joblib');ids=[c['case_id'] for c in test['cases']]
    sources={n:sha(HERE/n) for n in ['results/summary.json','results/feature_manifest.json','results/frozen_before_test.json','protocol.json','audit_results.py','data_contract.py']}
    deltas=[];artifacts={};comparisons=[];nonfinite=[];bounds=[]
    def finite(v,path='summary'):
        if isinstance(v,float) and not math.isfinite(v):nonfinite.append(path)
        elif isinstance(v,dict):
            for k,value in v.items():finite(value,path+'.'+k)
        elif isinstance(v,list):
            for k,value in enumerate(v):finite(value,path+'.'+str(k))
    finite(summary)
    frozen=read(HERE/'results/frozen_before_test.json')
    for seed in read(HERE/'protocol.json')['seeds']:
        name=f'results/test_seed_{seed}.json';report=read(HERE/name);sources[name]=sha(HERE/name)
        selection=f'results/selection_seed_{seed}.json';sources[selection]=sha(HERE/selection)
        assert report['selection_sha256']==sources[selection]==frozen['selections_sha256'][str(seed)]
        predictions_path=PRIVATE/f'seed_{seed}/all_test_predictions.joblib'
        saved=joblib.load(predictions_path);assert saved['case_ids']==ids
        artifacts[f'seed_{seed}/all_test_predictions.joblib']=sha(predictions_path)
        mats={name:matrix(saved['predictions'][name],test['truth']) for name in report['methods']}
        for name,counts in mats.items():
            expected=[report['methods'][name][k] for k in ['drug_micro_f1','core_order_micro_f1']]
            assert np.allclose(endpoints(counts.sum(axis=0)),expected,atol=1e-12,rtol=0)
        for group,field in [('patient','patient_hash'),('hospital','hospital_hash')]:
            boot,bound=resample(mats,[c[field] for c in test['cases']]);bounds.append(bound)
            for contrast,original in summary['paired'][str(seed)].items():
                left,right=contrast.split('__minus__')
                interval=np.quantile(boot[left]-boot[right],[.025,.975],axis=0)
                expected=np.asarray(original[group+'_ci95'])
                delta=float(np.max(np.abs(interval-expected))) if np.isfinite(expected).all() else None
                if delta is not None:deltas.append(delta)
                comparisons.append({'seed':seed,'cluster':group,'contrast':contrast,
                                    'integer_reference_ci95':interval.tolist(),'maximum_absolute_difference':delta})
        print(json.dumps({'seed':seed,'integer_bootstrap_recounted':True}),flush=True)
    assert all(sha(HERE/name)==value for name,value in sources.items())
    passed=not nonfinite and len(comparisons)==36 and len(deltas)==36 and max(deltas)<=1e-12
    result={'status':'passed' if passed else 'failed','trigger':'Floating-matmul runtime warnings in the original audit; numerical cause is not inferred.',
            'source_sha256':sources,'artifact_sha256':artifacts,'script_sha256':sha(Path(__file__)),
            'sealed_bundle_sha256':manifest['sealed_evaluation_sha256'],'nonfinite_original_values':nonfinite,
            'cluster_contrasts_recomputed':len(comparisons),'interval_bounds_recomputed':len(comparisons)*4,
            'bootstrap_draws':2000,'seed':42,'accumulation_dtype':'int64',
            'maximum_integer_accumulation_bound':max(bounds),'maximum_absolute_interval_difference':max(deltas) if deltas else None,
            'comparisons':comparisons,'models_or_choices_changed':False,'original_scores_replaced':False,'api_calls':0}
    save(HERE/'results/interval_numeric_audit.json',result)
    assert passed,'Original intervals failed independent integer accumulation checks'
    print(json.dumps({k:result[k] for k in ['status','cluster_contrasts_recomputed','maximum_absolute_interval_difference']}),flush=True)


if __name__=='__main__':main()
