"""Wait for immutable training/selection receipts, then score and independently recount."""
import fcntl
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from evaluation_gate import check

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIVATE = Path.home() / 'Desktop/MedTreeBench/dataset/restricted/prismatic-v32'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    handle = (PRIVATE / 'evaluation-process.lock').open('a')
    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    def check_preflight():
        proof = json.loads((HERE / 'results/evaluation_probe.json').read_text())
        assert proof['status'] == 'passed' and proof['synthetic_only']
        assert proof['probe_sha256'] == sha(HERE / 'probe_evaluation.py')
        assert all(sha(ROOT / name) == digest for name, digest in proof['source_sha256'].items())

    check_preflight()
    env = {**os.environ, 'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1',
           'VECLIB_MAXIMUM_THREADS': '1'}

    def run(script, *args):
        subprocess.run([sys.executable, '-u', str(HERE / script), *args], env=env, check=True)

    arms = json.loads((HERE / 'protocol.json').read_text())['arms']
    previous = None
    while True:
        complete = tuple(arm for arm in arms if (PRIVATE / arm / 'training_complete.json').exists())
        if complete != previous:
            print(json.dumps({'stage': 'wait_for_all_training', 'completed_arms': complete}), flush=True)
            run('report.py')
            previous = complete
        if len(complete) == len(arms):
            break
        time.sleep(30)
    # A changed runtime, source file, target or adapter stops the observer; there is no silent retry.
    check_preflight()
    run('audit_training.py')
    run('evaluate.py', 'proposal')
    run('audit_evaluation.py', 'proposal')
    run('report.py')
    previous = None
    while True:
        gate = check('guard')
        current = (gate['status'], tuple(gate['pending']))
        if current != previous:
            print(json.dumps({'stage': 'wait_for_guard_gate', **gate}), flush=True)
            run('report.py')
            previous = current
        if gate['status'] == 'open':
            break
        time.sleep(30)
    check_preflight()
    run('evaluate.py', 'guard')
    run('audit_evaluation.py', 'guard')
    run('report.py')
    print(json.dumps({'status': 'four_arm_repair_scored_and_independently_recounted'}), flush=True)


if __name__ == '__main__':
    main()
