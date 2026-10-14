"""Compare literal benchmark-order serialization with actual FHIR round trips."""
import json,sys,uuid
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'upgrade_v14'))
from probe_fhir_state import request,total
from order_compiler import compile_order

def main():
    (HERE/'results').mkdir(exist_ok=True);before={r:total(r) for r in ['Patient','MedicationRequest','Observation','ServiceRequest']};owned=[];out={}
    try:
        code,p=request('POST','Patient',{'resourceType':'Patient','name':[{'text':'Synthetic compiler integration probe'}],'identifier':[{'system':'urn:prismatic:probe','value':uuid.uuid4().hex}]});assert code==201
        patient='Patient/'+p['id'];owned.append(patient)
        original={'resourceType':'MedicationRequest','status':'draft','intent':'proposal','subject':{'reference':patient},
            'medicationCodeableConcept':{'text':'Synthetic structural test, no administration'},
            'dosageInstruction':[{'route':'IV','doseAndRate':[{'doseQuantity':{'value':1,'unit':'g'},'rateQuantity':{'value':1,'unit':'h'}}]}]}
        canonical,audit=compile_order(original)
        for label,payload in [('literal_benchmark_shape',original),('canonical_r4_shape',canonical)]:
            code,result=request('POST','MedicationRequest',payload);item={'post_http_status':code}
            if code==201:
                path='MedicationRequest/'+result['id'];owned.append(path);read_code,stored=request('GET',path)
                item.update({'read_http_status':read_code,'dosage_fields_preserved':stored.get('dosageInstruction')==payload['dosageInstruction']})
            else:item['server_issue_codes']=[i.get('code') for i in result.get('issue',[])]
            out[label]=item
        assert out['canonical_r4_shape']['post_http_status']==201 and out['canonical_r4_shape']['dosage_fields_preserved']
        assert original['dosageInstruction'][0]['route']=='IV'
    finally:
        for path in reversed(owned):
            code,_=request('DELETE',path);assert code in (200,204)
    after={r:total(r) for r in before};assert before==after
    out.update({'mapping_audit':audit,'counts_before':before,'counts_after':after,'cleanup_verified':True,'model_calls':0,
        'source':'https://hl7.org/fhir/R4/dosage-definitions.html#Dosage.route',
        'scope':'Structural serialization only. The duration-like rate field is preserved and explicitly not clinically validated.'})
    (HERE/'results/order_compiler_probe.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))

if __name__=='__main__':main()
