"""Executable, order-specific memory. Execution never reads reference labels.

Recorded-diagnosis conditions describe documentation, not verified indications.
An absent prior order is absence in the available record, not absence of therapy.
"""
from common53 import *
def diagnosis_features(c):
    out=set()
    for diagnosis in c['context']['diagnoses']:
        parts=[p.strip().lower() for p in diagnosis.split('|')]
        for depth in range(2,len(parts)+1):
            out.add('dx:'+'|'.join(parts[:depth]))
    return out
def features(c,code):
    seen=any(o.get('drug_code')==code for o in c['context']['prior_orders'])
    return diagnosis_features(c)|{'prior_record:present' if seen else 'prior_record:absent'}
def applies(c,card):
    f=features(c,card['drug_code'])
    return set(card['when']).issubset(f) and not set(card['unless'])&f
def operate(orders,card):
    code=card['drug_code'];op=card['op'];selected=any(o['drug_code']==code for o in orders)
    if op=='remove':return [o for o in orders if o['drug_code']!=code]
    if op=='add':return uniq(orders+[dict(card['template'])]) if not selected else orders
    if op=='replace':
        return uniq([o for o in orders if o['drug_code']!=code]+[dict(card['template'])]) if selected else orders
    raise ValueError('Unknown operation')
def execute(c,orders,state,unscoped=False):
    result=list(orders)
    for card in state:
        if unscoped or applies(c,card):result=operate(result,card)
    return result
def predict(cases,base,state,unscoped=False):
    return [execute(c,p,state,unscoped) for c,p in zip(cases,base)]
def joint_field_mismatch(pred,gold):
    """For shared drug identities, count reference tuples not exactly recovered.

    Report denominator separately: removing an identity changes denominator,
    so this measure must be interpreted jointly with missed-drug counts.
    """
    shared={o['drug_code'] for o in pred}&{o['drug_code'] for o in gold}
    pp={key(o) for o in pred if all(o.get(f) for f in FIELDS)}
    gg={key(o) for o in gold if o['drug_code'] in shared and all(o.get(f) for f in FIELDS)}
    return len(gg-pp),len(gg)
