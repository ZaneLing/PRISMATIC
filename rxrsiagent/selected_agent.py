"""Current benchmark agent; historical core.py/evaluated_profile.json stay archived.

Only load the trusted local calibration file bound by the selected profile hash.
A changed choice never inherits the source-agent explanation as its own rationale.
"""
import hashlib,json,pickle,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'upgrade_v35'))
from workflow import Agent
from common import RUN
from calibrate import predict
class SelectedRxRSIAgent:
 def __init__(self,calibration_path=None):
  self.profile=json.loads((ROOT/'rxrsiagent/selected_profile.json').read_text())
  for f,h in self.profile['code_sha256'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h
  p=Path(calibration_path) if calibration_path else RUN/'calibration/selected.pkl'
  assert hashlib.sha256(p.read_bytes()).hexdigest()==self.profile['calibration_sha256']
  with p.open('rb') as f:self.calibration=pickle.load(f)
  self.agent=Agent()
 def finalize(self,c,trace):
  scored=predict(self.calibration,[c],[trace],.2)[0];changed=scored['prediction']!=trace['prediction']
  return {'case_id':c['id'],'prediction':scored['prediction'],'decision_provenance':'supervised_calibration' if scored['applied'] else 'source_agent','choice_changed':changed,'calibration':scored,'source_agent_choice':trace['prediction'],'source_agent_explanation':trace.get('final',{}).get('evidence'),'final_explanation':None if changed else trace.get('final',{}).get('evidence'),'unresolved':['Calibration override requires a newly validated explanation'] if changed else [],'trace':trace,'scope':'Offline benchmark option selection; no clinical clearance'}
 def solve(self,c):
  assert all(k in c for k in ('id','dialogue','options'))
  clean={k:c[k] for k in ('id','dialogue','options')}
  return self.finalize(clean,self.agent.solve(clean,'verified_evidence'))
