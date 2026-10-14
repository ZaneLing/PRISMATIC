"""Recount public pilot grades, resource cleanup, and fixture patient coverage."""
import collections,json,sys,types
from pathlib import Path
from run_agent_pilot import HERE,LOCAL,RESOURCE,grader_module,BASE
from probe_fhir_state import request,total

def main():
    cases=json.loads((RESOURCE/'data/medagentbench/split_dev.json').read_text());by_id={c['id']:c for c in cases}
    grader=grader_module();result=json.loads((HERE/'results/agent_development_pilot.json').read_text());audit={'methods':{}}
    for method,summary in result['methods'].items():
        rows=[json.loads(p.read_text()) for p in sorted((LOCAL/'pilot').glob(method+'-*.json'))];passed=0;groups={}
        for r in rows:
            c=by_id[r['case_id']];trace=[types.SimpleNamespace(role='agent' if h['role']=='assistant' else h['role'],content=h['content']) for h in r['history'][2:]]
            obj=types.SimpleNamespace(history=trace,result=r['answer'])
            correct=False
            if r['status']=='completed' and r['answer'] is not None:
                correct=bool(getattr(grader,c['id'].split('_')[0])(c,obj,BASE)) and all(r['write_checks'])
            assert correct==r['live_execution_correct'];passed+=correct
            group=groups.setdefault(c['id'].split('_')[0],{'n':0,'correct':0});group['n']+=1;group['correct']+=correct
        assert passed==summary['live_execution_correct'] and len(rows)==summary['n']
        audit['methods'][method]={'independent_regrade':'passed','correct':passed,'n':len(rows),'status_counts':dict(collections.Counter(r['status'] for r in rows)),'task_types':groups}
    before=json.loads((HERE/'results/fhir_state_probe.json').read_text())['counts_before']
    after={k:total(k) for k in before};assert before==after
    assert not list((LOCAL/'active').glob('*.json'))
    mrns=sorted({c['eval_MRN'] for c in cases});present=sum(request('GET','Patient/'+m)[0]==200 for m in mrns)
    assert present==len(mrns)
    audit.update({'post_pilot_resource_counts':after,'original_counts_restored':True,'active_cleanup_journals':0,
        'development_fixture_coverage':{'unique_patients':len(mrns),'present':present},'test_used':False})
    (HERE/'results/pilot_audit.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(audit))

if __name__=='__main__':main()
