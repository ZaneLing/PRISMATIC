"""Pinned GRASP author-core skill at the common4608-token output allowance."""
import json,sys,threading
from concurrent.futures import ThreadPoolExecutor,as_completed
from common import ROOT,HERE,RUN,LOCAL,MODEL,configure,save,sha,digest,request
RESOURCE=LOCAL.parent/'resources/GRASP'
sys.path[:0]=[str(RESOURCE),str(ROOT/'upgrade_v10')]
from grasp.skills.repository import SkillRepository
from grasp.skills.agent import SkillAwareAgent
from grasp_task import MedicationTask
class Backend:
 def __init__(self):self.local=threading.local()
 def inference(self,history,tools=None):
  assert tools is None
  messages=[{'role':'assistant' if m['role']=='agent' else m['role'],'content':m['content']} for m in history]
  self.local.receipt=request(messages,MODEL,4608,role='rx35_grasp_common_budget')
  if self.local.receipt.get('error'):raise RuntimeError('Incomplete transport')
  return self.local.receipt['raw']
def main():
 configure();data=json.loads((LOCAL/'data.json').read_text());base=RUN/'empty_grasp';base.mkdir(exist_ok=True);skills=LOCAL/'official-grasp-seed-42/skills/best';backend=Backend();agent=SkillAwareAgent(backend,SkillRepository(base_dir=base,learned_dir=skills));task=MedicationTask()
 save(HERE/'grasp_budget_protocol.json',{'core_commit':'9d7d125a3e9b46ed591692475eb07aff4ae67d34','skill_sha256':{p.name:sha(p) for p in skills.glob('*.md')},'code_sha256':sha(HERE/'run_grasp_budget.py'),'output_allowance':4608,'calls':1,'training':'Same previously selected author-core skill; no new feedback.'})
 for split,cases in [('test',data['parts']['test']),('rxqa',data['transfer'])]:
  folder=RUN/'grasp'/split;folder.mkdir(parents=True,exist_ok=True)
  def one(c):
   p=folder/(digest(c['id'])+'.json')
   if p.exists():return json.loads(p.read_text())
   output=task.rollout({k:c[k] for k in ('id','dialogue','options')},agent);r={'case_id':c['id'],'prediction':output.answer or None,'calls':[backend.local.receipt]};save(p,r);return r
  out={}
  with ThreadPoolExecutor(max_workers=24) as pool:
   for f in as_completed([pool.submit(one,c) for c in cases]):
    r=f.result();out[r['case_id']]=r
    if len(out)%100==0:print(json.dumps({'method':'grasp','split':split,'done':len(out),'n':len(cases)}),flush=True)
  rows=[out[c['id']] for c in cases];calls=[r['calls'][0] for r in rows];d={'status':'complete','n':len(cases),'correct':sum(r['prediction']==c['gold'] for r,c in zip(rows,cases)),'invalid':sum(r['prediction'] is None for r in rows),'calls':len(calls),'input_tokens':sum(r['input_tokens'] for r in calls),'output_tokens':sum(r['output_tokens'] for r in calls),'logical_cost_usd':sum(r['cost_usd'] or 0 for r in calls),'predictions_sha256':digest([r['prediction'] for r in rows])};d['accuracy']=d['correct']/d['n'];save(HERE/'results'/f'grasp-{split}.json',d);print(json.dumps(d),flush=True)
if __name__=='__main__':main()
