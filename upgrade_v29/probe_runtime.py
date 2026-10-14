"""Material protocol probes before any v29 clinical fitting or API proposal."""
import inspect,json
from pathlib import Path
import numpy as np
from scipy import sparse
from programs import canonical,apply,calibrate,agreement,candidate,verify,context
from partition import partitions
from train import sources
HERE=Path(__file__).resolve().parent
def main():
    people=np.array([f'synthetic-{i//2}' for i in range(240)]);roles=partitions(people,42)
    fit=set(roles['fit_patients']);wit=set(roles['witness_patients']);batches=[set(x) for x in roles['witness_batches']]
    assert fit.isdisjoint(wit) and fit|wit==set(people) and sum(map(len,batches))==len(wit) and set.union(*batches)==wit
    for i,a in enumerate(batches):
        assert a.isdisjoint(fit)
        for b in batches[i+1:]:assert a.isdisjoint(b)
    for fold in range(3):
        train={p for p,v in roles['folds'].items() if v!=fold};held={p for p,v in roles['folds'].items() if v==fold}
        assert train.isdisjoint(held) and train.isdisjoint(wit) and held.isdisjoint(wit)
    x=np.ones((240,3));x[120:,1]=0;x[:,2]=0;x=sparse.csr_matrix(x);prob=np.full((240,2),.4);thresholds=np.array([.5,.5])
    raw={'drug_index':0,'conditions':[{'feature_index':0,'present':True},{'feature_index':1,'present':False}],'action':'include'}
    rule=canonical(raw,[0,1,2],[0,1]);pred=apply([rule],x,prob,thresholds)
    assert not pred[:120].any() and pred[120:,0].all() and not pred[:,1].any()
    assert 'target' not in inspect.signature(apply).parameters and 'gold' not in inspect.signature(apply).parameters
    for bad in [{**raw,'gold':1},{**raw,'drug_index':9},{**raw,'conditions':[{'feature_index':0,'present':False}]},{**raw,'conditions':[{'feature_index':0,'present':True},{'feature_index':0,'present':False}]}]:
        try:canonical(bad,[0,1,2],[0,1])
        except ValueError:pass
        else:raise AssertionError('Invalid rule accepted')
    y=pred.copy();op=candidate({'operation':'ADD','rule':rule},[],x,prob,thresholds,y,people);assert op and op['affected_visits']==120 and op['affected_patients']==60
    state,log=verify([], [op], x,prob,thresholds,y,people);assert state==[rule] and log[0]['accepted']
    state,log=verify([], [op], x,prob,thresholds,np.zeros_like(y),people);assert not state and not log[0]['accepted']
    state,log=verify([], [op], x,prob,thresholds,np.zeros_like(y),people,gate=False);assert state==[rule] and log[0]['accepted']
    payload,pool,search=context([],x,prob,thresholds,y,people,['feature-a','feature-b','feature-c'],['class-a','class-b'],expanded=True)
    assert any(z['rule']==rule for z in pool),'Conditional search must recover a useful conjunction even when its broad predicate has no gain.'
    assert all(z['affected_visits']>=30 and z['affected_patients']>=20 for z in payload['single_predicate_evidence'])
    trained,events=calibrate(prob,y,people,.5);old=agreement(prob>=.5,y,people)['patient_jaccard'];new=agreement(prob>=trained,y,people)['patient_jaccard']
    assert new>=old and abs(new-old-sum(e['induction_jaccard_gain'] for e in events))<1e-12
    result={'status':'passed','source_sha256':sources(),'probes':{'patient_role_and_fresh_witness_disjointness':'passed','fold_patient_disjointness':'passed',
      'positive_negative_conjunction':'passed','conditional_search_including_nonpositive_components':'passed','unknown_and_target_injection_rejection':'passed','actual_support_counts':'passed','witness_accept_reject_and_ablation':'passed','calibration_coordinate_gain_recount':'passed'},
      'clinical_performance_claim':False,'clinical_model_fits':0,'api_calls':0}
    (HERE/'results').mkdir(exist_ok=True);(HERE/'results/runtime_probe.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
if __name__=='__main__':main()
