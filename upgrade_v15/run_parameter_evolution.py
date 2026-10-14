"""Local QLoRA uniform versus feedback-prioritized updates with equal step budgets."""
import argparse,gc,hashlib,json,subprocess,sys,time
from pathlib import Path
import numpy as np
import mlx.core as mx
from mlx_lm import load,batch_generate
from mlx_lm.sample_utils import make_sampler
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'upgrade_v7'))
from rx_agent import compile_selection,score,hash_data
from selection_parser import compile_model_selection,bind_cached_output
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v15'
MODEL=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/models/qwen3-4b-instruct-2507-4bit'

def filehash(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,x):path.write_text(json.dumps(x,indent=2)+'\n')

def infer(cases,adapter=None):
    version=filehash(adapter/'adapters.safetensors') if adapter else 'base-50d427756c6b1b2fe0c0a10f67fbda1fc8e82c1b'
    cache=PRIVATE/'inference';cache.mkdir(exist_ok=True);records={};pending=[]
    for c in cases:
        sig=hash_data([version,c['messages'],128]);path=cache/(sig+'.json')
        if path.exists():
            row=bind_cached_output(json.loads(path.read_text()),c)
            records[c['case_id']]=row
        else:pending.append((c,path))
    if pending:
        model,tok=load(str(MODEL),adapter_path=str(adapter) if adapter else None)
        for lo in range(0,len(pending),32):
            chunk=pending[lo:lo+32];prompts=[tok.apply_chat_template(c['messages'],tokenize=True,add_generation_prompt=True,return_dict=False) for c,path in chunk]
            start=time.time();response=batch_generate(model,tok,prompts,max_tokens=128,sampler=make_sampler(temp=0),prefill_batch_size=4,completion_batch_size=16)
            for (c,path),raw in zip(chunk,response.texts):
                parsed=compile_model_selection(raw,c['catalogue']);row={'case_id':c['case_id'],'raw':raw,**parsed,'adapter_sha256':version,'seconds_per_batch_case':(time.time()-start)/len(chunk)}
                save(path,row);records[c['case_id']]=row
            print(json.dumps({'stage':'local_inference','adapter':version[:12],'completed':min(lo+32,len(pending)),'total':len(pending)}),flush=True)
        del model,tok;gc.collect();mx.clear_cache()
    return [records[c['case_id']] for c in cases]

def metric(rows,cases):
    assert [r['case_id'] for r in rows]==[c['case_id'] for c in cases]
    out=score([r['orders'] for r in rows],[c['gold'] for c in cases]);out['invalid_json']=sum(r['status']=='invalid_json' for r in rows)
    out['raw_strict_invalid_json']=sum(r.get('raw_strict_status',r['status'])=='invalid_json' for r in rows)
    out['empty_reasoning_envelope_removed']=sum(r.get('empty_reasoning_envelope_removed',False) for r in rows)
    return out

def run(arms):
    config=json.loads((HERE/'protocol.json').read_text());data=json.loads((PRIVATE/'cases.json').read_text())
    # Audit complete sequence lengths before training. Do not truncate target completions.
    from transformers import AutoTokenizer
    tokenizer=AutoTokenizer.from_pretrained(str(MODEL))
    lengths=[]
    for c in sum(data['blocks'],[])+data['validation']:
        messages=c['messages']+[{'role':'assistant','content':json.dumps({'include':c['target_mask']})}]
        lengths.append(len(tokenizer.apply_chat_template(messages,tokenize=True,return_dict=False)))
    assert max(lengths)<=config['max_sequence_length'],f"Sequence limit too short ({max(lengths)}); freeze a sufficient limit before training"
    save(HERE/'results/sequence_audit.json',{'max_tokens':max(lengths),'median_tokens':float(np.median(lengths)),'training_target_truncations':0})
    del tokenizer
    base_guard=infer(data['guard']);base_metric=metric(base_guard,data['guard'])
    for arm in arms:
        journal=HERE/f'results/{arm}_rounds.json'
        versions=json.loads(journal.read_text()) if journal.exists() else [{'round':0,'adapter':None,'guard':base_metric,'active_round':0,'training_cases':0}]
        accumulated=[];errors={};latest=None;best_score=base_metric['promotion_score'];best_round=0
        for r,block in enumerate(data['blocks'],1):
            accumulated+=block
            if len(versions)>r:
                previous=versions[r];errors.update(json.loads((PRIVATE/f'{arm}-errors-{r}.json').read_text()))
                latest=PRIVATE/f'{arm}-round-{r}'
                if previous['guard']['promotion_score']>best_score:best_score=previous['guard']['promotion_score'];best_round=r
                continue
            before=infer(block,latest)
            for c,row in zip(block,before):
                # Attribute feedback to the module being updated: selecting reachable
                # tool actions. Missing catalogue coverage cannot be fixed by LoRA here.
                predicted={o['drug_name'] for o in row['orders']}
                target={c['catalogue'][i]['drug_name'] for i in c['target']}
                denom=len(predicted)+len(target)
                errors[c['case_id']]=1-(2*len(predicted&target)/denom if denom else 1.)
            save(PRIVATE/f'{arm}-errors-{r}.json',errors)
            weights=np.array([1+3*errors[c['case_id']] if arm=='error_prioritized_sft' else 1 for c in accumulated],dtype=float);weights/=weights.sum()
            rng=np.random.default_rng(42+r);selected=rng.choice(len(accumulated),400,replace=False,p=weights)
            folder=PRIVATE/f'{arm}-data-{r}';folder.mkdir(exist_ok=True)
            def serialize(c):return {'messages':c['messages']+[{'role':'assistant','content':json.dumps({'include':c['target_mask']})}]}
            (folder/'train.jsonl').write_text(''.join(json.dumps(serialize(accumulated[i]))+'\n' for i in selected))
            (folder/'valid.jsonl').write_text(''.join(json.dumps(serialize(c))+'\n' for c in data['validation']))
            destination=PRIVATE/f'{arm}-round-{r}';destination.mkdir(exist_ok=True)
            command=[sys.executable,'-m','mlx_lm','lora','--model',str(MODEL),'--train','--data',str(folder),
               '--fine-tune-type','lora','--mask-prompt','--num-layers','8','--batch-size','4','--iters','100',
               '--learning-rate','0.0001','--steps-per-report','20','--steps-per-eval','100','--val-batches','8',
               '--save-every','100','--max-seq-length',str(config['max_sequence_length']),'--adapter-path',str(destination),'--seed','42']
            if latest:command+=['--resume-adapter-file',str(latest/'adapters.safetensors')]
            training_start=time.time()
            if not (destination/'training_complete.json').exists():
                with (destination/'training.log').open('w') as log:subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True)
                save(destination/'training_complete.json',{'optimizer_steps':100,'seconds':time.time()-training_start,'command':command})
            latest=destination;guard=infer(data['guard'],latest);gm=metric(guard,data['guard'])
            promoted=gm['promotion_score']>best_score
            if promoted:best_score=gm['promotion_score'];best_round=r
            version={'round':r,'training_cases':len(accumulated),'trained_examples_this_round':400,'optimizer_steps_this_round':100,
              'adapter_sha256':filehash(latest/'adapters.safetensors'),'guard':gm,'promoted':promoted,'active_round':best_round,
              'training_member_sha256':hash_data([accumulated[i]['case_id'] for i in selected]),
              'mean_sampled_preupdate_error':float(np.mean([errors[accumulated[i]['case_id']] for i in selected])),
              'feedback_precedes_training':True,'training_seconds':json.loads((destination/'training_complete.json').read_text())['seconds']}
            versions.append(version);save(journal,versions)
            print(json.dumps({'arm':arm,'round':r,'guard':gm,'promoted':promoted,'active_round':best_round}),flush=True)
    # All branch selection is fixed before the first test-label evaluation.
    selection={arm:json.loads((HERE/f'results/{arm}_rounds.json').read_text())[-1]['active_round'] for arm in arms}
    save(HERE/'results/frozen_selection.json',{'arms':selection,'test_labels_used':False})
    base=infer(data['test']);report={'base':metric(base,data['test']),'arms':{}}
    save(PRIVATE/'base-test.json',base)
    for arm in arms:
        curve=[]
        for r in range(1,4):
            rows=infer(data['test'],PRIVATE/f'{arm}-round-{r}');save(PRIVATE/f'{arm}-round-{r}-test.json',rows)
            curve.append({'round':r,'metrics':metric(rows,data['test'])})
        best=selection[arm];report['arms'][arm]={'raw_checkpoint_curve':curve,'chosen_round':best,'selected_test':report['base'] if best==0 else curve[best-1]['metrics']}
        save(HERE/'results/parameter_results.json',report)
    print(json.dumps(report),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--arms',nargs='+',default=['uniform_sft','error_prioritized_sft']);a=parser.parse_args();run(a.arms)
