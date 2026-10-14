"""Learn real-tool skills on development, freeze before full ID/OOD evaluation."""
import hashlib,json,os,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
RESOURCE=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/resources/GRASP'
sys.path[:0]=[str(RESOURCE),str(ROOT/'upgrade_v8'),str(ROOT/'upgrade_v14')]
from grasp.cycle import SkillCycleRunner
from grasp.skills.repository import SkillRepository
from grasp.skills.agent import SkillAwareAgent
from public_client import LOCAL as API_LOCAL
from probe_fhir_state import total

def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')

def main():
    (HERE/'results').mkdir(exist_ok=True)
    protocol={'source_commit':'9d7d125a3e9b46ed591692475eb07aff4ae67d34','optimizer':'Unmodified author GRASP core; new real-FHIR task adapter',
        'train_n':96,'validation_n':80,'id_test_n':64,'heldout_task_type_test_n':60,'feedback_batches':4,'cases_per_batch':24,
        'proposal_slots':4,'balanced_training_probe_n':12,'max_action_calls':8,'actor_tokens':512,'proposer_tokens':3072,
        'model':'deepseek/deepseek-v4.1-flash','evolving':['Language skill files'],'fixed':['FHIR compiler','protocol feedback','backbone weights'],
        'controls':['literal direct tools','fixed compiled/verified harness'],'serialized_episodes':True,
        'episode_cache':'Revision2 exact code/mode/case/skill digest. Legacy compiled episodes may be adopted only with successful field-preserving readbacks/cleanup, unchanged compiler output and exact case/skills. Only grades are recomputed; learned legacy skills are discarded. Physical operations and logical cost are distinguished.',
        'actor_inputs':'instruction/context and actual tool replies only; no sol/eval_MRN fields',
        'feedback':'Patient-ID-redacted training traces and revised automatic state grades; only task1 includes literal sol, all other literal targets remain null and use the reference grader; no test labels in learning.',
        'patient_split_note':'Official task splits overlap in patients; not patient-disjoint.',
        'state_score':'Unchanged original reference evaluated through lossless legacy shape views, AND canonical intent fields preserved on real readback. Singleton note arrays become legacy objects and text-only route objects become legacy strings for grading only. Same projection and canonical intent comparison apply to every arm; original raw grades are reported separately. Not an unmodified official benchmark score. Duration-like legacy rate fields remain semantically unvalidated.',
        'grading_revision':'Development discovered13 false negatives from FHIR R4 note arrays. Prior run stopped before selection/test, archived and restarted with empty skills. No ID/OOD test informed this revision; see results/grading_revision.json.',
        'selection':'End-of-epoch best validation checkpoint from the author core, before ID/OOD testing.',
        'cost_cap_cumulative_usd':28}
    save(HERE/'protocol.json',protocol)
    if '--register-only' in sys.argv:return
    # Finish the funded model comparison first; avoid charging competing studies.
    while True:
        processes=subprocess.check_output(['ps','-axo','command'],text=True)
        transfer=ROOT/'upgrade_v18/results/method_results.json'
        transfer_complete=transfer.exists() and json.loads(transfer.read_text()).get('status')=='complete'
        if transfer_complete and not any(any(s in x for s in ['python upgrade_v18/run_backbone_transfer.py','python upgrade_v17/run_rounds.py']) for x in processes.splitlines()):break
        time.sleep(30)
    os.environ['RXRSI_PUBLIC_COST_CAP_USD']='28'
    # Load the executor only when the queued experiment starts, so its saved
    # code digest describes the code actually executed after preparation.
    from fhir_task import FHIRTask,FHIRBackend,LOCAL
    pin=subprocess.check_output(['git','rev-parse','HEAD'],cwd=RESOURCE,text=True).strip();assert pin==protocol['source_commit']
    assert not subprocess.check_output(['git','diff','--','grasp'],cwd=RESOURCE,text=True).strip()
    counts={r:total(r) for r in ['Patient','MedicationRequest','Observation','ServiceRequest']}
    assert counts==json.loads((HERE/'results/grading_revision.json').read_text())['resource_counts_after_stop']
    task=FHIRTask();folder=LOCAL/'grasp-v19';folder.mkdir(exist_ok=True);empty=folder/'empty';empty.mkdir(exist_ok=True)
    config={'agent':{'module':'fhir_task.FHIRBackend','parameters':{'model':protocol['model'],'temperature':0}},'skills':{'base_dir':str(empty)},'_resume':True,
        'cycle':{'epochs':1,'update_every':24,'batch_concurrency':1,'max_proposals':1,'max_learned_skills':6,'grpo_k':4,'grpo_eval_n':12,'run_baseline':True,'proposal_temperature':.7,'seed':42}}
    save(folder/'execution_config.json',config);SkillCycleRunner(config,folder,task).run()
    best=folder/'skills/best';hashes={str(p.relative_to(best)):hashlib.sha256(p.read_bytes()).hexdigest() for p in best.rglob('*') if p.is_file()}
    save(HERE/'results/frozen_skills.json',{'skills_sha256':hashes,'test_used':False,'protocol':protocol})
    report={'status':'partial','methods':{}}
    for name,environment,skills in [('direct_tools',FHIRTask('direct'),empty),('fixed_compiled',task,empty),('evolving_compiled',task,best)]:
        actor=SkillAwareAgent(FHIRBackend(protocol['model']),SkillRepository(base_dir=empty,learned_dir=skills));report['methods'][name]={}
        for split in ['id_test','test']:
            rows=[]
            for case in environment.samples(split):
                r=environment.rollout(case,actor);rows.append(r.raw)
            save(folder/(name+'-'+split+'.json'),rows)
            report['methods'][name][split]={'n':len(rows),'trace_correct':sum(r['original_trace_correct'] for r in rows),'state_correct':sum(r['live_execution_correct'] for r in rows),
                'legacy_live_reference_correct':sum(r['legacy_live_reference_correct'] for r in rows),'semantic_reference_correct':sum(r['semantic_reference_correct'] for r in rows),
                'model_calls':sum(r['model_calls'] for r in rows),'tool_calls':sum(r['tool_calls'] for r in rows),'logical_cost_usd':sum(r['cost_usd'] for r in rows),
                'writes':sum(r['writes'] for r in rows),'failed_readback':sum(not all(r['write_checks']) for r in rows)}
            save(HERE/'results/method_results.json',report);print(json.dumps({'method':name,'split':split,**report['methods'][name][split]}),flush=True)
    after={r:total(r) for r in counts};assert after==counts
    report.update(status='complete',resource_counts_before=counts,resource_counts_after=after);save(HERE/'results/method_results.json',report)
    subprocess.run([sys.executable,str(HERE/'summarize.py')],check=True)

if __name__=='__main__':main()
