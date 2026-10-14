"""Run fixed checkpoints on original and rank-preserving reordered catalogues."""
import hashlib,json,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v26';SOURCE=PRIVATE.parent/'prismatic-v15'
sys.path.insert(0,str(ROOT/'upgrade_v15'))
import run_parameter_evolution as local
local.PRIVATE=PRIVATE

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    protocol=json.loads((HERE/'protocol.json').read_text());assert sha(PRIVATE/'guard_conditions.json')==protocol['prepared_guard_sha256']
    lock={'protocol_sha256':sha(HERE/'protocol.json'),'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [HERE/'run_diagnostic.py',HERE/'prepare.py',ROOT/'upgrade_v15/run_parameter_evolution.py',ROOT/'upgrade_v15/generation_receipts.py',ROOT/'upgrade_v15/selection_parser.py']}}
    lp=HERE/'results/execution_lock.json'
    if lp.exists():assert json.loads(lp.read_text())==lock
    else:local.save(lp,lock)
    data=json.loads((PRIVATE/'guard_conditions.json').read_text());progress={'status':'partial','models':{}}
    for model,adapter in [('base',None),('uniform_sft_round2',SOURCE/'uniform_sft-round-2'),('error_prioritized_sft_round2',SOURCE/'error_prioritized_sft-round-2')]:
        if adapter:assert sha(adapter/'adapters.safetensors')==protocol['adapter_sha256'][model.removesuffix('_round2')]
        progress['models'][model]={}
        for condition,cases in data.items():
            start=time.time();rows=local.infer(cases,adapter);local.save(PRIVATE/(model+'-'+condition+'.json'),rows)
            metrics=local.metric(rows,cases);progress['models'][model][condition]={'metrics':metrics,'wall_seconds':time.time()-start}
            local.save(HERE/'results/generation_progress.json',progress)
            print(json.dumps({'model':model,'condition':condition,'drug_order_f1':[metrics['drug_micro_f1'],metrics['core_order_micro_f1']],'complete':True}),flush=True)
    progress['status']='complete';local.save(HERE/'results/generation_progress.json',progress)
    subprocess.run([sys.executable,str(HERE/'summarize.py')],check=True)

if __name__=='__main__':main()
