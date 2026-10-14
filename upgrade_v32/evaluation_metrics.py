"""Scoring and paired patient resampling for the fixed-template repair pilot."""
import sys
from collections import defaultdict
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'upgrade_v7'))
from rx_agent import score
CORE=('drug_name','route','dose_value','dose_unit')

def outputs(probabilities,cases,threshold):
    p=np.asarray(probabilities);assert p.shape==(len(cases),20) and np.isfinite(p).all() and ((p>=0)&(p<=1)).all()
    return [[order for order,value in zip(c['catalogue'].values(),p) if value>=threshold] for p,c in zip(probabilities,cases)]
def direct(cases,n):
    return [[order for order,rank in zip(c['catalogue'].values(),c['original_rank_by_position']) if rank<=n] for c in cases]
def auc(y,p):
    y=np.asarray(y,dtype=bool);p=np.asarray(p);n=int(y.sum());m=len(y)-n
    if not n or not m:return None
    order=np.argsort(p,kind='stable');ranks=np.empty(len(p),dtype=float);lo=0
    while lo<len(p):
        hi=lo+1
        while hi<len(p) and p[order[hi]]==p[order[lo]]:hi+=1
        ranks[order[lo:hi]]=(lo+1+hi)/2;lo=hi
    return float((ranks[y].sum()-n*(n+1)/2)/(n*m))
def probability_metrics(p,cases):
    y=np.asarray([c['target_mask'] for c in cases]).reshape(-1);p=np.asarray(p,dtype=float).reshape(-1);q=np.clip(p,1e-12,1-1e-12)
    return {'conditional_binary_bce':float(-(y*np.log(q)+(1-y)*np.log1p(-q)).mean()),'binary_auroc':auc(y,p),'brier':float(np.mean((p-y)**2)),'positive_slots':int(y.sum()),'total_slots':len(y),'mean_probability_one':float(p.mean()),'fraction_at_or_above_half':float((p>=.5).mean())}
def evidence(pred,cases):
    assert len(pred)==len(cases) and cases
    counts=[];values=[];people=[]
    for orders,c in zip(pred,cases):
        p={o['drug_name'] for o in orders};g={o['drug_name'] for o in c['gold']};pc={tuple(o.get(k) for k in CORE) for o in orders if all(o.get(k) is not None for k in CORE)};gc={tuple(o.get(k) for k in CORE) for o in c['gold'] if all(o.get(k) is not None for k in CORE)}
        counts.append([len(p&g),len(p),len(g),len(pc&gc),len(pc),len(gc)]);values.append([2*len(p&g)/(len(p)+len(g)) if p or g else 1.,2*len(pc&gc)/(len(pc)+len(gc)) if pc or gc else 1.]);people.append(c['subject_hash'])
    counts=np.asarray(counts,dtype=float);values=np.asarray(values,dtype=float);keys=sorted(set(people));index=np.asarray([keys.index(k) for k in people]);cluster_counts=np.zeros((len(keys),6));cluster_values=np.zeros((len(keys),2))
    for i in range(len(keys)):cluster_counts[i]=counts[index==i].sum(axis=0);cluster_values[i]=values[index==i].mean(axis=0)
    metrics=score(pred,[c['gold'] for c in cases]);metrics.update(patients=len(keys),patient_drug_f1=float(cluster_values[:,0].mean()),patient_order_f1=float(cluster_values[:,1].mean()),compiler_schema_failures=0)
    return metrics,{'case_counts':counts,'case_values':values,'patient_counts':cluster_counts,'patient_values':cluster_values,'patient_keys':keys}
def compile_metrics(p,cases,threshold):return evidence(outputs(p,cases,threshold),cases)
def micro(counts):
    return np.stack([2*counts[...,0]/np.maximum(1,counts[...,1]+counts[...,2]),2*counts[...,3]/np.maximum(1,counts[...,4]+counts[...,5])],axis=-1)
def contrast(parts,draws=4000):
    # parts = [(coefficient,evidence), ...], supporting factorial interactions.
    keys=parts[0][1]['patient_keys'];assert all(e['patient_keys']==keys for _,e in parts)
    rng=np.random.default_rng(32032);sample=rng.integers(0,len(keys),(draws,len(keys)));delta_micro=np.zeros((draws,2));delta_patient=np.zeros((draws,2));observed_micro=np.zeros(2);observed_patient=np.zeros(2);case_delta=np.zeros_like(parts[0][1]['case_values'])
    for weight,e in parts:
        delta_micro+=weight*micro(e['patient_counts'][sample].sum(axis=1));delta_patient+=weight*e['patient_values'][sample].mean(axis=1);observed_micro+=weight*micro(e['patient_counts'].sum(axis=0));observed_patient+=weight*e['patient_values'].mean(axis=0);case_delta+=weight*e['case_values']
    return {name:{'micro_f1_difference':float(observed_micro[j]),'micro_f1_patient_ci95':np.quantile(delta_micro[:,j],[.025,.975]).tolist(),'patient_f1_difference':float(observed_patient[j]),'patient_f1_ci95':np.quantile(delta_patient[:,j],[.025,.975]).tolist(),'positive_admission_contrast':int((case_delta[:,j]>1e-12).sum()),'negative_admission_contrast':int((case_delta[:,j]<-1e-12).sum()),'zero_admission_contrast':int((abs(case_delta[:,j])<=1e-12).sum()),'patients':len(keys),'admission_count_interpretation':'F1 fixes/regressions for two-state contrasts; algebraic interaction signs for four-state contrasts'} for j,name in enumerate(['drug','core_order'])}
def invariance(first,second):
    assert len(first)==len(second);agreements=[];jaccard=[];nonempty=[]
    for x,y in zip(first,second):
        a={o['drug_name'] for o in x};b={o['drug_name'] for o in y};agreements.append(a==b);v=len(a&b)/len(a|b) if a or b else 1.;jaccard.append(v)
        if a or b:nonempty.append(v)
    return {'cases':len(first),'drug_set_agreement':float(np.mean(agreements)),'mean_jaccard':float(np.mean(jaccard)),'nonempty_union_cases':len(nonempty),'nonempty_union_mean_jaccard':float(np.mean(nonempty)) if nonempty else None}
