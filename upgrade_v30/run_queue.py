"""Wait for immutable audited sources, then run all registered seed variants."""
import argparse,json,os,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v30'
def main(panel):
    PRIVATE.mkdir(exist_ok=True);env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','VECLIB_MAXIMUM_THREADS':'1'}
    for seed in [42,137,2026]:
        source=HERE.parent/f'upgrade_v29/results/{panel}-audit-seed{seed}.json'
        while not source.exists():time.sleep(30)
        assert json.loads(source.read_text())['status']=='passed'
        print(json.dumps({'starting':[panel,seed]}),flush=True)
        with (PRIVATE/f'{panel}-seed{seed}.log').open('a') as log:subprocess.run([sys.executable,'-u',str(HERE/'run.py'),panel,str(seed)],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    print(json.dumps({'all_registered_runs_frozen':panel}),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('panel',choices=['full','molecular']);a=p.parse_args();main(a.panel)
