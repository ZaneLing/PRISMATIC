"""Local parameter updates with exact feedback receipts and frozen guard selection."""
import argparse,copy,fcntl,hashlib,json,os,subprocess,sys,time
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;V15=ROOT/'upgrade_v15';sys.path[:0]=[str(HERE),str(V15),str(ROOT)]
import run_parameter_evolution as local
from views import view,serialize,digest
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v31';MODEL=local.MODEL;local.PRIVATE=PRIVATE
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as stream:
        for b in iter(lambda:stream.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()
def save(p,z):
    p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(z,indent=2)+'\n');tmp.replace(p)
def sources():
    paths=[HERE/f for f in ['run.py','views.py','train_cli.py','training_config.yaml']]+[V15/f for f in ['run_parameter_evolution.py','generation_receipts.py','selection_parser.py']]+[ROOT/'upgrade_v7/rx_agent.py']
    return {str(p.relative_to(ROOT)):sha(p) for p in paths}
def sampling(cases,errors,arm,seed,r):
    error=np.array([errors[c['case_id']] for c in cases],dtype=float)
    if arm=='permuted_shuffled_error':error=error[np.random.default_rng(seed+10000*r).permutation(len(error))]
    weights=1+3*error if arm in ['permuted_own_error','permuted_shuffled_error'] else np.ones(len(error));weights=weights/weights.sum()
    selected=np.random.default_rng(seed+r).choice(len(cases),400,replace=False,p=weights)
    return selected,weights
def error_value(case,row):
    predicted={o['drug_name'] for o in row['orders']};target={case['catalogue'][k]['drug_name'] for k in case['target']};denom=len(predicted)+len(target)
    return 1-(2*len(predicted&target)/denom if denom else 1.)
def proposal_objective(metrics):return sum(z['promotion_score'] for z in metrics.values())/len(metrics)
def emit(folder,event,**fields):
    with (folder/'events.jsonl').open('a') as stream:stream.write(json.dumps({'event':event,'time_ns':time.time_ns(),**fields})+'\n')
def main(seed):
    protocol=json.loads((HERE/'protocol.json').read_text());assert seed in protocol['seeds'];budget=protocol['training_budget'];arms=protocol['arms']
    data_audit=json.loads((HERE/'results/data_audit.json').read_text());assert data_audit['status']=='passed' and data_audit['prepared_sha256']==sha(PRIVATE/'cases.json') and data_audit['protocol_sha256']==sha(HERE/'protocol.json') and data_audit['view_source_sha256']==sha(HERE/'views.py')
    probe=json.loads((HERE/'results/runtime_probe.json').read_text());assert probe['status']=='passed' and probe['source_sha256']==sources()
    assert all(sha(MODEL/f)==v for f,v in data_audit['model_files_sha256'].items())
    folder=PRIVATE/f'seed{seed}';folder.mkdir(exist_ok=True)
    process_lock=(folder/'process.lock').open('w');fcntl.flock(process_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    import mlx_lm,mlx_lm.lora,mlx_lm.tuner.trainer
    lock={'seed':seed,'protocol_sha256':sha(HERE/'protocol.json'),'data_audit_sha256':sha(HERE/'results/data_audit.json'),'source_sha256':sources(),'runtime':mlx_lm.__version__,'trainer_sha256':sha(Path(mlx_lm.tuner.trainer.__file__)),'trainer_cli_sha256':sha(Path(mlx_lm.lora.__file__))}
    if (folder/'lock.json').exists():assert json.loads((folder/'lock.json').read_text())==lock
    else:save(folder/'lock.json',lock)
    public=HERE/f'results/seed{seed}.json'
    if public.exists() and json.loads(public.read_text())['status']=='executed_pending_audit':return
    data=json.loads((PRIVATE/'cases.json').read_text());order=protocol['seed_block_orders'][str(seed)];proposal={kind:[view(c,kind) for c in data['validation']] for kind in ['ranked','permuted']}
    base_metrics={}
    for kind,cases in proposal.items():
        rows=local.infer(cases);save(folder/f'base-proposal-{kind}.json',rows);base_metrics[kind]=local.metric(rows,cases)
    histories={a:[] for a in arms};errors={a:{} for a in arms};best={a:{'round':0,'objective':proposal_objective(base_metrics),'proposal':base_metrics} for a in arms};accumulated=[]
    for r,index in enumerate(order,1):
        block=data['blocks'][index];accumulated+=block
        for arm in arms:
            part=folder/f'{arm}-round{r}';part.mkdir(exist_ok=True);completed=part/'complete.json'
            if completed.exists():
                row=json.loads(completed.read_text());assert row['adapter_sha256']==sha(part/'adapter/adapters.safetensors');histories[arm].append(row);errors[arm]=json.loads((part/'errors.json').read_text());best[arm]=copy.deepcopy(row['best']);continue
            previous=folder/f'{arm}-round{r-1}/adapter' if r>1 else None;kind='ranked' if arm=='ranked_uniform' else 'permuted';feedback=[view(c,kind,seed,r,'feedback') for c in block]
            emit(folder,'feedback_begin',arm=arm,round=r);before=local.infer(feedback,previous);receipt=part/'feedback.json'
            if receipt.exists():assert json.loads(receipt.read_text())==before
            else:save(receipt,before)
            for case,row in zip(feedback,before):errors[arm][case['case_id']]=error_value(case,row)
            save(part/'errors.json',errors[arm]);selected,weights=sampling(accumulated,errors[arm],arm,seed,r)
            members=[accumulated[i] for i in selected];training=[view(c,kind,seed,r,'train') for c in members];train_dir=part/'data';train_dir.mkdir(exist_ok=True)
            training_text=''.join(json.dumps(serialize(c))+'\n' for c in training);valid_text=''.join(json.dumps(serialize(c))+'\n' for c in proposal['ranked'])
            for name,text in [('train.jsonl',training_text),('valid.jsonl',valid_text)]:
                path=train_dir/name
                if path.exists():assert path.read_text()==text
                else:path.write_text(text)
            sampling_record={'accumulated_case_ids':[c['case_id'] for c in accumulated],'selected_indices':selected.tolist(),'selected_case_ids':[c['case_id'] for c in members],'normalized_weights':weights.tolist(),'feedback_receipts_sha256':sha(receipt),'train_jsonl_sha256':sha(train_dir/'train.jsonl'),'valid_jsonl_sha256':sha(train_dir/'valid.jsonl')};save(part/'sampling.json',sampling_record)
            emit(folder,'feedback_and_sampling_saved',arm=arm,round=r,feedback_sha256=sha(receipt),sampling_sha256=sha(part/'sampling.json'))
            destination=part/'adapter';completion=part/'training_complete.json'
            if not completion.exists():
                if destination.exists() and any(destination.iterdir()):
                    archived=part/f'interrupted-adapter-{time.time_ns()}';destination.rename(archived)
                    if (part/'training.log').exists():(part/'training.log').rename(archived/'training.log')
                    emit(folder,'interrupted_training_archived',arm=arm,round=r,directory=archived.name)
                destination.mkdir(exist_ok=True)
                command=[sys.executable,str(HERE/'train_cli.py'),'--model',str(MODEL),'--train','--data',str(train_dir),'--fine-tune-type','lora','--mask-prompt','--num-layers','8','--batch-size','4','--iters','100','--learning-rate','0.0001','--steps-per-report','20','--steps-per-eval','100','--val-batches','8','--save-every','100','--max-seq-length',str(budget['max_sequence_length']),'--adapter-path',str(destination),'--seed',str(seed),'--config',str(HERE/'training_config.yaml'),'--grad-checkpoint']
                if previous:command+=['--resume-adapter-file',str(previous/'adapters.safetensors')]
                emit(folder,'training_begin',arm=arm,round=r);start=time.perf_counter()
                with (part/'training.log').open('w') as log:subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True)
                save(completion,{'optimizer_steps':100,'seconds':time.perf_counter()-start,'command':command,'adapter_sha256':sha(destination/'adapters.safetensors')});emit(folder,'training_complete',arm=arm,round=r,adapter_sha256=sha(destination/'adapters.safetensors'))
            result={}
            for condition,cases in proposal.items():
                rows=local.infer(cases,destination);save(part/f'proposal-{condition}.json',rows);result[condition]=local.metric(rows,cases)
            objective=proposal_objective(result);promoted=objective>best[arm]['objective']+1e-12
            if promoted:best[arm]={'round':r,'objective':objective,'proposal':result}
            row={'round':r,'source_block':index,'new_feedback_cases':len(block),'accumulated_cases':len(accumulated),'accumulated_patients':len({c['subject_hash'] for c in accumulated}),'trained_cases':len(selected),'optimizer_steps':100,'adapter_sha256':sha(destination/'adapters.safetensors'),'previous_adapter_sha256':sha(previous/'adapters.safetensors') if previous else None,'feedback_sha256':sha(receipt),'training_members_sha256':digest([c['case_id'] for c in members]),'supervision_sha256':sha(train_dir/'train.jsonl'),'training_seconds':json.loads(completion.read_text())['seconds'],'proposal':result,'objective':objective,'promoted':promoted,'best':copy.deepcopy(best[arm])}
            save(completed,row);histories[arm].append(row);save(public,{'status':'training','lock':lock,'base_proposal':base_metrics,'arms':histories,'test_inference':False,'guard_generated':False});print(json.dumps({'seed':seed,'arm':arm,'round':r,'proposal_objective':objective,'promoted':promoted,'active_round':best[arm]['round']}),flush=True)
    frozen={'arms':best,'all_arms_complete':all(len(h)==3 for h in histories.values()),'guard_generation_preceded_selection':False,'test_inference':False};assert frozen['all_arms_complete']
    selection=folder/'frozen_selection.json'
    if selection.exists():assert json.loads(selection.read_text())==frozen
    else:save(selection,frozen);emit(folder,'all_selections_frozen',sha256=sha(selection))
    report={'status':'guard_running','lock':lock,'base_proposal':base_metrics,'arms':histories,'selection':frozen,'guard':{},'test_inference':False}
    states=[('base',None)]+[(f'{a}-round{r}',folder/f'{a}-round{r}/adapter') for a in arms for r in range(1,4)]
    for name,adapter in states:
        report['guard'][name]={}
        for condition in ['ranked','permuted','reversed']:
            cases=[view(c,condition) for c in data['guard']];rows=local.infer(cases,adapter);save(folder/f'{name}-guard-{condition}.json',rows);report['guard'][name][condition]=local.metric(rows,cases);save(public,report)
            print(json.dumps({'seed':seed,'guard_state':name,'condition':condition,'drug_f1':report['guard'][name][condition]['drug_micro_f1']}),flush=True)
    report['status']='executed_pending_audit';save(public,report);print(json.dumps({'seed':seed,'status':report['status']}),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('seed',type=int);a=p.parse_args();main(a.seed)
