"""One sequential seed queue for each registered label panel."""
import argparse,json,os,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v27'
def main(panel):
    env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','VECLIB_MAXIMUM_THREADS':'1'}
    for seed in [42,137,2026]:
        path=HERE/f'results/{panel}-rsi-seed{seed}.json'
        if path.exists() and json.loads(path.read_text())['status']=='selection_frozen':continue
        print(json.dumps({'starting':panel,'seed':seed}),flush=True)
        with (PRIVATE/f'{panel}-rsi-seed{seed}.log').open('a') as stream:
            subprocess.run([sys.executable,'-u',str(HERE/'train_rule_agent.py'),panel,str(seed)],stdout=stream,stderr=subprocess.STDOUT,env=env,check=True)
    print(json.dumps({'queue_complete':panel,'test_inference':False}),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('panel',choices=['full','molecular']);main(p.parse_args().panel)
