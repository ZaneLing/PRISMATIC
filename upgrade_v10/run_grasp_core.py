"""Execute the pinned author GRASP core on our public Task adapter."""
import argparse,hashlib,json,subprocess,sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
HERE=Path(__file__).resolve().parent
RESOURCE=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/resources/GRASP'
PIN='9d7d125a3e9b46ed591692475eb07aff4ae67d34'
sys.path.insert(0,str(RESOURCE));sys.path.insert(0,str(HERE.parent/'upgrade_v8'))
from public_client import LOCAL,digest
from grasp.cycle import SkillCycleRunner
from grasp.skills.repository import SkillRepository
from grasp.skills.agent import SkillAwareAgent
from grasp_task import MedicationTask,PublicBackend

def run(seed):
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=RESOURCE,text=True).strip();assert commit==PIN
    assert not subprocess.check_output(['git','diff','--','grasp'],cwd=RESOURCE,text=True).strip()
    task=MedicationTask();folder=LOCAL/f'official-grasp-seed-{seed}';folder.mkdir(exist_ok=True)
    base=folder/'empty-base';base.mkdir(exist_ok=True)
    config={'agent':{'module':'grasp_task.PublicBackend','parameters':{'model':'deepseek/deepseek-v4.1-flash','temperature':0}},
      'skills':{'base_dir':str(base)},'_resume':True,
      'cycle':{'epochs':1,'update_every':157,'batch_concurrency':10,'max_proposals':1,'max_learned_skills':6,
       'grpo_k':4,'grpo_eval_n':40,'run_baseline':True,'proposal_temperature':.7,'seed':seed}}
    (folder/'execution_config.json').write_text(json.dumps(config,indent=2)+'\n')
    runner=SkillCycleRunner(config,folder,task);runner.run()
    best=folder/'skills/best';repo=SkillRepository(base_dir=base,learned_dir=best)
    agent=SkillAwareAgent(PublicBackend('deepseek/deepseek-v4.1-flash'),repo)
    frozen={str(p.relative_to(best)):hashlib.sha256(p.read_bytes()).hexdigest() for p in best.rglob('*') if p.is_file()}
    (HERE/'results').mkdir(exist_ok=True)
    manifest={'source_commit':PIN,'core_modified':False,'adapter':'grasp_task.py','seed':seed,'train_n':625,'validation_n':387,
        'configuration':config,'frozen_skill_sha256':frozen,'test_labels_used_for_updates':False,
        'comparison_note':'Author core on our new task adapter; not an original MedAgentBench or FHIR-AgentBench score. Training/proposal cost differs from v8.'}
    (HERE/f'results/grasp_core_frozen_seed_{seed}.json').write_text(json.dumps(manifest,indent=2)+'\n')
    report={'seed':seed,'source_commit':PIN,'datasets':{}}
    for name,cases in [('rxsafebench',task.samples('test')),('rxqa',task.transfer)]:
        def one(c):
            r=task.rollout(c,agent)
            return {'case_id':c['id'],'prediction':r.answer or None,'correct':task.evaluate(c,r),'status':r.status}
        with ThreadPoolExecutor(max_workers=10) as pool:rows=list(pool.map(one,cases))
        (folder/(name+'-test.json')).write_text(json.dumps(rows)+'\n')
        report['datasets'][name]={'n':len(rows),'correct':sum(r['correct'] for r in rows),'accuracy':sum(r['correct'] for r in rows)/len(rows),'invalid':sum(r['prediction'] is None for r in rows)}
        (HERE/f'results/grasp_core_seed_{seed}.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({'dataset':name,**report['datasets'][name]}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seed',type=int,default=42);a=p.parse_args();run(a.seed)
