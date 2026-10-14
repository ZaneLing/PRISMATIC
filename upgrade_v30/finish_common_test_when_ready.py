"""Wait for all registered frozen methods, then evaluate/audit/report once."""
import json,os,subprocess,sys,time
from pathlib import Path
from common_test_gate import check
HERE=Path(__file__).resolve().parent
def main():
    env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','VECLIB_MAXIMUM_THREADS':'1'};previous=None
    while True:
        gate=check();current=(gate['status'],len(gate['pending']))
        if current!=previous:print(json.dumps({'common_test_gate':current[0],'pending_items':current[1]}),flush=True);previous=current
        if gate['status']=='open':break
        time.sleep(30)
    for script in ('evaluate_program_tests.py','audit_program_tests.py','report_common_test.py'):
        subprocess.run([sys.executable,'-u',str(HERE/script)],env=env,check=True)
    print(json.dumps({'status':'program_test_extension_and_audit_complete'}),flush=True)
if __name__=='__main__':main()
