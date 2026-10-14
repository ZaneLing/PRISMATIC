"""v28 fixed-engineering factorial, adapted from the preserved v19 executor."""
import hashlib,importlib,json,sys,types,uuid
from pathlib import Path
HERE=Path(__file__).resolve().parent
RESOURCE=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/resources/GRASP/benchmarks/MedAgentBench'
LOCAL=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/medagentbench-native'
sys.path[:0]=[str(HERE.parent/'upgrade_v8'),str(HERE.parent/'upgrade_v14'),str(HERE.parent/'upgrade_v19')]
from public_client import request as model_request,digest
from probe_fhir_state import request as http_request,BASE
from order_compiler import compile_order
from reference_compat import reference_view
from contracts import infer as infer_contract,validate as validate_contract
from observation_tools import retrieve as retrieve_observations


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


def run_case(case,method,grader,actor=None,compile_payloads=True,repair_protocol=True,answer_contract=False,statistics=False):
    funcs=json.loads((RESOURCE/'data/medagentbench/funcs_v1.json').read_text())
    prompt={'phase':'task_execution','task':{'description':case['instruction'],'context':case['context']+'\nCurrent time: 2023-11-13T10:15:00+00:00'},
        'api':{'base_url':BASE,'functions':funcs},'response_format':{'options':['GET url?parameters','POST url\n{json_payload}','FINISH([answer1, answer2, ...])'],
        'rules':['Exactly one action per turn; no other text.','FINISH contains a JSON list.']}}
    contract=infer_contract(case['instruction']) if answer_contract else None
    if contract:prompt['response_format']['task_answer_contract']=contract
    if statistics:prompt['api']['observation_view']='Patient-filtered Observation queries return source-bound latest/last24h statistics grouped by code and unit, actual page counts, completeness and omitted-record flags. Respect incomplete or missing evidence. The task supplies conditional ordering instructions.'
    system='Solve this public MedAgentBench research task using the local FHIR API. Use only facts in the task and retrieved records.'
    verified=method=='verified_state_harness'
    if verified:system+=' Resolve the requested patient, retrieve needed observations and respect the stated clinical time. Before a write, check resource type, patient reference and all requested fields. Use the server receipt/readback to confirm execution. Finish only after every requested question or write is handled.'
    if contract:system+=' '+contract['instruction']
    history=[{'role':'system','content':system},{'role':'user','content':json.dumps(prompt)}]
    original=[];live=[];created=[];tools=[];usage=[];answer=None;status='round_limit';post_checks=[];active_post_checks=[];compilation_audits=[];protocol_repairs=0
    write_audits=[];cleanup_checks=[];grader_errors=[];observation_audits=[];answer_shape_rejections=0
    active=LOCAL/'active';active.mkdir(exist_ok=True);journal=active/(uuid.uuid4().hex+'.json')
    try:
        for round_index in range(8):
            response=actor(history) if actor else model_request(history,'deepseek/deepseek-v4.1-flash',512,role='fhir_actor')
            if response.get('error'):raise RuntimeError('Incomplete model transport response; no task score emitted')
            raw=response['raw'].strip();usage.append({k:response.get(k,0) for k in ['input_tokens','output_tokens','cost_usd','seconds']})
            if raw.startswith('```') and raw.endswith('```'):raw=raw.split('\n',1)[-1].rsplit('```',1)[0].strip()
            history.append({'role':'assistant','content':raw});original.append({'role':'agent','content':raw});live.append({'role':'agent','content':raw})
            if raw.startswith('FINISH(') and raw.endswith(')'):
                try:
                    parsed=json.loads(raw[7:-1]);assert isinstance(parsed,list)
                    if contract and not validate_contract(parsed,contract):
                        answer_shape_rejections+=1;protocol_repairs+=1
                        message='Invalid answer shape. '+contract['instruction']+' Keep the evidence-derived answer; do not guess a different value. This retry consumes the same eight-call budget.'
                        for trace in [history,live,original]:trace.append({'role':'user','content':message})
                        status='round_limit';continue
                    answer=raw[7:-1];status='completed'
                except (ValueError,AssertionError):status='invalid_finish'
                if status=='invalid_finish' and repair_protocol:
                    message='Invalid FINISH format. Return exactly FINISH([...]) containing a valid JSON list, without prose.'
                    for trace in [history,live,original]:trace.append({'role':'user','content':message})
                    status='round_limit';protocol_repairs+=1;continue
                break
            if raw.startswith('GET '):
                try:path=valid_path(raw[4:].strip())
                except ValueError:status='invalid_action';break
                if statistics:
                    code,payload,calls,evidence=retrieve_observations(path,http_request,BASE,'2023-11-13T10:15:00+00:00')
                    tools.extend({'method':'GET',**call,'observation_paging':True} for call in calls)
                    if evidence is not None:observation_audits.append(evidence)
                else:
                    code,payload=http_request('GET',path);tools.append({'method':'GET','path':path,'status':code})
                message='FHIR response: '+json.dumps(tool_view(payload))
                if len(message)>60000:message=message[:60000]+'\n[Response truncated at 60,000 characters; use narrower search parameters.]'
                original_message=message
            elif raw.startswith('POST '):
                try:
                    line,body=raw.split('\n',1);path=valid_path(line[5:].strip());payload=json.loads(body)
                    assert path in ['Observation','MedicationRequest','ServiceRequest'] and isinstance(payload,dict)
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
                        stored_payload,compile_audit=compile_order(payload)
                        submitted_payload=stored_payload if compile_payloads else payload
                        compile_audit['applied_to_submission']=compile_payloads
                        compilation_audits.append(compile_audit)
                        code,result=http_request('POST',path,submitted_payload);tools.append({'method':'POST','path':path,'status':code})
                        audit={'submitted_payload':submitted_payload,'canonical_payload':stored_payload,'create_status':code,'create_receipt':result,'readback_status':None,'readback':None,'persisted':False,'rolled_back':False}
                        write_audits.append(audit)
                        if code==201 and isinstance(result,dict) and result.get('id'):
                            new_path=path+'/'+result['id'];created.append(new_path);journal.write_text(json.dumps(created))
                            read_code,stored=http_request('GET',new_path)
                            persisted=read_code==200 and stored.get('resourceType')==payload.get('resourceType')
                            for field in stored_payload:
                                if field not in ['id','meta']:persisted &= stored.get(field)==stored_payload[field]
                            audit.update(readback_status=read_code,readback=stored,persisted=bool(persisted))
                            post_checks.append(bool(persisted));tools.append({'method':'GET','path':new_path,'status':read_code,'postcondition_audit':True,'shown_to_actor':verified})
                            if not persisted and repair_protocol:
                                rollback_code,_=http_request('DELETE',new_path)
                                tools.append({'method':'DELETE','path':new_path,'status':rollback_code,'rollback':True})
                                if rollback_code not in (200,204):raise RuntimeError('Readback-mismatch rollback failed; cleanup journal retained')
                                audit.update(rolled_back=True,rollback_status=rollback_code)
                                created.pop();journal.write_text(json.dumps(created))
                                missing=[k for k in stored_payload if k not in ['id','meta'] and stored.get(k)!=stored_payload[k]]
                                message='The submitted write failed field preservation and was rolled back. Repair these fields before retrying: '+json.dumps(missing)
                            else:
                                active_post_checks.append(bool(persisted))
                                message='POST request accepted and executed successfully.'
                                if verified:message+=' Readback verified: '+json.dumps({k:stored[k] for k in ['resourceType','id','status','subject','medicationCodeableConcept','dosageInstruction'] if k in stored})
                        else:message='FHIR POST rejected: '+json.dumps(result)
            else:
                if not repair_protocol:status='invalid_action';break
                protocol_repairs+=1
                message='Invalid action. Return exactly one GET URL, POST URL followed by JSON, or FINISH([...]). Do not add explanatory prose. This retry consumes the same eight-turn budget.'
                original_message=message
            history.append({'role':'user','content':message});live.append({'role':'user','content':message});original.append({'role':'user','content':original_message})
        def grade(trace,kind):
            if answer is None or status!='completed':return False
            obj=types.SimpleNamespace(history=[types.SimpleNamespace(**x) for x in trace],result=answer)
            try:return bool(getattr(grader,case['id'].split('_')[0])(case,obj,BASE))
            except Exception as error:
                grader_errors.append({'exception':type(error).__name__,'trace_kind':kind})
                raise RuntimeError('Reference grading failed; incomplete evaluator evidence must not become a model score') from None
        semantic_trace,projection_audits=reference_view(live)
        trace_correct=grade(original,'original');legacy_live=grade(live,'live');live_correct=grade(semantic_trace,'semantic')
        return {'case_id':case['id'],'method':method,'status':status,'original_trace_correct':trace_correct,
            'live_execution_correct':live_correct and all(active_post_checks),'writes':len(created),'write_checks':post_checks,'model_calls':len(usage),
            'tool_calls':len(tools),'cost_usd':sum(x['cost_usd'] or 0 for x in usage),'usage':usage,'tools':tools,'history':history,
            'answer':answer,'cleanup':'performed_in_finally','cleanup_checks':cleanup_checks,'protocol_repairs':protocol_repairs,'compilation_audits':compilation_audits,
            'original_trace':original,'live_trace':live,'semantic_trace':semantic_trace,'legacy_live_reference_correct':legacy_live,
            'semantic_reference_correct':live_correct,'reference_projection_audits':projection_audits,'grading_revision':'lossless_reference_views_v2',
            'answer_contract':contract,'answer_shape_rejections':answer_shape_rejections,'observation_audits':observation_audits,'statistics_enabled':statistics,
            'active_post_checks':active_post_checks,'write_audits':write_audits,'grader_errors':grader_errors}
    finally:
        failed=[]
        for path in reversed(created):
            code,_=http_request('DELETE',path)
            cleanup_checks.append({'path':path,'status':code})
            if code not in (200,204):failed.append(path)
        if failed:raise RuntimeError('Owned probe resources failed cleanup; private active journal retained')
        if journal.exists():journal.unlink()
