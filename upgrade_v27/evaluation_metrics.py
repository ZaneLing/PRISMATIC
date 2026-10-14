"""Independent set scoring and patient-paired descriptive uncertainty.

This module does not import training metrics or rule-induction arithmetic.
Targets are sets of class strings, preserving out-of-vocabulary labels.
"""
import math
import numpy as np

def score(prediction, gold, people, medications, ddi=None, covered=()):
    prediction=np.asarray(prediction,dtype=bool)
    assert prediction.shape==(len(gold),len(medications)) and len(people)==len(gold)
    rows=[];buckets={};tp_total=pred_total=gold_total=0;edges=pairs=covered_pairs=0
    covered=set(covered)
    for row,truth,person in zip(prediction,gold,people):
        ix=np.flatnonzero(row);chosen={medications[i] for i in ix};truth=set(truth)
        tp=len(chosen&truth);pn=len(chosen);gn=len(truth)
        f=2*tp/(pn+gn) if pn+gn else 1.;j=tp/len(chosen|truth) if chosen|truth else 1.
        rows.append((f,j,pn,gn));buckets.setdefault(str(person),[]).append((f,j))
        tp_total+=tp;pred_total+=pn;gold_total+=gn
        for a,i in enumerate(ix):
            for k in ix[a+1:]:
                pairs+=1;covered_pairs+=int(i in covered and k in covered)
                if ddi is not None:edges+=int(bool(ddi[i,k]))
    keys=sorted(buckets)
    patient=np.array([[math.fsum(v[c] for v in buckets[k])/len(buckets[k]) for c in (0,1)] for k in keys])
    values=np.array(rows)
    result={'patients':len(keys),'visits':len(gold),
      'patient_f1':math.fsum(patient[:,0])/len(keys),'patient_jaccard':math.fsum(patient[:,1])/len(keys),
      'micro_f1':2*tp_total/max(1,pred_total+gold_total),'micro_precision':tp_total/max(1,pred_total),
      'micro_recall':tp_total/max(1,gold_total),'mean_medications':pred_total/len(gold),
      'empty_prediction_fraction':float(np.mean(values[:,2]==0)),'empty_target_fraction':float(np.mean(values[:,3]==0))}
    if ddi is not None:
        result.update(known_graph_pair_rate_all_predictions=edges/max(1,pairs),
          ddi_source_covered_pair_fraction=covered_pairs/max(1,pairs),known_graph_pair_rate_covered_pairs=edges/max(1,covered_pairs))
    strata={}
    for name,mask in [('zero_target',values[:,3]==0),('nonzero_target',values[:,3]>0)]:
        grouped={}
        for use,pair,person in zip(mask,values,people):
            if use:grouped.setdefault(str(person),[]).append(pair)
        strata[name]={'visits':int(mask.sum()),'patients':len(grouped)}
        if grouped:
            for col,key in [(0,'patient_f1'),(1,'patient_jaccard')]:
                strata[name][key]=math.fsum(math.fsum(v[col] for v in group)/len(group) for group in grouped.values())/len(grouped)
    result['strata']=strata
    return result,patient,keys

def compare(recorded,actual,tolerance=1e-12):
    for key,value in actual.items():
        if key=='strata':continue
        assert key in recorded and abs(value-recorded[key])<tolerance,(key,value,recorded.get(key))

def paired(first,second,draws=4000):
    """Inputs are seed x patient x metric, or patient x metric.

    Average seeds before resampling patients. This interval is conditional on
    observed seeds; it is not a hierarchical seed-uncertainty interval.
    """
    a=np.asarray(first);b=np.asarray(second)
    if a.ndim==3:a=a.mean(0)
    if b.ndim==3:b=b.mean(0)
    delta=a-b;assert delta.ndim==2 and delta.shape[1]==2
    rng=np.random.default_rng(42);indices=rng.integers(0,len(delta),(draws,len(delta)))
    means=delta[indices].mean(1)
    return {key:{'difference':float(delta[:,i].mean()),'patient_ci95':np.quantile(means[:,i],[.025,.975]).tolist()} for i,key in enumerate(['patient_f1','patient_jaccard'])}
