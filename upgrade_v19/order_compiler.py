"""Lossless structural adapter from benchmark intent to FHIR R4 payloads."""
import copy

def compile_order(payload):
    out=copy.deepcopy(payload);changes=[];warnings=[]
    if out.get('resourceType')=='ServiceRequest' and isinstance(out.get('note'),dict):
        out['note']=[out['note']]
        changes.append({'path':'note','conversion':'Annotation object -> singleton Annotation array; all fields preserved'})
    if out.get('resourceType')=='MedicationRequest':
        for i,dosage in enumerate(out.get('dosageInstruction') or []):
            if isinstance(dosage.get('route'),str):
                dosage['route']={'text':dosage['route']}
                changes.append({'path':f'dosageInstruction[{i}].route','conversion':'string -> CodeableConcept.text; text preserved verbatim'})
            for j,amount in enumerate(dosage.get('doseAndRate') or []):
                unit=(amount.get('rateQuantity') or {}).get('unit')
                if unit in ['h','hour','hours','min','minute','minutes']:
                    warnings.append({'path':f'dosageInstruction[{i}].doseAndRate[{j}].rateQuantity',
                        'kind':'duration_unit_in_rate_field','action':'preserved; no inferred rate or duration conversion',
                        'clinical_semantics_validated':False})
    return out,{'changes':changes,'semantic_warnings':warnings}
