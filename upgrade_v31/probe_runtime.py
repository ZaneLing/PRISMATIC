"""Synthetic tests of target transport, blinded prompts and shuffled priorities."""
import json
from pathlib import Path
import numpy as np
from run import sources,save,sampling,error_value
from views import view
HERE=Path(__file__).resolve().parent
def main():
    orders=[{'drug_name':f'drug_{i}','route':'oral','dose_value':str(i+1),'dose_unit':'mg','frequency_per_24h':'1'} for i in range(20)]
    c={'case_id':'synthetic','subject_hash':'person','catalogue':{f'O{i+1}':o for i,o in enumerate(orders)},'gold':[orders[2],orders[9]],'target':['O3','O10'],'target_mask':[int(i in [2,9]) for i in range(20)],'messages':[{'role':'system','content':'Return inclusion JSON.'},{'role':'user','content':'Synthetic context\nCandidate order tools:\nplaceholder'}]}
    permutations=[]
    for condition in ['ranked','permuted','reversed']:
        z=view(c,condition,42,1,'train');selected=[o for o,t in zip(z['catalogue'].values(),z['target_mask']) if t]
        assert {o['drug_name'] for o in selected}=={'drug_2','drug_9'};assert all(o==orders[r-1] for r,o in zip(z['original_rank_by_position'],z['catalogue'].values()))
        alternate={**c,'gold':[orders[1]]};assert view(alternate,condition,42,1,'train')['messages']==z['messages'];permutations.append(z['original_rank_by_position'])
    assert permutations[0]!=permutations[1]!=permutations[2] and view(c,'permuted',42,1,'train')==view(c,'permuted',42,1,'train')
    assert view(c,'permuted',42,1,'train')['messages']!=view(c,'permuted',42,1,'feedback')['messages']
    cases=[{'case_id':str(i)} for i in range(600)];errors={str(i):i/599 for i in range(600)}
    chosen={};weights={}
    for arm in ['permuted_uniform','ranked_uniform','permuted_own_error','permuted_shuffled_error']:
        chosen[arm],weights[arm]=sampling(cases,errors,arm,42,1);assert len(set(chosen[arm]))==400 and abs(weights[arm].sum()-1)<1e-12
    np.testing.assert_array_equal(chosen['permuted_uniform'],chosen['ranked_uniform']);np.testing.assert_allclose(np.sort(weights['permuted_own_error']),np.sort(weights['permuted_shuffled_error']),atol=1e-15)
    assert not np.array_equal(weights['permuted_own_error'],weights['permuted_shuffled_error'])
    assert error_value(c,{'orders':[orders[2],orders[9]]})==0 and error_value(c,{'orders':[]})==1
    none={**c,'target':[]};assert error_value(none,{'orders':[]})==0
    import mlx.core as mx
    from train_cli import completion_loss
    from mlx_lm.tuner.trainer import default_loss
    class Dummy:
        def __call__(self,inputs):return mx.broadcast_to(mx.arange(10,dtype=mx.float32),(inputs.shape[0],inputs.shape[1],10))
    batch=mx.array([[1,2,3,4,5,0,0],[1,2,3,4,5,6,0]]);lengths=mx.array([[2,5],[3,6]])
    alternate=mx.array([[1,2,3,4,5,9,9],[1,2,3,4,5,6,9]])
    a,n=completion_loss(Dummy(),batch,lengths);b,n2=completion_loss(Dummy(),alternate,lengths);old,old_n=default_loss(Dummy(),batch,lengths);other,_=default_loss(Dummy(),alternate,lengths)
    assert n.item()==n2.item()==6 and old_n.item()==8 and abs(a.item()-b.item())<1e-7 and abs(old.item()-other.item())>.1
    result={'status':'passed','source_sha256':sources(),'checks':['identity_preserving_mask_transport','original_rank_and_fields_preserved','gold_changes_never_change_prompts','deterministic_label_independent_permutation','feedback_and_training_views_distinct','uniform_membership_matched','shuffled_error_weight_multiset_preserved','four_hundred_unique_samples','reachable_error_and_empty_target_semantics','strict_completion_mask_excludes_padding','padding_target_changes_do_not_change_loss'],'synthetic_mask_tokens':{'strict':6,'installed_default':8},'clinical_fits':0,'model_generations':0,'api_calls':0}
    save(HERE/'results/runtime_probe.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':main()
