"""Real-state MedAgentBench task adapter for an unchanged GRASP skill loop."""
import hashlib,json,re,sys,threading
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
RESOURCE=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/resources/GRASP'
sys.path[:0]=[str(RESOURCE),str(ROOT/'upgrade_v8'),str(ROOT/'upgrade_v10'),str(ROOT/'upgrade_v14')]
from grasp import Task,Rollout
from grasp_task import PublicBackend
from public_client import digest,request
from fhir_executor import run_case,grader_module,LOCAL
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
        self.cache=LOCAL/'learning-v19';self.cache.mkdir(exist_ok=True)
        self.code_hash=digest([hashlib.sha256((HERE/f).read_bytes()).hexdigest() for f in ['fhir_executor.py','order_compiler.py','fhir_task.py']])

    def samples(self,split):
        return [dict(c,description=redact(c['instruction']+'\n'+c['context']),answer=redact(c['sol']),type=c['id'].split('_')[0]) for c in self.parts[split]]

    def rollout(self,sample,agent):
        skills=agent.skill_repo.load_all() if hasattr(agent,'skill_repo') else []
        signature=digest([self.code_hash,self.mode,sample['id'],skills]);path=self.cache/(signature+'.json')
        with STATE_LOCK:
            if path.exists():row=json.loads(path.read_text())
            else:
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
        return Rollout(history=redact(row['history']),agent_actions=redact([m['content'] for m in row['history'] if m['role']=='assistant']),
            answer=row['answer'] or '',status=row['status'],raw=summary)

    def evaluate(self,sample,rollout):return bool(rollout.raw['live_execution_correct'])
    def failure_tags(self,sample,rollout):
        tags=[sample['id'].split('_')[0],rollout.status]
        if not all(rollout.raw['write_checks']):tags.append('persisted_field_loss')
        return tags
