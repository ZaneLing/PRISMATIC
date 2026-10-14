"""Audit newly completed states while training continues; no API or test calls."""
import hashlib,json,os,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v31'
def main():
    last={};done=set();env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','VECLIB_MAXIMUM_THREADS':'1'}
    while len(done)<3:
        for seed in [42,137,2026]:
            folder=PRIVATE/f'seed{seed}'
            if not all((folder/f'base-proposal-{c}.json').exists() for c in ['ranked','permuted']):continue
            paths=sorted(folder.glob('*-round*/complete.json'));state=HERE/f'results/seed{seed}.json';status=json.loads(state.read_text())['status'] if state.exists() else 'base_only'
            signature=(len(paths),status,hashlib.sha256((HERE/'audit_learning.py').read_bytes()).hexdigest())
            if last.get(seed)==signature:continue
            print(json.dumps({'audit_seed':seed,'completed_updates':len(paths),'stage':status}),flush=True)
            with (PRIVATE/f'audit-seed{seed}.log').open('a') as log:subprocess.run([sys.executable,'-u',str(HERE/'audit_learning.py'),str(seed)],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
            last[seed]=signature
            if json.loads((HERE/f'results/audit-seed{seed}.json').read_text())['status']=='passed':done.add(seed)
        subprocess.run([sys.executable,str(HERE/'report.py')],env=env,check=True)
        if len(done)<3:time.sleep(30)
    print(json.dumps({'status':'three_seeds_audited','test_inference':False}),flush=True)
if __name__=='__main__':main()
