"""Resume pinned medical-agent workflows; keep raw public traces outside Git."""
import argparse
import hashlib
import fcntl
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from medical_agents import run, PINS, RESOURCES, MODEL, MDA_REPAIRS
from public_client import LOCAL, digest, ledger_total

HERE = Path(__file__).resolve().parent
RUN = LOCAL.parent/'rxrsi-v34'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n');temp.replace(path)


def prepare():
    data=json.loads((LOCAL/'data.json').read_text())
    path=HERE/'protocol.json'
    if not path.exists():
        hashes={}
        for name,pin in PINS.items():
            folder=RESOURCES/name
            assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=folder,text=True).strip()==pin
            assert not subprocess.check_output(['git','diff','HEAD'],cwd=folder,text=True).strip()
            hashes[name]={p.name:sha(p) for p in folder.glob('*.py')}
        source=RESOURCES/'MedAgents/datasets/MedQA/test.jsonl'
        rows=[json.loads(l) for l in source.read_text().splitlines()]
        old_text={' '.join(c['dialogue'].lower().split()) for cs in list(data['parts'].values())+[data['transfer']] for c in cs}
        candidates=[]
        for r in rows:
            if ' '.join(r['question'].lower().split()) in old_text:continue
            candidates.append({'id':digest(r['question']), 'dialogue':r['question'],
                'options':[r['options'][k] for k in sorted(r['options'])], 'gold':r['answer_idx'], 'type':'medqa'})
        cases=sorted(candidates,key=lambda c:digest(['independent-medqa-20261016',c['id']]))[:200]
        assert len({c['id'] for c in cases})==200
        save(RUN/'independent_medqa.json',cases)
        protocol={'created_utc':datetime.now(timezone.utc).isoformat(), 'model':MODEL,
            'author_pins':PINS,'author_source_sha256':hashes,
            'adapter_sha256':sha(HERE/'medical_agents.py'),
            'main_data_sha256':sha(LOCAL/'data.json'),
            'methods':['medagents','mdagents'], 'max_calls_per_case':80, 'max_output_tokens_per_case':24000,
            'medagents':'Author syn_verif, max_attempt_vote=3, original per-stage output caps, custom OpenRouter transport. Missing report header retained as raw report.',
            'mdagents':'Author adaptive workflow, zero demonstrations on the new task, same backbone for every role,1024 tokens/call, temperature0. Three explicit source repairs below. Budget-exhausted received trajectories count as unsuccessful, not silently excluded.',
            'mdagents_repairs':[{'before':a,'after':b} for a,b in MDA_REPAIRS],
            'budget_note':'Native-style workflow with declared caps, NOT equal inference budget to historical one-call rows. Report calls, tokens, costs and exhaustion.',
            'pilot':'20 development cases selected by hash, then the full190 proposal cases; no tuning on test outcomes.',
            'independent_task':{'name':'MedQA general medical reasoning transfer; not a prescription-order benchmark','source_sha256':sha(source),'n':200,
                'selection':'Hash order of question text only; no labels, method predictions or medication-keyword filtering used.',
                'membership_sha256':digest([c['id'] for c in cases]),'normalized_exact_overlap_with_prior_cases':0,
                'status':'Frozen before new agent learning; pretraining exposure and semantic duplicates are not ruled out.'},
            'research_target':{'absolute_gain_pp':10,'comparator':'strongest fully executed same-task baseline, with matched-budget analysis required',
                'not_a_claim':'Engineering target, not an observed result or guaranteed outcome',
                'confirmation':'Independent frozen task, paired intervals, at least3 learning seeds, fixed and shuffled-feedback controls, no clinical-risk endpoint regression'},
            'ledger_start_usd':ledger_total(),'max_incremental_usd':15,'restricted_data_sent':False}
        save(path,protocol)
    protocol=json.loads(path.read_text())
    assert protocol['adapter_sha256']==sha(HERE/'medical_agents.py')
    assert protocol['main_data_sha256']==sha(LOCAL/'data.json')
    for name,files in protocol['author_source_sha256'].items():
        assert all(sha(RESOURCES/name/file)==value for file,value in files.items())
    os.environ['RXRSI_PUBLIC_COST_CAP_USD']=str(protocol['ledger_start_usd']+protocol['max_incremental_usd'])
    return data,protocol


def main():
    p=argparse.ArgumentParser();p.add_argument('--split',choices=['proposal','test','rxqa','medqa'],default='proposal')
    p.add_argument('--method',choices=['medagents','mdagents'],required=True);p.add_argument('--limit',type=int);p.add_argument('--workers',type=int,default=12)
    a=p.parse_args()
    locks=RUN/'locks';locks.mkdir(parents=True,exist_ok=True)
    # Independent datasets may run concurrently; duplicate launchers for the
    # same method/dataset wait and then reuse completed records.
    lock=(locks/(a.method+'-'+a.split+'.lock')).open('a')
    fcntl.flock(lock,fcntl.LOCK_EX)
    data,protocol=prepare()
    cases=json.loads((RUN/'independent_medqa.json').read_text()) if a.split=='medqa' else data['transfer'] if a.split=='rxqa' else data['parts'][a.split]
    if a.limit:cases=sorted(cases,key=lambda c:digest(['author-adapter-pilot',c['id']]))[:a.limit]
    tag=a.split+('-pilot'+str(a.limit) if a.limit else '')
    folder=RUN/a.method/a.split;folder.mkdir(parents=True,exist_ok=True)
    save(HERE/'results'/f'{a.method}-{tag}-manifest.json',{'case_membership_sha256':digest([c['id'] for c in cases]),'n':len(cases),'protocol_sha256':sha(HERE/'protocol.json')})
    def one(c):
        path=folder/(digest(c['id'])+'.json')
        if path.exists():return json.loads(path.read_text())
        row=run(a.method,c,protocol['max_calls_per_case'],protocol['max_output_tokens_per_case'])
        save(path,row);return row
    out={}
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        jobs=[pool.submit(one,c) for c in cases]
        for f in as_completed(jobs):
            r=f.result();out[r['case_id']]=r
            if len(out)%5==0:print(json.dumps({'method':a.method,'split':tag,'completed':len(out),'n':len(cases)}),flush=True)
    rows=[out[c['id']] for c in cases]
    correct=sum(r['prediction']==c['gold'] for r,c in zip(rows,cases))
    calls=[x for r in rows for x in r['calls']]
    result={'status':'complete','method':a.method,'split':tag,'n':len(rows),'correct':correct,'accuracy':correct/len(rows),
        'outcome_counts':{s:sum(r['status']==s for r in rows) for s in sorted({r['status'] for r in rows})},
        'model_calls':len(calls),'mean_calls':len(calls)/len(rows),'input_tokens':sum(r['input_tokens'] for r in calls),
        'output_tokens':sum(r['output_tokens'] for r in calls),'logical_cost_usd':sum(r.get('cost_usd') or 0 for r in calls),
        'predictions_sha256':digest([{'case_id':r['case_id'],'prediction':r['prediction']} for r in rows]),
        'ledger_increment_usd':ledger_total()-protocol['ledger_start_usd']}
    save(HERE/'results'/f'{a.method}-{tag}.json',result);print(json.dumps(result),flush=True)


if __name__=='__main__':main()
