"""Run the registered subset analysis after both frozen parent comparisons pass."""
import json,os,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
def main():
    env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','VECLIB_MAXIMUM_THREADS':'1'};paths=[ROOT/'upgrade_v27/results/test_audit.json',ROOT/'upgrade_v30/results/common_test_audit.json'];last=None
    while True:
        pending=[str(p.relative_to(ROOT)) for p in paths if not p.exists() or json.loads(p.read_text()).get('status')!='passed']
        if pending!=last:print(json.dumps({'pending_parent_audits':pending}),flush=True);last=pending
        if not pending:break
        time.sleep(30)
    for script in ('evaluate_prior_case_subsets.py','report_exposure.py'):subprocess.run([sys.executable,'-u',str(HERE/script)],env=env,check=True)
    print(json.dumps({'status':'registered_prior_case_subset_scoring_complete'}),flush=True)
if __name__=='__main__':main()
