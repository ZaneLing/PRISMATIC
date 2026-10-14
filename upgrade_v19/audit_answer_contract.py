"""Post-test task7 format/value diagnosis; does not alter any main score."""
import collections,datetime,hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
LOCAL=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/medagentbench-native'
RESOURCE=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/resources/GRASP/benchmarks/MedAgentBench'
sys.path.insert(0,str(ROOT/'upgrade_v14'))
from probe_fhir_state import request

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    cases=[c for c in json.loads((RESOURCE/'data/medagentbench/split_test.json').read_text()) if c['id'].startswith('task7_')]
    expected={};gets=0
    for c in cases:
        status,data=request('GET','Observation?patient='+c['eval_MRN']+'&code=GLU&_count=5000&_format=json');gets+=1;assert status==200
        entries=[e['resource'] for e in data.get('entry',[])];assert data.get('total',len(entries))==len(entries)
        latest=max(entries,key=lambda e:datetime.datetime.fromisoformat(e['effectiveDateTime'])) if entries else None
        expected[c['id']]=latest['valueQuantity']['value'] if latest else -1
    output={}
    sources=[(m,LOCAL/'grasp-v19'/(m+'-test.json')) for m in ['direct_tools','fixed_compiled','evolving_compiled']]
    for m in ['name_only','lab_only']:
        p=LOCAL/'grasp-v19-ablation'/(m+'-test.json')
        if p.exists():sources.append((m,p))
    for m,path in sources:
        rows=[r for r in json.loads(path.read_text()) if r['case_id'] in expected];assert len(rows)==len(cases)
        counts=collections.Counter();trace_shapes=collections.Counter();signatures=[]
        for row in rows:
            raw_path=LOCAL/'learning-v19-rev2'/(row['episode_digest']+'.json');raw=json.loads(raw_path.read_text());signatures.append(sha(raw_path))
            counts['cases']+=1;counts['original_state_correct']+=row['live_execution_correct'];counts['completed_status']+=raw['status']=='completed'
            try:answer=json.loads(raw['answer'])
            except (ValueError,TypeError):answer=None
            shape='unparseable' if not isinstance(answer,list) else 'list_'+str(len(answer))+'_'+('_'.join(type(x).__name__ for x in answer))
            trace_shapes[shape]+=1
            first_numeric=isinstance(answer,list) and len(answer)>0 and type(answer[0]) in (int,float)
            if first_numeric:
                counts['first_element_numeric']+=1
                equal=answer[0]==expected[row['case_id']]
                counts['first_numeric_equals_reference']+=equal
                counts['correct_numeric_but_extra_elements']+=equal and len(answer)>1
                counts['first_numeric_differs_from_reference']+=not equal
            if isinstance(answer,list) and len(answer)==2 and type(answer[0]) in (int,float) and isinstance(answer[1],str):
                try:datetime.datetime.fromisoformat(answer[1]);counts['numeric_plus_iso_timestamp']+=1
                except ValueError:pass
        output[m]={'counts':dict(counts),'answer_shapes':dict(trace_shapes),'source_rows_sha256':sha(path),
                   'episode_receipt_digest':hashlib.sha256(json.dumps(signatures).encode()).hexdigest()}
    result={'status':'complete','scope':'Post-test descriptive task7 diagnosis only; no model/skill selected and no main score replaced',
      'restricted_data_used':False,'model_calls':0,'writes':0,'get_calls':gets,'methods':output,
      'reference':'Original task7 latest GLU value over all retrieved entries, no new temporal filter; query completeness asserted',
      'claim_boundary':'Matching the first numeric element is a counterfactual field-projection diagnostic, not an executed repaired-agent score. It can separate format-only failures from wrong numeric answers, but does not establish general clinical correctness or identify a causal skill without the removal contrast.'}
    (HERE/'results/answer_contract_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)

if __name__=='__main__':main()
