"""Audit the completed fixed factorial and render its bilingual report."""
import json,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main():
    while True:
        try:z=json.loads((HERE/'results/method_results.json').read_text())
        except (FileNotFoundError,json.JSONDecodeError):time.sleep(30);continue
        if z['status']=='execution_complete_pending_independent_audit':break
        time.sleep(30)
    for script in ['audit_results.py','report.py']:
        subprocess.run([sys.executable,str(HERE/script)],check=True)
    print(json.dumps({'status':'factorial_complete_and_audited'}),flush=True)
if __name__=='__main__':main()
