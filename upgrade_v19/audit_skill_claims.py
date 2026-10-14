"""Read-only engineering checks of model-authored claims, after main testing.

This audit cannot select a replacement skill. Original frozen skill bytes and
the separately registered ablation remain unchanged.
"""
import hashlib,json,shutil,sys,urllib.parse
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
LOCAL=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/medagentbench-native'
sys.path.insert(0,str(ROOT/'upgrade_v14'))
from probe_fhir_state import request

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    expected=json.loads((HERE/'results/frozen_skills.json').read_text())['skills_sha256']
    source=LOCAL/'grasp-v19/skills/best';export=HERE/'artifacts/model_authored_skills';export.mkdir(parents=True,exist_ok=True)
    for name,digest in expected.items():
        assert sha(source/name)==digest;shutil.copyfile(source/name,export/name)
    # Public benchmark illustration from the generated skill; no restricted data.
    raw='Patient?name=Christopher Cruz&birthdate=1940-08-28'
    encoded=raw.replace(' ','%20');safe='/?&=,%:@+$;[]-._~'
    a=urllib.parse.quote(raw,safe=safe);b=urllib.parse.quote(encoded,safe=safe)
    assert a==b
    ac,av=request('GET',raw);bc,bv=request('GET',encoded)
    def canonical(payload):
        return sorted([e.get('resource',{}) for e in payload.get('entry',[])],key=lambda x:json.dumps(x,sort_keys=True))
    assert ac==bc==200 and av.get('total')==bv.get('total') and canonical(av)==canonical(bv)
    tests=[]
    for code in ['A1C','MG']:
        result={}
        for parameter in ['code','code:text']:
            status,payload=request('GET',f'Observation?{parameter}={code}&_summary=count')
            result[parameter]={'status':status,'total':payload.get('total'),
                'issue_codes':[i.get('code') for i in payload.get('issue',[])]}
        tests.append({'public_lab_token':code,'queries':result})
    report={'status':'complete','timing':'Post-test read-only diagnostic; no skill selection or main-result change',
      'restricted_data_used':False,'model_calls':0,'writes':0,'get_calls':6,
      'skill_sha256':expected,'http_adapter_sha256':sha(ROOT/'upgrade_v14/probe_fhir_state.py'),
      'name_claim':{'claim':'Literal spaces cause empty bundles whereas explicit percent-encoding fixes them',
        'verdict':'Contradicted for this adapter: it percent-encodes both inputs to the identical request',
        'identical_encoded_url':True,'equal_status_count_resource_content':True,'matched_public_fixture_count':av.get('total'),
        'causal_limit':'This does not identify which other text in the skill changes agent decisions.'},
      'lab_claim':{'global_count_probes':tests,
        'verdict':'Report query counts, not a clinical rule. Medication route serialization does not establish the encoding of stored lab observations.',
        'causal_limit':'Global counts do not prove a patient-specific fallback is useful or that a lab exists for a task patient.'},
      'provenance_limits':['The generated files include illustrative observations that were authored by the model; they are not physical tool receipts.',
          'The name skill retains an example name/date despite updater guidance against memorizing names/dates; public benchmark data, not restricted MIMIC records.',
          'Probe score improvement does not validate the explanatory claim or establish held-out transfer.']}
    (HERE/'results/skill_claim_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)

if __name__=='__main__':main()
