"""Finish independent development audits as each registered rule run freezes."""
import json,os,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v27'
def main():
    env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','VECLIB_MAXIMUM_THREADS':'1'}
    pending={(panel,seed) for panel in ['full','molecular'] for seed in [42,137,2026]}
    while pending:
        changed=False
        for panel,seed in sorted(pending):
            state=HERE/f'results/{panel}-rsi-seed{seed}.json'
            if not state.exists() or json.loads(state.read_text())['status']!='selection_frozen':continue
            for kind,script,status in [('crossfit','audit_rule_crossfit.py','complete'),('learning','audit_rule_learning.py','passed')]:
                result=HERE/f'results/{panel}-rsi-{kind}-audit-seed{seed}.json'
                if result.exists() and json.loads(result.read_text())['status']==status:continue
                print(json.dumps({'audit':kind,'panel':panel,'seed':seed}),flush=True)
                with (PRIVATE/f'{kind}-audit-{panel}-{seed}.log').open('a') as log:
                    subprocess.run([sys.executable,'-u',str(HERE/script),panel,str(seed)],stdout=log,stderr=subprocess.STDOUT,env=env,check=True)
            pending.remove((panel,seed));changed=True
        if pending and not changed:time.sleep(30)
    subprocess.run([sys.executable,str(HERE/'audit_rule_decisions.py')],env=env,check=True)
    subprocess.run([sys.executable,str(HERE/'summarize_rule_learning.py')],env=env,check=True)
    subprocess.run([sys.executable,str(HERE/'report.py')],env=env,check=True)
    print(json.dumps({'status':'all_rule_development_audits_complete','test_inference':False}),flush=True)
if __name__=='__main__':main()
