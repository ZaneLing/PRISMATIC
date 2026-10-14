"""Execute the four registered100-step repair fits serially and preserve original weights."""
import fcntl,hashlib,json,os,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v32';MODEL=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/models/qwen3-4b-instruct-2507-4bit'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,z):
    p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(z,indent=2)+'\n');tmp.replace(p)
def sources():return {name:sha(HERE/name) for name in ['protocol.json','decision_loss.py','train_cli.py','training_config.yaml','prepare.py','run_training.py','results/data_audit.json']}
def main():
    spec=json.loads((HERE/'protocol.json').read_text());audit=json.loads((HERE/'results/data_audit.json').read_text());probe=json.loads((HERE/'results/runtime_probe.json').read_text());assert audit['status']=='passed' and probe['status']=='passed' and probe['source_sha256']==sources()
    assert sha(PRIVATE/'data/train.jsonl')==audit['source_train_sha256'] and sha(PRIVATE/'data/valid.jsonl')==audit['source_valid_sha256'] and sha(PRIVATE/'decision_config.json')==audit['decision_config_sha256'] and sha(HERE/'protocol.json')==audit['protocol_sha256']
    handle=(PRIVATE/'training-process.lock').open('w');fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
    lock={'source_sha256':sources(),'runtime_probe_sha256':sha(HERE/'results/runtime_probe.json'),'model_files_sha256':probe['model_files_sha256']}
    assert all(sha(MODEL/name)==h for name,h in lock['model_files_sha256'].items())
    if (PRIVATE/'training-lock.json').exists():assert json.loads((PRIVATE/'training-lock.json').read_text())==lock
    else:save(PRIVATE/'training-lock.json',lock)
    result={'status':'training','lock':lock,'arms':{},'proposal_scores_available':False,'guard_or_test_inference':False,'api_calls':0};env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','VECLIB_MAXIMUM_THREADS':'1'}
    for arm in spec['arms']:
        folder=PRIVATE/arm;folder.mkdir(exist_ok=True);done=folder/'training_complete.json'
        if done.exists():
            receipt=json.loads(done.read_text());assert sha(folder/'adapter/adapters.safetensors')==receipt['adapter_sha256'];result['arms'][arm]=receipt;continue
        adapter=folder/'adapter'
        if adapter.exists() and any(adapter.iterdir()):
            archived=folder/f'interrupted-adapter-{time.time_ns()}';adapter.rename(archived)
            if (folder/'training.log').exists():(folder/'training.log').rename(archived/'training.log')
        command=[sys.executable,str(HERE/'train_cli.py'),'--decision-arm',arm,'--decision-config',str(PRIVATE/'decision_config.json'),'--model',str(MODEL),'--train','--data',str(PRIVATE/'data'),'--fine-tune-type','lora','--mask-prompt','--num-layers','8','--batch-size','4','--iters','100','--learning-rate','0.0001','--steps-per-report','20','--steps-per-eval','100','--val-batches','8','--save-every','100','--max-seq-length','1536','--adapter-path',str(adapter),'--seed','42','--config',str(HERE/'training_config.yaml'),'--grad-checkpoint']
        save(HERE/'results/training_progress.json',{**result,'current_arm':arm});print(json.dumps({'training_begin':arm,'steps':100}),flush=True);start=time.perf_counter()
        with (folder/'training.log').open('w') as stream:subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,env=env,check=True)
        receipt={'arm':arm,'optimizer_steps':100,'binary_target_decisions_expected':8000,'seconds':time.perf_counter()-start,'adapter_sha256':sha(adapter/'adapters.safetensors'),'training_log_sha256':sha(folder/'training.log'),'command':command};save(done,receipt);result['arms'][arm]=receipt;save(HERE/'results/training_progress.json',result);print(json.dumps({'training_complete':arm,'seconds':receipt['seconds']}),flush=True)
    result['status']='four_fits_executed_pending_evaluation_and_audit';save(HERE/'results/training_progress.json',result);print(json.dumps({'status':result['status']}),flush=True)
if __name__=='__main__':main()
