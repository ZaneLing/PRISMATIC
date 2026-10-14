"""Bounded sequential jobs per method; CPU and GPU lanes may run concurrently."""
import argparse, json, os, subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v27'

def main(method):
    jobs=[(panel,seed) for panel in (['molecular'] if method=='SafeDrug' else ['full','molecular']) for seed in [42,137,2026]]
    env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','VECLIB_MAXIMUM_THREADS':'1'}
    for panel,seed in jobs:
        out=HERE/f'results/{panel}-{method}-seed{seed}.json'
        if out.exists() and json.loads(out.read_text())['status']=='selection_frozen':continue
        print(json.dumps({'starting':[panel,method,seed]}),flush=True)
        with (PRIVATE/f'{panel}-{method}-seed{seed}.log').open('a') as log:
            subprocess.run([sys.executable,'-u',str(HERE/'train_author.py'),panel,method,str(seed)],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    print(json.dumps({'queue_complete':method,'test_inference':False}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('method',choices=['ARMR','GAMENet','SafeDrug']);main(p.parse_args().method)
