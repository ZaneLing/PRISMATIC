"""Reconstruct actual feedback, sampled labels, adapter identity and mask failures."""
import hashlib,json,re,sys
from collections import Counter
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'upgrade_v7'))
from rx_agent import hash_data
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v15'

def read(p):return json.loads(p.read_text())
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def mask(raw):
    obj=json.loads(re.sub(r'^<think>\s*</think>\s*','',raw.strip(),count=1));bits=obj['include']
    assert len(bits)==20 and all(type(v) is int and v in (0,1) for v in bits)
    return bits
def audit_outputs(rows,cases,adapter):
    assert [r['case_id'] for r in rows]==[c['case_id'] for c in cases]
    masks=[]
    for row,c in zip(rows,cases):
        assert row['adapter_sha256']==adapter
        bits=mask(row['raw']);masks.append(bits)
        assert row['orders']==[o for o,v in zip(c['catalogue'].values(),bits) if v]
    counts=[sum(m) for m in masks]
    return {'n':len(rows),'raw_mask_count_histogram':dict(sorted(Counter(counts).items())),
      'distinct_masks':len({tuple(m) for m in masks}),'zero_mask_fraction':float(np.mean(np.array(counts)==0)),
      'prefix_mask_fraction':float(np.mean([m==[1]*sum(m)+[0]*(20-sum(m)) for m in masks])),
      'gold_prefix_mask_fraction':float(np.mean([c['target_mask']==[1]*sum(c['target_mask'])+[0]*(20-sum(c['target_mask'])) for c in cases])),
      'all_one_mask_fraction':float(np.mean(np.array(counts)==20)),
      'empty_envelope_removed':sum(r['empty_reasoning_envelope_removed'] for r in rows)}

def main():
    data=read(PRIVATE/'cases.json');frozen=read(HERE/'results/frozen_selection.json');assert not frozen['test_labels_used']
    base='base-50d427756c6b1b2fe0c0a10f67fbda1fc8e82c1b';audits=[];diagnostics={};feedback_gaps=[]
    all_cases=sum(data['blocks'],[])+data['validation']+data['guard']+data['test']
    input_counts=Counter(hash_data(c['messages']) for c in all_cases)
    diagnostics['base']=audit_outputs(read(PRIVATE/'base-test.json'),data['test'],base)
    for arm in ['uniform_sft','error_prioritized_sft']:
        journal=read(HERE/f'results/{arm}_rounds.json');assert len(journal)==4
        current=base;accumulated=[];errors={};best=journal[0]['guard']['promotion_score'];choice=0
        for r,block in enumerate(data['blocks'],1):
            accumulated+=block
            for c in block:
                path=PRIVATE/'inference'/(hash_data([current,c['messages'],128])+'.json');row=read(path)
                bits=mask(row['raw']);pred={o['drug_name'] for o,b in zip(c['catalogue'].values(),bits) if b};gold={c['catalogue'][i]['drug_name'] for i in c['target']}
                den=len(pred)+len(gold);errors[c['case_id']]=1-(2*len(pred&gold)/den if den else 1)
            saved_errors=read(PRIVATE/f'{arm}-errors-{r}.json');mismatches=0
            for c in block:
                if errors[c['case_id']]!=saved_errors[c['case_id']]:
                    # Identical prompts may have been independently generated
                    # before their shared cache entry was written. Preserve this
                    # audit gap; never replace the actual recorded feedback.
                    assert input_counts[hash_data(c['messages'])]>1,'Unexplained unique-input feedback mismatch'
                    mismatches+=1
            feedback_gaps.append({'arm':arm,'round':r,'new_feedback_cases':len(block),'cache_feedback_matches':len(block)-mismatches,
              'duplicate_input_feedback_unrecoverable':mismatches})
            errors=saved_errors
            w=np.array([1+3*errors[c['case_id']] if arm=='error_prioritized_sft' else 1 for c in accumulated],dtype=float);w/=w.sum()
            ix=np.random.default_rng(42+r).choice(len(accumulated),400,replace=False,p=w);j=journal[r]
            assert hash_data([accumulated[i]['case_id'] for i in ix])==j['training_member_sha256']
            train=[json.loads(line) for line in (PRIVATE/f'{arm}-data-{r}/train.jsonl').read_text().splitlines()]
            assert len(train)==400
            for row,i in zip(train,ix):
                c=accumulated[i];assert row['messages'][:-1]==c['messages']
                assert mask(row['messages'][-1]['content'])==[int(k in c['target']) for k in c['catalogue']]
            folder=PRIVATE/f'{arm}-round-{r}';current=digest(folder/'adapters.safetensors');assert current==j['adapter_sha256']
            completion=read(folder/'training_complete.json');assert completion['optimizer_steps']==100
            log=re.sub(r'\x1b\[[0-9;]*m','',(folder/'training.log').read_text())
            assert re.search(r'100\s*/100',log) and '0000100_adapters.safetensors' in log, 'Training log lacks final step'
            assert '--mask-prompt' in completion['command']
            if j['guard']['promotion_score']>best:best=j['guard']['promotion_score'];choice=r
            assert choice==j['active_round']
            diagnostics[f'{arm}_round_{r}']=audit_outputs(read(PRIVATE/f'{arm}-round-{r}-test.json'),data['test'],current)
            audits.append({'arm':arm,'round':r,'preupdate_cache_and_error_recount':'passed' if mismatches==0 else 'duplicate-input receipt gap',
              'sampling_from_recorded_weights_and_serialized_labels':'passed',
              'actual_adapter_sha256':current,'training_steps':100,'train_rows':400,
              'training_target_empty_fraction':float(np.mean([not accumulated[i]['target'] for i in ix])),
              'training_target_mean_count':float(np.mean([len(accumulated[i]['target']) for i in ix]))})
        assert choice==frozen['arms'][arm]
    gaps=sum(r['duplicate_input_feedback_unrecoverable'] for r in feedback_gaps)
    report={'status':'passed' if gaps==0 else 'completed_with_feedback_receipt_gaps','scope':'Post-hoc failure diagnosis and independent learning-artifact audit; no new selection or training',
      'feedback_source':'Each arm latest training checkpoint, not best accepted inference checkpoint; this matches the frozen protocol.',
      'checks':audits,'feedback_reconstruction':feedback_gaps,'unrecoverable_duplicate_input_feedback':gaps,
      'receipt_limit':'Input-keyed caches can overwrite independent generations for identical prompts. Sampling is verified from original recorded weights; incomplete feedback replay is disclosed and not repaired using test outcomes.',
      'test_output_diagnostics':diagnostics,'new_model_calls':0,'test_based_selection':False}
    (HERE/'results/learning_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'rounds_audited':len(audits),'feedback_receipt_gaps':feedback_gaps,'output_diagnostics':diagnostics}))

if __name__=='__main__':main()
