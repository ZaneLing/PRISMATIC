"""No-network gate ablation with complete cached tool traces and fixed resources."""
import copy,json,random,sys
from pathlib import Path
import joblib,numpy as np
from scipy.sparse import vstack
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import Ridge
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'upgrade_v11'))
from run_router_evolution import feature_text
from agent import metrics,transition
from public_client import digest,LOCAL as DATA_LOCAL
from evidence_tool import LOCAL
ACTIONS=['cot','balanced','safety']

def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def choose(rows,sel):return [rows[ACTIONS[int(a)]][i] for i,a in enumerate(sel)]
def route(state,x):
    if state is None:return np.zeros(x.shape[0],dtype=int)
    d=state['model'].predict(x);r=d.argmax(1)+1;r[d.max(1)<=state['threshold']]=0;return r

def run():
    (HERE/'results').mkdir(exist_ok=True);p=json.loads((DATA_LOCAL/'data.json').read_text())['parts']
    outputs={s:{k:v for k,v in json.loads((LOCAL/(s+'-review-actions.json')).read_text()).items() if k in ACTIONS} for s in p}
    for split,actions in outputs.items():
        assert set(actions)==set(ACTIONS)
        for rows in actions.values():
            assert not any(r.get('error') for r in rows)
            assert [r['case_id'] for r in rows]==[c['id'] for c in p[split]]
    protocol={'network_calls':0,'seeds':[42,137,2026],'gates':['independent_guard','joint_validation'],
        'actions':ACTIONS,'excluded_action':'indication, because 153 test requests are unavailable after HTTP 402; no observed accuracy is used to justify exclusion.',
        'purpose':'Matched action-set gate ablation; a development extension, not untouched confirmation.',
        'primary_difference':'Same 387 development labels; two-stage 190/197 selection versus pooled selection. All method choices freeze before this script scores test labels.'}
    save(HERE/'protocol.json',protocol)
    vec=HashingVectorizer(n_features=65536,alternate_sign=False,ngram_range=(1,2),stop_words='english',norm='l2')
    x={s:vec.transform([feature_text(c,r) for c,r in zip(p[s],outputs[s]['cot'])]) for s in p}
    combo=p['proposal']+p['guard'];cx=vstack([x['proposal'],x['guard']]);co={a:outputs['proposal'][a]+outputs['guard'][a] for a in ACTIONS}
    correct=np.array([[outputs['train'][a][i]['prediction']==c['gold'] for a in ACTIONS] for i,c in enumerate(p['train'])],dtype=float)
    reward=correct[:,1:]-correct[:,0,None];saved={};decisions={};static=max(ACTIONS,key=lambda a:metrics(co[a],combo)['accuracy'])
    for seed in protocol['seeds']:
        order=list(range(len(p['train'])));random.Random(seed).shuffle(order)
        fitted={}
        for r in range(1,5):
            ix=order[:r*len(order)//4]
            for alpha in [1.,10.,100.]:
                clf=Ridge(alpha=alpha,solver='lsqr');clf.fit(x['train'][ix],reward[ix]);fitted[r,alpha]=clf
        for gate in protocol['gates']:
            active=None;states=[None];journal=[]
            select_cases,select_x,select_outputs=(combo,cx,co) if gate=='joint_validation' else (p['proposal'],x['proposal'],outputs['proposal'])
            for r in range(1,5):
                old_select=choose(select_outputs,route(active,select_x));best=(metrics(old_select,select_cases)['accuracy'],active,None)
                for alpha in [1.,10.,100.]:
                    for threshold in [0.,.025,.075]:
                        state={'model':fitted[r,alpha],'threshold':threshold,'alpha':alpha,'trained_n':r*len(order)//4}
                        rows=choose(select_outputs,route(state,select_x));score=metrics(rows,select_cases)['accuracy']
                        if score>best[0]:best=(score,state,[alpha,threshold])
                guard_before=choose(outputs['guard'],route(active,x['guard']));guard_after=choose(outputs['guard'],route(best[1],x['guard']));gd=transition(guard_before,guard_after,p['guard'])
                merged_before=choose(co,route(active,cx));merged_after=choose(co,route(best[1],cx));md=transition(merged_before,merged_after,combo)
                accept=(md if gate=='joint_validation' else gd)['fixes']>(md if gate=='joint_validation' else gd)['regressions']
                if accept:active=best[1]
                states.append(copy.deepcopy(active));journal.append({'round':r,'training_seen':r*len(order)//4,'accepted':accept,
                    'selection':best[2],'guard_transition':gd,'pooled_transition':md,'active_training_n':active['trained_n'] if active else 0,
                    'parameter_sha256':digest({'coef':active['model'].coef_.tolist(),'intercept':active['model'].intercept_.tolist(),'threshold':active['threshold']}) if active else digest('base')})
            key=f'{gate}_seed_{seed}';saved[key]=states;decisions[key]=journal
    save(HERE/'results/frozen_decisions.json',{'decisions':decisions,'static_control':static,'test_feedback_used':False});joblib.dump(saved,LOCAL/'gate-audit-v12-states.joblib')
    results={'methods':{a:metrics(rows,p['test']) for a,rows in outputs['test'].items()},'static_selected_action':static,'runs':{}}
    preds={}
    for key,states in saved.items():
        curve=[];previous=outputs['test']['cot'];preds[key]=[]
        for r,state in enumerate(states):
            sel=route(state,x['test']);rows=choose(outputs['test'],sel);curve.append({'round':r,'score':metrics(rows,p['test']),
                'mean_calls':float(1+np.mean(sel!=0)),'action_counts':{a:int((sel==i).sum()) for i,a in enumerate(ACTIONS)},**transition(previous,rows,p['test'])});preds[key].append(rows);previous=rows
        results['runs'][key]={'curve':curve,'final':curve[-1]['score'],'versus_static':transition(outputs['test'][static],previous,p['test'])}
    save(LOCAL/'gate-audit-v12-predictions.json',preds);save(HERE/'results/gate_audit.json',results)
    print(json.dumps({'static':static,'final_correct':{k:v['final']['correct'] for k,v in results['runs'].items()},'test_n':988}),flush=True)

if __name__=='__main__':run()
