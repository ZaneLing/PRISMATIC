"""Recount and publish the finite local diagnosis after its saved report is complete."""
import json,os,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main():
    path=HERE/'results/collapse_diagnostic.json'
    while not path.exists() or json.loads(path.read_text()).get('status')!='executed':
        commands=subprocess.check_output(['ps','-axo','command'],text=True).splitlines()
        if not any('python -u upgrade_v31/diagnose_collapse.py' in c or 'python3.12' in c and 'diagnose_collapse.py' in c for c in commands):raise RuntimeError('Diagnostic stopped before completion; inspect its saved log.')
        time.sleep(30)
    env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','VECLIB_MAXIMUM_THREADS':'1'}
    for script in ['audit_collapse_diagnostic.py','plot_collapse.py','report_collapse.py','report.py']:
        subprocess.run([sys.executable,str(HERE/script)],env=env,check=True)
    print(json.dumps({'status':'collapse_diagnostic_recounted_and_reported','test_predictions_read':False}),flush=True)
if __name__=='__main__':main()
