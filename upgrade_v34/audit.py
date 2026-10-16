"""Independently recount method outputs, update gates and frozen task curves."""
import json
import random
import re
import sys
import collections
import numpy as np
from run_comparators import HERE,RUN,LOCAL,save,sha
from public_client import digest
from medical_agents import parse_answer


def correctness(rows,cases):
    assert [r['case_id'] for r in rows]==[c['id'] for c in cases]
    return np.array([r['prediction']==c['gold'] for r,c in zip(rows,cases)],dtype=int)


def interval(before,after,cases):
    diff=after-before;groups=collections.defaultdict(list)
    for i,c in enumerate(cases):groups[c.get('group_id',c['id'])].append(i)
    idx=list(groups.values());sums=np.array([diff[g].sum() for g in idx]);sizes=np.array([len(g) for g in idx])
    rng=np.random.default_rng(34);draws=[]
    for _ in range(4000):
        sampled=rng.integers(0,len(idx),len(idx));draws.append(sums[sampled].sum()/sizes[sampled].sum())
    return {'difference':float(diff.mean()),'ci95':np.quantile(draws,[.025,.975]).tolist(),
            'fixes':int((diff==1).sum()),'regressions':int((diff==-1).sum())}


def verify_receipts(rows):
    for r in rows:
        for call in r['calls']:
            assert not call.get('error')
            cached=json.loads((LOCAL/'cache'/(call['request_sha256']+'.json')).read_text())
            assert all(cached[k]==call[k] for k in ('raw','input_tokens','output_tokens','model_returned'))


def main():
    data=json.loads((LOCAL/'data.json').read_text());protocol=json.loads((HERE/'protocol.json').read_text())
    assert protocol['adapter_sha256']==sha(HERE/'medical_agents.py')
    result={'status':'audited_available_results','author_methods':{},'learning':{},'transfer':{},
            'audit_sha256':sha(HERE/'audit.py'),'protocol_sha256':sha(HERE/'protocol.json'),
            'interval_note':'Exploratory paired bootstrap4000 draws, scenario clusters on RxSafe, items on MedQA/RxQA; no multiplicity adjustment.'}
    for method in ('medagents','mdagents'):
        result['author_methods'][method]={}
        for split in ('proposal','test','rxqa','medqa'):
            report_path=HERE/'results'/f'{method}-{split}.json'
            if not report_path.exists():continue
            d=json.loads(report_path.read_text())
            cases=json.loads((RUN/'independent_medqa.json').read_text()) if split=='medqa' else data['transfer'] if split=='rxqa' else data['parts'][split]
            rows=[json.loads((RUN/method/split/(digest(c['id'])+'.json')).read_text()) for c in cases]
            assert len(rows)==d['n'] and int(correctness(rows,cases).sum())==d['correct']
            assert sum(len(r['calls']) for r in rows)==d['model_calls']
            for r,c in zip(rows,cases):
                assert len(r['calls'])<=protocol['max_calls_per_case']
                if r['status'] in ('complete','invalid_final_answer'):
                    assert r['prediction']==parse_answer(r['raw_output'],len(c['options']))
            verify_receipts(rows)
            result['author_methods'][method][split]=d
            invalid=[r for r in rows if r['prediction'] is None]
            d['invalid_output_diagnosis']={
                'empty_final_text':sum(not str(r.get('raw_output','')).strip() for r in invalid),
                'explicit_no_valid_option':sum(bool(re.search(r'(?i)(?:option\s*:\s*none|none of|no (?:valid|listed|appropriate) option)',str(r.get('raw_output','')))) for r in invalid),
                'interpretation':'Output-behavior flags only. Model disagreement with the reference is not proof that the reference is clinically wrong; all remain in the primary accuracy denominator.'}
            if split in ('test','rxqa'):
                ds='rxsafebench' if split=='test' else 'rxqa'
                legacy=LOCAL/'grounded-grasp-v17-seed-42'
                incumbent=json.loads((legacy/f'evolving_grounded-{ds}.json').read_text())
                result['author_methods'][method][split]['incumbent_minus_author']=interval(correctness(rows,cases),correctness(incumbent,cases),cases)
    for seed in (42,137,2026):
        p=HERE/'results'/f'memory-seed{seed}.json'
        if not p.exists():continue
        public=json.loads(p.read_text());folder=RUN/'memory'/str(seed)
        states=json.loads((folder/'states.json').read_text())
        feedback=json.loads((folder/'training_feedback.json').read_text());by={r['case_id']:r for r in feedback}
        assert len(by)==625
        train=list(data['parts']['train']);random.Random(seed).shuffle(train);gold={c['id']:c['gold'] for c in train}
        rows=[]
        for state in states:
            accepted=state.get('accepted',False)
            if state['round']:
                previous=states[state['round']-1];m=state['candidate_proposal'];b=previous['proposal']
                pass_proposal=m['correct']>b['correct'] and m['invalid']<=b['invalid']
                assert state['proposal_pass']==pass_proposal
                gm=state['candidate_guard'];gb=previous['guard']
                assert accepted==(pass_proposal and gm['correct']>gb['correct'] and gm['invalid']<=gb['invalid'])
                if not accepted:assert state['cards']==previous['cards']
            seen={c['id'] for c in train[:state['cases_seen']]}
            for card in state['cards']:
                assert set(card['support_ids']+card['counterexample_ids'])<=seen
                assert all(by[i]['prediction']!=gold[i] for i in card['support_ids'])
                assert all(by[i]['prediction']==gold[i] for i in card['counterexample_ids'])
                assert all(card[k].strip() for k in ('applies_when','exclude_when','procedure'))
            for split in ('proposal','guard'):
                cases=data['parts'][split]
                key=digest({'cards':state['cards'],'cases':[c['id'] for c in cases]})
                stored=json.loads((folder/'development'/(key+'.json')).read_text())
                assert int(correctness(stored,cases).sum())==state[split]['correct']
                verify_receipts(stored)
            rows.append({'round':state['round'],'cases_seen':state['cases_seen'],'skills':len(state['cards']),
                'accepted':accepted,'state_sha256':digest(state['cards']),
                'proposal_correct':state['proposal']['correct'],'guard_correct':state['guard']['correct']})
        result['learning'][str(seed)]=rows
        path=HERE/'results'/f'transfer-seed{seed}.json'
        if path.exists():
            transfer=json.loads(path.read_text());cases=json.loads((RUN/'independent_medqa.json').read_text())
            before=None;curve=[]
            for state,record in zip(states,transfer['rounds']):
                key=digest({'cards':state['cards'],'cases':[c['id'] for c in cases]})
                stored=json.loads((folder/'transfer'/(key+'.json')).read_text())
                arr=correctness(stored,cases);verify_receipts(stored)
                assert int(arr.sum())==record['metrics']['correct']
                if before is None:before=arr
                curve.append({**record,'versus_initial':interval(before,arr,cases)})
            result['transfer'][str(seed)]=curve
    if (all(set(splits)=={'proposal','test','rxqa','medqa'} for splits in result['author_methods'].values())
            and len(result['transfer'])==3):
        result['status']='passed_complete'
    save(HERE/'results/audit.json',result)
    print(json.dumps({'status':result['status'],'author_splits':{k:list(v) for k,v in result['author_methods'].items()},'seeds':list(result['learning']),'transfer':list(result['transfer'])}))


if __name__=='__main__':main()
