"""Learn evidence-tool routing from the fixed agent's own counterfactual feedback."""
import argparse,copy,json,random,sys
from pathlib import Path
import joblib,numpy as np
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import Ridge
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'upgrade_v8'))
from public_client import LOCAL as DATA_LOCAL,digest
from agent import empty_state,metrics,transition
from evidence_tool import EvidenceAgent,PROFILES,LOCAL
ACTIONS=['cot']+list(PROFILES)

def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')

def outputs(agent,cases,label):
    path=LOCAL/(label+'-review-actions.json')
    if path.exists():
        result=json.loads(path.read_text())
        result={a:rows for a,rows in result.items() if not any(r.get('error') for r in rows)}
        if set(result)==set(ACTIONS):return result
    else:result={}
    base=agent.batch(cases,empty_state());result['cot']=base;save(path,result)
    # Identical first draft is supplied to every evidence-review profile.
    from concurrent.futures import ThreadPoolExecutor
    for action in ACTIONS[1:]:
        if action in result:continue
        state=empty_state();state['evidence_profile']=action
        def one(pair):
            case,first=pair;r=agent.solve(case,state,initial=first['prediction'])
            for key in ['input_tokens','output_tokens','cost_usd','seconds']:r[key]=(r.get(key) or 0)+(first.get(key) or 0)
            r['first_prediction']=first['prediction'];return r
        with ThreadPoolExecutor(max_workers=10) as pool:result[action]=list(pool.map(one,zip(cases,base)))
        save(path,result);print(json.dumps({'stage':'counterfactual_feedback','split':label,'action':action,'n':len(cases)}),flush=True)
    for rows in result.values():assert [r['case_id'] for r in rows]==[c['id'] for c in cases]
    return result

def feature_text(c,base):
    answer=base['prediction'];selected=c['options'][ord(answer)-65] if answer in [chr(65+i) for i in range(len(c['options']))] else 'invalid'
    return c['dialogue']+'\nOptions: '+' | '.join(c['options'])+'\nInitial proposed medication: '+selected+'\nInitial evidence: '+base.get('evidence','')

def correctness(actions,cases):return np.array([[actions[a][i]['prediction']==c['gold'] for a in ACTIONS] for i,c in enumerate(cases)],dtype=float)

def routes(model,x,threshold):
    delta=model.predict(x);chosen=delta.argmax(axis=1)+1;chosen[delta.max(axis=1)<=threshold]=0;return chosen

def choose(actions,selection):return [actions[ACTIONS[int(a)]][i] for i,a in enumerate(selection)]

def run(seed):
    data=json.loads((DATA_LOCAL/'data.json').read_text());p=data['parts'];model_name='deepseek/deepseek-v4.1-flash';agent=EvidenceAgent(p['train'],model_name)
    config={'seed':seed,'actions':ACTIONS,'rounds':4,'alpha_candidates':[1.,10.,100.],'threshold_candidates':[0.,.025,.075],
        'actor_cap':512,'max_inference_calls':2,'training_feedback':'Base and three counterfactual evidence reviews; only current/past train labels fit routing parameters.',
        'gate':'Proposal validation selects; independent guard requires positive net fixes.','representation':'Fixed nonlearned word/bigram hashing, 65536 dimensions; no future-data vocabulary fitting.',
        'test_used_for_selection':False}
    save(HERE/'results/router_protocol.json',config)
    actions={s:outputs(agent,p[s],s) for s in ['train','proposal','guard']}
    vec=HashingVectorizer(n_features=65536,alternate_sign=False,ngram_range=(1,2),stop_words='english',norm='l2')
    x={s:vec.transform([feature_text(c,r) for c,r in zip(p[s],actions[s]['cot'])]) for s in actions}
    y=correctness(actions['train'],p['train']);reward=y[:,1:]-y[:,0,None]
    order=list(range(len(p['train'])));random.Random(seed).shuffle(order)
    states=[None];versions=[{'round':0,'active_round':0,'guard':metrics(actions['guard']['cot'],p['guard']),'accepted':True}]
    active=None;active_idx=0;active_guard=actions['guard']['cot'];active_proposal=actions['proposal']['cot']
    for r in range(1,5):
        seen=order[:r*len(order)//4];best=(metrics(active_proposal,p['proposal'])['accuracy'],active,'unchanged');audits=[]
        for alpha in config['alpha_candidates']:
            predictor=Ridge(alpha=alpha,solver='lsqr');predictor.fit(x['train'][seen],reward[seen])
            for threshold in config['threshold_candidates']:
                policy={'model':predictor,'threshold':threshold,'training_n':len(seen),'alpha':alpha}
                selection=routes(predictor,x['proposal'],threshold);rows=choose(actions['proposal'],selection);score=metrics(rows,p['proposal'])
                audits.append({'alpha':alpha,'threshold':threshold,'proposal_correct':score['correct'],'mean_calls':float(1+np.mean(selection!=0))})
                if score['accuracy']>best[0]:best=(score['accuracy'],policy,[alpha,threshold])
        proposed=best[1]
        next_guard=actions['guard']['cot'] if proposed is None else choose(actions['guard'],routes(proposed['model'],x['guard'],proposed['threshold']))
        delta=transition(active_guard,next_guard,p['guard']);accepted=delta['fixes']>delta['regressions']
        if accepted:
            active=proposed;active_idx=r;active_guard=next_guard
            active_proposal=choose(actions['proposal'],routes(active['model'],x['proposal'],active['threshold']))
        states.append(copy.deepcopy(active))
        fingerprint=digest({'coefficients':active['model'].coef_.tolist(),'intercepts':active['model'].intercept_.tolist(),'threshold':active['threshold']}) if active else digest('base')
        versions.append({'round':r,'training_seen':len(seen),'training_member_sha256':digest([p['train'][i]['id'] for i in seen]),
            'accepted':accepted,'active_round':active_idx,'guard':metrics(active_guard,p['guard']),'guard_transition':delta,
            'selected_candidate':best[2],'candidates':audits,'routing_parameter_sha256':fingerprint})
        save(HERE/f'results/router_seed_{seed}_versions.json',versions)
        print(json.dumps({'round':r,'accepted':accepted,'guard':versions[-1]['guard']['accuracy'],'active_round':active_idx}),flush=True)
    # Equal-access static control, selected only on proposal validation.
    static=max(ACTIONS,key=lambda a:metrics(actions['proposal'][a],p['proposal'])['accuracy'])
    frozen={'seed':seed,'static_selected_action':static,'active_round':active_idx,'test_labels_used':False}
    save(HERE/f'results/router_seed_{seed}_frozen.json',frozen);joblib.dump({'states':states,'versions':versions,'vectorizer':vec},LOCAL/f'router-seed-{seed}.joblib')
    # Generate all static controls only after every routing choice is frozen.
    test_actions=outputs(agent,p['test'],'test');xt=vec.transform([feature_text(c,r) for c,r in zip(p['test'],test_actions['cot'])])
    report={'seed':seed,'test_n':len(p['test']),'model':model_name,'methods':{a:metrics(rows,p['test']) for a,rows in test_actions.items()},'round_curves':[]}
    previous=test_actions['cot'];saved={}
    for r,state in enumerate(states):
        selected=np.zeros(len(p['test']),dtype=int) if state is None else routes(state['model'],xt,state['threshold'])
        rows=choose(test_actions,selected);saved[str(r)]=rows
        report['round_curves'].append({'round':r,'score':metrics(rows,p['test']),'mean_inference_calls':float(1+np.mean(selected!=0)),
            'action_counts':{a:int((selected==i).sum()) for i,a in enumerate(ACTIONS)},**transition(previous,rows,p['test'])});previous=rows
    report['methods']['rxrsi_evidence_router']=metrics(previous,p['test']);report['methods']['validation_selected_static']=report['methods'][static]
    report['versus_static']=transition(test_actions[static],previous,p['test']);report['static_selected_action']=static
    save(LOCAL/f'router-seed-{seed}-test.json',saved);save(HERE/f'results/router_seed_{seed}.json',report);print(json.dumps(report),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--seed',type=int,default=42);a=parser.parse_args();run(a.seed)
