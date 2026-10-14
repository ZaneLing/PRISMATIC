"""Independently rebuild guard features/predictions from the audited visit source."""
import hashlib,json
from pathlib import Path
import joblib,numpy as np
from scipy import sparse
from sklearn.preprocessing import normalize
HERE=Path(__file__).resolve().parent;PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v27'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def reconstruct(patients,vocab,meds):
    d={s:i for i,s in enumerate(vocab['diagnoses'])};p={s:i for i,s in enumerate(vocab['procedures'])};m={s:i for i,s in enumerate(meds)}
    widths=[len(d)+1,len(p)+1,len(d)+1,len(p)+1,len(m),len(m)]
    offsets=np.r_[0,np.cumsum(widths)];rows=[];cols=[];values=[];gold=[];last=[];people=[];groups=[];row=0
    for group,patient in enumerate(patients):
        for j,visit in enumerate(patient['visits']):
            prior=patient['visits'][:j]
            sets=[{d.get(s,len(d)) for s in visit['diagnoses']},{p.get(s,len(p)) for s in visit['procedures']},
                  {d.get(s,len(d)) for v in prior for s in v['diagnoses']},{p.get(s,len(p)) for v in prior for s in v['procedures']},
                  {m[s] for s in prior[-1]['medications'] if s in m} if prior else set()]
            blocks=[{i:1. for i in b} for b in sets];counts={}
            for v in prior:
                for s in set(v['medications']):
                    if s in m:counts[m[s]]=counts.get(m[s],0)+1
            blocks.append({k:v/len(prior) for k,v in counts.items()})
            for k,block in enumerate(blocks):
                for c,val in block.items():rows.append(row);cols.append(int(offsets[k])+c);values.append(val)
            gold.append(set(visit['medications']));last.append(sets[4]);people.append(patient['subject_hash']);groups.append(group);row+=1
    raw=sparse.csr_matrix((np.asarray(values,dtype=np.float32),(rows,cols)),shape=(row,int(offsets[-1])))
    # Preserve the declared float32 two-stage normalization: algebraically
    # merging its norms changes tie ordering at floating-point boundaries.
    normalized=normalize(sparse.hstack([normalize(raw[:,offsets[k]:offsets[k+1]]) for k in range(6)],format='csr'))
    return normalized,gold,last,np.array(people),np.array(groups)

def main():
    source=joblib.load(PRIVATE/'visits.joblib');manifest=json.loads((HERE/'results/cohort_manifest.json').read_text())
    assert sha(PRIVATE/'visits.joblib')==manifest['bundle_sha256'];result={'status':'passed','test_inference':False,'panels':{}}
    for panel in ['full','molecular']:
        original=json.loads((HERE/f'results/{panel}-controls.json').read_text());assert original['status']=='selection_frozen'
        for file,digest in original['lock']['sources'].items():assert sha(HERE/file)==digest
        path=PRIVATE/(panel+'-models.joblib');assert sha(path)==original['lock']['bundle_sha256'];b=joblib.load(path);meds=b['medications'];mi={x:i for i,x in enumerate(meds)}
        train,tg,_,tp,_=reconstruct(source['data']['train'],source['vocab'],meds)
        x,gold,last,people,groups=reconstruct(source['data']['guard'],source['vocab'],meds)
        targets=np.array([[c in g for c in meds] for g in tg],dtype=np.float32)
        y=np.array([[c in g for c in meds] for g in gold],dtype=bool)
        guard_gold=[g if panel=='full' else g&set(meds) for g in gold]
        folder=PRIVATE/(panel+'-controls');predictions={}
        predictions['prevalence']=np.tile(targets.mean(0),(len(gold),1))
        predictions['last_visit']=np.zeros(y.shape,dtype=np.float32)
        for i,codes in enumerate(last):predictions['last_visit'][i,list(codes)]=1
        k=original['methods']['cosine_knn']['selection']['k'];knn=np.zeros(y.shape,dtype=np.float32)
        for start in range(0,len(gold),128):
            sim=(x[start:start+128]@train.T).toarray()
            for i,row in enumerate(sim):
                row[tp==people[start+i]]=-np.inf
                ix=np.lexsort((np.arange(len(row)),-row))[:k];knn[start+i]=targets[ix].mean(0)
        predictions['cosine_knn']=knn
        models=joblib.load(folder/'logistic.joblib')
        assert all(isinstance(m,float) or m.C==original['methods']['structured_logistic']['selection']['C'] for m in models)
        predictions['structured_logistic']=np.column_stack([np.full(len(gold),m) if isinstance(m,float) else m.predict_proba(x)[:,1] for m in models])
        rows={}
        for name,prob in predictions.items():
            saved=np.load(folder/(name+'-guard.npy'));max_delta=float(np.max(np.abs(saved-prob)))
            np.testing.assert_allclose(saved,prob,atol=2e-6,rtol=2e-5)
            t=original['methods'][name]['selection']['threshold'];assert np.array_equal(saved>=t,prob>=t)
            pred=prob>=t;tp=(pred&y).sum(1);pn=pred.sum(1);gn=np.array([len(g) for g in guard_gold]);den=pn+gn
            f=np.divide(2*tp,den,out=np.ones(len(den)),where=den>0);j=np.divide(tp,den-tp,out=np.ones(len(den)),where=(den-tp)>0)
            means={key:float(np.mean([v[groups==g].mean() for g in np.unique(groups)])) for key,v in [('patient_f1',f),('patient_jaccard',j)]}
            for key,val in means.items():assert abs(val-original['methods'][name]['guard'][key])<1e-12
            rows[name]={'independent_source_features_predictions_and_scores':'passed','probability_max_abs_delta':max_delta,
                        'guard_probabilities_sha256':sha(folder/(name+'-guard.npy')),**means}
        result['panels'][panel]={'patients':len(source['data']['guard']),'visits':len(gold),'methods':rows}
    (HERE/'results/control_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)

if __name__=='__main__':main()
