"""Sequential seed jobs in each declared label panel."""
import argparse,json,os,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v29'
def main(panel):
    PRIVATE.mkdir(exist_ok=True);env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','VECLIB_MAXIMUM_THREADS':'1'}
    for seed in [42,137,2026]:
        result=HERE/f'results/{panel}-seed{seed}.json'
        if result.exists() and json.loads(result.read_text())['status']=='selection_frozen':continue
        print(json.dumps({'starting':[panel,seed]}),flush=True)
        with (PRIVATE/f'{panel}-seed{seed}.log').open('a') as log:
            subprocess.run([sys.executable,'-u',str(HERE/'train.py'),panel,str(seed)],stdout=log,stderr=subprocess.STDOUT,env=env,check=True)
    print(json.dumps({'status':'panel_selection_frozen','panel':panel,'test_inference':False}),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('panel',choices=['full','molecular']);main(p.parse_args().panel)
