"""Typed conditional rule programs and ordinary calibration; no arbitrary code."""
import hashlib,itertools,json
import numpy as np

def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()
def patient_weights(groups):
    _,ix,count=np.unique(groups,return_inverse=True,return_counts=True)
    return 1./(len(count)*count[ix])
def agreement(pred,y,groups):
    tp=(pred&y.astype(bool)).sum(1);pn=pred.sum(1);gn=y.sum(1);w=patient_weights(groups)
    f=np.divide(2*tp,pn+gn,out=np.ones(len(tp)),where=pn+gn>0)
    j=np.divide(tp,pn+gn-tp,out=np.ones(len(tp)),where=pn+gn-tp>0)
    return {'patient_f1':float(np.sum(f*w)),'patient_jaccard':float(np.sum(j*w))}
def canonical(raw,allowed_features,allowed_drugs):
    if not isinstance(raw,dict) or set(raw)!={'drug_index','conditions','action'}:raise ValueError('rule_schema')
    d=raw['drug_index'];conditions=raw['conditions']
    if type(d) is not int or d not in allowed_drugs or raw['action'] not in ['include','exclude']:raise ValueError('drug_or_action')
    if not isinstance(conditions,list) or len(conditions) not in [1,2]:raise ValueError('predicate_count')
    checked=[]
    for c in conditions:
        if not isinstance(c,dict) or set(c)!={'feature_index','present'} or type(c['feature_index']) is not int or type(c['present']) is not bool or c['feature_index'] not in allowed_features:raise ValueError('predicate_schema')
        checked.append(dict(c))
    if len({c['feature_index'] for c in checked})!=len(checked) or not any(c['present'] for c in checked):raise ValueError('contradictory_or_unanchored_predicates')
    rule={'drug_index':d,'conditions':sorted(checked,key=lambda c:c['feature_index']),'action':raw['action']}
    return {**rule,'id':digest(rule)[:20]}
def mask(rule,x,prob,thresholds,cache=None):
    selected=np.ones(x.shape[0],dtype=bool)
    for c in rule['conditions']:
        f=c['feature_index']
        if cache is not None:
            if f not in cache:cache[f]=x[:,f].toarray().ravel()>0
            v=cache[f]
        else:v=x[:,f].toarray().ravel()>0
        selected&=v if c['present'] else ~v
    d=rule['drug_index'];p=prob[:,d];t=thresholds[d]
    return selected&((p>=t-.15)&(p<t) if rule['action']=='include' else (p>=t)&(p<=t+.15))
def apply(memory,x,prob,thresholds):
    pred=prob>=thresholds;cache={}
    for rule in memory:pred[mask(rule,x,prob,thresholds,cache),rule['drug_index']]=rule['action']=='include'
    return pred
def edited(memory,operation):
    if operation['operation']=='DELETE':return [r for r in memory if r['id']!=operation['rule']['id']]
    if len(memory)>=20 or any(r['id']==operation['rule']['id'] for r in memory):return list(memory)
    return memory+[operation['rule']]

def calibrate(prob,y,groups,threshold):
    """Two exact coordinate passes, fixed class order and no-change tie priority."""
    y=y.astype(bool);w=patient_weights(groups);ts=np.full(y.shape[1],threshold,dtype=float);pred=prob>=ts;events=[]
    offsets=[-.15,-.10,-.05,0.,.05,.10,.15]
    for iteration in range(2):
        for d in range(y.shape[1]):
            old=pred[:,d];tp=(pred&y).sum(1);pn=pred.sum(1);gn=y.sum(1);union=pn+gn-tp
            before=np.divide(tp,union,out=np.ones(len(tp)),where=union>0);best_gain=0.;chosen=ts[d];column=old
            for t in sorted(set(np.clip(threshold+np.array(offsets),.01,.99))):
                next_col=prob[:,d]>=t;change=next_col.astype(int)-old.astype(int)
                next_tp=tp+change*y[:,d];next_union=union+change-change*y[:,d]
                after=np.divide(next_tp,next_union,out=np.ones(len(tp)),where=next_union>0)
                gain=float(np.sum((after-before)*w))
                if gain>best_gain+1e-12:best_gain=gain;chosen=float(t);column=next_col
            if chosen!=ts[d]:events.append({'pass':iteration+1,'drug_index':d,'old_threshold':float(ts[d]),'new_threshold':chosen,'induction_jaccard_gain':best_gain})
            ts[d]=chosen;pred[:,d]=column
    return ts,events

def gain_stats(before,after_col,drug,y,groups,weights,retain_nonpositive=False):
    changed=before[:,drug]!=after_col;used=np.flatnonzero(changed);n=len(used);patients=len(np.unique(groups[used]))
    if n<30 or patients<20:return None
    tp=(before[used]&y[used]).sum(1);pn=before[used].sum(1);gn=y[used].sum(1);union=pn+gn-tp
    old=np.divide(tp,union,out=np.ones(n),where=union>0)
    diff=after_col[used].astype(int)-before[used,drug].astype(int);ntp=tp+diff*y[used,drug];nu=union+diff-diff*y[used,drug]
    new=np.divide(ntp,nu,out=np.ones(n),where=nu>0);gain=float(np.sum((new-old)*weights[used]))
    if gain<=1e-12 and not retain_nonpositive:return None
    return {'induction_jaccard_gain':gain,'affected_visits':n,'affected_patients':patients}

def candidate(operation,memory,x,prob,thresholds,y,groups,before=None,cache=None,retain_nonpositive=False):
    before=apply(memory,x,prob,thresholds) if before is None else before;rule=operation['rule'];d=rule['drug_index']
    if operation['operation']=='DELETE':column=apply(edited(memory,operation),x,prob,thresholds)[:,d]
    else:
        if any(r['id']==rule['id'] for r in memory) or len(memory)>=20:return None
        column=before[:,d].copy();column[mask(rule,x,prob,thresholds,cache)]=rule['action']=='include'
    stats=gain_stats(before,column,d,y.astype(bool),groups,patient_weights(groups),retain_nonpositive)
    return {**operation,**stats,'id':('delete-' if operation['operation']=='DELETE' else '')+rule['id']} if stats else None

def context(memory,x,prob,thresholds,y,groups,feature_names,drug_names,expanded=False):
    """Expose only aggregate supports; search program effects on policy-fit data."""
    before=apply(memory,x,prob,thresholds);y=y.astype(bool);w=patient_weights(groups);cache={};freq=np.asarray((x>0).sum(0)).ravel()
    features=np.lexsort((np.arange(len(freq)),-freq))[:128].tolist();burden=np.sum((before!=y)*w[:,None],axis=0)
    drugs=[]
    for d in np.lexsort((np.arange(len(drug_names)),-burden)):
        changed=before[:,d]!=y[:,d];visits=int(changed.sum());patients=len(np.unique(groups[changed]))
        if visits>=30 and patients>=20:drugs.append({'drug_index':int(d),'drug':drug_names[d],'error_visits':visits,'error_patients':patients,'weighted_disagreement':float(burden[d])})
        if len(drugs)==12:break
    candidates=[];contexts=[];trials=0
    for item in drugs:
        d=item['drug_index'];singles=[]
        for f in features:
            for action in ['include','exclude']:
                rule=canonical({'drug_index':d,'conditions':[{'feature_index':f,'present':True}],'action':action},features,[d]);trials+=1
                z=candidate({'operation':'ADD','rule':rule},memory,x,prob,thresholds,y,groups,before,cache,retain_nonpositive=True)
                if z:singles.append(z)
        singles.sort(key=lambda z:(-z['induction_jaccard_gain'],z['id']));positive=[z for z in singles if z['induction_jaccard_gain']>1e-12]
        negative=sorted([z for z in singles if z['induction_jaccard_gain']<=1e-12],key=lambda z:(z['induction_jaccard_gain'],z['id']));candidates.extend(positive)
        seen=[];selected=[]
        for pool,cap in [(positive,4),(negative,8),(positive+negative,8)]:
            for c in pool:
                if len(seen)>=cap:break
                f=c['rule']['conditions'][0]['feature_index']
                if f not in seen:seen.append(f);selected.append(c)
        contexts.extend({'drug_index':d,'drug':drug_names[d],'feature_index':c['rule']['conditions'][0]['feature_index'],'feature':feature_names[c['rule']['conditions'][0]['feature_index']],
          'action':c['rule']['action'],**{k:c[k] for k in ['induction_jaccard_gain','affected_visits','affected_patients']}} for c in selected)
        if expanded:
            for a,b in itertools.combinations(seen,2):
                for pa,pb in [(True,True),(True,False),(False,True)]:
                    for action in ['include','exclude']:
                        rule=canonical({'drug_index':d,'conditions':[{'feature_index':a,'present':pa},{'feature_index':b,'present':pb}],'action':action},features,[d]);trials+=1
                        z=candidate({'operation':'ADD','rule':rule},memory,x,prob,thresholds,y,groups,before,cache)
                        if z:candidates.append(z)
    for r in memory:
        trials+=1;z=candidate({'operation':'DELETE','rule':r},memory,x,prob,thresholds,y,groups,before,cache)
        if z:candidates.append(z)
    candidates=sorted({c['id']:c for c in candidates}.values(),key=lambda c:(-c['induction_jaccard_gain'],c['id']))
    payload={'allowed_features':[{'feature_index':f,'feature':feature_names[f]} for f in features],
      'focus_drugs':drugs,'single_predicate_evidence':contexts,'retained_rules':memory}
    return payload,candidates,{'evaluated_programs':trials,'eligible_programs':len(candidates)}

def verify(memory,operations,x,prob,thresholds,y,groups,gate=True):
    state=list(memory);journal=[]
    for op in operations:
        proposed=edited(state,op);old=apply(state,x,prob,thresholds);new=apply(proposed,x,prob,thresholds)
        affected=len(np.unique(groups[np.any(old!=new,axis=1)]));a=agreement(old,y,groups);b=agreement(new,y,groups)
        accept=state!=proposed and (not gate or (affected>=3 and b['patient_f1']-a['patient_f1']>1e-12 and b['patient_jaccard']-a['patient_jaccard']>=-1e-12))
        journal.append({'operation':op,'before_memory_sha256':digest(state),'proposed_memory_sha256':digest(proposed),'affected_witness_patients':affected,
          'witness_before':a,'witness_after':b,'gate_enabled':gate,'accepted':bool(accept)})
        if accept:state=proposed
    return state,journal
