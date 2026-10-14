"""Answer-feedback, evidence integrity and real read-only tool checks."""
import datetime,hashlib,json,sys,types
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path[:0]=[str(ROOT/'upgrade_v14')]
from probe_fhir_state import request,BASE,total
from contracts import infer,validate
from observation_tools import summarize,retrieve
from execution import run_case
NOW='2023-11-13T10:15:00+00:00'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    def obs(i,value,time='2023-11-13T09:00:00+00:00',unit='mg/dL'):
        return {'resource':{'resourceType':'Observation','id':str(i),'code':{'text':'SYNTHETIC'},'valueQuantity':{'value':value,'unit':unit},'effectiveDateTime':time}}
    page={'resourceType':'Bundle','total':8,'entry':[obs(1,10),obs(2,20),obs(3,99,'2023-11-11T09:00:00+00:00'),obs(4,1000,'2023-11-14T09:00:00+00:00'),obs(5,2,unit='mmol/L'),obs(6,'unknown'),obs(7,3,time='not-time'),obs(8,4,unit=None)]}
    view=summarize([page],NOW,True);assert len(view['numeric_groups'])==2
    a=next(g for g in view['numeric_groups'] if g['unit']['unit']=='mg/dL')
    assert a['latest']['value']==10 and a['last24h']['mean']==15 and a['last24h']['count']==2
    assert a['latest_timestamp_tie_count']==2 and a['latest_timestamp_distinct_values']==[10,20]
    assert view['omitted']=={'future_measurement':1,'non_numeric':1,'missing_or_unzoned_time':1,'missing_unit':1}
    numeric=infer('What is the most recent glucose value of a patient?');assert numeric['kind']=='number'
    assert validate([12],numeric) and not validate([12,NOW],numeric) and not validate(['12'],numeric) and not validate([True],numeric) and not validate([float('nan')],numeric)
    two=infer('What is the last glucose value and when was it recorded?');assert two['kind']=='number_time' and validate([12,NOW],two) and validate([-1],two)
    identifier=infer('What is the MRN of the patient with name Example Person?')
    assert identifier['kind']=='identifier' and validate(['SAMPLE'],identifier) and not validate([12],identifier)
    pages=[{'resourceType':'Bundle','total':2,'entry':[obs(1,10)],'link':[{'relation':'next','url':BASE+'Observation?cursor=next'}]},
           {'resourceType':'Bundle','total':2,'entry':[obs(2,20)]}]
    calls_mock=[]
    def mock_http(method,path):calls_mock.append(path);return 200,pages[len(calls_mock)-1]
    _,v,calls_paging,_=retrieve('Observation?patient=SAMPLE&code=SYNTHETIC',mock_http,BASE,NOW)
    assert v['complete_search'] and len(calls_paging)==2 and v['numeric_groups'][0]['last24h']['mean']==15
    calls_mock.clear();_,limited,_,_=retrieve('Observation?patient=SAMPLE&code=SYNTHETIC',mock_http,BASE,NOW,max_pages=1)
    assert not limited['complete_search']
    before={r:total(r) for r in ['Patient','MedicationRequest','Observation','ServiceRequest']}
    fake=types.SimpleNamespace(probe=lambda case,result,base:json.loads(result.result)==[12])
    calls=[]
    def actor(history):
        calls.append(history[-1]['content']);return {'raw':'FINISH([12, "2023-11-13T09:00:00+00:00"])' if len(calls)==1 else 'FINISH([12])','cost_usd':0,'input_tokens':0,'output_tokens':0,'seconds':0}
    row=run_case({'id':'probe_1','instruction':'What is the most recent glucose value?','context':'Synthetic runtime probe.','sol':'SECRET_LABEL_MUST_NOT_APPEAR'},'verified_state_harness',fake,actor=actor,answer_contract=True)
    assert row['model_calls']==2 and row['answer_shape_rejections']==1 and row['live_execution_correct'] and not row['tools']
    assert 'Invalid answer shape' in calls[1] and 'SECRET_LABEL_MUST_NOT_APPEAR' not in json.dumps(row['history'])
    # Exercise real public fixture retrieval; no actor and no write.
    path=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/resources/GRASP/benchmarks/MedAgentBench/data/medagentbench/split_dev.json'
    case=next(c for c in json.loads(path.read_text()) if c['id'].startswith('task4_'))
    code,payload,http,evidence=retrieve('Observation?patient='+case['eval_MRN']+'&code=MG&_count=1',request,BASE,NOW)
    assert code==200 and evidence is not None and payload['complete_search']
    all_records=[e['resource'] for p in evidence['pages'] for e in p.get('entry',[])]
    now=datetime.datetime.fromisoformat(NOW)
    for group in payload['numeric_groups']:
        records=[r for r in all_records if r['id'] in group['evidence_resource_ids']]
        times=[datetime.datetime.fromisoformat(r['effectiveDateTime']) for r in records]
        latest=records[times.index(max(times))];recent=[r for r,t in zip(records,times) if now-datetime.timedelta(hours=24)<=t<=now]
        assert group['latest']['value']==latest['valueQuantity']['value']
        assert group['last24h']['count']==len(recent)
        if recent:assert abs(group['last24h']['mean']-sum(r['valueQuantity']['value'] for r in recent)/len(recent))<1e-12
    after={r:total(r) for r in before};assert before==after
    report={'status':'passed','model_calls':0,'synthetic_actor_decisions':2,'real_fixture_http_gets':len(http),'writes':0,'real_observations':len(all_records),
      'checks':['numeric/date/identifier-shape contract','invalid shape consumes a real next decision slot','hidden answer excluded from actor prompt','mixed units not averaged','future/missing/non-numeric measurements explicitly omitted','equal timestamps preserve source order and expose ambiguity','real page completeness and independent arithmetic recount','original resource counts restored'],
      'resource_counts_before':before,'resource_counts_after':after,'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [HERE/'execution.py',HERE/'contracts.py',HERE/'observation_tools.py']},
      'scope':'Engineering execution probe, not a language-agent performance score.'}
    (HERE/'results').mkdir(exist_ok=True);(HERE/'results/runtime_probe.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)

if __name__=='__main__':main()
