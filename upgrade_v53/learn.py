"""Learn a bounded executable memory from development errors, never audit labels."""
import copy,random,json
from collections import Counter,defaultdict
from common53 import *
from programs import *
from runtime_decoder import decode
def err(pred,cs):return [sum(counts(p,c['gold'])[j] for p,c in zip(pred,cs)) for j in range(3)]
def diff(a,b):return [x-y for x,y in zip(a,b)]
def pareto(d):return max(d)<=0 and sum(d)<0
def load_development():
    cs={s:json.loads((DEV/(s+'.json')).read_text()) for s in ['reflection','proposal','guard']}
    base={s:[decode(r['receipt']['raw'],c)['orders'] for r,c in zip(json.loads((DEV/('qwen-'+s+'.json')).read_text()),cases)] for s,cases in cs.items()}
    return cs,base
def templates(cases):
    # Count distinct patients, not repeated rows. Fully observed joint fields only.
    freq=Counter(k for c in cases for k in {key(o) for o in c['gold'] if all(o.get(f) for f in FIELDS)})
    return [dict(zip(FIELDS,k)) for k,n in sorted(freq.items()) if n>=3]
def candidates(cases,current,state):
    scope=defaultdict(list)
    for i,c in enumerate(cases):
        for f in diagnosis_features(c):scope[f].append(i)
    tuples=defaultdict(list)
    for o in templates(cases):tuples[o['drug_code']].append(o)
    codes=sorted({o['drug_code'] for p in current for o in p}|set(tuples))
    out=[];existing={digest({k:v for k,v in card.items() if k in ['when','unless','op','drug_code','template']}) for card in state}
    oldcounts=[counts(p,c['gold'])[:3] for p,c in zip(current,cases)]
    for code in codes:
        feat=[features(c,code) for c in cases]
        actions=[dict(op='remove',drug_code=code,template=None)]
        actions += [dict(op=op,drug_code=code,template=o) for o in tuples[code] for op in ['add','replace']]
        for action in actions:
            changed=[operate(p,action) for p in current]
            ds=[diff(counts(a,c['gold'])[:3],b) for a,b,c in zip(changed,oldcounts,cases)]
            for condition,idx in sorted(scope.items()):
                if len(idx)<4:continue
                for prior in [None,'prior_record:present','prior_record:absent']:
                    active=[i for i in idx if prior is None or prior in feat[i]]
                    if len(active)<4:continue
                    harmful=[i for i in active if max(ds[i])>0]
                    exc=Counter(f for i in harmful for f in feat[i] if f!=condition and f!=prior)
                    for exception in [None]+sorted(f for f,n in exc.items() if n>=2):
                        use=[i for i in active if exception is None or exception not in feat[i]]
                        if len(use)<4:continue
                        d=[sum(ds[i][j] for i in use) for j in range(3)]
                        helpful=[i for i in use if max(ds[i])<=0 and sum(ds[i])<0]
                        if not pareto(d) or len(helpful)<3:continue
                        card=dict(action,when=[condition]+([prior] if prior else []),unless=[exception] if exception else [])
                        if digest(card) in existing:continue
                        protected=[i for i in harmful if exception and exception in feat[i]]
                        out.append(dict(card=card,training_delta=d,active=len(use),helpful=len(helpful),harmful=sum(max(ds[i])>0 for i in use),counterexamples=len(protected),support_cases=[cases[i]['case_id'] for i in helpful],counterexample_cases=[cases[i]['case_id'] for i in protected]))
    return out
def learn(seed,shuffle=False):
    splits,base=load_development()
    if shuffle:
        truth=[c['gold'] for c in splits['reflection']];perm=list(range(len(truth)));random.Random(7353).shuffle(perm)
        splits=copy.deepcopy(splits)
        for i,c in enumerate(splits['reflection']):c['gold']=truth[perm[i]]
    order=list(range(len(splits['reflection'])));random.Random(seed).shuffle(order)
    state=[];states=[[]];history=[];rejected=set()
    for rnd in range(1,7):
        ids=order[:32*rnd];seen=[splits['reflection'][i] for i in ids];initial=[base['reflection'][i] for i in ids]
        current=predict(seen,initial,state);proposals=candidates(seen,current,state)
        pp=predict(splits['proposal'],base['proposal'],state);gg=predict(splits['guard'],base['guard'],state)
        pe=err(pp,splits['proposal']);ge=err(gg,splits['guard']);passing=[]
        for item in proposals:
            sig=digest([state,item['card']])
            if sig in rejected:continue
            pd=diff(err(predict(splits['proposal'],pp,[item['card']]),splits['proposal']),pe)
            if pareto(pd):passing.append(dict(item,proposal_delta=pd))
        passing.sort(key=lambda x:(sum(x['proposal_delta']),sum(x['training_delta']),len(x['card']['unless']),digest(x['card'])))
        attempts=[];accepted=None
        for item in passing[:3]:
            after=predict(splits['guard'],gg,[item['card']]);gd=diff(err(after,splits['guard']),ge)
            lost=sum(counts(a,c['gold'])[0]>counts(b,c['gold'])[0] for a,b,c in zip(after,gg,splits['guard']))
            changed=sum(set(map(key,a))!=set(map(key,b)) for a,b in zip(after,gg))
            ok=max(gd)<=0 and lost==0 and changed>0
            attempts.append(dict(card_hash=digest(item['card']),op=item['card']['op'],exceptions=bool(item['card']['unless']),guard_delta=gd,guard_omission_harmed=lost,changed=changed,accepted=ok))
            if ok:
                accepted=item;state=state+[dict(item['card'],round=rnd,seen=len(seen),support=item['helpful'],counterexamples=item['counterexamples'])];break
            rejected.add(digest([state,item['card']]))
        states.append(copy.deepcopy(state))
        row=dict(round=rnd,seen=len(seen),skills=len(state),candidates=len(proposals),proposal_pass=len(passing),attempts=attempts,accepted_hash=digest(accepted['card']) if accepted else None,accepted_op=accepted['card']['op'] if accepted else None,retained_counterexample_skills=sum(bool(c['unless']) for c in state),training_errors=err(predict(seen,initial,state),seen),proposal_errors=err(predict(splits['proposal'],base['proposal'],state),splits['proposal']),guard_errors=err(predict(splits['guard'],base['guard'],state),splits['guard']))
        history.append(row)
        if accepted:save(PRIVATE/(f'{seed}-'+('shuffled-' if shuffle else '')+f'evidence-{rnd}.json'),accepted)
        print(json.dumps({k:row[k] for k in ['round','seen','skills','candidates','proposal_pass','accepted_op']}),flush=True)
    name=str(seed)+('-shuffled' if shuffle else '')
    save(PRIVATE/(name+'-states.json'),states)
    save(HERE/'results'/(name+'-learning.json'),dict(seed=seed,shuffled_reflection=shuffle,history=history,states_sha256=sha(PRIVATE/(name+'-states.json')),private_rule_bodies=True,audit_used=False))
if __name__=='__main__':
    PRIVATE.mkdir(exist_ok=True)
    for seed in [53,153,253]:learn(seed)
    learn(53,True)
    save(PRIVATE/'learning_lock.json',dict(protocol=sha(HERE/'protocol.json'),code={p.name:sha(p) for p in HERE.glob('*.py')},states={p.name:sha(p) for p in PRIVATE.glob('*-states.json')},audit_predictions_present=any(PRIVATE.glob('*-audit.json'))))
