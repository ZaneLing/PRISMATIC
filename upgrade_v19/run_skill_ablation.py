"""Evaluate frozen single-skill states only after the main study fully audits."""
import contextlib,hashlib,io,json,os,shutil,subprocess,sys,time,types
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
RESOURCE=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/resources/GRASP'
LOCAL=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/medagentbench-native'
sys.path[:0]=[str(RESOURCE),str(ROOT/'upgrade_v8'),str(ROOT/'upgrade_v14')]
from grasp.skills.repository import SkillRepository
from grasp.skills.agent import SkillAwareAgent
from public_client import digest

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')

def audit(row,case,task,skills):
    """Recompute reference outcomes and physical field/cleanup validity."""
    from reference_compat import reference_view
    from fhir_executor import BASE
    from order_compiler import compile_order
    signature=digest([task.code_hash,task.mode,case['id'],skills]);assert row['episode_digest']==signature
    raw=read(task.cache/(signature+'.json'));assert raw['case_id']==case['id'] and not raw['grader_errors']
    assert raw['model_calls']==len(raw['usage'])<=8 and raw['tool_calls']==len(raw['tools'])
    active=[];all_checks=[]
    for w in raw['write_audits']:
        if w['create_status']!=201 or not isinstance(w['create_receipt'],dict) or not w['create_receipt'].get('id'):continue
        canonical=w['canonical_payload'];assert compile_order(w.get('submitted_payload',canonical))[0]==canonical
        stored=w['readback'];valid=w['readback_status']==200 and all(stored.get(k)==v for k,v in canonical.items() if k not in ['id','meta'])
        assert valid==w['persisted'];all_checks.append(valid)
        if w['rolled_back']:assert w['rollback_status'] in (200,204)
        else:active.append(valid)
    assert all_checks==raw['write_checks'] and active==raw['active_post_checks']
    assert len(active)==raw['writes']==len(raw['cleanup_checks'])
    assert all(c['status'] in (200,204) for c in raw['cleanup_checks'])
    semantic,conversions=reference_view(raw['live_trace'])
    assert semantic==raw['semantic_trace'] and conversions==raw['reference_projection_audits']
    def grade(trace):
        if raw['status']!='completed' or raw['answer'] is None:return False
        obj=types.SimpleNamespace(history=[types.SimpleNamespace(**m) for m in trace],result=raw['answer'])
        with contextlib.redirect_stdout(io.StringIO()):return bool(getattr(task.grader,case['id'].split('_')[0])(case,obj,BASE))
    original=grade(raw['original_trace']);legacy=grade(raw['live_trace']);reference=grade(semantic);correct=reference and all(active)
    assert original==raw['original_trace_correct'] and legacy==raw['legacy_live_reference_correct']
    assert reference==raw['semantic_reference_correct'] and correct==raw['live_execution_correct']==row['live_execution_correct']
    assert abs(raw['cost_usd']-sum(x['cost_usd'] or 0 for x in raw['usage']))<1e-12
    return int(correct)

def main():
    protocol=read(HERE/'ablation_protocol.json')
    while not (HERE/'results/summary.json').exists():
        processes=subprocess.check_output(['ps','-axo','command'],text=True)
        if not any('python upgrade_v19/run_fhir_evolution.py' in x for x in processes.splitlines()):raise RuntimeError('Main study stopped before audit; ablation does not start.')
        time.sleep(30)
    main_report=read(HERE/'results/summary.json');assert main_report['status']=='complete'
    os.environ['RXRSI_PUBLIC_COST_CAP_USD']=str(protocol['cumulative_successful_response_cap_usd'])
    from fhir_task import FHIRTask,FHIRBackend
    from probe_fhir_state import total
    from summarize import interval,patient_interval
    best=LOCAL/'grasp-v19/skills/best';assert {p.name:sha(p) for p in best.glob('*.md')}==protocol['frozen_skill_sha256']
    before={r:total(r) for r in main_report['resource_counts_after']};assert before==main_report['resource_counts_after']
    assert not list((LOCAL/'active').glob('*.json'))
    folder=LOCAL/'grasp-v19-ablation';folder.mkdir(exist_ok=True);empty=LOCAL/'grasp-v19/empty'
    task=FHIRTask();report={'status':'partial','methods':{},'source_code_hash':task.code_hash,'protocol_sha256':sha(HERE/'ablation_protocol.json')};correctness={}
    for condition,filename in protocol['conditions'].items():
        single=folder/condition;single.mkdir(exist_ok=True)
        assert not any(p.name!=filename for p in single.iterdir())
        shutil.copyfile(best/filename,single/filename);assert sha(single/filename)==protocol['frozen_skill_sha256'][filename]
        actor=SkillAwareAgent(FHIRBackend(protocol['model']),SkillRepository(base_dir=empty,learned_dir=single));skills=actor.skill_repo.load_all()
        correctness[condition]={};report['methods'][condition]={}
        for split in ['id_test','test']:
            cases=task.samples(split);rows=[];values=[]
            for case in cases:
                row=task.rollout(case,actor).raw;values.append(audit(row,case,task,skills));rows.append(row)
            save(folder/(condition+'-'+split+'.json'),rows);correctness[condition][split]=np.array(values)
            z={'n':len(rows),'state_correct':sum(values),'original_trace_correct':sum(r['original_trace_correct'] for r in rows),
               'model_calls':sum(r['model_calls'] for r in rows),'tool_calls':sum(r['tool_calls'] for r in rows),'logical_cost_usd':sum(r['cost_usd'] for r in rows),
               'independent_reference_receipt_and_skill_binding_audit':'passed'}
            report['methods'][condition][split]=z;save(HERE/'results/skill_ablation.json',report)
            print(json.dumps({'condition':condition,'split':split,**z}),flush=True)
    for condition,method in [('neither','fixed_compiled'),('both','evolving_compiled')]:
        correctness[condition]={};report['methods'][condition]=main_report['methods'][method]
        for split in ['id_test','test']:
            rows=read(LOCAL/'grasp-v19'/(method+'-'+split+'.json'))
            correctness[condition][split]=np.array([int(r['live_execution_correct']) for r in rows])
    report['paired']={}
    for split in ['id_test','test']:
        cases=task.samples(split);v={k:z[split] for k,z in correctness.items()};pairs={}
        for label,delta in {'both_minus_name_only':v['both']-v['name_only'],'both_minus_lab_only':v['both']-v['lab_only'],
              'name_only_minus_neither':v['name_only']-v['neither'],'lab_only_minus_neither':v['lab_only']-v['neither'],
              'interaction':v['both']-v['name_only']-v['lab_only']+v['neither']}.items():
            pairs[label]={'task_bootstrap':interval(delta),'patient_bootstrap':patient_interval(delta,cases)}
        report['paired'][split]=pairs
    after={r:total(r) for r in before};assert after==before and not list((LOCAL/'active').glob('*.json'))
    report.update(status='complete',resource_counts_before=before,resource_counts_after=after,claim_boundary=protocol['claim_boundary'])
    save(HERE/'results/skill_ablation.json',report);print(json.dumps(report),flush=True)

if __name__=='__main__':main()
