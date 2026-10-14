"""Freeze a development-only catalogue-position diagnostic after v15."""
import copy,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v26'
SOURCE=PRIVATE.parent/'prismatic-v15'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def transform(case,kind):
    c=copy.deepcopy(case);orders=list(case['catalogue'].values());n=len(orders);assert n==20
    ids=list(range(n))
    if kind=='permuted_rank_explicit':
        ids.sort(key=lambda i:hashlib.sha256(('v26:'+case['case_id']+':'+str(i)).encode()).hexdigest())
    elif kind=='reversed_rank_explicit':ids=list(reversed(ids))
    elif kind not in ['original','ranked_explicit']:raise ValueError(kind)
    c['original_rank_by_position']=[i+1 for i in ids]
    if kind=='original':return c
    c['catalogue']={f'O{j+1}':orders[i] for j,i in enumerate(ids)}
    context=case['messages'][1]['content'].split('\nCandidate order tools:\n')[0]
    lines=[f"O{j+1}: {orders[i]['drug_name'][:70]} | {orders[i]['route']} | {orders[i]['dose_value']} {orders[i]['dose_unit']} | original retrieval rank {i+1}" for j,i in enumerate(ids)]
    c['messages'][1]['content']=context+'\nCandidate order tools:\n'+'\n'.join(lines)
    c['messages'][0]['content']+=' Original retrieval rank is provided on every candidate; smaller rank means a higher score from the same fixed retrieval tool. Return the inclusion mask in the displayed O1 through O20 order.'
    gold={o['drug_name'] for o in c['gold']};c['target']=[k for k,o in c['catalogue'].items() if o['drug_name'] in gold];c['target_mask']=[int(k in c['target']) for k in c['catalogue']]
    assert sorted(c['catalogue'].values(),key=lambda o:json.dumps(o,sort_keys=True))==sorted(case['catalogue'].values(),key=lambda o:json.dumps(o,sort_keys=True))
    assert c['gold']==case['gold'];return c

def main():
    PRIVATE.mkdir(exist_ok=True);(HERE/'results').mkdir(exist_ok=True)
    source=SOURCE/'cases.json';guard=json.loads(source.read_text())['guard'];assert len(guard)==200
    conditions=['original','ranked_explicit','permuted_rank_explicit','reversed_rank_explicit']
    data={k:[transform(c,k) for c in guard] for k in conditions}
    prepared=PRIVATE/'guard_conditions.json';prepared.write_text(json.dumps(data)+'\n')
    frozen=json.loads((ROOT/'upgrade_v15/results/frozen_selection.json').read_text());assert frozen['arms']=={'uniform_sft':2,'error_prioritized_sft':2}
    adapters={arm:sha(SOURCE/f'{arm}-round-2/adapters.safetensors') for arm in frozen['arms']}
    protocol={'study':'v0.26 development-only position dependence with explicit retained retrieval rank',
      'registration':'After completed v15 results/diagnostics, before any v26 model generation. Post-test-motivated development experiment, not confirmation.',
      'cases':200,'split':'The existing v15 guard only; no training/test task is evaluated here.',
      'source_cases_sha256':sha(source),'prepared_guard_sha256':sha(prepared),'models':['base','uniform_sft_round2','error_prioritized_sft_round2'],
      'adapter_sha256':adapters,'model_revision':'50d427756c6b1b2fe0c0a10f67fbda1fc8e82c1b','conditions':conditions,
      'intervention':'Ranked/permuted/reversed-explicit conditions share every candidate, field and original retrieval rank; only displayed position and local O IDs change. No rank-information removal. Original condition separately measures the added-rank prompt shift.',
      'permutation':'Deterministic case-specific hash order, independent of GT. Gold masks remapped for scoring only.',
      'generation':'Frozen weights, greedy128-token cap, same local MLX backend. Generate distinct input once, bind to each case, store immutable receipts. Fresh original condition avoids comparing against overwritten legacy caches.',
      'endpoints':['drug/core-order microF1','empty/invalid rate','display-prefix and original-rank-prefix fraction','medication-set agreement and Jaccard across reordered conditions','patient-cluster paired descriptive intervals1000'],
      'controls':['direct original-rank top8 tools','all20 tools'],'selection':'No training, model selection, checkpoint choice or prompt winner will be promoted from this diagnostic.',
      'claim_boundary':'Development sensitivity to candidate display order while retaining rank information. It does not establish clinical reasoning, causality of training collapse, or an RSI improvement. Restricted data/generation remain local.'}
    (HERE/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    manifest={'status':'prepared','guard_cases':200,'guard_patients':len({c['subject_hash'] for c in guard}),'conditions':conditions,'all_candidate_sets_and_gold_equal':True,
      'test_cases_used':0,'model_calls':0,'prepared_guard_sha256':sha(prepared)}
    (HERE/'results/data_audit.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest))

if __name__=='__main__':main()
