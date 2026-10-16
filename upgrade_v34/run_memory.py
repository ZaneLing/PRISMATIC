"""Four feedback rounds with disjoint development roles and frozen transfer.

Independent-task evaluation is permitted only after all three seed runs freeze.
No test outcome is used to decide whether to accept a skill update.
"""
import argparse
import copy
import json
import random
from datetime import datetime,timezone
from run_comparators import prepare,save,sha,HERE,RUN
from public_client import digest
from scoped_memory import ScopedMemory,propose


def batch(cases,cards,train,folder):
    path=folder/(digest({'cards':cards,'cases':[c['id'] for c in cases]})+'.json')
    if path.exists():return json.loads(path.read_text())
    rows=ScopedMemory(train,cards).batch(cases)
    save(path,rows);return rows


def metrics(rows,cases):
    assert [r['case_id'] for r in rows]==[c['id'] for c in cases]
    return {'n':len(cases),'correct':sum(r['prediction']==c['gold'] for r,c in zip(rows,cases)),
            'invalid':sum(r['prediction'] is None for r in rows),
            'activated':sum(bool(r['selected_card_indices']) for r in rows),
            'calls':sum(len(r['calls']) for r in rows),
            'input_tokens':sum(x['input_tokens'] for r in rows for x in r['calls']),
            'output_tokens':sum(x['output_tokens'] for r in rows for x in r['calls']),
            'cost_usd':sum(x.get('cost_usd') or 0 for r in rows for x in r['calls']),
            'predictions_sha256':digest([{'case_id':r['case_id'],'prediction':r['prediction']} for r in rows])}


def transition(before,after,cases):
    a=[r['prediction']==c['gold'] for r,c in zip(before,cases)]
    b=[r['prediction']==c['gold'] for r,c in zip(after,cases)]
    return {'fixes':sum(not x and y for x,y in zip(a,b)), 'regressions':sum(x and not y for x,y in zip(a,b))}


def main():
    p=argparse.ArgumentParser();p.add_argument('--seed',type=int,choices=[42,137,2026],default=42)
    p.add_argument('--stage',choices=['learn','transfer'],default='learn');a=p.parse_args()
    data,_=prepare();parts=data['parts'];protocol_path=HERE/'memory_protocol.json'
    if not protocol_path.exists():
        assert a.stage=='learn'
        save(protocol_path,{'created_utc':datetime.now(timezone.utc).isoformat(),
            'learning_seeds':[42,137,2026],'cases_seen':[0,156,312,468,625],
            'proposer':'At most2 cards/round from training mistakes and nearest training successes; explicit support and counterexample bindings.',
            'runtime':'TF-IDF shortlist4 cards, semantic selection at most2, positive activation quote must be exact input substring. The model checks negative conditions; this is not a verified clinical rule engine.',
            'updates':'Append procedural cards only; no model-weight, tool-source or optimizer-code update.',
            'gate':'Strictly more correct on190 proposal with no invalid-count increase, then strictly more correct on197 guard with no invalid-count increase. Keep incumbent otherwise.',
            'tokens':{'router':512,'actor':1024,'proposer':2048},
            'controls':'Empty memory uses identical1024-token actor; needs separate matched-budget/refinement and equal-data retrieval controls before superiority claim.',
            'independent_transfer':'Freeze all three seed trajectories before evaluating pre-frozen200 MedQA cases. Report every retained round, no test-driven selection.',
            'exposure':'RxSafe development reused historically; MedQA task frozen before learning, no new task labels used for updates.',
            'code_sha256':sha(HERE/'scoped_memory.py'),'runner_sha256':sha(HERE/'run_memory.py')})
    protocol=json.loads(protocol_path.read_text())
    assert protocol['code_sha256']==sha(HERE/'scoped_memory.py')
    assert protocol['runner_sha256']==sha(HERE/'run_memory.py')
    folder=RUN/'memory'/str(a.seed);folder.mkdir(parents=True,exist_ok=True)
    states_path=folder/'states.json';history_path=folder/'training_feedback.json'
    if a.stage=='transfer':
        frozen=[HERE/'results'/f'memory-seed{s}.json' for s in protocol['learning_seeds']]
        assert all(p.exists() and json.loads(p.read_text())['status']=='frozen' for p in frozen), 'Freeze all learning seeds first'
        freeze=HERE/'results/independent_transfer_freeze.json'
        expected={str(p.name):sha(p) for p in frozen}
        if freeze.exists():assert json.loads(freeze.read_text())['seed_artifacts']==expected
        else:save(freeze,{'created_utc':datetime.now(timezone.utc).isoformat(),'seed_artifacts':expected,'case_manifest':json.loads((HERE/'protocol.json').read_text())['independent_task']})
        cases=json.loads((RUN/'independent_medqa.json').read_text());states=json.loads(states_path.read_text());report=[]
        prior=None
        for s in states:
            rows=batch(cases,s['cards'],parts['train'],folder/'transfer')
            report.append({'round':s['round'],'cases_seen':s['cases_seen'],'skills':len(s['cards']),
                'state_sha256':digest(s['cards']),'metrics':metrics(rows,cases),
                'transition':transition(prior,rows,cases) if prior else None})
            prior=rows;print(json.dumps({'seed':a.seed,'transfer_round':s['round'],'metrics':report[-1]['metrics']}),flush=True)
        save(HERE/'results'/f'transfer-seed{a.seed}.json',{'status':'complete','seed':a.seed,'rounds':report});return
    train=list(parts['train']);random.Random(a.seed).shuffle(train)
    states=json.loads(states_path.read_text()) if states_path.exists() else []
    feedback=json.loads(history_path.read_text()) if history_path.exists() else []
    if not states:
        before=batch(parts['proposal'],[],train,folder/'development')
        guard=batch(parts['guard'],[],train,folder/'development')
        states=[{'round':0,'cases_seen':0,'cards':[],'proposal':metrics(before,parts['proposal']),'guard':metrics(guard,parts['guard'])}]
        save(states_path,states)
    for round_index,(start,end) in enumerate([(0,156),(156,312),(312,468),(468,625)],1):
        if len(states)>round_index:continue
        old=states[-1]['cards'];block=train[start:end]
        rows=batch(block,old,train,folder/'training')
        # Reconstruct the complete feedback prefix for resumability.
        feedback=[r for r in feedback if r['case_id'] not in {c['id'] for c in block}]+rows
        save(history_path,feedback)
        proposal_path=folder/f'proposal-{round_index}.json'
        if proposal_path.exists():candidate=json.loads(proposal_path.read_text())['cards']
        else:
            candidate,receipt=propose(train[:end],feedback,old,a.seed,round_index)
            save(proposal_path,{'cards':candidate,'receipt':receipt})
        before=batch(parts['proposal'],old,train,folder/'development')
        after=batch(parts['proposal'],candidate,train,folder/'development')
        b=metrics(before,parts['proposal']);m=metrics(after,parts['proposal'])
        proposal_pass=m['correct']>b['correct'] and m['invalid']<=b['invalid']
        accepted=False;guard_delta=None;gm=states[-1]['guard']
        if proposal_pass:
            g0=batch(parts['guard'],old,train,folder/'development');g1=batch(parts['guard'],candidate,train,folder/'development')
            gb=metrics(g0,parts['guard']);gm=metrics(g1,parts['guard'])
            guard_delta=transition(g0,g1,parts['guard'])
            accepted=gm['correct']>gb['correct'] and gm['invalid']<=gb['invalid']
        state={'round':round_index,'cases_seen':end,'cards':candidate if accepted else old,
               'candidate_cards':candidate,'accepted':accepted,'proposal_pass':proposal_pass,
               'candidate_proposal':m,'proposal':m if accepted else b,
               'proposal_transition':transition(before,after,parts['proposal']),
               'guard':gm if accepted else states[-1]['guard'],'candidate_guard':gm if proposal_pass else None,
               'guard_transition':guard_delta}
        states.append(state);save(states_path,states)
        save(HERE/'results'/f'memory-seed{a.seed}-progress.json',{'seed':a.seed,'rounds':[{k:v for k,v in x.items() if k not in ('cards','candidate_cards')} for x in states]})
        print(json.dumps({'seed':a.seed,'round':round_index,'candidate_cards':len(candidate),'retained_cards':len(state['cards']),'accepted':accepted,'proposal':m,'guard_transition':guard_delta}),flush=True)
    save(HERE/'results'/f'memory-seed{a.seed}.json',{'status':'frozen','seed':a.seed,
        'frozen_utc':datetime.now(timezone.utc).isoformat(),'protocol_sha256':sha(protocol_path),
        'rounds':[{**{k:v for k,v in s.items() if k not in ('cards','candidate_cards')},
                   'cards':s['cards'],'state_sha256':digest(s['cards'])} for s in states]})


if __name__=='__main__':main()
