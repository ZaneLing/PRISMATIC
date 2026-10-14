"""Synthetic causal controls for memory resets; no clinical scoring or API."""
import json,sys
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix
HERE=Path(__file__).resolve().parent;sys.path[:0]=[str(HERE.parent),str(HERE)]
from run import sources,save,arms
from gates import check,rebase,promote,split_witness
from upgrade_v29.programs import canonical,verify
from upgrade_v29.audit import execute,agreement

def main():
    groups=np.array([f'patient{i}' for i in range(285) for _ in range(2)])
    a,b=split_witness(groups,42,1);assert len(set(groups[a]))==142 and len(set(groups[b]))==143
    assert not set(groups[a])&set(groups[b]) and len(a)+len(b)==len(groups)
    x=csr_matrix(np.ones((6,1)));prob=np.full((6,1),.45);ts=np.array([.5]);people=np.array([f'p{i}' for i in range(6)])
    rule=canonical({'drug_index':0,'conditions':[{'feature_index':0,'present':True}],'action':'include'},[0],[0]);positive=np.ones((6,1));negative=np.zeros((6,1));memory=[rule]
    good=check(memory,x,prob,ts,positive,people);bad=check(memory,x,prob,ts,negative,people)
    assert good['passed'] and not bad['passed']
    for y,z in [(positive,good),(negative,bad)]:
        for key,state in [('empty',[]),('memory',memory)]:
            actual=agreement(execute(state,x,prob,ts),y,people)
            assert all(abs(actual[k]-z[key][k])<1e-12 for k in actual)
    assert rebase(memory,good,bad,True)==[] and rebase(memory,good,bad,False)==memory
    assert rebase(memory,good,good,True)==memory
    edited,journal=verify([],[{'operation':'ADD','rule':rule}],x,prob,ts,positive,people)
    assert journal[0]['accepted'] and edited==memory
    assert promote(edited,bad,True)==[] and promote(edited,bad,False)==memory
    assert promote(edited,good,True)==memory
    low_support=check(memory,x[:2],prob[:2],ts,positive[:2],people[:2]);assert not low_support['passed']
    assert not check([],x,prob,ts,negative,people)['passed']
    protocol=json.loads((HERE/'protocol.json').read_text());assert len(arms(protocol))==protocol['factorial']['total_arms']==14
    result={'status':'passed','source_sha256':sources(),'checks':['patient_disjoint_142_143_split','all_patient_visits_stay_together','independent_scalar_whole_state_metrics','stale_memory_reset_vs_shadow','candidate_passes_A_but_fails_B','supported_memory_retention','fewer_than_three_patients_rejected','empty_memory_no_promotion','fourteen_registered_arms'],'clinical_fits':0,'api_calls':0,'test_inference':False}
    save(HERE/'results/runtime_probe.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':main()
