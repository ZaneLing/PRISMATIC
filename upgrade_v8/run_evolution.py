"""Run multiple published-mechanism adaptations and RxRSI, with persistent versions."""
import argparse,copy,json,random,time
from pathlib import Path
from public_client import LOCAL,digest
from agent import Agent,empty_state,metrics,transition,propose
HERE=Path(__file__).resolve().parent
EVOLVERS=['reflexion_adapt','grasp_adapt','evotool_adapt','rxrsi']

def save(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')

def run(seed,methods,test_limit=None):
    config=json.loads((HERE/'protocol.json').read_text());data=json.loads((LOCAL/'data.json').read_text());p=data['parts']
    agent=Agent(p['train'],config['backbone']);train=list(p['train']);random.Random(seed).shuffle(train)
    blocks=[train[i*len(train)//4:(i+1)*len(train)//4] for i in range(4)]
    out=LOCAL/f'seed-{seed}';out.mkdir(exist_ok=True)
    # Every method evolves before any method is scored on test by this run.
    for method in [m for m in methods if m in EVOLVERS]:
        path=out/(method+'-versions.json');versions=json.loads(path.read_text()) if path.exists() else []
        state=versions[-1]['active'] if versions else empty_state()
        if not versions:
            vp=agent.batch(p['proposal'],state);vg=agent.batch(p['guard'],state)
            versions=[{'round':0,'active':state,'state_sha256':digest(state),'proposal':metrics(vp,p['proposal']),'guard':metrics(vg,p['guard']),
                       'accepted':True,'memory_cases':0}];save(path,versions)
        for r,block in enumerate(blocks,1):
            if len(versions)>r:continue
            old=copy.deepcopy(state);before=agent.batch(block,old)
            if method=='rxrsi':
                candidates,proposal_record=propose(method,old,block,before,agent,r)
                seen_ids=[c['id'] for bs in blocks[:r] for c in bs]
                for candidate in candidates:
                    if candidate['memory_ids']!=old['memory_ids']:candidate['memory_ids']=seen_ids
            else:
                # Give each comparator the same four-candidate evaluation budget.
                # It may spend more proposal tokens; all usage is retained.
                candidates=[];proposal_record=[]
                for mutation in range(4):
                    cs,pr=propose(method,old,block,before,agent,r*17+mutation)
                    candidates.extend(cs);proposal_record.append(pr)
            prev_val=agent.batch(p['proposal'],old);best=(metrics(prev_val,p['proposal'])['accuracy'],old,prev_val,'unchanged')
            candidate_audit=[]
            for idx,candidate in enumerate(candidates):
                rows=agent.batch(p['proposal'],candidate);m=metrics(rows,p['proposal'])
                candidate_audit.append({'index':idx,'state_sha256':digest(candidate),'score':m,'delta':transition(prev_val,rows,p['proposal'])})
                if m['accuracy']>best[0]:best=(m['accuracy'],candidate,rows,idx)
            old_guard=agent.batch(p['guard'],old);new_guard=agent.batch(p['guard'],best[1]);delta=transition(old_guard,new_guard,p['guard'])
            accepted=delta['fixes']>delta['regressions']
            if accepted:state=copy.deepcopy(best[1])
            changes={k:{'before_sha256':digest(old[k]),'after_sha256':digest(state[k]),'changed':old[k]!=state[k]} for k in state}
            version={'round':r,'training_seen':sum(map(len,blocks[:r])),'active':state,'state_sha256':digest(state),
               'accepted':accepted,'selected_proposal':best[3],'candidates':candidate_audit,'guard_transition':delta,
               'proposal':metrics(best[2],p['proposal']),'guard':metrics(new_guard if accepted else old_guard,p['guard']),
               'artifact_changes':changes,'memory_cases':len(state['memory_ids']),
               'proposal_record':proposal_record,'training_feedback_count':len(block)}
            versions.append(version);save(path,versions)
            save(HERE/f'results/{method}_seed_{seed}_versions.json',versions)
            print(json.dumps({'method':method,'seed':seed,'round':r,'accepted':accepted,'guard':version['guard']['accuracy'],'changes':{k:v['changed'] for k,v in changes.items()}}),flush=True)
    # Freeze chosen artifacts before held-out evaluations.
    manifest={m:json.loads((out/(m+'-versions.json')).read_text())[-1]['state_sha256'] for m in methods if m in EVOLVERS}
    save(HERE/f'results/frozen_seed_{seed}.json',{'states':manifest,'test_feedback_used':False,'protocol_sha256':digest(config)})
    test=p['test'] if not test_limit else p['test'][:test_limit]
    report={'seed':seed,'test_n':len(test),'model':config['backbone'],'methods':{},'round_curves':{}}
    for method in methods:
        if method in EVOLVERS:
            versions=json.loads((out/(method+'-versions.json')).read_text());state=versions[-1]['active']
        elif method=='case_rag':state=empty_state();state['memory_ids']=[c['id'] for c in train]
        else:state=empty_state()
        rows=agent.batch(test,state,method);report['methods'][method]=metrics(rows,test);save(out/(method+'-test.json'),rows)
        print(json.dumps({'method':method,'test':report['methods'][method]}),flush=True)
        if method in EVOLVERS:
            curve=[];prior=None
            for v in versions:
                current=agent.batch(test,v['active']);entry={'round':v['round'],'state_sha256':v['state_sha256'],'score':metrics(current,test)}
                if prior is not None:entry.update(transition(prior,current,test))
                curve.append(entry);prior=current
            report['round_curves'][method]=curve
        if method=='rxrsi':
            report['ablations']={}
            for name,field in [('without_memory','memory_ids'),('without_skills','skills'),('without_tool_update','focus_terms')]:
                ab=copy.deepcopy(state);ab[field]=[];rr=agent.batch(test,ab);report['ablations'][name]=metrics(rr,test);save(out/(name+'-test.json'),rr)
            # Transfer labels are evaluated only after evolution is frozen.
            transfer=data['transfer'];rr=agent.batch(transfer,state);base=agent.batch(transfer,empty_state())
            report['rxqa_transfer']={'rxrsi':metrics(rr,transfer),'cot':metrics(base,transfer),'change':transition(base,rr,transfer)}
            save(out/'rxqa-transfer.json',{'rxrsi':rr,'cot':base})
        save(HERE/f'results/public_results_seed_{seed}.json',report)
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--seed',type=int,default=42);parser.add_argument('--methods',nargs='+',default=['direct','cot','self_refine','case_rag']+EVOLVERS);parser.add_argument('--test-limit',type=int)
    a=parser.parse_args();run(a.seed,a.methods,a.test_limit)
