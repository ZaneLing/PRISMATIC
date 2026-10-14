"""Observe actual training completion before sealed evaluation and reporting."""
import json,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent

def main():
    seeds=json.loads((HERE/'protocol.json').read_text())['seeds']
    while True:
        missing=[]
        for seed in seeds:
            p=HERE/f'results/selection_seed_{seed}.json'
            if not p.exists() or json.loads(p.read_text()).get('status')!='selection_frozen':missing.append(seed)
        if not missing:break
        processes=subprocess.check_output(['ps','-axo','command'],text=True).splitlines()
        for seed in missing:
            if not any(f'upgrade_v25/train.py {seed}' in line for line in processes):
                raise RuntimeError(f'Seed {seed} ended before selection freeze. Inspect its log; no automatic restart.')
        time.sleep(30)
    for script in ['evaluate.py','audit_results.py','report.py']:
        subprocess.run([sys.executable,str(HERE/script)],check=True)

if __name__=='__main__':main()
