"""Serialize GPU studies; independently summarize the completed preceding run."""
import json,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent

def main():
    while True:
        processes=subprocess.check_output(['ps','-axo','command'],text=True)
        if not any('python upgrade_v9/run_parameter_evolution.py' in line for line in processes.splitlines()):break
        time.sleep(30)
    path=ROOT/'upgrade_v9/results/parameter_results.json'
    if not path.exists():raise RuntimeError('Previous run ended before final results; v15 not launched')
    result=json.loads(path.read_text())
    assert set(result['arms'])=={'uniform_sft','error_prioritized_sft'}
    assert all(len(v['raw_checkpoint_curve'])==3 for v in result['arms'].values())
    py=str(Path.home()/'Desktop/PRISMATIC/upgrade_v2/.venv/bin/python')
    subprocess.run([py,str(ROOT/'upgrade_v9/summarize.py')],check=True,cwd=ROOT)
    print('v9 final predictions verified; starting the predeclared v15 intervention.',flush=True)
    subprocess.run([sys.executable,str(ROOT/'upgrade_v15/run_parameter_evolution.py')],check=True,cwd=ROOT)
    subprocess.run([py,str(ROOT/'upgrade_v15/summarize.py')],check=True,cwd=ROOT)

if __name__=='__main__':main()
