"""Freeze all feedback and static choices without loading test cases."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1');os.environ.setdefault('OMP_NUM_THREADS','1');os.environ.setdefault('VECLIB_MAXIMUM_THREADS','1')
import json,sys,time
import numpy as np,joblib
from data_contract import HERE,PRIVATE,sha,digest,save
from learning import Policy,OrderTool,score,ranked_rows,choose,feedback_weights,dump

def main(seed):
    protocol=json.loads((HERE/'protocol.json').read_text());assert seed in protocol['seeds']
    assert json.loads((PRIVATE/'protocol_lock.json').read_text())['sha256']==sha(HERE/'protocol.json')
    folder=PRIVATE/f'seed_{seed}';folder.mkdir(exist_ok=True)
    code={p:sha(HERE/p) for p in ['train.py','learning.py','data_contract.py']};runlock=folder/'execution_lock.json'
    signature={'protocol_sha256':sha(HERE/'protocol.json'),'code_sha256':code}
    if runlock.exists():assert json.loads(runlock.read_text())==signature,'Source changed after training started'
    else:save(runlock,signature)
    final=HERE/f'results/selection_seed_{seed}.json'
    if final.exists() and json.loads(final.read_text())['status']=='selection_frozen':return
    meta=json.loads((HERE/'results/feature_manifest.json').read_text());assert sha(PRIVATE/'development.joblib')==meta['development_sha256']
    b=joblib.load(PRIVATE/'development.joblib');assert 'test' not in b
    lookup=joblib.load(PRIVATE/'retrieval_development.joblib');assert lookup['development_sha256']==meta['development_sha256']
    arms=protocol['arms'];sizes=protocol['round_sizes'];thresholds=protocol['thresholds'];classes=b['classes'];ids=[c['case_id'] for c in b['train']['cases']]
    sequence=np.r_[np.arange(8000),np.random.default_rng(seed).permutation(np.arange(8000,40000))];dump(sequence,folder/'case_order.joblib')
    weights={a:np.ones(40000) for a in arms};active={};journals={a:[] for a in arms};raw={a:[] for a in arms};old={}
    for a in arms:
        p=HERE/f'results/journal_seed_{seed}_{a}.json';old[a]={x['round']:x for x in json.loads(p.read_text())} if p.exists() else {}
    def assess(p,tool,split,threshold=None,conditional=True):
        rows,probs=ranked_rows(p,tool,b[split]['word'],classes,conditional)
        if threshold is None:threshold=max(thresholds,key=lambda t:score(choose(rows,probs,t),b[split]['truth'])['promotion_score'])
        pred=choose(rows,probs,threshold);return score(pred,b[split]['truth']),pred,threshold
    for r,n in enumerate(sizes):
        ix=sequence[:n]
        if r:
            new=sequence[sizes[r-1]:n];parent=active['error_prioritized'];p=parent['model'].predict_proba(b['train']['x'][new])
            w=feedback_weights(p,b['y'][new],parent['state']['threshold']);perm=np.random.default_rng(seed*100+r).permutation(len(w))
            weights['error_prioritized'][new]=w;weights['permuted_priority'][new]=w[perm]
            dump({'case_ids':[ids[i] for i in new],'parent':parent['state'],'preupdate_probabilities':p,'weights':w,'permutation':perm},folder/f'feedback_round_{r}.joblib')
        truth=[b['train']['truth'][i] for i in ix];toolpath=folder/f'tool_round_{r}.joblib'
        completed=[old[a][r] for a in arms if r in old[a]]
        if completed:
            assert sha(toolpath)==completed[0]['candidate']['tool_sha256'];tool=joblib.load(toolpath)
        else:tool=OrderTool(truth,b['train']['word'][ix],seed);dump(tool,toolpath)
        toolhash=sha(toolpath);initial=None
        for arm in arms:
            past=old[arm].get(r);modelpath=folder/f'{arm}_policy_round_{r}.joblib';w=weights[arm][ix].copy();w/=w.mean()
            start=time.time()
            if past:
                model=joblib.load(modelpath);assert model.sha256==past['candidate']['policy_sha256'];assert digest(w.tolist())==past['sample_weight_sha256'];elapsed=past['physical_training_seconds']
            elif r==0 and initial is not None:model=initial;elapsed=0.
            else:model=Policy(b['train']['x'][ix],b['y'][ix],w,seed);elapsed=time.time()-start
            if r==0:initial=model
            if not past:dump(model,modelpath)
            proposal,_,threshold=assess(model.predict_proba(b['proposal']['x']),tool,'proposal')
            guard,pred,_=assess(model.predict_proba(b['guard']['x']),tool,'guard',threshold)
            state={'arm':arm,'round':r,'training_cases':n,'threshold':threshold,'policy_file':modelpath.name,'policy_sha256':model.sha256,
              'tool_file':toolpath.name,'tool_sha256':toolhash}
            previous=active.get(arm);before=previous['guard'] if previous else None
            accepted=before is None or (guard['promotion_score']>before['promotion_score'] and all(guard[k]>=before[k]-.002 for k in ['drug_micro_f1','core_order_micro_f1']))
            if accepted:active[arm]={'model':model,'state':state,'guard':guard}
            raw[arm].append(state)
            journal={'round':r,'training_cases':n,'candidate':state,'active':active[arm]['state'],'accepted':accepted,'proposal':proposal,
              'raw_guard':guard,'active_guard':active[arm]['guard'],'sample_weight_sha256':digest(w.tolist()),'weight_range':[float(w.min()),float(w.max())],
              'training_membership_sha256':digest([ids[i] for i in ix]),'tool_membership_sha256':tool.membership_sha256,
              'epochs_per_classifier':60,'classifiers':len(classes),'logical_training_case_exposures':n*60*len(classes),
              'physical_training_seconds':elapsed,'initial_model_reused':r==0 and arm!='uniform'}
            if past:assert journal['active']==past['active'] and journal['raw_guard']==past['raw_guard'] and accepted==past['accepted']
            journals[arm].append(journal);save(HERE/f'results/journal_seed_{seed}_{arm}.json',journals[arm])
            print(json.dumps({'seed':seed,'round':r,'arm':arm,'accepted':accepted,'guard_drug_order':[guard['drug_micro_f1'],guard['core_order_micro_f1']],'training_seconds':elapsed}),flush=True)
    # Static controls have full-data fits, with their extra search budget disclosed.
    static={};models={}
    for kind in ['word','char']:
        path=folder/f'static_{kind}.joblib'
        if path.exists():model=joblib.load(path)
        else:
            model=Policy(b['train'][kind][sequence],b['y'][sequence],np.ones(40000),seed);dump(model,path)
        models[kind]=model;print(json.dumps({'seed':seed,'static_fit':kind,'complete':True}),flush=True)
    probabilities={s:{kind:m.predict_proba(b[s][kind]) for kind,m in models.items()} for s in ['proposal','guard']}
    prevalence=b['y'].mean(0)
    for name,conditional in [('prevalence_global',False),('retrieval_conditional',True),('word_global',False),('word_conditional',True)]:
        def probability(s):
            if name.startswith('prevalence'):return np.tile(prevalence,(len(b[s]['truth']),1))
            if name.startswith('retrieval'):return lookup[s]
            return probabilities[s]['word']
        pm,_,t=assess(probability('proposal'),tool,'proposal',conditional=conditional);gm,_,_=assess(probability('guard'),tool,'guard',t,conditional)
        static[name]={'threshold':t,'conditional':conditional,'proposal':pm,'guard':gm}
    options=[]
    for weight in [0.,.25,.5,.75,1.]:
        p=weight*probabilities['proposal']['word']+(1-weight)*probabilities['proposal']['char'];pm,_,t=assess(p,tool,'proposal')
        options.append({'word_weight':weight,'threshold':t,'proposal':pm})
    selected=max(options,key=lambda v:v['proposal']['promotion_score']);w=selected['word_weight']
    selected['guard']=assess(w*probabilities['guard']['word']+(1-w)*probabilities['guard']['char'],tool,'guard',selected['threshold'])[0]
    static['word_char_ensemble']=selected;static['reuse_prior_orders']={'rule':'Latest one prior tuple per reachable code, at most20, no learned threshold'}
    dump({'prevalence':prevalence,'static_models':models,'static_choices':static},folder/'static_controls.joblib')
    save(final,{'status':'selection_frozen','seed':seed,'selected':{a:v['state'] for a,v in active.items()},'raw_states':raw,
      'static':static,'static_model_hashes':{k:v.sha256 for k,v in models.items()},'static_fit_budget':{k:{'classifiers':len(classes),'epochs':60,'case_exposures':40000*60*len(classes),'training_seconds':v.training_seconds} for k,v in models.items()},'static_tool_file':toolpath.name,'static_tool_sha256':toolhash,
      'protocol_sha256':sha(HERE/'protocol.json'),'code_sha256':code,'test_loaded':False})
    print(json.dumps({'seed':seed,'status':'selection_frozen'}),flush=True)

if __name__=='__main__':main(int(sys.argv[1]))
