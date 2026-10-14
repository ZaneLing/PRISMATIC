"""Copy only training/proposal/guard cases and audit all registered prompt views."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
from transformers import AutoTokenizer
from views import view,serialize,digest
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v31';SOURCE=PRIVATE.parent/'prismatic-v15/cases.json';MODEL=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/models/qwen3-4b-instruct-2507-4bit'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as stream:
        for part in iter(lambda:stream.read(8*1024*1024),b''):h.update(part)
    return h.hexdigest()
def main():
    PRIVATE.mkdir(exist_ok=True);(HERE/'results').mkdir(exist_ok=True);protocol=json.loads((HERE/'protocol.json').read_text())
    expected=json.loads((ROOT/'upgrade_v26/protocol.json').read_text())['source_cases_sha256'];assert sha(SOURCE)==expected
    original=json.loads(SOURCE.read_text());data={k:original[k] for k in ['blocks','validation','guard']};assert [len(z) for z in data['blocks']]==[600]*3 and len(data['validation'])==100 and len(data['guard'])==200
    groups=[{c['subject_hash'] for c in z} for z in data['blocks']+[data['validation'],data['guard']]]
    for i,a in enumerate(groups):
        for b in groups[i+1:]:assert not a&b
    assert not set().union(*groups)&{c['subject_hash'] for c in original['test']}
    assert len({c['case_id'] for block in data['blocks'] for c in block})==1800
    prepared=PRIVATE/'cases.json';content=json.dumps(data)+'\n'
    if prepared.exists():assert prepared.read_text()==content
    else:prepared.write_text(content)
    tok=AutoTokenizer.from_pretrained(str(MODEL));lengths=[];target_lengths=[];checked=0;prefix=[];seen=set()
    def verify(case,condition,seed=0,r=0,purpose='evaluation'):
        nonlocal checked
        c=view(case,condition,seed,r,purpose);assert c['gold']==case['gold'] and c['subject_hash']==case['subject_hash']
        assert sorted(map(lambda z:json.dumps(z,sort_keys=True),c['catalogue'].values()))==sorted(map(lambda z:json.dumps(z,sort_keys=True),case['catalogue'].values()))
        assert c['messages'][1]['content'].split('\nCandidate order tools:\n')[0]==case['messages'][1]['content'].split('\nCandidate order tools:\n')[0]
        for rank,order in zip(c['original_rank_by_position'],c['catalogue'].values()):assert order==list(case['catalogue'].values())[rank-1]
        expected_mask=[int(o['drug_name'] in {g['drug_name'] for g in case['gold']}) for o in c['catalogue'].values()];assert c['target_mask']==expected_mask
        identity=digest(serialize(c))
        if identity not in seen:
            seen.add(identity);tokens=tok.apply_chat_template(serialize(c)['messages'],tokenize=True,return_dict=False);prompt=tok.apply_chat_template(c['messages'],tokenize=True,add_generation_prompt=True,return_dict=False)
            assert tokens[:len(prompt)]==prompt;lengths.append(len(tokens));target_lengths.append(len(tokens)-len(prompt))
        n=sum(c['target_mask']);prefix.append(c['target_mask']==[1]*n+[0]*(20-n));checked+=1
    for seed in protocol['seeds']:
        accumulated=[]
        for r,index in enumerate(protocol['seed_block_orders'][str(seed)],1):
            block=data['blocks'][index];accumulated+=block
            for c in block:
                verify(c,'ranked',seed,r,'feedback');verify(c,'permuted',seed,r,'feedback')
            for c in accumulated:
                verify(c,'ranked',seed,r,'train');verify(c,'permuted',seed,r,'train')
    for split in ['validation','guard']:
        for condition in ['ranked','permuted','reversed']:
            for c in data[split]:verify(c,condition)
    limit=protocol['training_budget']['max_sequence_length'];assert max(lengths)<=limit,(max(lengths),limit)
    model_files={p.name:sha(p) for p in sorted(MODEL.iterdir()) if p.is_file() and (p.suffix in ['.json','.safetensors'] or p.name=='tokenizer.model')}
    result={'status':'passed','source_sha256':expected,'prepared_sha256':sha(prepared),'protocol_sha256':sha(HERE/'protocol.json'),'view_source_sha256':sha(HERE/'views.py'),'model_files_sha256':model_files,'feedback_block_cases':[600,600,600],'feedback_block_patients':[len(g) for g in groups[:3]],'proposal_cases':100,'proposal_patients':len(groups[3]),'guard_cases':200,'guard_patients':len(groups[4]),'all_patient_role_overlap':0,'old_test_patient_overlap':0,'old_test_cases_copied_or_scored':0,'views_checked':checked,'unique_supervised_sequences':len(seen),'max_sequence_tokens':max(lengths),'median_sequence_tokens':float(np.median(lengths)),'target_token_lengths':sorted(set(target_lengths)),'target_truncations':0,'candidate_and_gold_identity_verified':True,'api_calls':0,'model_generations':0,'clinical_fits':0}
    (HERE/'results/data_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
if __name__=='__main__':main()
