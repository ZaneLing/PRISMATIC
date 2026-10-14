"""Audit each completed development run; no test evaluation is scheduled."""
import json,os,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v29'
def main():
    pending={(p,s) for p in ['full','molecular'] for s in [42,137,2026]};env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','VECLIB_MAXIMUM_THREADS':'1'}
    while pending:
        changed=False
        for panel,seed in sorted(pending):
            path=HERE/f'results/{panel}-seed{seed}.json';out=HERE/f'results/{panel}-audit-seed{seed}.json'
            if not path.exists() or json.loads(path.read_text())['status']!='selection_frozen':continue
            if not out.exists():
                print(json.dumps({'auditing':[panel,seed]}),flush=True)
                with (PRIVATE/f'audit-{panel}-seed{seed}.log').open('a') as log:
                    subprocess.run([sys.executable,'-u',str(HERE/'audit.py'),panel,str(seed)],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
            assert json.loads(out.read_text())['status']=='passed';pending.remove((panel,seed));changed=True
        if pending and not changed:time.sleep(30)
    for script in ['summarize.py','report.py']:
        subprocess.run([sys.executable,str(HERE/script)],env=env,check=True)
    print(json.dumps({'status':'all_development_runs_audited','test_inference':False}),flush=True)
if __name__=='__main__':main()
