"""Prescription-domain adaptation; current QA runtime is preserved unchanged."""
import json,re
from common import *
from evidence import retrieve
TASK='''Research task: predict NEW or CHANGED prescription orders entered in the next six hours, at hospital admission +6h. Existing orders are context, not automatically targets. Information is incomplete. Do not invent diagnoses, allergies, renal clearance or future test results. The catalogue is a training-derived suggestion, not evidence of an indication. Select any number, including zero, of relevant catalogue orders. This is retrospective order prediction, not an instruction to a clinician. Dose, route, unit and frequency are joint templates; missing values remain unknown.'''
FINAL='Return only JSON {"order_ids":["A1",...]}. Use only actual catalogue IDs. No prose or additional fields.'
def view(c):
    cat='\n'.join(i+' | '+' | '.join(str(o.get(f)) for f in FIELDS) for i,o in c['catalogue'].items())
    return 'AVAILABLE PATIENT CONTEXT:\n'+c['input']+'\nORDER CATALOGUE (ID | drug | route | dose | unit | frequency/day):\n'+cat
def skills(c,state):
    return '\n'.join('CONDITION: '+x['condition']+'; ACTION: '+x['instruction']+'; COUNTEREXAMPLE: '+x['counterexample'] for x in state.get('cards',[]) if condition(c,x['condition']))
def check_facts(c,raw):
    obj=parse(raw);facts=obj.get('facts',[]);valid=[];rejected=0
    if not isinstance(facts,list):facts=[]
    for f in facts:
        if isinstance(f,dict) and isinstance(f.get('quote'),str) and f['quote'] and f['quote'] in c['input']:
            valid.append(f['quote'])
        else:rejected+=1
    return {'verified_input_quotes':valid,'rejected_quotes':rejected,
      'clinical_applicability':'unknown unless supported; no verified allergy, eGFR, DDI or indication database in this task'}
def compile_raw(raw,c):
    obj=parse(raw);ids=obj.get('order_ids');invalid=not isinstance(ids,list)
    ids=ids if isinstance(ids,list) else []
    clean=list(dict.fromkeys(x for x in ids if isinstance(x,str) and x in c['catalogue']))
    bad=sum(not isinstance(x,str) or x not in c['catalogue'] for x in ids)
    return {'orders':[c['catalogue'][i] for i in clean],'order_ids':clean,'invalid':invalid,'invalid_ids':bad}
def run(backend,cases,method='rxrsi',state=None,tag=''):
    state=state or {'cards':[]};base=[view(c) for c in cases]
    if method=='rxrsi':
        s1='Extract up to three decision-relevant exact patient quotes. Return JSON {"facts":[{"quote":"verbatim substring"}],"focus":"brief treatment question"}. No inferred patient findings.'
        s2='Assess candidate indications, timing of new/change orders, supportive therapy and joint order fields using verified quotes. Return JSON {"consider":["A1"],"avoid":["A2"],"reason":"brief justification"}. Unknown is not a confirmed contraindication.'
    elif method=='saferx':
        s1='Independent SafeRx-Agent task adaptation: act as relevant specialty consultants AND a supportive-care consultant. Propose a coherent candidate order set, considering missing supportive therapy and potential overprescribing. Return JSON {"specialty":["A1"],"supportive":["A2"],"rationale":"brief"}.'
        s2='Act as the independent global critic: inspect the consultant draft for unnecessary duplication, drug interactions, contraindications, missing supportive orders and unsupported diagnoses. Return JSON {"keep":["A1"],"flags":[{"id":"A2","reason":"brief"}]}. Unavailable information must be marked unknown.'
    elif method=='skemex':
        s1='Apply the retrieved skill memory where its conditions hold. Plan medication selection for this new/change order task. Return JSON {"draft":["A1"],"reason":"brief"}.'
        s2='Review the plan using the retrieved skills. Check applicability, uncertainty, missing therapies and unnecessary orders. Return JSON {"keep":["A1"],"change":"brief"}.'
    else:
        s1='Draft a likely set of new or changed prescription orders. Return JSON {"draft":["A1"],"reason":"brief"}.'
        s2='Critique the initial draft for omissions, extras and incorrect order fields. Return JSON {"keep":["A1"],"change":"brief"}.'
    mem=[c.get('retrieved_memory','') if method=='skemex' else skills(c,state) for c in cases]
    first=backend.batch([[{'role':'system','content':TASK+'\n'+s1+'\n'+m},{'role':'user','content':b}] for b,m in zip(base,mem)],128,tag+'/plan')
    checks=[check_facts(c,r['raw']) if method=='rxrsi' else {'status':'no exact quote gate'} for c,r in zip(cases,first)]
    ev=[retrieve(c,r['raw']) for c,r in zip(cases,first)]
    second=backend.batch([[{'role':'system','content':TASK+'\n'+s2+'\n'+m},{'role':'user','content':b+'\nDRAFT:\n'+r['raw']+'\nCHECKS:\n'+json.dumps(ck)+'\nOFFLINE LABEL TOOL:\n'+json.dumps(e)}] for b,m,r,ck,e in zip(base,mem,first,checks,ev)],128,tag+'/assess')
    final=backend.batch([[{'role':'system','content':TASK+'\n'+FINAL+'\n'+m},{'role':'user','content':b+'\nDRAFT:\n'+r['raw']+'\nASSESSMENT:\n'+a['raw']+'\nCHECKS:\n'+json.dumps(ck)+'\nOFFLINE LABEL TOOL:\n'+json.dumps(e)}] for b,m,r,a,ck,e in zip(base,mem,first,second,checks,ev)],96,tag+'/final')
    rows=[]
    for c,p,a,f,ck,e in zip(cases,first,second,final,checks,ev):
        rows.append({'case_id':c['case_id'],**compile_raw(f['raw'],c),'state_sha256':digest(state),'checks':ck,'evidence':e,
           'plan':p['raw'],'assessment':a['raw'],'raw':f['raw'],'logical_calls':3,
           'input_tokens':sum(x['input_tokens'] for x in [p,a,f]),'output_tokens':sum(x['output_tokens'] for x in [p,a,f])})
    return rows
