"""Evaluate all frozen skill versions, including exact factorial controls."""
import hashlib,json,os,shutil,subprocess,sys,threading,time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
RESOURCE=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/resources/GRASP'
sys.path[:0]=[str(RESOURCE),str(ROOT/'upgrade_v8'),str(ROOT/'upgrade_v10')]
from public_client import LOCAL,request
from grasp.skills.repository import SkillRepository
from grasp.skills.agent import SkillAwareAgent
from grasp_task import MedicationTask
from grounded_task import GroundedMedicationTask

class TrackedBackend:
    def __init__(self):self.latest=threading.local()
    def inference(self,history,tools=None):
        assert tools is None
        messages=[{'role':'assistant' if h['role']=='agent' else h['role'],'content':h['content']} for h in history]
        r=request(messages,'deepseek/deepseek-v4.1-flash',512,'grasp_actor')
        if r.get('error'):raise RuntimeError('Incomplete transport response')
        self.latest.response=r;return r['raw']

def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')

def main():
    os.environ['RXRSI_PUBLIC_COST_CAP_USD']='25'
    save(HERE/'results/round_evaluation_protocol.json',{'purpose':'Reconstruct and evaluate every accepted skill state on fixed test and transfer sets after selection is frozen.',
        'training_cases':[0,157,314,471,625],'rounds':[0,1,2,3,4],'states':['empty','empty','history_v1','history_v2','final'],
        'selection_unchanged':True,'test_used_for_selection':False,'cost_cap_cumulative_usd':25})
    while True:
        processes=subprocess.check_output(['ps','-axo','command'],text=True)
        if not any('python upgrade_v17/run_grounded_skills.py' in x for x in processes.splitlines()):break
        time.sleep(30)
    assert json.loads((HERE/'results/method_results.json').read_text())['status']=='complete'
    folder=LOCAL/'grounded-grasp-v17-seed-42';best=folder/'skills/best';base=folder/'empty-base'
    artifact=HERE/'artifacts';artifact.mkdir(exist_ok=True)
    # Only public-task generated skill text; no patient data or raw traces.
    hashes={}
    for name,source in [('round_2',best/'.history/label_indication_and_caution_parsing_v1.md'),('round_3',best/'.history/label_indication_and_caution_parsing_v2.md'),('round_4',best/'label_indication_and_caution_parsing.md')]:
        out=artifact/name;out.mkdir(exist_ok=True);path=out/'label_indication_and_caution_parsing.md';shutil.copyfile(source,path)
        hashes[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    save(HERE/'results/round_artifacts.json',hashes)
    evidence=GroundedMedicationTask();ordinary=MedicationTask();author=LOCAL/'official-grasp-seed-42/skills/best'
    methods=[('cot',ordinary,base),('author_grasp',ordinary,author),('fixed_grounded',evidence,base),
        ('round_2',evidence,artifact/'round_2'),('round_3',evidence,artifact/'round_3'),('round_4',evidence,artifact/'round_4')]
    result={'status':'partial','methods':{}};cache=folder/'round_evaluation';cache.mkdir(exist_ok=True)
    for name,task,skills in methods:
        result['methods'][name]={};backend=TrackedBackend();agent=SkillAwareAgent(backend,SkillRepository(base_dir=base,learned_dir=skills))
        for dataset,cases in [('rxsafebench',task.samples('test')),('rxqa',task.transfer)]:
            def one(c):
                r=task.rollout(c,agent);u=backend.latest.response
                return {'case_id':c['id'],'prediction':r.answer or None,'correct':task.evaluate(c,r),**{k:u.get(k) for k in ['cost_usd','input_tokens','output_tokens','request_sha256']}}
            with ThreadPoolExecutor(max_workers=8) as pool:rows=list(pool.map(one,cases))
            save(cache/(name+'-'+dataset+'.json'),rows)
            result['methods'][name][dataset]={'n':len(rows),'correct':sum(r['correct'] for r in rows),'accuracy':sum(r['correct'] for r in rows)/len(rows),
                'invalid':sum(r['prediction'] is None for r in rows),'logical_cost_usd':sum(r['cost_usd'] or 0 for r in rows)}
            save(HERE/'results/round_metrics.json',result);print(json.dumps({'method':name,'dataset':dataset,**result['methods'][name][dataset]}),flush=True)
    result['status']='complete';save(HERE/'results/round_metrics.json',result)

if __name__=='__main__':main()
