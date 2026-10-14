"""Execute all preregistered frozen repair conditions on the real local service."""
import hashlib,itertools,json,os,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
RESOURCE=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/resources/GRASP'
sys.path[:0]=[str(RESOURCE),str(ROOT/'upgrade_v8'),str(ROOT/'upgrade_v14'),str(ROOT/'upgrade_v19')]
from grasp.skills.repository import SkillRepository
from grasp.skills.agent import SkillAwareAgent
from fhir_task import FHIRBackend
from probe_fhir_state import total
from public_client import digest,ledger_total
from execution import run_case,grader_module,LOCAL

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
    tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(x,indent=2)+'\n');tmp.replace(p)
def code_lock():
    return {str(p.relative_to(ROOT)):sha(p) for p in [HERE/'execution.py',HERE/'contracts.py',HERE/'observation_tools.py',HERE/'run_factorial.py',
            ROOT/'upgrade_v19/order_compiler.py',ROOT/'upgrade_v19/reference_compat.py',ROOT/'upgrade_v19/fhir_task.py',ROOT/'upgrade_v14/probe_fhir_state.py']}
def main():
    protocol=json.loads((HERE/'protocol.json').read_text());os.environ['RXRSI_PUBLIC_COST_CAP_USD']=str(protocol['cumulative_successful_api_response_cap_usd'])
    assert not list((LOCAL/'active').glob('*.json'))
    counts={r:total(r) for r in ['Patient','MedicationRequest','Observation','ServiceRequest']}
    assert counts==json.loads((ROOT/'upgrade_v19/results/summary.json').read_text())['resource_counts_after']
    runtime=json.loads((HERE/'results/runtime_probe.json').read_text());assert runtime['status']=='passed'
    code=code_lock();assert all(sha(ROOT/p)==value for p,value in runtime['source_sha256'].items())
    frozen=json.loads((ROOT/'upgrade_v19/results/frozen_skills.json').read_text())['skills_sha256'];skills=LOCAL/'grasp-v19/skills/best'
    assert {p.name:sha(p) for p in skills.glob('*.md')}==frozen
    lock={'protocol_sha256':sha(HERE/'protocol.json'),'source_sha256':code,'skills_sha256':frozen,'model':protocol['model']}
    folder=LOCAL/'factorial-v28';folder.mkdir(exist_ok=True);cache=folder/'episodes';cache.mkdir(exist_ok=True)
    if (folder/'execution_lock.json').exists():assert json.loads((folder/'execution_lock.json').read_text())==lock
    else:save(folder/'execution_lock.json',lock)
    report={'status':'partial','lock':lock,'conditions':{},'resource_counts_before':counts,'physical_successful_response_ledger_start_usd':ledger_total()}
    result_path=HERE/'results/method_results.json'
    if result_path.exists():
        prior=json.loads(result_path.read_text());assert prior['lock']==lock
        if prior['status']=='complete':return
        report=prior
    save(result_path,report);grader=grader_module();empty=LOCAL/'grasp-v19/empty'
    # Finish all validation conditions before any test condition. No promotion.
    for split in ['val','id_test','test']:
        path=RESOURCE/'benchmarks/MedAgentBench/data/medagentbench'/('split_'+split+'.json')
        manifest=json.loads((ROOT/'upgrade_v14/results/task_manifest.json').read_text());assert sha(path)==manifest['splits'][split]['sha256']
        cases=json.loads(path.read_text());assert len(cases)==protocol['splits'][split]
        for contract,statistics,learned in itertools.product([False,True],repeat=3):
            condition=f'C{int(contract)}S{int(statistics)}K{int(learned)}';rows=[]
            state=SkillRepository(base_dir=empty,learned_dir=skills if learned else empty)
            backend=FHIRBackend(protocol['model']);agent=SkillAwareAgent(backend,state)
            def actor(history):agent.inference(history);return backend.latest.response
            report['conditions'].setdefault(condition,{'contract':contract,'statistics':statistics,'frozen_skills':learned,'splits':{}})
            for i,case in enumerate(cases):
                signature=digest([lock,condition,case['id']]);p=cache/(signature+'.json')
                if p.exists():row=json.loads(p.read_text())
                else:
                    row=run_case(case,'verified_state_harness',grader,actor=actor,answer_contract=contract,statistics=statistics)
                    row.update(episode_digest=signature,condition=condition);save(p,row)
                assert row['case_id']==case['id'] and row['condition']==condition and not row['grader_errors']
                assert row['model_calls']<=8 and len(row['usage'])==row['model_calls']
                rows.append(row)
                if (i+1)%20==0:print(json.dumps({'condition':condition,'split':split,'cases':i+1}),flush=True)
            save(folder/(condition+'-'+split+'.json'),[{'case_id':r['case_id'],'episode_digest':r['episode_digest']} for r in rows])
            summary={'n':len(rows),'state_correct':sum(r['live_execution_correct'] for r in rows),'raw_trace_correct':sum(r['original_trace_correct'] for r in rows),
              'model_calls':sum(r['model_calls'] for r in rows),'http_calls_excluding_cleanup':sum(r['tool_calls'] for r in rows),
              'logical_cost_usd':sum(r['cost_usd'] for r in rows),'answer_shape_rejections':sum(r['answer_shape_rejections'] for r in rows),
              'incomplete_observation_searches':sum(not a['view']['complete_search'] for r in rows for a in r['observation_audits']),
              'writes':sum(r['writes'] for r in rows),'failed_readbacks':sum(not x for r in rows for x in r['write_checks'])}
            report['conditions'][condition]['splits'][split]=summary;save(result_path,report);print(json.dumps({'condition':condition,'split':split,**summary}),flush=True)
    after={r:total(r) for r in counts};assert after==counts and not list((LOCAL/'active').glob('*.json'))
    report.update(status='execution_complete_pending_independent_audit',resource_counts_after=after,physical_successful_response_ledger_end_usd=ledger_total())
    save(result_path,report)

if __name__=='__main__':main()
