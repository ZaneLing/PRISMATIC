"""Develop scoped language skills; unchanged cases retain the exact base prompt."""
import argparse,copy,json,random,re,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'upgrade_v8'))
from public_client import LOCAL,request,json_object,digest
from agent import Agent,empty_state,metrics,transition

STOP={'patient','doctor','drug','medication','option','treatment','condition','choose','select'}

def terms(values):
    return list(dict.fromkeys(str(t).strip().lower() for t in values if isinstance(t,str) and 3<=len(t.strip())<=60 and t.strip().lower() not in STOP))[:8] if isinstance(values,list) else []

def normalize_card(c):
    if not isinstance(c,dict):return None
    all_terms=terms(c.get('all_terms',[]));any_terms=terms(c.get('any_terms',[]))
    rule=c.get('rule');name=c.get('id')
    if not isinstance(rule,str) or not rule.strip() or not (all_terms or any_terms):return None
    return {'id':str(name or 'skill')[:80],'all_terms':all_terms,'any_terms':any_terms,'rule':rule.strip()[:1000]}

def matches(card,text):
    text=text.casefold()
    def hit(t):return re.search(r'(?<!\w)'+re.escape(t.casefold())+r'(?!\w)',text) is not None
    return all(hit(t) for t in card['all_terms']) and (not card['any_terms'] or any(hit(t) for t in card['any_terms']))

class ScopedAgent(Agent):
    def solve(self,c,state,method='cot',initial=None):
        cards=state.get('cards',[]);active=[s for s in cards if matches(s,self.context(c))][:2]
        runtime=empty_state();runtime['skills']=[{'id':s['id'],'text':s['rule']} for s in active]
        out=super().solve(c,runtime,method,initial);out['scoped_skill_ids']=[s['id'] for s in active]
        out['persistent_state_sha256']=digest(state)
        return out

def proposals(state,block,rows,model,round_id):
    failed=[(c,r) for c,r in zip(block,rows) if r['prediction']!=c['gold']]
    passed=[(c,r) for c,r in zip(block,rows) if r['prediction']==c['gold']]
    sample=sorted(failed,key=lambda z:digest([round_id,z[0]['id']]))[:8]+sorted(passed,key=lambda z:digest([round_id,z[0]['id']]))[:4]
    feedback=[{'dialogue':c['dialogue'][:2000],'options':c['options'],'prediction':r['prediction'],'reference':c['gold'],'correct':r['prediction']==c['gold'],'evidence':r.get('evidence','')[:350]} for c,r in sample]
    prompt='''Improve a medication-choice agent from these training failures and successes. Propose four distinct, narrowly applicable reusable skill edits. A skill is injected ONLY when every all_terms phrase and at least one any_terms phrase occur as whole phrases in the current patient dialogue or options (an empty list imposes no condition). At least one list must be nonempty. Generic terms such as patient, drug, option and choose are prohibited. Use observable risk factors or drug/condition terms; include synonyms in any_terms when helpful. Match applicability before changing the decision. Preserve successful reasoning. Do not memorize answer letters, case IDs, hidden facts or item positions. Prefer a concrete conditional decision rule over general reminders. Do not fabricate medical facts from missing information. Each edit adds or replaces one card by id. Do not propose executable code.
Return JSON only: {"diagnosis":"brief", "edits":[{"id":"name","all_terms":[],"any_terms":[],"rule":"conditional decision procedure"}]}.
Current cards:
'''+json.dumps(state['cards'])+'\nTraining feedback:\n'+json.dumps(feedback)
    record=request([{'role':'user','content':prompt}],model,3072,'scoped_rsi_proposer',temperature=.7,cache_salt=['scoped-rsi',round_id,digest(state),digest(feedback)])
    parsed=json_object(record['raw']);edits=parsed.get('edits',[]) if isinstance(parsed,dict) else [];out=[]
    for raw in edits[:4]:
        card=normalize_card(raw)
        if card is None:continue
        cards=[s for s in state['cards'] if s['id']!=card['id']]
        if len(cards)>=6:continue
        out.append({'cards':cards+[card]})
    return out,record

def save(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

def run(seed):
    data=json.loads((LOCAL/'data.json').read_text());p=data['parts'];model='deepseek/deepseek-v4.1-flash';agent=ScopedAgent(p['train'],model)
    train=list(p['train']);random.Random(seed).shuffle(train);blocks=[train[i*len(train)//4:(i+1)*len(train)//4] for i in range(4)]
    folder=LOCAL/f'scoped-rsi-seed-{seed}';folder.mkdir(exist_ok=True);(HERE/'results').mkdir(exist_ok=True)
    path=folder/'versions.json';versions=json.loads(path.read_text()) if path.exists() else []
    state=versions[-1]['active'] if versions else {'cards':[]}
    if not versions:
        versions=[{'round':0,'active':state,'state_sha256':digest(state),'guard':metrics(agent.batch(p['guard'],state),p['guard']),'accepted':True}];save(path,versions)
    for r,block in enumerate(blocks,1):
        if len(versions)>r:continue
        old=copy.deepcopy(state);train_rows=agent.batch(block,old);candidates,record=proposals(old,block,train_rows,model,[seed,r])
        val_before=agent.batch(p['proposal'],old);best=(metrics(val_before,p['proposal'])['accuracy'],old,'unchanged');audits=[]
        for idx,candidate in enumerate(candidates):
            rows=agent.batch(p['proposal'],candidate);m=metrics(rows,p['proposal'])
            audits.append({'candidate':candidate,'metrics':m,'transition':transition(val_before,rows,p['proposal']),'activated_cases':sum(bool(x['scoped_skill_ids']) for x in rows)})
            if m['accuracy']>best[0]:best=(m['accuracy'],candidate,idx)
        guard_before=agent.batch(p['guard'],old);guard_after=agent.batch(p['guard'],best[1]);delta=transition(guard_before,guard_after,p['guard'])
        accepted=delta['fixes']>delta['regressions']
        if accepted:state=copy.deepcopy(best[1])
        version={'round':r,'training_seen':sum(len(x) for x in blocks[:r]),'active':state,'state_sha256':digest(state),'accepted':accepted,
          'guard_transition':delta,'guard':metrics(guard_after if accepted else guard_before,p['guard']),'selected_candidate':best[2],
          'candidate_audit':audits,'proposal_record':record}
        versions.append(version);save(path,versions);save(HERE/f'results/scoped_rsi_seed_{seed}_versions.json',versions)
        print(json.dumps({'round':r,'accepted':accepted,'guard':version['guard']['accuracy'],'skills':len(state['cards'])}),flush=True)
    save(HERE/f'results/scoped_rsi_seed_{seed}_frozen.json',{'state_sha256':digest(state),'test_feedback_used':False})
    report={'seed':seed,'model':model,'methods':{},'round_curves':[]}
    base=agent.batch(p['test'],{'cards':[]});prior=base
    for v in versions:
        rows=agent.batch(p['test'],v['active']);report['round_curves'].append({'round':v['round'],'score':metrics(rows,p['test']),**transition(prior,rows,p['test'])});prior=rows
    final=prior;report['methods']['cot']=metrics(base,p['test']);report['methods']['scoped_rsi']=metrics(final,p['test']);report['test_transition']=transition(base,final,p['test'])
    save(folder/'test.json',{'cot':base,'scoped_rsi':final})
    # Exact same learned cards, remove only runtime applicability routing.
    unscoped=empty_state();unscoped['skills']=[{'id':s['id'],'text':s['rule']} for s in state['cards']]
    ordinary=Agent(p['train'],model);rr=ordinary.batch(p['test'],unscoped);report['methods']['same_cards_without_routing']=metrics(rr,p['test']);save(folder/'unscoped-test.json',rr)
    tr=data['transfer'];tr0=agent.batch(tr,{'cards':[]});tr1=agent.batch(tr,state)
    report['rxqa_transfer']={'cot':metrics(tr0,tr),'scoped_rsi':metrics(tr1,tr),'change':transition(tr0,tr1,tr)}
    save(folder/'transfer.json',{'cot':tr0,'scoped_rsi':tr1});save(HERE/f'results/scoped_rsi_seed_{seed}.json',report)
    print(json.dumps(report),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seed',type=int,default=42);a=p.parse_args();run(a.seed)
