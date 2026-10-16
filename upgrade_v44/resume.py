"""Complete missing cases with a recorded runtime-only schema repair."""
import sys,json,importlib.util
from pathlib import Path
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'upgrade_v37'));sys.path.insert(0,str(ROOT/'upgrade_v40'))
from common37 import RUN as BASE_RUN,save,sha,digest,configure
from runtime import RuntimeAgent
s=importlib.util.spec_from_file_location('resume_runner',ROOT/'upgrade_v40/run40.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.RUN=BASE_RUN.parent/'rxrsi-v44';m.Agent40=RuntimeAgent

def main():
 configure();data=json.loads((BASE_RUN/'data.json').read_text());learn=json.loads((HERE/'results/learning.json').read_text());freeze=json.loads((HERE/'test_freeze.json').read_text());assert sha(HERE/'results/learning.json')==freeze['learning_sha256'];cs=data['test_rx'];state=learn['rounds'][-1]['state'];assert state==learn['rounds'][0]['state']
 p=HERE/'runtime_amendment.json';folder=m.RUN/'runs'/digest(state)/'test_rx'
 if not p.exists():
  done={f.name:sha(f) for f in folder.glob('*.json')};missing=[c['id'] for c in cs if (digest(c['id'])+'.json') not in done];save(p,{'created_utc':datetime.now(timezone.utc).isoformat(),'reason':'Two incomplete cases raised TypeError because extracted focus was a list. Convert only non-string focus values for evidence-query construction. No GT or test correctness selects the repair.','runtime_code_sha256':sha(HERE/'runtime.py'),'resume_code_sha256':sha(__file__),'original_test_freeze_sha256':sha(HERE/'test_freeze.json'),'completed_before':len(done),'missing_case_ids':missing,'completed_file_hashes':done,'changes_to_completed_predictions':False})
 a=json.loads(p.read_text());assert a['runtime_code_sha256']==sha(HERE/'runtime.py') and a['resume_code_sha256']==sha(__file__)
 for name,h in a['completed_file_hashes'].items():assert sha(folder/name)==h
 rows,metrics=m.batch(cs,state,'test_rx');repairs=sum(bool(r['evidence'].get('schema_repairs')) for r in rows)
 for name,h in a['completed_file_hashes'].items():assert sha(folder/name)==h
 out={k:{'state_sha256':digest(state),'metrics':metrics} for k in ['initial','final']};out['runtime_amendment']={'file':'upgrade_v44/runtime_amendment.json','schema_repaired_cases':repairs};save(HERE/'results/main-test_rx.json',out);print(json.dumps({'metrics':metrics,'schema_repaired':repairs}))
if __name__=='__main__':main()
