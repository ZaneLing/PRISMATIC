"""Replay validated local proposals, finish repaired aggregate updates and evaluate."""
import json,os,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v51'
for name in ['learn.py','cloud_learn.py','cloud_evaluate.py']:
 env=os.environ.copy()
 if name=='learn.py':env['RXRSI_REFLECTION_REPLAY']=str(PRIVATE/'local_before_schema_fix')
 else:env.pop('RXRSI_REFLECTION_REPLAY',None)
 with (PRIVATE/('final-'+name.replace('.py','.log'))).open('w') as log:
  code=subprocess.call([sys.executable,'-u',str(HERE/name)],cwd=HERE.parent,env=env,stdout=log,stderr=subprocess.STDOUT)
 if code:raise RuntimeError(name+' failed with code '+str(code))
 if name=='learn.py':
  old=json.loads((PRIVATE/'local_before_schema_fix/trajectory.json').read_text());new=json.loads((HERE/'results/trajectory.json').read_text())
  assert [r['metrics'] for r in old['trajectory']]==[r['metrics'] for r in new['trajectory']], 'Frozen local metrics changed'
  print('Local metrics preserved after schema/optional-diagnosis repair.',flush=True)
 print(name+' complete',flush=True)
