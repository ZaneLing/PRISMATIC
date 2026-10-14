"""Frozen-evidence plus author-core skill updates, with a no-update control."""
import hashlib,json,subprocess,sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
HERE=Path(__file__).resolve().parent
RESOURCE=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/resources/GRASP'
PIN='9d7d125a3e9b46ed591692475eb07aff4ae67d34'
sys.path.insert(0,str(RESOURCE));sys.path.insert(0,str(HERE.parent/'upgrade_v8'))
from public_client import LOCAL
from grasp.cycle import SkillCycleRunner
from grasp.skills.repository import SkillRepository
from grasp.skills.agent import SkillAwareAgent
from grounded_task import GroundedMedicationTask,PublicBackend

def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')

def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=RESOURCE,text=True).strip()==PIN
    assert not subprocess.check_output(['git','diff','--','grasp'],cwd=RESOURCE,text=True).strip()
    (HERE/'results').mkdir(exist_ok=True)
    folder=LOCAL/'grounded-grasp-v17-seed-42';folder.mkdir(exist_ok=True);base=folder/'empty-base';base.mkdir(exist_ok=True)
    protocol={'source_commit':PIN,'core_modified':False,'attribution':'GRASP author core optimizer plus RxRSI grounded task harness; no novel optimizer claim',
        'seed':42,'train':625,'validation':387,'test':988,'transfer':300,'round_size':157,'candidate_slots':4,'probe_n':40,
        'actor_tokens':512,'proposer_tokens':3072,'test_calls_per_case':1,'evidence_profile':'balanced (fixed before this experiment)',
        'evolving_objects':['language skill files'],'fixed_objects':['LLM weights','retrieval source code','label corpus','profile'],
        'controls':['same evidence and actor without skill updates','v10 author core without label evidence'],
        'test_selection':'Freeze best skills on validation before test; same test was observed in earlier development, so exploratory extension.',
        'restricted_data_sent':False}
    save(HERE/'protocol.json',protocol)
    task=GroundedMedicationTask()
    config={'agent':{'module':'grounded_task.PublicBackend','parameters':{'model':'deepseek/deepseek-v4.1-flash','temperature':0}},
        'skills':{'base_dir':str(base)},'_resume':True,'cycle':{'epochs':1,'update_every':157,'batch_concurrency':10,'max_proposals':1,
        'max_learned_skills':6,'grpo_k':4,'grpo_eval_n':40,'run_baseline':True,'proposal_temperature':.7,'seed':42}}
    save(folder/'execution_config.json',config)
    SkillCycleRunner(config,folder,task).run()
    best=folder/'skills/best';frozen={str(p.relative_to(best)):hashlib.sha256(p.read_bytes()).hexdigest() for p in best.rglob('*') if p.is_file()}
    save(HERE/'results/frozen_skills.json',{'skills_sha256':frozen,'test_used_for_selection':False,'protocol':protocol})
    report={'status':'partial','methods':{}}
    for method,learned in [('fixed_grounded',base),('evolving_grounded',best)]:
        actor=SkillAwareAgent(PublicBackend('deepseek/deepseek-v4.1-flash'),SkillRepository(base_dir=base,learned_dir=learned))
        report['methods'][method]={}
        for dataset,cases in [('rxsafebench',task.samples('test')),('rxqa',task.transfer)]:
            def one(c):
                r=task.rollout(c,actor)
                return {'case_id':c['id'],'prediction':r.answer or None,'correct':task.evaluate(c,r),'status':r.status}
            with ThreadPoolExecutor(max_workers=10) as pool:rows=list(pool.map(one,cases))
            save(folder/(method+'-'+dataset+'.json'),rows)
            report['methods'][method][dataset]={'n':len(rows),'correct':sum(r['correct'] for r in rows),'accuracy':sum(r['correct'] for r in rows)/len(rows),'invalid':sum(r['prediction'] is None for r in rows)}
            save(HERE/'results/method_results.json',report)
            print(json.dumps({'method':method,'dataset':dataset,**report['methods'][method][dataset]}),flush=True)
    report['status']='complete';save(HERE/'results/method_results.json',report)

if __name__=='__main__':main()
