"""Run local cases; propose rules from training only; freeze before test scores."""
import argparse,json,time,re
from common import *
from local_backend import Backend
from actor import run
def execute(b,cases,method,state,tag):
    path=PRIVATE/(tag.replace('/','_')+'.json')
    sig=digest([b.model_hash,method,state,[c['case_id'] for c in cases],sha(HERE/'actor.py'),sha(HERE/'evidence.py')])
    if path.exists():
        d=json.loads(path.read_text())
        if d['signature']==sig:return d['rows']
    rows=run(b,cases,method,state,tag)
    save(path,{'signature':sig,'rows':rows});return rows
def propose(b,cases,rows,state,r):
    errors=[]
    for c,p in zip(cases,rows):
        gs={x['drug_name'] for x in c['gold']};ps={x['drug_name'] for x in p['orders']}
        if gs==ps:continue
        errors.append({'context':c['input'],'prediction':p['orders'],'gold':c['gold'],
           'missing':sorted(gs-ps),'extra':sorted(ps-gs),'assessment':p['assessment']})
    prompt='''You improve a frozen prescription agent through procedural memory, not model training or threshold tuning. Analyze recurring discrepancies in these TRAINING cases. Recorded gold is an action target, not proof of a clinical indication. Identify a common decision error supported by at least two cases and propose ONE scoped decision procedure. No memorized patient identifiers, drug-name-only rule, blanket frequency prior, or invented diagnosis. Return JSON with root_cause, support_count, condition (one of always/labs_present/labs_missing/prior_orders_present/prior_orders_missing), instruction (max 90 words, a procedure), counterexample (when this rule should NOT apply). A rule may be rejected; if no justified rule exists return {}.\nCURRENT MEMORY:\n'''+json.dumps(state)+'\nERRORS:\n'+json.dumps(errors[:12])
    history=[]
    for attempt in range(2):
        messages=[{'role':'system','content':'You produce strict JSON, with evidence-supported scoped improvements only.'},{'role':'user','content':prompt}]+history
        rec=b.batch([messages],512,f'reflect/{r}/{attempt}')[0]
        x=parse(rec['raw']);reason=validate_card(x)
        rec.update(feedback_cases_shown=min(12,len(errors)),training_cases_observed=len(cases),schema_rejection=reason)
        save(PRIVATE/f'reflection-{r}-{attempt}.json',rec)
        if reason is None:return x
        history.extend([{'role':'assistant','content':rec['raw']},{'role':'user','content':'REJECTED: '+reason+'. Repair the rule once. Its applicability and every action must depend only on visible patient context, catalogue, and retrieved evidence. The reference/GT/future correct prescription is unavailable during inference. Do not use it as a condition or action. Do not replace this with a drug-name-only or unconditional frequency rule. Return {} if no supported procedure exists.'}])
    return None
def validate_card(x):
    if not all(isinstance(x.get(k),str) and x[k] for k in ['root_cause','condition','instruction','counterexample']):return 'invalid_or_absent_scoped_rule'
    if x['condition'] not in ['always','labs_present','labs_missing','prior_orders_present','prior_orders_missing']:return 'unknown_observable_condition'
    executable=x['instruction']+' '+x['counterexample']
    if re.search(r'\b(?:gold(?:[- ]standard)?|ground[- ]?truth|gt|reference(?:[- ]standard)?|correct answer|target (?:drug|medication|prescription))\b',executable,re.I):return 'unobservable_reference_predicate'
    if len(x['instruction'].split())>120:return 'instruction_too_long'
    return None
def learn(b,data):
    journal=HERE/'results/learning.json'
    if journal.exists() and json.loads(journal.read_text()).get('complete'):return json.loads(journal.read_text())['selected_state']
    state={'cards':[]};basep=execute(b,data['proposal'],'rxrsi',state,'proposal-base');baseg=execute(b,data['guard'],'rxrsi',state,'guard-base')
    pm=metrics(basep,data['proposal']);gm=metrics(baseg,data['guard'])
    trajectory=[{'round':0,'cases_seen':0,'state':state,'proposal':pm,'guard':gm,'accepted':False}]
    for r in range(1,4):
        cases=data['train'][(r-1)*24:r*24];before=execute(b,cases,'rxrsi',state,'train-before-'+str(r))
        card=propose(b,cases,before,state,r);trial={'round':r,'cases_seen':r*24,'candidate':card,'accepted':False,'training_before':metrics(before,cases)}
        if card:
            candidate={'cards':state['cards']+[card]}
            after=execute(b,cases,'rxrsi',candidate,'train-after-'+str(r));trial['training_after']=metrics(after,cases)
            pp=execute(b,data['proposal'],'rxrsi',candidate,'proposal-'+str(r));gg=execute(b,data['guard'],'rxrsi',candidate,'guard-'+str(r))
            pnew=metrics(pp,data['proposal']);gnew=metrics(gg,data['guard']);trial.update(candidate_proposal=pnew,candidate_guard=gnew)
            accept=pnew['promotion_score']>pm['promotion_score'] and gnew['drug_micro_f1']>=gm['drug_micro_f1'] and gnew['core_order_micro_f1']>=gm['core_order_micro_f1']
            trial['accepted']=accept
            if accept:state=candidate;pm=pnew;gm=gnew
        else:trial['rejection']='invalid_or_absent_scoped_rule'
        trial.update(state=state,proposal=pm,guard=gm)
        trajectory.append(trial);save(journal,{'complete':False,'rounds':trajectory,'selected_state':state})
        print(json.dumps({'round':r,'retained':len(state['cards']),'accepted':trial['accepted'],'proposal_f1':pm['drug_micro_f1'],'guard_f1':gm['drug_micro_f1']}),flush=True)
    save(journal,{'complete':True,'rounds':trajectory,'selected_state':state})
    save(HERE/'test_freeze.json',{'state':state,'state_sha256':digest(state),'actor_sha256':sha(HERE/'actor.py'),
      'evidence_sha256':sha(HERE/'evidence.py'),'protocol_sha256':sha(HERE/'protocol.json'),'selection_used_test_labels':False,'time':time.time()})
    return state
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--stage',choices=['learn','test','all','transfer'],default='all');a=ap.parse_args()
    data=load_cases();b=Backend('llama' if a.stage=='transfer' else 'qwen')
    if a.stage in ['learn','all']:state=learn(b,data)
    else:state=json.loads((HERE/'test_freeze.json').read_text())['state']
    if a.stage=='learn':return
    report={};path=HERE/'results'/('transfer.json' if a.stage=='transfer' else 'comparison.json')
    methods=[('rxrsi_base','rxrsi',{'cards':[]}),('rxrsi_selected','rxrsi',state)]
    if a.stage!='transfer':methods += [('direct','direct',{'cards':[]}),('saferx','saferx',{'cards':[]})]
    for name,method,st in methods:
        rows=execute(b,data['test'],method,st,b.name+'-test-'+name)
        report[name]=metrics(rows,data['test']);save(path,{'model':b.name,'model_sha256':b.model_hash,'methods':report,'complete':False})
        print(json.dumps({'method':name,'metrics':report[name]}),flush=True)
    save(path,{'model':b.name,'model_sha256':b.model_hash,'methods':report,'complete':True})
if __name__=='__main__':main()
