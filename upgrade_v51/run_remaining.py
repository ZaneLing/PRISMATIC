"""Finish the declared proposer control and transfer serially, without GPU contention."""
import json,os,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v51'
source_pid=int(sys.argv[1])
while True:
 try:os.kill(source_pid,0)
 except ProcessLookupError:break
 time.sleep(10)
trajectory=HERE/'results/trajectory.json'
if not trajectory.exists() or not json.loads(trajectory.read_text()).get('complete'):raise RuntimeError('Local control did not complete; no dependent run started')
for name in ['cloud_learn.py','cloud_evaluate.py']:
 with (PRIVATE/('cloud-'+name.replace('.py','.log'))).open('w') as log:
  code=subprocess.call([sys.executable,'-u',str(HERE/name)],cwd=HERE.parent,stdout=log,stderr=subprocess.STDOUT)
 if code:raise RuntimeError(name+' failed with code '+str(code))
print('Both proposer trajectories, static control, and transfer completed.',flush=True)
