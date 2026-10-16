"""Prescription-domain adaptation; current QA runtime is preserved unchanged."""
import json,re
from common import *
from evidence import retrieve
TASK='''Research task: predict NEW or CHANGED prescription orders entered in the next six hours, at hospital admission +6h. Existing orders are context, not automatically targets. Information is incomplete. Do not invent diagnoses, allergies, renal clearance or future test results. The catalogue is a training-derived suggestion, not evidence of an indication. Select any number, including zero, of relevant catalogue orders. This is retrospective order prediction, not an instruction to a clinician. Dose, route, unit and frequency are joint templates; missing values remain unknown.'''
FINAL='Return only JSON {"order_ids":["A1",...]}. Use only actual catalogue IDs. No prose or additional fields.'
def view(c):
    cat='\n'.join(i+' | '+' | '.join(str(o.get(f)) for f in FIELDS) for i,o in c['catalogue'].items())
    facts='\n'.join(f'F{i+1}: {s}' for i,s in enumerate(c['input'].split(' ; ')))
    return 'AVAILABLE PATIENT FACTS (F identifiers reference exact observed text):\n'+facts+'\nORDER CATALOGUE (ID | drug | route | dose | unit | frequency/day):\n'+cat
def skills(c,state):
    return '\n'.join('CONDITION: '+x['condition']+'; ACTION: '+x['instruction']+'; COUNTEREXAMPLE: '+x['counterexample'] for x in state.get('cards',[]) if condition(c,x['condition']))
def check_facts(c,raw):
    obj=parse(raw);facts=obj.get('facts',[]);valid=[];rejected=0
    if not isinstance(facts,list):facts=[]
    pool={f'F{i+1}':s for i,s in enumerate(c['input'].split(' ; '))}
    for f in facts:
        if isinstance(f,str) and f in pool:valid.append(pool[f])
        elif isinstance(f,dict) and isinstance(f.get('quote'),str) and f['quote'] and f['quote'] in c['input']:
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
    result=[]
    for start in range(0,len(cases),8):
        backend.prefix.clear()
        result+=run_chunk(backend,cases[start:start+8],method,state,tag+f'/{start}')
    return result
def run_chunk(backend,cases,method='rxrsi',state=None,tag=''):
    state=state or {'cards':[]};base=[view(c) for c in cases]
    if method=='rxrsi':
        s1='Identify up to THREE decision-relevant observed patient facts by their F identifiers. Return ONLY JSON {"facts":["F1","F2"]}. No free text, quotations, explanations, or additional fields. Never infer a diagnosis from a prior medicine.'
        s2='Assess candidate indications, timing of new/change orders, supportive therapy and joint order fields using verified facts. Return ONLY JSON {"consider":["A1"],"avoid":["A2"]}. No free text or additional fields. Unknown is not a confirmed contraindication.'
    elif method=='saferx':
        s1='Independent SafeRx-Agent task adaptation: act as relevant specialty consultants AND a supportive-care consultant. Propose a coherent candidate order set, considering missing supportive therapy and potential overprescribing. Return ONLY JSON {"specialty":["A1"],"supportive":["A2"]}. No free text or additional fields.'
        s2='Act as the independent global critic: inspect the consultant draft for unnecessary duplication, drug interactions, contraindications, missing supportive orders and unsupported diagnoses. Return ONLY JSON {"keep":["A1"],"flag_ids":["A2"]}. Flags are suspicions, not verified facts. No free text or additional fields.'
    elif method=='skemex':
        s1='Apply the retrieved skill memory where its conditions hold. Plan medication selection for this new/change order task. Return ONLY JSON {"draft":["A1"]}. No free text or additional fields.'
        s2='Review the plan using the retrieved skills. Check applicability, uncertainty, missing therapies and unnecessary orders. Return ONLY JSON {"keep":["A1"],"avoid":["A2"]}. No free text or additional fields.'
    else:
        s1='Draft a likely set of new or changed prescription orders. Return ONLY JSON {"draft":["A1"]}. No free text or additional fields.'
        s2='Critique the initial draft for omissions, extras and incorrect order fields. Return ONLY JSON {"keep":["A1"],"avoid":["A2"]}. No free text or additional fields.'
    mem=[c.get('retrieved_memory','') if method=='skemex' else skills(c,state) for c in cases]
    messages=[[{'role':'system','content':TASK+'\n'+m},{'role':'user','content':b+'\nCURRENT STAGE:\n'+s1}] for b,m in zip(base,mem)]
    first=backend.batch(messages,128,tag+'/plan')
    checks=[check_facts(c,r['raw']) if method=='rxrsi' else {'status':'no exact quote gate'} for c,r in zip(cases,first)]
    for c,ck in zip(cases,checks):
        if method=='rxrsi' and any(x.get('fact_scope')=='all_observed' and condition(c,x['condition']) for x in state.get('cards',[])):
            ck['verified_input_quotes']=c['input'].split(' ; ')
            ck['fact_scope']='all_observed_input_fields; no inferred diagnosis or clinical entailment claim'
    ev=[retrieve(c,r['raw']) for c,r in zip(cases,first)]
    for msg,r,ck,e in zip(messages,first,checks,ev):msg.extend([{'role':'assistant','content':r['raw']},{'role':'user','content':'CURRENT STAGE:\n'+s2+'\nCHECKS:\n'+json.dumps(ck)+'\nOFFLINE LABEL TOOL:\n'+json.dumps(e)}])
    second=backend.batch(messages,128,tag+'/assess')
    for msg,a in zip(messages,second):msg.extend([{'role':'assistant','content':a['raw']},{'role':'user','content':'CURRENT STAGE: Finalize the prescription set.\n'+FINAL}])
    final=backend.batch(messages,96,tag+'/final')
    rows=[]
    for c,p,a,f,ck,e in zip(cases,first,second,final,checks,ev):
        rows.append({'case_id':c['case_id'],**compile_raw(f['raw'],c),'state_sha256':digest(state),'checks':ck,'evidence':e,
           'plan':p['raw'],'assessment':a['raw'],'raw':f['raw'],'logical_calls':3,
           'input_tokens':sum(x['input_tokens'] for x in [p,a,f]),'output_tokens':sum(x['output_tokens'] for x in [p,a,f])})
    return rows
