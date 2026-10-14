"""Real-write development pilot; original trace grading and state checks separate."""
import hashlib,importlib,json,sys,types,uuid
from pathlib import Path
HERE=Path(__file__).resolve().parent
RESOURCE=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/resources/GRASP/benchmarks/MedAgentBench'
LOCAL=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/medagentbench-native'
sys.path.insert(0,str(HERE.parent/'upgrade_v8'))
from public_client import request as model_request,digest
from probe_fhir_state import request as http_request,BASE


def grader_module():
    folder=RESOURCE/'src/server/tasks/medagentbench'
    name='prismatic_reference';module=types.ModuleType(name);module.__path__=[str(folder)];sys.modules[name]=module
    return importlib.import_module(name+'.refsol')


def tool_view(payload):
    # Remove only response-envelope IDs/timestamps; preserve clinical values,
    # patient/resource IDs, clinical times, query links and nested resources.
    if not isinstance(payload,dict):return payload
    d=dict(payload)
    if d.get('resourceType')=='Bundle':
        d.pop('id',None);d.pop('meta',None)
    return d


def valid_path(url):
    if not url.startswith(BASE):raise ValueError('Only the local benchmark FHIR endpoint is permitted')
    path=url[len(BASE):]
    if '..' in path or '://' in path:raise ValueError('Invalid local FHIR path')
    return path


def run_case(case,method,grader):
    funcs=json.loads((RESOURCE/'data/medagentbench/funcs_v1.json').read_text())
    prompt={'phase':'task_execution','task':{'description':case['instruction'],'context':case['context']+'\nCurrent time: 2023-11-13T10:15:00+00:00'},
        'api':{'base_url':BASE,'functions':funcs},'response_format':{'options':['GET url?parameters','POST url\n{json_payload}','FINISH([answer1, answer2, ...])'],
        'rules':['Exactly one action per turn; no other text.','FINISH contains a JSON list.']}}
    system='Solve this public MedAgentBench research task using the local FHIR API. Use only facts in the task and retrieved records.'
    verified=method=='verified_state_harness'
    if verified:system+=' Resolve the requested patient, retrieve needed observations and respect the stated clinical time. Before a write, check resource type, patient reference and all requested fields. Use the server receipt/readback to confirm execution. Finish only after every requested question or write is handled.'
    history=[{'role':'system','content':system},{'role':'user','content':json.dumps(prompt)}]
    original=[];live=[];created=[];tools=[];usage=[];answer=None;status='round_limit';post_checks=[]
    active=LOCAL/'active';active.mkdir(exist_ok=True);journal=active/(uuid.uuid4().hex+'.json')
    try:
        for round_index in range(8):
            response=model_request(history,'deepseek/deepseek-v4.1-flash',512,role='fhir_actor')
            if response.get('error'):raise RuntimeError('Incomplete model transport response; no task score emitted')
            raw=response['raw'].strip();usage.append({k:response.get(k,0) for k in ['input_tokens','output_tokens','cost_usd','seconds']})
            if raw.startswith('```') and raw.endswith('```'):raw=raw.split('\n',1)[-1].rsplit('```',1)[0].strip()
            history.append({'role':'assistant','content':raw});original.append({'role':'agent','content':raw});live.append({'role':'agent','content':raw})
            if raw.startswith('FINISH(') and raw.endswith(')'):
                try:
                    parsed=json.loads(raw[7:-1]);assert isinstance(parsed,list)
                    answer=raw[7:-1];status='completed'
                except (ValueError,AssertionError):status='invalid_finish'
                break
            if raw.startswith('GET '):
                try:path=valid_path(raw[4:].strip())
                except ValueError:status='invalid_action';break
                code,payload=http_request('GET',path);tools.append({'method':'GET','path':path,'status':code})
                message='FHIR response: '+json.dumps(tool_view(payload))
                if len(message)>60000:message=message[:60000]+'\n[Response truncated at 60,000 characters; use narrower search parameters.]'
                original_message=message
            elif raw.startswith('POST '):
                try:
                    line,body=raw.split('\n',1);path=valid_path(line[5:].strip());payload=json.loads(body)
                    assert path in ['Patient','Observation','MedicationRequest','ServiceRequest'] and isinstance(payload,dict)
                except (ValueError,AssertionError):
                    message='Invalid POST request';original_message=message
                else:
                    original_message='POST request accepted and executed successfully.'
                    preflight=True
                    if verified:
                        preflight=payload.get('resourceType')==path
                        reference=(payload.get('subject') or {}).get('reference')
                        if reference:
                            if not reference.startswith('Patient/'):preflight=False
                            else:
                                code,_=http_request('GET',reference);tools.append({'method':'GET','path':reference,'status':code,'harness_preflight':True});preflight &= code==200
                    if not preflight:message='Invalid POST request: verify the resource type and existing Patient reference.'
                    else:
                        code,result=http_request('POST',path,payload);tools.append({'method':'POST','path':path,'status':code})
                        if code==201 and isinstance(result,dict) and result.get('id'):
                            new_path=path+'/'+result['id'];created.append(new_path);journal.write_text(json.dumps(created))
                            read_code,stored=http_request('GET',new_path)
                            persisted=read_code==200 and stored.get('resourceType')==payload.get('resourceType')
                            for field in ['subject','medicationCodeableConcept','dosageInstruction']:
                                if field in payload:persisted &= stored.get(field)==payload[field]
                            post_checks.append(bool(persisted));tools.append({'method':'GET','path':new_path,'status':read_code,'postcondition_audit':True,'shown_to_actor':verified})
                            message='POST request accepted and executed successfully.'
                            if verified:message+=' Verified persisted state: '+json.dumps({k:stored[k] for k in ['resourceType','id','status','subject','medicationCodeableConcept','dosageInstruction'] if k in stored})
                        else:message='FHIR POST rejected: '+json.dumps(result)
            else:status='invalid_action';break
            history.append({'role':'user','content':message});live.append({'role':'user','content':message});original.append({'role':'user','content':original_message})
        def grade(trace):
            if answer is None or status!='completed':return False
            obj=types.SimpleNamespace(history=[types.SimpleNamespace(**x) for x in trace],result=answer)
            try:return bool(getattr(grader,case['id'].split('_')[0])(case,obj,BASE))
            except Exception:return False
        trace_correct=grade(original);live_correct=grade(live)
        return {'case_id':case['id'],'method':method,'status':status,'original_trace_correct':trace_correct,
            'live_execution_correct':live_correct and all(post_checks),'writes':len(created),'write_checks':post_checks,'model_calls':len(usage),
            'tool_calls':len(tools),'cost_usd':sum(x['cost_usd'] or 0 for x in usage),'usage':usage,'tools':tools,'history':history,
            'answer':answer,'cleanup':'performed_in_finally'}
    finally:
        failed=[]
        for path in reversed(created):
            code,_=http_request('DELETE',path)
            if code not in (200,204):failed.append(path)
        if failed:raise RuntimeError('Owned probe resources failed cleanup; private active journal retained')
        if journal.exists():journal.unlink()


def main():
    assert json.loads((HERE/'results/fhir_state_probe.json').read_text())['status']=='passed'
    manifest=json.loads((HERE/'results/task_manifest.json').read_text())
    data_path=RESOURCE/'data/medagentbench/split_dev.json'
    assert hashlib.sha256(data_path.read_bytes()).hexdigest()==manifest['splits']['dev']['sha256']
    all_cases=json.loads(data_path.read_text());groups={}
    for c in all_cases:groups.setdefault(c['id'].split('_')[0],[]).append(c)
    cases=[c for k in sorted(groups) for c in groups[k][:2]]
    protocol={'dataset':'MedAgentBench released GRASP split, development only','n':len(cases),'selection':'First two cases of each of eight development task types',
        'methods':['direct_tool','verified_state_harness'],'max_model_calls':8,'max_output_tokens':512,'model':'deepseek/deepseek-v4.1-flash',
        'tool_protocol':'Actual local HTTP writes for both methods; original trace grade and persisted-state grade reported separately.',
        'evolution':False,'test_used':False,'patient_fields_in_actor':'Only released instruction/context and queried public fixture resources. eval_MRN/sol never enter actor prompts.',
        'response_cap_characters':60000,'model_transport_failure':'Stop, retain complete cases, emit no score for unavailable calls.'}
    (HERE/'results/agent_pilot_protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    grader=grader_module();folder=LOCAL/'pilot';folder.mkdir(exist_ok=True);result={}
    for method in protocol['methods']:
        rows=[]
        for case in cases:
            path=folder/(method+'-'+case['id']+'.json')
            if path.exists():row=json.loads(path.read_text())
            else:
                row=run_case(case,method,grader);path.write_text(json.dumps(row,indent=2)+'\n')
            if row['status']!='completed' or row.get('answer') is None:
                row['original_trace_correct']=False;row['live_execution_correct']=False
                path.write_text(json.dumps(row,indent=2)+'\n')
            rows.append(row);print(json.dumps({'method':method,'completed':len(rows),'n':len(cases),'trace_correct':sum(r['original_trace_correct'] for r in rows),'live_correct':sum(r['live_execution_correct'] for r in rows)}),flush=True)
        result[method]={'n':len(rows),'original_trace_correct':sum(r['original_trace_correct'] for r in rows),
            'live_execution_correct':sum(r['live_execution_correct'] for r in rows),'writes':sum(r['writes'] for r in rows),
            'persisted_write_checks':sum(len(r['write_checks']) for r in rows),'persisted_write_checks_passed':sum(sum(r['write_checks']) for r in rows),
            'model_calls':sum(r['model_calls'] for r in rows),'tool_calls':sum(r['tool_calls'] for r in rows),'cost_usd':sum(r['cost_usd'] for r in rows)}
        (HERE/'results/agent_development_pilot.json').write_text(json.dumps({'status':'complete' if len(result)==2 else 'partial','methods':result,'test_evaluated':False,'evolution_performed':False},indent=2)+'\n')

if __name__=='__main__':main()
