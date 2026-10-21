"""Run after all development decisions, before audit inference and metrics."""
import datetime
from common52 import *
names=['qwen-52','qwen-152','qwen-52-shuffle','tool-52']
path=PRIVATE/'selection_lock.json'
assert not path.exists(),'Selection already frozen; do not overwrite'
assert not (PRIVATE/'qwen-audit.json').exists(),'Audit actor already started'
assert not (HERE/'results/evaluation.json').exists(),'Audit metrics already exist'
save(path,{'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'states':{n:sha(PRIVATE/(n+'-states.json')) for n in names},'implementation':{p.name:sha(p) for p in HERE.glob('*.py')},'audit_used_for_selection':False})
save(HERE/'results/selection_lock.json',json.loads(path.read_text()))
print('All learning states frozen before new-patient audit inference.',flush=True)
