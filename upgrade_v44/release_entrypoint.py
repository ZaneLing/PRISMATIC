"""Current frozen RxRSIAgent; no numerical option-calibration override."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'upgrade_v44'))
from runtime import RuntimeAgent
class SelectedRxRSIAgent:
 def __init__(self):
  self.profile=json.loads((ROOT/'rxrsiagent/selected_profile.json').read_text())
  for path,value in self.profile['code_sha256'].items():
   assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==value,path
  self.state=self.profile['state'];self.agent=RuntimeAgent(self.state)
 def solve(self,c):
  assert all(k in c for k in ('id','dialogue','options'))
  clean={k:c[k] for k in ('id','dialogue','options','multiple') if k in c}
  r=self.agent.solve(clean)
  return dict(r,method='RxRSIAgent',decision_provenance='frozen_source_and_procedural_workflow',numeric_calibration_applied=False,scope='Offline option selection; source checks are not clinical clearance')
