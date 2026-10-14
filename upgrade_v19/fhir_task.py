"""Real-state MedAgentBench task adapter for an unchanged GRASP skill loop."""
import hashlib,json,re,sys,threading
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
RESOURCE=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/resources/GRASP'
sys.path[:0]=[str(RESOURCE),str(ROOT/'upgrade_v8'),str(ROOT/'upgrade_v10'),str(ROOT/'upgrade_v14')]
from grasp import Task,Rollout
from grasp_task import PublicBackend
from public_client import digest,request
from fhir_executor import run_case,grader_module,LOCAL,BASE
from order_compiler import compile_order
from reference_compat import regrade_cached
STATE_LOCK=threading.Lock()

class FHIRBackend(PublicBackend):
    def __init__(self,model,temperature=0):super().__init__(model,temperature);self.latest=threading.local()
    def inference(self,history,tools=None):
        if self.temperature>0:return super().inference(history,tools)
        messages=[{'role':'assistant' if m['role']=='agent' else m['role'],'content':m['content']} for m in history]
        result=request(messages,self.model,512,'fhir_actor')
        if result.get('error'):raise RuntimeError('Incomplete FHIR actor transport response')
        self.latest.response=result;return result['raw']

def redact(value):
    return json.loads(re.sub(r'\bS[0-9]{4,}\b','[PATIENT_ID]',json.dumps(value)))

class FHIRTask(Task):
    name='medagentbench-real-fhir-compiled'
    updater_task_family='FHIR tool execution and conditional prescription ordering'
    updater_guidance='Learn reusable retrieval, temporal comparison, conditional ordering and strict action-format procedures from training failures. Never memorize patient IDs, names, dates, task IDs or final numeric answers. Read needed records before deciding. The task states the numerical ordering rules; do not invent clinical guidelines. The fixed harness compiles route strings to FHIR CodeableConcept.text and checks actual stored fields.'
    updater_failure_examples='invalid_action, incorrect_patient_search, wrong_latest_measurement, missed_conditional_order, incorrect_order_field, persisted_field_loss'

    def __init__(self,mode='compiled'):
        self.mode=mode;self.grader=grader_module();self.parts={};folder=RESOURCE/'benchmarks/MedAgentBench/data/medagentbench'
        manifest=json.loads((ROOT/'upgrade_v14/results/task_manifest.json').read_text())
        for split in ['dev','val','id_test','test']:
            p=folder/f'split_{split}.json';assert hashlib.sha256(p.read_bytes()).hexdigest()==manifest['splits'][split]['sha256']
            self.parts[split]=json.loads(p.read_text())
        self.cache=LOCAL/'learning-v19-rev2';self.cache.mkdir(exist_ok=True)
        self.code_hash=digest([hashlib.sha256((HERE/f).read_bytes()).hexdigest() for f in ['fhir_executor.py','order_compiler.py','reference_compat.py','fhir_task.py']])

    def adopt_legacy(self,sample,skills):
        # Replay only identical physical compiled episodes. Failed readbacks or
        # changed submitted bodies would alter the next actor turn and must run
        # again. No learned skill state from the invalidated run is adopted.
        if self.mode!='compiled':return None
        revision=json.loads((HERE/'results/grading_revision.json').read_text())
        old_digest=digest([revision['legacy_code_hash'],self.mode,sample['id'],skills])
        path=LOCAL/'learning-v19'/(old_digest+'.json')
        if not path.exists():return None
        row=json.loads(path.read_text())
        if row['case_id']!=sample['id'] or row['method']!='verified_state_harness' or row.get('grader_errors'):return None
        if not all(row['write_checks']) or not all(row['active_post_checks']):return None
        if len(row['cleanup_checks'])!=row['writes'] or any(c['status'] not in (200,204) for c in row['cleanup_checks']):return None
        for w in row['write_audits']:
            if w['create_status']!=201 or not w['persisted'] or w['rolled_back']:return None
            p=w['canonical_payload'];stored=w['readback']
            if compile_order(p)[0]!=p:return None
            if w['readback_status']!=200 or any(stored.get(k)!=v for k,v in p.items() if k not in ['id','meta']):return None
        revised=regrade_cached(row,sample,self.grader,BASE)
        revised.update(physical_episode_digest=old_digest,cache_adoption='legacy physical receipts; unchanged payload/actor replies; revised grades only',
            legacy_cache_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        return revised

    def samples(self,split):
        # Only task1 supplies a literal solution. Other released task types are
        # graded by reference functions against FHIR data/action state. Missing
        # literal answers are unknown, not empty answers or failed tasks.
        return [dict(c,description=redact(c['instruction']+'\n'+c['context']),answer=redact(c.get('sol')),type=c['id'].split('_')[0]) for c in self.parts[split]]

    def rollout(self,sample,agent):
        skills=agent.skill_repo.load_all() if hasattr(agent,'skill_repo') else []
        signature=digest([self.code_hash,self.mode,sample['id'],skills]);path=self.cache/(signature+'.json')
        with STATE_LOCK:
            if path.exists():row=json.loads(path.read_text())
            else:
                row=self.adopt_legacy(sample,skills)
                if row is None:
                    backend=agent
                    while hasattr(backend,'agent'):backend=backend.agent
                    def actor(history):
                        agent.inference(history);return backend.latest.response
                    compiled=self.mode=='compiled'
                    row=run_case(sample,'verified_state_harness' if compiled else 'direct_tool',self.grader,actor=actor,compile_payloads=compiled,repair_protocol=compiled)
                path.write_text(json.dumps(row,indent=2)+'\n')
        # Source IDs are scheduling/evaluation data only, never actor inputs.
        # Feedback history is redacted to discourage identity-specific skills.
        summary={k:row[k] for k in ['case_id','status','original_trace_correct','live_execution_correct','model_calls','tool_calls','cost_usd','writes','write_checks','protocol_repairs','compilation_audits']}
        summary.update(episode_digest=signature,physical_episode_digest=row.get('physical_episode_digest',signature),
            legacy_live_reference_correct=row['legacy_live_reference_correct'],semantic_reference_correct=row['semantic_reference_correct'],
            grading_revision=row['grading_revision'],grader_exception_count=len(row.get('grader_errors',[])))
        return Rollout(history=redact(row['history']),agent_actions=redact([m['content'] for m in row['history'] if m['role']=='assistant']),
            answer=row['answer'] or '',status=row['status'],raw=summary)

    def evaluate(self,sample,rollout):return bool(rollout.raw['live_execution_correct'])
    def failure_tags(self,sample,rollout):
        tags=[sample['id'].split('_')[0],rollout.status]
        if not all(rollout.raw['write_checks']):tags.append('persisted_field_loss')
        return tags
