"""Complete research order representation and conservative structural review.

An evaluable structure is not clinical correctness. No status means approved for
administration. Missing knowledge is always surfaced, never treated as zero risk.
"""
from __future__ import annotations
import copy,json,math,re
from pathlib import Path

TEXT_FIELDS=['drug_name','ingredient_id','formulation','concentration','atc4','dose_unit',
             'route','frequency','duration','indication','fluid_purpose','reassessment']
NUMBER_FIELDS=['dose_value','volume_ml','rate_ml_h']
ALL_FIELDS=TEXT_FIELDS+NUMBER_FIELDS+['evidence_ids','uncertainty']
FLUID_PURPOSES=['resuscitation','maintenance','replacement','carrier','flush','unknown',None]

def schema():
    fields={k:{'type':['string','null']} for k in TEXT_FIELDS}
    fields.update({k:{'type':['number','null'],'exclusiveMinimum':0} for k in NUMBER_FIELDS})
    fields['fluid_purpose']={'enum':FLUID_PURPOSES}
    fields['atc4']={'type':['string','null'],'pattern':'^[A-Z][0-9]{2}[A-Z]{2}$'}
    fields['evidence_ids']={'type':'array','uniqueItems':True,'items':{'type':'string'}}
    fields['uncertainty']={'type':'array','items':{'type':'string'}}
    return {'$schema':'https://json-schema.org/draft/2020-12/schema','title':'PRISMATIC research order bundle v1',
      'type':'object','additionalProperties':False,'required':['orders'],
      'properties':{'orders':{'type':'array','maxItems':5,'items':{'type':'object',
        'required':ALL_FIELDS,'additionalProperties':False,'properties':fields}}}}

def normalize(payload):
    """Complete absent fields as explicit unknowns; never infer clinical values."""
    if not isinstance(payload,dict) or not isinstance(payload.get('orders'),list):raise ValueError('orders list required')
    result=[]
    for order in payload['orders']:
        if not isinstance(order,dict):raise ValueError('each order must be an object')
        if set(order)-set(ALL_FIELDS):raise ValueError('unknown order fields')
        item={key:copy.deepcopy(order.get(key,None)) for key in TEXT_FIELDS+NUMBER_FIELDS}
        item['evidence_ids']=copy.deepcopy(order.get('evidence_ids',[]))
        item['uncertainty']=copy.deepcopy(order.get('uncertainty',[]))
        if not isinstance(item['uncertainty'],list):raise ValueError('uncertainty must be list')
        for key in ALL_FIELDS:
            if key not in order:item['uncertainty'].append('not_supplied:'+key)
        # Preserve the raw payload in the trace; unresolved code granularity is
        # unknown, never guessed by truncating a possibly invented ATC code.
        if isinstance(item['atc4'],str) and not re.fullmatch(r'[A-Z][0-9]{2}[A-Z]{2}',item['atc4']):
            item['uncertainty'].append('unresolved_atc4:'+item['atc4'])
            item['atc4']=None
        result.append(item)
    return {'orders':result}

def review(bundle,patient_evidence_ids):
    """Checks reference existence and structure, not indication entailment."""
    findings=[];seen={}
    for i,order in enumerate(bundle['orders']):
        missing=[k for k in ['drug_name','ingredient_id','dose_value','dose_unit','route','frequency','indication'] if order[k] is None or order[k]=='']
        if missing:findings.append({'order':i,'kind':'missing_fields','fields':missing})
        refs=order['evidence_ids']
        if order['atc4'] is None:findings.append({'order':i,'kind':'unresolved_atc_mapping'})
        if not refs:findings.append({'order':i,'kind':'no_patient_evidence'})
        if any(r not in patient_evidence_ids for r in refs):findings.append({'order':i,'kind':'invalid_evidence_reference'})
        code=order['ingredient_id']
        if code:
            if code in seen:findings.append({'order':i,'kind':'duplicate_ingredient','other_order':seen[code]})
            seen[code]=i
        name=(order['drug_name'] or '').lower()
        fluid=any(term in name for term in ['saline','sodium chloride','lactated ringer']) or order['fluid_purpose'] is not None
        if fluid:
            absent=[k for k in ['fluid_purpose','volume_ml','rate_ml_h','reassessment'] if order[k] is None or order[k] in ['', 'unknown']]
            if absent:findings.append({'order':i,'kind':'fluid_information_missing','fields':absent})
        for key in NUMBER_FIELDS:
            v=order[key]
            if v is not None and (isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<=0):
                findings.append({'order':i,'kind':'invalid_numeric_value','field':key})
    findings.append({'kind':'clinical_knowledge_unavailable','checks':['ingredient_DDI','renal_adjustment','allergy_cross_reactivity']})
    return {'status':'abstained' if not bundle['orders'] else 'needs_information' if len(findings)>1 else 'needs_clinical_review',
            'findings':findings,'reference_check':'existence only; clinical entailment unreviewed','clinically_validated':False}

if __name__=='__main__':
    (Path(__file__).parent/'order_schema.json').write_text(json.dumps(schema(),indent=2)+'\n')
