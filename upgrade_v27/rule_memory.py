"""Constrained, auditable rule memory; labels are never inputs to apply()."""
import hashlib,json
import numpy as np

def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()
def patient_weights(groups):
    _,ix,counts=np.unique(groups,return_inverse=True,return_counts=True)
    return 1./(len(counts)*counts[ix])
def agreement(pred,target,groups,gold_counts=None):
    tp=(pred&target.astype(bool)).sum(1);pn=pred.sum(1);gn=target.sum(1) if gold_counts is None else gold_counts
    f=np.divide(2*tp,pn+gn,out=np.ones(len(tp)),where=(pn+gn)>0)
    j=np.divide(tp,pn+gn-tp,out=np.ones(len(tp)),where=(pn+gn-tp)>0)
    weights=patient_weights(groups)
    return {'patient_f1':float(f@weights),'patient_jaccard':float(j@weights)}

def applies(rule,x,prob,threshold):
    feature=np.asarray(x[:,rule['feature_index']].toarray()).ravel()>0
    p=prob[:,rule['drug_index']]
    # The band follows the shared current policy threshold; no target is read.
    if rule['action']=='include':return feature&(p>=threshold-.15)&(p<threshold)
    return feature&(p>=threshold)&(p<=threshold+.15)

def apply(memory,x,prob,threshold):
    pred=prob>=threshold
    for rule in memory:
        mask=applies(rule,x,prob,threshold)
        pred[mask,rule['drug_index']]=rule['action']=='include'
    return pred

def feature_labels(vocab,medications):
    groups=[('current_diagnosis',vocab['diagnoses']+['UNKNOWN']),('current_procedure',vocab['procedures']+['UNKNOWN']),
            ('prior_diagnosis',vocab['diagnoses']+['UNKNOWN']),('prior_procedure',vocab['procedures']+['UNKNOWN']),
            ('last_visit_medication',medications),('prior_medication_history',medications)]
    return [kind+':'+code for kind,items in groups for code in items]

def induce(memory,x,prob,target,groups,threshold,feature_names,drug_names):
    """Rank additions using only the induction partition, never witness labels."""
    pred=apply(memory,x,prob,threshold);target=target.astype(bool)
    weights=patient_weights(groups);tp=(pred&target).sum(1);pn=pred.sum(1);gn=target.sum(1);union=pn+gn-tp
    old=np.divide(tp,union,out=np.ones(len(tp)),where=union>0)
    freq=np.asarray((x>0).sum(0)).ravel();fi=np.lexsort((np.arange(len(freq)),-freq))[:128]
    candidates=[];existing={r['id'] for r in memory}
    for f in fi:
        ix=x[:,f].nonzero()[0]
        if len(ix)<30:continue
        for action in ['include','exclude']:
            active=((prob[ix]>=threshold-.15)&(prob[ix]<threshold)&~pred[ix]) if action=='include' else ((prob[ix]>=threshold)&(prob[ix]<=threshold+.15)&pred[ix])
            affected=active.sum(0)
            for d in np.flatnonzero(affected>=30):
                used=ix[active[:,d]];patients=np.unique(groups[used]).size
                if patients<20:continue
                change=1 if action=='include' else -1
                new_tp=tp[used]+change*target[used,d];new_union=union[used]+change-change*target[used,d]
                now=np.divide(new_tp,new_union,out=np.ones(len(used)),where=new_union>0)
                gain=float((now-old[used])@weights[used])
                if gain<=0:continue
                rule={'feature_index':int(f),'feature':feature_names[f],'drug_index':int(d),'drug':drug_names[d],'action':action}
                rule['id']=digest(rule)[:20]
                if rule['id'] in existing:continue
                candidates.append({'operation':'ADD','id':rule['id'],'rule':rule,'induction_jaccard_gain':gain,
                    'affected_visits':int(len(used)),'affected_patients':int(patients)})
    baseline=agreement(pred,target,groups)
    for rule in memory:
        without=[r for r in memory if r['id']!=rule['id']];alternative=apply(without,x,prob,threshold)
        changed=np.any(alternative!=pred,axis=1);visits=int(changed.sum());patients=int(np.unique(groups[changed]).size)
        gain=agreement(alternative,target,groups)['patient_jaccard']-baseline['patient_jaccard']
        if visits>=30 and patients>=20 and gain>0:
            candidates.append({'operation':'DELETE','id':'delete-'+rule['id'],'rule':rule,'induction_jaccard_gain':gain,'affected_visits':visits,'affected_patients':patients})
    return sorted(candidates,key=lambda c:(-c['induction_jaccard_gain'],c['id']))[:24]

def edit(memory,candidate):
    if candidate['operation']=='DELETE':return [r for r in memory if r['id']!=candidate['rule']['id']]
    if any(r['id']==candidate['rule']['id'] for r in memory) or len(memory)>=20:return list(memory)
    return list(memory)+[candidate['rule']]

def verify_edits(memory,candidates,selected,x,prob,target,groups,threshold,gate=True):
    """Apply sequential edits, recording actual witness deltas and unchanged cases."""
    by_id={c['id']:c for c in candidates};assert len(selected)<=4 and len(set(selected))==len(selected) and all(i in by_id for i in selected)
    state=list(memory);journal=[]
    for identifier in selected:
        candidate=by_id[identifier];proposal=edit(state,candidate)
        before=apply(state,x,prob,threshold);after=apply(proposal,x,prob,threshold)
        changed=np.any(before!=after,axis=1);patients=int(np.unique(groups[changed]).size)
        old=agreement(before,target,groups);new=agreement(after,target,groups)
        accept=state!=proposal and (not gate or (patients>=5 and new['patient_f1']>old['patient_f1'] and new['patient_jaccard']>=old['patient_jaccard']))
        journal.append({'candidate':candidate,'before_memory_sha256':digest(state),'proposed_memory_sha256':digest(proposal),
            'affected_witness_patients':patients,'witness_before':old,'witness_after':new,'accepted':bool(accept),'gate_enabled':gate})
        if accept:state=proposal
    return state,journal
