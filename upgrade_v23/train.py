"""Three matched feedback arms; never load the separate evaluation bundle."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1');os.environ.setdefault('OMP_NUM_THREADS','1');os.environ.setdefault('VECLIB_MAXIMUM_THREADS','1')
import json,sys,time
import joblib,numpy as np
from components import HERE,PRIVATE,save,dump,hash_data,sha,WeightedPolicy,feedback_weights,compile_ranked,choose,score
from order_tools import ConditionalOrderTool

def main(seed):
    start=time.time();protocol=json.loads((HERE/'protocol.json').read_text());assert seed in protocol['seeds']
    assert json.loads((PRIVATE/'protocol_lock.json').read_text())['sha256']==hash_data(protocol)
    folder=PRIVATE/f'seed_{seed}';folder.mkdir(exist_ok=True)
    signature={'protocol':hash_data(protocol),'code':{p:sha(HERE/p) for p in ['components.py','train.py']}}
    run_lock=folder/'execution_lock.json'
    if run_lock.exists():assert json.loads(run_lock.read_text())==signature,'Source changed; do not silently mix checkpoint implementations'
    else:save(run_lock,signature)
    report_path=HERE/f'results/selection_seed_{seed}.json'
    if report_path.exists() and json.loads(report_path.read_text())['status']=='selection_frozen':return
    b=joblib.load(PRIVATE/'development.joblib');assert 'test' not in b['truth']
    order=np.r_[np.arange(8000),np.random.default_rng(seed).permutation(np.arange(8000,40000))]
    dump(order,folder/'case_order.joblib')
    arms=protocol['arms'];active={};journals={a:[] for a in arms};weights={a:np.ones(40000) for a in arms}
    raw_states={a:[] for a in arms};case_ids=b['parts']['train'].hadm_id.tolist()
    previous_journals={}
    for a in arms:
        path=HERE/f'results/journal_seed_{seed}_{a}.json'
        previous_journals[a]={v['round']:v for v in json.loads(path.read_text())} if path.exists() else {}
    thresholds=protocol['thresholds'];training_seconds={a:0. for a in arms}
    def state_eval(model,tool,split,threshold=None):
        rows,probs=compile_ranked(model,tool,b['x'][split],b['word'][split],b['classes'])
        if threshold is None:
            opts=[(score(choose(rows,probs,t),b['truth'][split])['promotion_score'],t) for t in thresholds]
            threshold=max(opts,key=lambda z:z[0])[1]
        pred=choose(rows,probs,threshold)
        return score(pred,b['truth'][split]),pred,threshold
    for r,n in enumerate(protocol['round_sizes']):
        ix=order[:n];new=order[protocol['round_sizes'][r-1]:n] if r else order[:n]
        if r:
            # Prediction is made before the updater receives this block's y.
            parent=active['error_prioritized'];p=parent['model'].predict_proba(b['x']['train'][new])
            block_weights=feedback_weights(p,b['y'][new],parent['state']['threshold'])
            perm=np.random.default_rng(seed*100+r).permutation(len(new));shuffled=block_weights[perm]
            assert np.array_equal(np.sort(block_weights),np.sort(shuffled))
            weights['error_prioritized'][new]=block_weights;weights['permuted_priority'][new]=shuffled
            dump({'case_ids':[case_ids[i] for i in new],'parent':parent['state'],'preupdate_probabilities':p,
                'feedback_weights':block_weights,'permuted_weights':shuffled,'permutation':perm},folder/f'feedback_round_{r}.joblib')
        seen_truth=[b['truth']['train'][i] for i in ix]
        tool_path=folder/f'tool_round_{r}.joblib'
        completed=[previous_journals[a][r] for a in arms if r in previous_journals[a]]
        if completed:
            assert sha(tool_path)==completed[0]['candidate']['tool_sha256'];tool=joblib.load(tool_path)
        else:
            tool=ConditionalOrderTool(seen_truth,b['word']['train'][ix],seed);dump(tool,tool_path)
        assert len(tool.memory.orders)==n
        tool_hash=sha(tool_path);shared_model=None
        for arm in arms:
            w=weights[arm][ix].copy();w/=w.mean();assert np.isclose(w.mean(),1)
            before=time.time()
            model_path=folder/f'{arm}_policy_round_{r}.joblib';past=previous_journals[arm].get(r)
            if past is not None:
                model=joblib.load(model_path);assert model.sha256==past['candidate']['policy_sha256']
                assert hash_data(w.tolist())==past['sample_weight_sha256'];elapsed=past['physical_training_seconds']
                if r==0:shared_model=model
            elif r==0 and shared_model is not None:model=shared_model;elapsed=0.
            else:
                model=WeightedPolicy(b['x']['train'][ix],b['y'][ix],w,seed,60);elapsed=time.time()-before
                if r==0:shared_model=model
            training_seconds[arm]+=elapsed
            if past is None:dump(model,model_path)
            proposal,_,threshold=state_eval(model,tool,'proposal')
            guard,pred,_=state_eval(model,tool,'guard',threshold)
            state={'round':r,'training_cases':n,'threshold':threshold,'arm':arm,'policy_sha256':model.sha256,'tool_sha256':tool_hash,
                'policy_file':model_path.name,'tool_file':tool_path.name}
            previous=active.get(arm);old=previous['guard'] if previous else None
            accepted=old is None or (guard['promotion_score']>old['promotion_score'] and all(guard[k]>=old[k]-.002 for k in ['drug_micro_f1','core_order_micro_f1']))
            if accepted:active[arm]={'model':model,'state':state,'guard':guard,'pred':pred}
            raw_states[arm].append(state)
            dump({'case_ids':b['parts']['guard'].hadm_id.tolist(),'raw_predictions':pred,'active_predictions':active[arm]['pred']},folder/f'{arm}_guard_round_{r}.joblib')
            journal={'round':r,'training_cases':n,'candidate':state,'accepted':accepted,'active':active[arm]['state'],'proposal':proposal,
                'raw_guard':guard,'active_guard':active[arm]['guard'],'epochs_per_classifier':60,'classifiers':len(model.iterations),
                'logical_training_case_exposures':int(n*60*len(model.iterations)),'physical_training_seconds':elapsed,'initial_model_physically_reused':r==0 and arm!='uniform',
                'sample_weight_sha256':hash_data(w.tolist()),'weight_mean':float(w.mean()),'weight_min':float(w.min()),'weight_max':float(w.max()),
                'training_membership_sha256':hash_data([case_ids[i] for i in ix]),'tool_training_rows':len(tool.memory.orders),
                'feedback_precedes_training':r>0,'tool_future_cases':0,'selected_conditional_tool_drugs':len(tool.models)}
            journals[arm].append(journal)
            if past is not None:
                assert journal['active']==past['active'] and journal['accepted']==past['accepted']
                assert journal['raw_guard']==past['raw_guard']
            save(HERE/f'results/journal_seed_{seed}_{arm}.json',journals[arm])
            print(json.dumps({'seed':seed,'arm':arm,'round':r,'accepted':accepted,'active_round':active[arm]['state']['round'],'guard':active[arm]['guard']['promotion_score'],'seconds':round(elapsed,2)}),flush=True)
        assert np.allclose(np.sort(weights['error_prioritized'][ix]),np.sort(weights['permuted_priority'][ix]))
    save(report_path,{'status':'selection_frozen','seed':seed,'protocol_sha256':hash_data(protocol),'selected':{a:v['state'] for a,v in active.items()},
      'raw_states':raw_states,'training_seconds':training_seconds,'test_loaded':False,'seconds':time.time()-start,
      'code_sha256':{p:sha(HERE/p) for p in ['components.py','train.py']}})

if __name__=='__main__':main(int(sys.argv[1]))
