"""Observe live seed processes, then run the frozen evaluation and audit chain."""
import json,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent

def main():
    seeds=[42,137,2026]
    while True:
        missing=[]
        for s in seeds:
            p=HERE/f'results/selection_seed_{s}.json'
            if not p.exists() or json.loads(p.read_text()).get('status')!='selection_frozen':missing.append(s)
        if not missing:break
        processes=subprocess.check_output(['ps','-axo','command'],text=True)
        for s in missing:
            if f'upgrade_v23/train.py {s}' not in processes and not (HERE/f'results/selection_seed_{s}.json').exists():
                raise RuntimeError(f'Seed {s} stopped before selection freeze; inspect its log before resuming')
        time.sleep(30)
    for script in ['evaluate.py','audit.py','report.py']:
        subprocess.run([sys.executable,str(HERE/script)],check=True)

if __name__=='__main__':main()
