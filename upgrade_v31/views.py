"""Preserve drug identity and retrieval evidence when changing display order."""
import copy,hashlib,json
def digest(z):return hashlib.sha256(json.dumps(z,sort_keys=True).encode()).hexdigest()
def view(case,condition,seed=0,round_number=0,purpose='evaluation'):
    c=copy.deepcopy(case);orders=list(case['catalogue'].values());assert len(orders)==20
    indices=list(range(20))
    if condition=='permuted':indices.sort(key=lambda i:hashlib.sha256(f'v31|{seed}|{round_number}|{purpose}|{case["case_id"]}|{i}'.encode()).hexdigest())
    elif condition=='reversed':indices.reverse()
    elif condition!='ranked':raise ValueError(condition)
    c['catalogue']={f'O{j+1}':orders[i] for j,i in enumerate(indices)};c['original_rank_by_position']=[i+1 for i in indices]
    context=case['messages'][1]['content'].split('\nCandidate order tools:\n')[0]
    rows=[f"O{j+1}: {orders[i]['drug_name'][:70]} | {orders[i]['route']} | {orders[i]['dose_value']} {orders[i]['dose_unit']} | original retrieval rank {i+1}" for j,i in enumerate(indices)]
    c['messages'][1]['content']=context+'\nCandidate order tools:\n'+'\n'.join(rows)
    c['messages'][0]['content']+=' Original retrieval rank is provided on every candidate; smaller rank means a higher score from the same fixed retrieval tool. Return the inclusion mask in the displayed O1 through O20 order.'
    names={o['drug_name'] for o in case['gold']};c['target']=[k for k,o in c['catalogue'].items() if o['drug_name'] in names];c['target_mask']=[int(k in c['target']) for k in c['catalogue']]
    return c
def serialize(case):return {'messages':case['messages']+[{'role':'assistant','content':json.dumps({'include':case['target_mask']})}]}
