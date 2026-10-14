"""Executable artifact evolution with proposal/guard separation and sealed test scoring."""
import json,sys,time,hashlib
from pathlib import Path
import joblib,numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.multiclass import OneVsRestClassifier
from sklearn.naive_bayes import MultinomialNB
from rx_agent import score,hash_data
from order_tools import ConditionalOrderTool
from prepare_data import PRIVATE
HERE=Path(__file__).resolve().parent

def choose(p,classes,t):
    rank=np.argsort(-p,axis=1,kind='stable')[:,:20]
    return [[classes[j] for j in row if p[i,j]>=t] for i,row in enumerate(rank)]

def knn(x,train,y):
    out=[]
    for lo in range(0,x.shape[0],64):
        sim=(x[lo:lo+64]@train.T).toarray();ix=np.argpartition(-sim,29,axis=1)[:,:30]
        w=np.take_along_axis(sim,ix,axis=1)
        out.extend((w[:,:,None]*y[ix]).sum(1)/np.maximum(1e-9,w.sum(1)[:,None]))
    return np.asarray(out)

def per_case(pred,truth):
    return np.array([score([p],[g])['promotion_score'] for p,g in zip(pred,truth)])

def run(seed=42,study_dir=None,data_dir=None):
    here=Path(study_dir) if study_dir is not None else HERE
    private=Path(data_dir) if data_dir is not None else PRIVATE
    started=time.time();config=json.loads((here/'evaluation_protocol.json' if study_dir is not None else here/'protocol.json').read_text());b=joblib.load(private/'data.joblib')
    classes=b['classes'];truth=b['truth'];ys=[{o['drug_name'] for o in row} for row in truth['train']]
    y=np.array([[c in row for c in classes] for row in ys],dtype=np.float32)
    v=TfidfVectorizer(min_df=3,max_features=16000,ngram_range=(1,2),sublinear_tf=True,token_pattern=r'(?u)\b\w+\b')
    v.fit(b['text']['train'][:8000]);x={s:v.transform(t) for s,t in b['text'].items()}
    tools={};probs={};mem={};models={};decisions=[];active=None;frozen={}
    # Inference features for test may be computed now; its labels are never scored in this loop.
    for round_index,n in enumerate(config['training_rounds']):
        clf=OneVsRestClassifier(SGDClassifier(loss='log_loss',alpha=1e-5,max_iter=60,tol=1e-3,random_state=seed),n_jobs=1)
        clf.fit(x['train'][:n],y[:n]);models[n]=clf
        tools[n]=ConditionalOrderTool(truth['train'][:n],x['train'][:n],seed)
        probs[n]={s:clf.predict_proba(x[s]) for s in ['proposal','guard','test']}
        mem[n]={s:knn(x[s],x['train'][:n],y[:n]) for s in ['proposal','guard','test']}
        def evaluate(state,split,return_orders=False):
            p=(1-state['beta'])*probs[state['policy_n']][split]+state['beta']*mem[state['memory_n']][split]
            names=choose(p,classes,state['threshold'])
            orders=tools[state['tool_n']].compile(names,x[split],state['conditional'])
            return orders if return_orders else score(orders,truth[split])
        states=[]
        if active is not None:states.append(dict(active,proposal='unchanged'))
        combinations=[('all',n,n,n),('parameters_only',n,active['tool_n'] if active else n,active['memory_n'] if active else n),
          ('tool_only',active['policy_n'] if active else n,n,active['memory_n'] if active else n),
          ('memory_only',active['policy_n'] if active else n,active['tool_n'] if active else n,n)]
        seen=set()
        for proposal,pn,tn,mn in combinations:
            for beta in config['memory_weights']:
                for conditional in [False,True]:
                    for threshold in config['thresholds']:
                        state=dict(policy_n=pn,tool_n=tn,memory_n=mn,beta=beta,conditional=conditional,threshold=threshold,proposal=proposal)
                        sig=hash_data({k:z for k,z in state.items() if k!='proposal'})
                        if sig not in seen:states.append(state);seen.add(sig)
        # Cache compiled top-20 orders for each policy/memory/tool variant; threshold only filters.
        compilation={}
        def fast(state,split):
            sig=(state['policy_n'],state['tool_n'],state['memory_n'],state['beta'],state['conditional'],split)
            if sig not in compilation:
                p=(1-state['beta'])*probs[state['policy_n']][split]+state['beta']*mem[state['memory_n']][split]
                ranks=np.argsort(-p,axis=1,kind='stable')[:,:20]
                rows=tools[state['tool_n']].compile([[classes[j] for j in row] for row in ranks],x[split],state['conditional'])
                for i,row in enumerate(rows):
                    for o,j in zip(row,ranks[i]):o['selection_score']=float(p[i,j])
                compilation[sig]=rows
            return [[o for o in row if o['selection_score']>=state['threshold']] for row in compilation[sig]]
        candidates=[]
        for state in states:
            metric=score(fast(state,'proposal'),truth['proposal']);candidates.append((metric['promotion_score'],state,metric))
        _,candidate,proposal_metric=max(candidates,key=lambda z:z[0])
        cg=score(fast(candidate,'guard'),truth['guard']);old_guard=score(fast(active,'guard'),truth['guard']) if active else None
        accepted=active is None or (cg['promotion_score']>old_guard['promotion_score'] and all(cg[k]>=old_guard[k]-.002 for k in ['drug_micro_f1','core_order_micro_f1']))
        previous=dict(active) if active else None
        if accepted:active=dict(candidate)
        current_guard=score(fast(active,'guard'),truth['guard'])
        delta=per_case(fast(active,'guard'),truth['guard'])-per_case(fast(previous,'guard'),truth['guard']) if previous else np.zeros(len(truth['guard']))
        artifact_path=private/f'round-{round_index}-seed-{seed}.joblib'
        joblib.dump({'model':clf,'tool':tools[n],'vectorizer':v,'classes':classes,'train_members':b['parts']['train'].hadm_id.iloc[:n].tolist()},artifact_path)
        decision={'round':round_index,'training_cases':n,'proposed':candidate,'accepted':accepted,'active':dict(active),
            'proposal_validation':proposal_metric,'candidate_guard':cg,'active_guard':current_guard,
            'guard_case_improvements':int((delta>1e-12).sum()),'guard_case_regressions':int((delta< -1e-12).sum()),
            'parameter_sha256':hash_data([m.coef_.tolist() for m in clf.estimators_]),
            'memory_sha256':hash_data(truth['train'][:n]),'tool_sha256':hash_data({'labels':{name:[list(k) for k in ks] for name,ks in tools[n].labels.items()},'weights':{name:m.coef_.tolist() for name,m in tools[n].models.items()}}),
            'conditional_tool_drugs':len(tools[n].models),'artifact_file_sha256':hashlib.sha256(artifact_path.read_bytes()).hexdigest(),
            'candidate_grid':[{'state':s,'proposal_composite':m} for m,s,_ in candidates]}
        decisions.append(decision);frozen[round_index]=dict(active)
        (here/f'results/decisions_seed_{seed}.json').write_text(json.dumps(decisions,indent=2)+'\n')
        print(json.dumps({k:decision[k] for k in ['round','training_cases','accepted','active','active_guard','guard_case_improvements','guard_case_regressions']}),flush=True)
    # All choices frozen. Save and compare actual baselines without using test for selection.
    baseline_states={}
    for name,conditional,beta in [('word_policy_global',False,0),('word_policy_conditional_tool',True,0),('retrieval_global',False,1),('retrieval_conditional_tool',True,1)]:
        opts=[]
        for t in config['thresholds']:
            state=dict(policy_n=40000,tool_n=40000,memory_n=40000,beta=beta,conditional=conditional,threshold=t,proposal=name)
            opts.append((score(fast(state,'proposal'),truth['proposal'])['promotion_score'],state))
        baseline_states[name]=max(opts,key=lambda z:z[0])[1]
    all_states={**baseline_states,'rxrsi_selected':active}
    for obj,keyname in [('parameters','policy_n'),('tool','tool_n'),('memory','memory_n')]:
        state=dict(active);state[keyname]=8000;all_states['without_'+obj+'_evolution']=state
    (here/f'results/final_selection_seed_{seed}.json').write_text(json.dumps(all_states,indent=2)+'\n')
    # This is the first test-label evaluation in this runner.
    test_predictions={name:fast(state,'test') for name,state in all_states.items()}
    curves=[];previous=None
    for i,state in frozen.items():
        pred=fast(state,'test');quality=per_case(pred,truth['test']);delta=quality-previous if previous is not None else np.zeros(len(quality));previous=quality
        curves.append({'round':i,'training_cases':config['training_rounds'][i],'metrics':score(pred,truth['test']),
          'case_improvements':int((delta>1e-12).sum()),'case_regressions':int((delta< -1e-12).sum())})
        test_predictions[f'round_{i}']=pred
    report={'seed':seed,'method_scores':{name:score(pred,truth['test']) for name,pred in test_predictions.items() if not name.startswith('round_')},
       'rounds':curves,'elapsed_seconds':time.time()-started,'protocol_sha256':hashlib.sha256((here/'evaluation_protocol.json' if study_dir is not None else here/'protocol.json').read_bytes()).hexdigest(),
       'test_labels_used_for_update':False,'parameter_learning':'Supervised SGD policy and conditional order tools; LLM unchanged',
       'caveat':'Round-zero and cumulative models differ in training data size. Full-data conditional-tool baseline controls for that advantage.'}
    joblib.dump({'predictions':test_predictions,'tools':tools,'probs':probs,'mem':mem,'models':models,'vectorizer':v,'x':x},private/f'run_seed_{seed}.joblib')
    (here/f'results/round_results_seed_{seed}.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)

if __name__=='__main__':run(int(sys.argv[1]) if len(sys.argv)>1 else 42)
