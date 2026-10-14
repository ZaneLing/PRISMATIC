"""Audit completed author runs, then execute the single common test gate."""
import json,os,subprocess,sys,time
from pathlib import Path
from test_gate import check
HERE=Path(__file__).resolve().parent;PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v27'
def main():
    env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','VECLIB_MAXIMUM_THREADS':'1'}
    jobs=[(p,m,s) for p in ['full','molecular'] for m in (['ARMR','GAMENet'] if p=='full' else ['ARMR','GAMENet','SafeDrug']) for s in [42,137,2026]]
    while True:
        for panel,method,seed in jobs:
            source=HERE/f'results/{panel}-{method}-seed{seed}.json';audit=HERE/f'results/{panel}-{method}-selection-audit-seed{seed}.json'
            if not source.exists() or json.loads(source.read_text())['status']!='selection_frozen':continue
            if audit.exists() and json.loads(audit.read_text())['status']=='passed':continue
            print(json.dumps({'auditing':[panel,method,seed]}),flush=True)
            with (PRIVATE/f'{panel}-{method}-selection-audit-seed{seed}.log').open('a') as log:
                subprocess.run([sys.executable,str(HERE/'audit_author_selection.py'),panel,method,str(seed)],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        gate=check()
        if gate['status']=='open':break
        time.sleep(30)
    print(json.dumps({'status':'all_selections_and_audits_frozen','starting_common_test':True}),flush=True)
    for script in ['evaluate_methods.py','audit_test_results.py','report.py']:
        subprocess.run([sys.executable,'-u',str(HERE/script)],env=env,check=True)
    print(json.dumps({'status':'common_test_and_audit_complete'}),flush=True)
if __name__=='__main__':main()
