"""Fixed cross-backbone comparison after development-only budget selection."""
import hashlib,json,os,subprocess,sys,threading,time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
RESOURCE=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/resources/GRASP'
sys.path[:0]=[str(RESOURCE),str(ROOT/'upgrade_v8'),str(ROOT/'upgrade_v10'),str(ROOT/'upgrade_v17')]
from public_client import LOCAL,request
from grasp.skills.repository import SkillRepository
from grasp.skills.agent import SkillAwareAgent
from grasp_task import MedicationTask
from grounded_task import GroundedMedicationTask

def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def hashes(folder):return {str(p.relative_to(folder)):hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file()}

class Backend:
    def __init__(self):self.latest=threading.local()
    def inference(self,history,tools=None):
        assert tools is None
        messages=[{'role':'assistant' if h['role']=='agent' else h['role'],'content':h['content']} for h in history]
        r=request(messages,'google/gemini-3.8-flash',2048,'backbone_transfer_actor',reasoning_effort='low',timeout_seconds=180)
        if r.get('error'):raise RuntimeError('Incomplete transport response ('+str(r['error'])+'); no task score emitted')
        self.latest.response=r;return r['raw']

def main():
    (HERE/'results').mkdir(exist_ok=True)
    protocol={'model':'google/gemini-3.8-flash','max_output_tokens':2048,'reasoning_effort':'low','test_n':988,'calls_per_case':1,
        'methods':['cot','frozen_author_grasp','fixed_grounded','frozen_grounded_grasp'],
        'skill_selection':'Transfer frozen DeepSeek-learned v10 and v17 skills unchanged; no Gemini skill learning or test-based selection.',
        'token_selection':'v16 development-only budget study, before Gemini test scoring',
        'prompt':'Same MedicationTask prompt/option parser; only declared label evidence and skill injection differ.',
        'scope':'Same derived RxSafeBench split, not original benchmark equivalence; cross-backbone artifact transfer.',
        'cost_cap_cumulative_usd':25,'cost_note':'After explicit user funding recovery. Engineering ledger cap includes historical public studies; not a per-method inference cost.'}
    save(HERE/'protocol.json',protocol)
    os.environ['RXRSI_PUBLIC_COST_CAP_USD']='25'
    # Wait without competing with the still-running proposer for its budget.
    while True:
        processes=subprocess.check_output(['ps','-axo','command'],text=True)
        if not any('python upgrade_v17/run_grounded_skills.py' in line for line in processes.splitlines()):break
        time.sleep(30)
    completed=json.loads((ROOT/'upgrade_v17/results/method_results.json').read_text());assert completed['status']=='complete'
    frozen=json.loads((ROOT/'upgrade_v16/results/frozen_test_configuration.json').read_text());assert not frozen['test_used']
    folder=LOCAL/'backbone-transfer-v18';folder.mkdir(exist_ok=True);empty=folder/'empty';empty.mkdir(exist_ok=True)
    author=LOCAL/'official-grasp-seed-42/skills/best';grounded=LOCAL/'grounded-grasp-v17-seed-42/skills/best'
    assert hashes(grounded)==json.loads((ROOT/'upgrade_v17/results/frozen_skills.json').read_text())['skills_sha256']
    assert hashes(author)==json.loads((ROOT/'upgrade_v10/results/grasp_core_frozen_seed_42.json').read_text())['frozen_skill_sha256']
    save(HERE/'results/frozen_transfer.json',{'protocol':protocol,'author_skill_hashes':hashes(author),'grounded_skill_hashes':hashes(grounded),'test_labels_used':False})
    ordinary=MedicationTask();evidence=GroundedMedicationTask();report={'status':'partial','methods':{}}
    for name,task,skills in [('cot',ordinary,empty),('frozen_author_grasp',ordinary,author),('fixed_grounded',evidence,empty),('frozen_grounded_grasp',evidence,grounded)]:
        backend=Backend();agent=SkillAwareAgent(backend,SkillRepository(base_dir=empty,learned_dir=skills));cases=task.samples('test')
        def one(c):
            r=task.rollout(c,agent);u=backend.latest.response
            return {'case_id':c['id'],'prediction':r.answer or None,'correct':task.evaluate(c,r),'status':r.status,
                **{k:u.get(k) for k in ['input_tokens','output_tokens','cost_usd','finish_reason','reasoning_tokens','request_sha256']}}
        with ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(one,cases))
        save(folder/(name+'-test.json'),rows)
        assert [r['case_id'] for r in rows]==[c['id'] for c in cases]
        report['methods'][name]={'n':len(rows),'correct':sum(r['correct'] for r in rows),'accuracy':sum(r['correct'] for r in rows)/len(rows),
            'invalid':sum(r['prediction'] is None for r in rows),'cost_usd':sum(r['cost_usd'] or 0 for r in rows),
            'input_tokens':sum(r['input_tokens'] or 0 for r in rows),'output_tokens':sum(r['output_tokens'] or 0 for r in rows),
            'finish_length':sum(r['finish_reason']=='length' for r in rows)}
        save(HERE/'results/method_results.json',report);print(json.dumps({'method':name,**report['methods'][name]}),flush=True)
    report['status']='complete';save(HERE/'results/method_results.json',report)

if __name__=='__main__':main()
