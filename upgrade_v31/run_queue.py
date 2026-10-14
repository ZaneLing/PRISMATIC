"""Run local seeds serially to bound memory pressure and preserve every state."""
import os,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v31'
def main():
    PRIVATE.mkdir(exist_ok=True);env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','VECLIB_MAXIMUM_THREADS':'1'}
    for seed in [42,137,2026]:
        with (PRIVATE/f'seed{seed}.log').open('a') as log:subprocess.run([sys.executable,'-u',str(HERE/'run.py'),str(seed)],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
if __name__=='__main__':main()
