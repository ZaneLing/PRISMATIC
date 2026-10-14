"""Real FHIR CRUD and atomic-failure probes, never a model benchmark score."""
import hashlib,json,time,urllib.request,urllib.error,urllib.parse,uuid
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE='http://127.0.0.1:18080/fhir/'

def request(method,path,body=None):
    assert not path.startswith('/') and '://' not in path and '..' not in path
    path=urllib.parse.quote(path,safe='/?&=,%:@+$;[]-._~')
    req=urllib.request.Request(BASE+path,data=None if body is None else json.dumps(body).encode(),
        headers={'Accept':'application/fhir+json','Content-Type':'application/fhir+json'},method=method)
    try:
        with urllib.request.urlopen(req,timeout=45) as r:
            raw=r.read();return r.status,json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raw=e.read()
        try:data=json.loads(raw)
        except ValueError:data={'resourceType':'NonJSONError'}
        return e.code,data

def total(resource):
    code,data=request('GET',resource+'?_summary=count');assert code==200
    return data['total']

def main():
    code,meta=request('GET','metadata');assert code==200 and meta['resourceType']=='CapabilityStatement'
    counts_before={r:total(r) for r in ['Patient','MedicationRequest','Observation','ServiceRequest']}
    marker='prismatic-state-probe-'+uuid.uuid4().hex;created=[];checks=[]
    patient={'resourceType':'Patient','active':True,'identifier':[{'system':'urn:prismatic:probe','value':marker}],
             'name':[{'family':'ResearchProbe','given':['Synthetic']}],'birthDate':'2000-01-01'}
    try:
        code,p=request('POST','Patient',patient);assert code==201
        patient_path='Patient/'+p['id'];created.append(patient_path)
        code,p2=request('GET',patient_path);assert code==200 and p2['identifier'][0]['value']==marker
        checks.append({'check':'patient_create_read','passed':True})
        medication={'resourceType':'MedicationRequest','status':'draft','intent':'proposal',
            'medicationCodeableConcept':{'text':'Research integration probe; no administration'},
            'subject':{'reference':patient_path},'identifier':[{'system':'urn:prismatic:probe','value':marker}]}
        code,m=request('POST','MedicationRequest',medication);assert code==201
        med_path='MedicationRequest/'+m['id'];created.append(med_path)
        code,m2=request('GET',med_path);assert code==200 and m2['subject']['reference']==patient_path
        checks.append({'check':'medication_create_and_referenced_patient_readback','passed':True})
        old=m2['meta']['versionId'];m2['status']='cancelled'
        code,m3=request('PUT',med_path,m2);assert code==200
        code,m4=request('GET',med_path);assert code==200 and m4['status']=='cancelled' and m4['meta']['versionId']!=old
        checks.append({'check':'medication_update_and_version_change','passed':True})
        atomic_marker=marker+'-atomic'
        invalid={'resourceType':'Bundle','type':'transaction','entry':[
            {'resource':{'resourceType':'Patient','identifier':[{'system':'urn:prismatic:probe','value':atomic_marker}]},'request':{'method':'POST','url':'Patient'}},
            {'resource':{'resourceType':'NotARealFHIRResource'},'request':{'method':'POST','url':'NotARealFHIRResource'}}]}
        code,failed=request('POST','',invalid);assert code in (400,422)
        code,found=request('GET','Patient?identifier='+atomic_marker);assert code==200 and found.get('total',0)==0
        checks.append({'check':'invalid_transaction_rejected_without_partial_patient','passed':True})
    finally:
        for path in reversed(created):
            code,_=request('DELETE',path);assert code in (200,204)
            code,_=request('GET',path);assert code in (404,410)
    counts_after={r:total(r) for r in counts_before};assert counts_after==counts_before
    checks.append({'check':'created_resources_deleted_and_original_counts_restored','passed':True})
    report={'status':'passed','kind':'engineering_integration_probe_not_agent_score','fhir_version':meta.get('fhirVersion'),
        'software':meta.get('software'),'bind':'127.0.0.1:18080','counts_before':counts_before,'counts_after':counts_after,
        'checks':checks,'restricted_records_used':False,'model_calls':0,
        'scope':'Official public image application/database on native JRE. Actual HTTP writes/readbacks are tested. Original benchmark wrapper scores POST traces without executing them; this probe is separately reported.'}
    (HERE/'results/fhir_state_probe.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)

if __name__=='__main__':main()
