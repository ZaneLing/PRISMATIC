"""Matched offline replay: does feedback improve a post-review verifier?"""
import copy,hashlib,json,random,sys,warnings
from pathlib import Path
import joblib,numpy as np
from sklearn.linear_model import Ridge
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'upgrade_v11'))
from evidence_tool import LOCAL
from public_client import LOCAL as DATA_LOCAL,digest
from agent import metrics,transition
from verifier import features,selections,select_rows


def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')


def signature(state):
    if state is None:return digest('fixed_balanced')
    return digest({'coef':state['model'].coef_.tolist(),'intercept':float(state['model'].intercept_),
                   'threshold':state['threshold'],'rich':state['rich']})


def run():
    (HERE/'results').mkdir(exist_ok=True)
    config={'status':'frozen_before_v13_test_scoring','actions':['cot','balanced'],'inference_calls':2,
        'seeds':[42,137,2026],'round_case_counts':[156,312,468,625],'alpha':[1.,10.,100.],'threshold':[-.1,0.,.1],
        'feature_variants':['response-relations-only','response-relations-and-three-text-hashes'],
        'arms':['uniform','error_prioritized'],'feedback_weight':'1 + 3 * pre-update reachable selection error; old weights retained',
        'training':'All currently seen cases, same labels and candidate counts per arm; no backbone update.',
        'selection':'190 proposal cases choose a candidate; 197 guard cases require positive net fixes.',
        'initial_state':'Balanced review selected in v11 development data.',
        'fixed_controls':['CoT','balanced review','full-data ordinary verifier with proposal-selected hyperparameters'],
        'scope':'Exploratory development extension on an already observed test; no new network requests.',
        'missing_actions':'Neither indication nor Gemini outputs are used.'}
    save(HERE/'protocol.json',config)
    parts=json.loads((DATA_LOCAL/'data.json').read_text())['parts']
    # Only development outputs are loaded until choices have been frozen.
    data={s:json.loads((LOCAL/(s+'-review-actions.json')).read_text()) for s in ['train','proposal','guard']}
    for s,actions in data.items():
        for a in config['actions']:
            assert not any(r.get('error') for r in actions[a])
            assert [r['case_id'] for r in actions[a]]==[c['id'] for c in parts[s]]
    x={rich:{s:features(parts[s],a['cot'],a['balanced'],rich) for s,a in data.items()} for rich in [False,True]}
    y=np.array([int(r['prediction']==c['gold'])-int(b['prediction']==c['gold']) for c,b,r in zip(parts['train'],data['train']['cot'],data['train']['balanced'])])
    reachable=np.array([b['prediction']==c['gold'] or r['prediction']==c['gold'] for c,b,r in zip(parts['train'],data['train']['cot'],data['train']['balanced'])])
    def infer(state,split):
        sel=np.ones(len(parts[split]),dtype=int) if state is None else selections(state,x[state['rich']][split],len(parts[split]))
        return select_rows(data[split]['cot'],data[split]['balanced'],sel)
    numerical={'fits':0,'runtime_warning_count':0,'warnings':[],'maximum_intercept_recount_difference':0.}
    def fit_candidates(ix,weights,incumbent):
        previous=infer(incumbent,'proposal');best=(metrics(previous,parts['proposal'])['accuracy'],incumbent);audit=[]
        for rich in [False,True]:
            for alpha in config['alpha']:
                model=Ridge(alpha=alpha,solver='lsqr')
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter('always',RuntimeWarning)
                    model.fit(x[rich]['train'][ix],y[ix],sample_weight=weights)
                numerical['fits']+=1
                numerical['runtime_warning_count']+=len(caught)
                numerical['warnings']=sorted(set(numerical['warnings']+[str(w.message) for w in caught]))
                assert np.isfinite(model.coef_).all() and np.isfinite(model.intercept_)
                # Independently recalculate the weighted intercept using elementwise
                # multiplication/sum, avoiding the dense dot path that issued warnings.
                mean_x=np.asarray(x[rich]['train'][ix].T@weights).ravel()/weights.sum()
                expected=np.sum(weights*y[ix])/weights.sum()-np.sum(mean_x*model.coef_)
                diff=abs(float(expected-model.intercept_))
                numerical['maximum_intercept_recount_difference']=max(numerical['maximum_intercept_recount_difference'],diff)
                assert diff<1e-8,'Weighted intercept differs from independent recount'
                for threshold in config['threshold']:
                    state={'model':model,'rich':rich,'alpha':alpha,'threshold':threshold,'training_n':len(ix)}
                    score=metrics(infer(state,'proposal'),parts['proposal'])['accuracy']
                    audit.append({'rich':rich,'alpha':alpha,'threshold':threshold,'proposal_accuracy':score})
                    if score>best[0]:best=(score,state)
        return best[1],audit
    saved={};journals={}
    static,static_audit=fit_candidates(np.arange(len(parts['train'])),np.ones(len(parts['train'])),None)
    saved['static_supervised']=[static];journals['static_supervised']={'candidates':static_audit,'sha256':signature(static)}
    for seed in config['seeds']:
        order=list(range(len(parts['train'])));random.Random(seed).shuffle(order)
        for arm in config['arms']:
            active=None;states=[None];journal=[];errors=np.zeros(len(order));previous_seen=0
            for r,n in enumerate(config['round_case_counts'],1):
                ix=np.array(order[:n]);new=np.array(order[previous_seen:n]);current=infer(active,'train')
                for i in new:errors[i]=float(reachable[i] and current[i]['prediction']!=parts['train'][i]['gold'])
                weights=1+3*errors[ix] if arm=='error_prioritized' else np.ones(n)
                candidate,audit=fit_candidates(ix,weights,active)
                delta=transition(infer(active,'guard'),infer(candidate,'guard'),parts['guard'])
                accepted=delta['fixes']>delta['regressions']
                if accepted:active=candidate
                states.append(copy.deepcopy(active));journal.append({'round':r,'training_seen':n,'promoted':accepted,
                    'guard_transition':delta,'active_sha256':signature(active),'proposed_sha256':signature(candidate),
                    'active_training_n':active['training_n'] if active else 0,'new_preupdate_reachable_error_rate':float(errors[new].mean()),
                    'weighted_cases':int((weights>1).sum()),'sample_weight_sha256':digest(weights.tolist()),'candidates':audit})
                previous_seen=n
            name=f'{arm}_seed_{seed}';saved[name]=states;journals[name]=journal
            print(json.dumps({'stage':'frozen','arm':arm,'seed':seed,'accepted':[j['promoted'] for j in journal]}),flush=True)
    save(HERE/'results/frozen_versions.json',{'test_feedback_used_for_choices':False,'versions':journals})
    numerical['all_coefficients_intercepts_and_scored_predictions_finite']=True
    save(HERE/'results/numerical_audit.json',numerical)
    joblib.dump(saved,LOCAL/'outcome-verifier-v13-states.joblib')
    # After all choices freeze, obtain the complete test actions and count outcomes.
    data['test']=json.loads((LOCAL/'test-review-actions.json').read_text())
    for a in config['actions']:
        assert not any(r.get('error') for r in data['test'][a])
        assert [r['case_id'] for r in data['test'][a]]==[c['id'] for c in parts['test']]
    for rich in [False,True]:x[rich]['test']=features(parts['test'],data['test']['cot'],data['test']['balanced'],rich)
    result={'status':'complete','controls':{a:metrics(data['test'][a],parts['test']) for a in config['actions']},'runs':{}}
    predictions={}
    for key,states in saved.items():
        previous=data['test']['balanced'];curve=[];predictions[key]=[]
        for r,state in enumerate(states):
            rows=infer(state,'test');predictions[key].append(rows)
            curve.append({'round':r,'score':metrics(rows,parts['test']),**transition(previous,rows,parts['test']),
                          'retained_initial':sum(a['prediction']==b['prediction'] for a,b in zip(rows,data['test']['cot']))})
            previous=rows
        result['runs'][key]={'curve':curve,'final':curve[-1]['score'],'versus_fixed_review':transition(data['test']['balanced'],previous,parts['test'])}
    save(LOCAL/'outcome-verifier-v13-predictions.json',predictions);save(HERE/'results/outcome_evolution.json',result)
    print(json.dumps({k:v['final']['correct'] for k,v in result['runs'].items()}),flush=True)


if __name__=='__main__':run()
