"""Reconstruct completed local updates independently from immutable case receipts.

This audits executed data, feedback, sampling, checkpoint and scoring evidence;
it does not claim to reproduce the floating-point optimizer trajectory.
"""
import argparse,hashlib,json,re,sys
from collections import defaultdict
from pathlib import Path
import numpy as np
import mlx.core as mx
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v31'
CORE=('drug_name','route','dose_value','dose_unit');FIELDS=CORE+('frequency_per_24h',)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(z,ascii=True):return hashlib.sha256(json.dumps(z,sort_keys=True,ensure_ascii=ascii).encode()).hexdigest()
def save(p,z):
    tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(z,indent=2)+'\n');tmp.replace(p)
def transform(original,condition,seed=0,r=0,purpose='evaluation'):
    orders=list(original['catalogue'].values());indices=list(range(20))
    if condition=='permuted':indices=sorted(indices,key=lambda i:hashlib.sha256(f'v31|{seed}|{r}|{purpose}|{original["case_id"]}|{i}'.encode()).hexdigest())
    elif condition=='reversed':indices=list(range(19,-1,-1))
    else:assert condition=='ranked'
    catalogue={f'O{j+1}':orders[i] for j,i in enumerate(indices)};names={o['drug_name'] for o in original['gold']};mask=[int(o['drug_name'] in names) for o in catalogue.values()]
    context=original['messages'][1]['content'].partition('\nCandidate order tools:\n')[0]
    lines=[f"O{j+1}: {orders[i]['drug_name'][:70]} | {orders[i]['route']} | {orders[i]['dose_value']} {orders[i]['dose_unit']} | original retrieval rank {i+1}" for j,i in enumerate(indices)]
    system=original['messages'][0]['content']+' Original retrieval rank is provided on every candidate; smaller rank means a higher score from the same fixed retrieval tool. Return the inclusion mask in the displayed O1 through O20 order.'
    return {**original,'catalogue':catalogue,'target_mask':mask,'original_rank_by_position':[i+1 for i in indices],'messages':[{'role':'system','content':system},{'role':'user','content':context+'\nCandidate order tools:\n'+'\n'.join(lines)}]}
def parse(raw,catalogue,normalize=True):
    text=raw.strip()
    if normalize:text=re.sub(r'^<think>\s*</think>\s*','',text,count=1)
    try:
        obj=json.loads(text);mask=obj['include'];assert isinstance(mask,list) and len(mask)==20 and all(type(v) is int and v in [0,1] for v in mask)
        return [o for o,v in zip(catalogue.values(),mask) if v],'valid',mask
    except (AssertionError,ValueError,TypeError,KeyError):return [],'invalid_json',None
def verify_rows(rows,cases,version):
    assert len(rows)==len(cases);pred=[]
    for row,c in zip(rows,cases):
        assert row['case_id']==c['case_id'];signature=digest([version,c['messages'],128],False);raw_path=PRIVATE/'inference-v2/raw'/(signature+'.json');raw=json.loads(raw_path.read_text());assert raw['generation_signature']==signature and raw['adapter_sha256']==version and raw['raw']==row['raw']
        key=digest([signature,c['case_id'],list(c['catalogue'].items())],False);path=PRIVATE/'inference-v2/cases'/(key+'.json');receipt=json.loads(path.read_text())
        assert row['case_receipt_key']==key and row['case_receipt_sha256']==sha(path) and receipt=={k:v for k,v in row.items() if k!='case_receipt_sha256'}
        orders,status,_=parse(row['raw'],c['catalogue']);_,strict,_=parse(row['raw'],c['catalogue'],False)
        assert row['orders']==orders and row['status']==status and row['raw_strict_status']==strict;pred.append(orders)
    return pred
def metrics(pred,cases,rows=None):
    counts=np.zeros(6,dtype=np.int64);field_hits=field_n=0;empty=0;patients=defaultdict(list)
    for orders,c in zip(pred,cases):
        p={o['drug_name'] for o in orders};g={o['drug_name'] for o in c['gold']};pc={tuple(o.get(f) for f in CORE) for o in orders if all(o.get(f) is not None for f in CORE)};gc={tuple(o.get(f) for f in CORE) for o in c['gold'] if all(o.get(f) is not None for f in CORE)}
        counts+=np.array([len(p&g),len(p),len(g),len(pc&gc),len(pc),len(gc)]);empty+=not p
        patients[c['subject_hash']].append((2*len(p&g)/(len(p)+len(g)) if p or g else 1.,2*len(pc&gc)/(len(pc)+len(gc)) if pc or gc else 1.))
        for order in orders:
            same=[o for o in c['gold'] if o['drug_name']==order['drug_name']]
            for field in FIELDS[1:]:
                observed={o[field] for o in same if o[field] is not None}
                if observed:field_n+=1;field_hits+=order[field] in observed
    hit,pn,gn,ohit,opn,ogn=map(int,counts);df=2*hit/max(1,pn+gn);of=2*ohit/max(1,opn+ogn)
    out={'cases':len(cases),'drug_micro_f1':df,'drug_precision':hit/max(1,pn),'drug_recall':hit/max(1,gn),'core_order_micro_f1':of,'known_field_accuracy_given_correct_drug':field_hits/max(1,field_n),'known_fields_scored':field_n,'core_gold_orders':ogn,'core_predicted_orders':opn,'mean_predicted_drugs':pn/len(cases),'empty_fraction':empty/len(cases),'promotion_score':(df+of)/2}
    if rows:out.update(invalid_json=sum(r['status']=='invalid_json' for r in rows),raw_strict_invalid_json=sum(r['raw_strict_status']=='invalid_json' for r in rows),empty_reasoning_envelope_removed=sum(r['empty_reasoning_envelope_removed'] for r in rows))
    extra={'patient_drug_f1':float(np.mean([np.mean(a,axis=0)[0] for a in patients.values()])),'patient_order_f1':float(np.mean([np.mean(a,axis=0)[1] for a in patients.values()])),'patients':len(patients)}
    return out,extra
def compare(a,b):
    for k,v in b.items():assert abs(a[k]-v)<1e-12,(k,a.get(k),v)
def main(seed):
    folder=PRIVATE/f'seed{seed}';lock=json.loads((folder/'lock.json').read_text());protocol=json.loads((HERE/'protocol.json').read_text());assert lock['protocol_sha256']==sha(HERE/'protocol.json') and all(sha(ROOT/p)==h for p,h in lock['source_sha256'].items())
    audit=json.loads((HERE/'results/data_audit.json').read_text());assert sha(HERE/'results/data_audit.json')==lock['data_audit_sha256'] and sha(PRIVATE/'cases.json')==audit['prepared_sha256']
    source=PRIVATE.parent/'prismatic-v15/cases.json';assert sha(source)==audit['source_sha256'];full=json.loads(source.read_text());data={k:full[k] for k in ['blocks','validation','guard']};assert data==json.loads((PRIVATE/'cases.json').read_text())
    base_version='base-50d427756c6b1b2fe0c0a10f67fbda1fc8e82c1b';base_metrics={}
    for condition in ['ranked','permuted']:
        path=folder/f'base-proposal-{condition}.json'
        if not path.exists():return
        cases=[transform(c,condition) for c in data['validation']];rows=json.loads(path.read_text());base_metrics[condition]=metrics(verify_rows(rows,cases,base_version),cases,rows)[0]
    best={a:{'round':0,'objective':sum(m['promotion_score'] for m in base_metrics.values())/2} for a in protocol['arms']};errors={a:{} for a in protocol['arms']};accum=[];result={'status':'partial','seed':seed,'lock_sha256':sha(folder/'lock.json'),'auditor_sha256':sha(Path(__file__)),'base_proposal':base_metrics,'arms':{a:[] for a in protocol['arms']},'guard':{},'test_inference':False}
    for r,index in enumerate(protocol['seed_block_orders'][str(seed)],1):
        block=data['blocks'][index];accum+=block
        for arm in protocol['arms']:
            part=folder/f'{arm}-round{r}';complete=part/'complete.json'
            if not complete.exists():continue
            assert len(result['arms'][arm])==r-1;record=json.loads(complete.read_text());kind='ranked' if arm=='ranked_uniform' else 'permuted';cases=[transform(c,kind,seed,r,'feedback') for c in block];rows=json.loads((part/'feedback.json').read_text())
            previous=sha(folder/f'{arm}-round{r-1}/adapter/adapters.safetensors') if r>1 else base_version;pred=verify_rows(rows,cases,previous)
            for p,c in zip(pred,cases):
                pn={o['drug_name'] for o in p};gn={o['drug_name'] for o,v in zip(c['catalogue'].values(),c['target_mask']) if v};den=len(pn)+len(gn);errors[arm][c['case_id']]=1-(2*len(pn&gn)/den if den else 1.)
            assert errors[arm]==json.loads((part/'errors.json').read_text());error=np.array([errors[arm][c['case_id']] for c in accum])
            if arm=='permuted_shuffled_error':error=error[np.random.default_rng(seed+10000*r).permutation(len(error))]
            weights=1+3*error if arm in ['permuted_own_error','permuted_shuffled_error'] else np.ones(len(accum));weights=weights/weights.sum();selected=np.random.default_rng(seed+r).choice(len(accum),400,replace=False,p=weights)
            sampling=json.loads((part/'sampling.json').read_text());assert sampling['accumulated_case_ids']==[c['case_id'] for c in accum] and selected.tolist()==sampling['selected_indices'];np.testing.assert_allclose(weights,sampling['normalized_weights'],atol=1e-15,rtol=1e-15)
            ids=[accum[i]['case_id'] for i in selected];assert ids==sampling['selected_case_ids'] and digest(ids)==record['training_members_sha256'];assert sha(part/'feedback.json')==record['feedback_sha256']==sampling['feedback_receipts_sha256']
            expected=[]
            for i in selected:
                c=transform(accum[i],kind,seed,r,'train');expected.append({'messages':c['messages']+[{'role':'assistant','content':json.dumps({'include':c['target_mask']})}]})
            training=[json.loads(line) for line in (part/'data/train.jsonl').read_text().splitlines()];assert training==expected and len(training)==400 and sha(part/'data/train.jsonl')==record['supervision_sha256']==sampling['train_jsonl_sha256']
            validation=[]
            for original in data['validation']:
                c=transform(original,'ranked');validation.append({'messages':c['messages']+[{'role':'assistant','content':json.dumps({'include':c['target_mask']})}]})
            assert [json.loads(line) for line in (part/'data/valid.jsonl').read_text().splitlines()]==validation and sha(part/'data/valid.jsonl')==sampling['valid_jsonl_sha256']
            adapter=part/'adapter/adapters.safetensors';assert sha(adapter)==record['adapter_sha256'];weights_actual=mx.load(str(adapter));assert all(bool(mx.all(mx.isfinite(v)).item()) for v in weights_actual.values());b_values=[v for k,v in weights_actual.items() if k.endswith('lora_b')];assert b_values and any(bool(mx.any(v!=0).item()) for v in b_values)
            if r>1:
                before=mx.load(str(folder/f'{arm}-round{r-1}/adapter/adapters.safetensors'));assert set(before)==set(weights_actual) and any(bool(mx.any(v!=before[k]).item()) for k,v in weights_actual.items())
            count=sum(v.size for v in weights_actual.values());del weights_actual;mx.clear_cache()
            finished=json.loads((part/'training_complete.json').read_text());assert finished['optimizer_steps']==record['optimizer_steps']==100 and finished['adapter_sha256']==record['adapter_sha256']
            command=finished['command'];assert command[command.index('--iters')+1]=='100' and command[command.index('--batch-size')+1]=='4' and '--grad-checkpoint' in command and str(HERE/'train_cli.py') in command
            config=json.loads((part/'adapter/adapter_config.json').read_text());assert config['seed']==seed and config['num_layers']==8 and config['mask_prompt'] and config['grad_checkpoint'] and config['max_seq_length']==1536 and config['lora_parameters']=={'rank':8,'dropout':0.0,'scale':20.0}
            log=re.sub(r'\x1b\[[0-9;]*m','',(part/'training.log').read_text());assert '0000100_adapters.safetensors' in log and '100/100' in re.sub(r'\s','',log) and 'will be truncated' not in log
            proposal={}
            for condition in ['ranked','permuted']:
                cs=[transform(c,condition) for c in data['validation']];rr=json.loads((part/f'proposal-{condition}.json').read_text());m,extra=metrics(verify_rows(rr,cs,record['adapter_sha256']),cs,rr);compare(record['proposal'][condition],m);proposal[condition]={**m,**extra}
            objective=sum(v['promotion_score'] for v in proposal.values())/2;assert abs(objective-record['objective'])<1e-12;promoted=objective>best[arm]['objective']+1e-12
            if promoted:best[arm]={'round':r,'objective':objective}
            assert record['promoted']==promoted and record['best']['round']==best[arm]['round']
            result['arms'][arm].append({'round':r,'complete_sha256':sha(complete),'adapter_sha256':record['adapter_sha256'],'adapter_parameters':int(count),'feedback_cases_verified':600,'sampling_and_targets_verified':400,'optimizer_steps':100,'completion_tokens_per_sequence':69,'expected_supervised_target_tokens':27600,'proposal':proposal,'promoted':promoted,'active_round':best[arm]['round']})
    public=HERE/f'results/seed{seed}.json'
    if public.exists():
        raw=public.read_bytes();state=json.loads(raw);result['source_public_snapshot_sha256']=hashlib.sha256(raw).hexdigest()
        if state['status']=='executed_pending_audit':
            assert all(len(v)==3 for v in result['arms'].values());frozen=json.loads((folder/'frozen_selection.json').read_text());assert all(frozen['arms'][a]['round']==best[a]['round'] for a in best)
            result['view_comparisons']={}
            for name,conditions in state['guard'].items():
                result['guard'][name]={};version=base_version if name=='base' else sha(folder/name/'adapter/adapters.safetensors')
                outputs={}
                for condition,record in conditions.items():
                    cs=[transform(c,condition) for c in data['guard']];rr=json.loads((folder/f'{name}-guard-{condition}.json').read_text());pred=verify_rows(rr,cs,version);m,extra=metrics(pred,cs,rr);compare(record,m);outputs[condition]=[{o['drug_name'] for o in p} for p in pred]
                    nontrivial=display=ranked=0
                    for row,c in zip(rr,cs):
                        _,_,mask=parse(row['raw'],c['catalogue'])
                        if mask is None or sum(mask) in [0,20]:continue
                        chosen=[i for i,v in enumerate(mask) if v];nontrivial+=1;display+=chosen==list(range(len(chosen)));ranked+=sorted(c['original_rank_by_position'][i] for i in chosen)==list(range(1,len(chosen)+1))
                    result['guard'][name][condition]={**m,**extra,'nontrivial_valid_masks':nontrivial,'display_prefix_fraction':display/nontrivial if nontrivial else None,'original_rank_prefix_fraction':ranked/nontrivial if nontrivial else None}
                result['view_comparisons'][name]={condition:{'same_drug_set_fraction':float(np.mean([a==b for a,b in zip(outputs['ranked'],outputs[condition])])),'drug_set_jaccard':float(np.mean([len(a&b)/len(a|b) if a or b else 1. for a,b in zip(outputs['ranked'],outputs[condition])]))} for condition in ['permuted','reversed']}
            result['direct_controls']={}
            for k in [8,20]:
                pred=[list(c['catalogue'].values())[:k] for c in data['guard']];m,extra=metrics(pred,data['guard']);result['direct_controls'][f'original_rank_top{k}']={**m,**extra}
            result['status']='passed';result['frozen_selection']=frozen
    result['scope']='Independent source/prompt/GT/feedback/sampling reconstruction, finite changed adapter tensors,100-step execution receipts and output regrading. Optimizer trajectory is not independently refit; guard is reused development data and old tests are not scored.'
    save(HERE/f'results/audit-seed{seed}.json',result);print(json.dumps({'seed':seed,'status':result['status'],'audited_rounds':{a:len(v) for a,v in result['arms'].items()}}),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('seed',type=int);a=p.parse_args();main(a.seed)
