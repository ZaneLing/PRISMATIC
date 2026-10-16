"""Six-round local trace reflection after a common output-interface repair."""
import json,re,time
from common import *
from actor import view
from local_backend import Backend
from experiment import execute,validate_card
from audit_results import counts

CONDITIONS={'always','labs_present','labs_missing','prior_orders_present','prior_orders_missing'}

def public_card(card):
    return {'card_sha256':digest(card),'condition':card.get('condition'),'fact_scope':card.get('fact_scope'),
      'generated_text_location':'restricted local learning.json; not automatically published'}

def write_learning(rounds,state,complete):
    full={'complete':complete,'rounds':rounds,'selected_state':state}
    save(PRIVATE/'learning.json',full)
    public=json.loads(json.dumps(full));public['selected_state']={'cards':[public_card(c) for c in state['cards']]}
    for r in public['rounds']:
        r['state']={'cards':[public_card(c) for c in r['state']['cards']]}
        for attempt in r.get('attempts',[]):attempt['card']=public_card(attempt['card']) if attempt.get('card') else {}
    save(HERE/'results/learning_scope.json',public)

def validate(card,cases):
    parts=[s.strip() for s in re.split(r'\s+and\s+|\s*&\s*',str(card.get('condition','')))]
    if not 1<=len(parts)<=2 or not all(p in CONDITIONS for p in parts):return 'unknown_observable_condition'
    base={**card,'condition':parts[0]};reason=validate_card(base)
    if reason:return reason
    card['condition']=' & '.join(parts)
    if card.get('fact_scope') not in ['selected','all_observed']:return 'unsupported_fact_scope'
    if not any(condition(c,card['condition']) for c in cases):return 'condition_never_applies_in_training'
    wording=(card['instruction']+' '+card['counterexample']).lower()
    if re.search(r'\b\d+(?:\.\d+)?\s*(?:mg|mcg|ml|units|liters)\b',wording):return 'unsupported_dose_rule'
    names={o['drug_name'].lower() for c in cases for o in c['catalogue'].values()}
    for name in names:
        if name and re.search(r'\b(?:prescribe|add|administer|start|choose|prefer|remove)\b[^.;]{0,40}\b'+re.escape(name)+r'\b',wording):
            return 'memorized_drug_action_without_source_validation'
    return None

def reflect_packet(cases,rows):
    ranked=[]
    for c,r in zip(cases,rows):
        ct=counts(c,r);m=score([r['orders']],[c['gold']]);ranked.append((c,r,ct,m))
    selected=[]
    for has_labs in [False,True]:
        pool=[x for x in ranked if bool(x[0]['context']['available_labs'])==has_labs and (x[2]['fn'] or x[2]['fp'])]
        if pool:selected.append((max(pool,key=lambda x:(x[2]['selection_missing'],x[2]['fp'])),'discrepant_example'))
    rest=[x for x in ranked if x[0]['case_id'] not in {z[0][0]['case_id'] for z in selected}]
    if rest:selected.append((max(rest,key=lambda x:x[3]['promotion_score']),'best_remaining_case_not_necessarily_correct'))
    traces=[]
    for i,((c,r,ct,m),role) in enumerate(selected):
        traces.append({'trace_id':f'T{i+1}','role':role,
          'available_input_and_catalogue':view(c),'reference_orders':c['gold'],'predicted_orders':r['orders'],
          'plan':r['plan'],'assessment':r['assessment'],'checks':r['checks'],'evidence':r['evidence'],
          'counts':ct,'drug_f1':m['drug_micro_f1'],'core4_f1':m['core_order_micro_f1']})
    return traces

def main():
    data=load_cases();assert len(data['train'])==144;b=Backend();state={'cards':[]}
    pm=metrics(execute(b,data['proposal'],'rxrsi',state,'proposal-base'),data['proposal'])
    gm=metrics(execute(b,data['guard'],'rxrsi',state,'guard-base'),data['guard'])
    rounds=[{'round':0,'cases_seen':0,'state':state,'proposal':pm,'guard':gm,'accepted':False}];history=[]
    for r in range(1,7):
        cases=data['train'][(r-1)*24:r*24];before=execute(b,cases,'rxrsi',state,f'train-before-{r}')
        traces=reflect_packet(cases,before);save(PRIVATE/f'reflection-traces-{r}.json',traces)
        prompt='''Review actual local training traces. Find the earliest observable workflow discrepancy between available information, selected facts, evidence, assessment and the recorded reference. Reference agreement is feedback, not proof of the only appropriate treatment. Never use reference/GT membership as a runtime condition and never copy a medication action merely because it appears in the reference. Propose one short general procedure with an explicit observable condition and a counterexample. You may keep fact_scope="selected" or change it to "all_observed", which makes all actual input fields available to the checker without inventing findings. This interface is already implemented; you are not writing new tool code. Output schemas are already descriptive; do not alter model weights, doses, candidate rankings, labels or schema code. No named-drug or dose action without independently validated source conditions. Inspect partly correct cases to avoid regressions; a best-scoring case is not necessarily completely correct. Return {} with no proposal if no supported edit exists.
Return strict JSON with root_cause, condition, instruction, counterexample, fact_scope. Conditions are always, labs_present, labs_missing, prior_orders_present, prior_orders_missing, or a conjunction of at most two using &. Use only these observable predicates. Instruction and counterexample must refer only to runtime observations, never the reference, correct answer or future outcome. Keep the instruction below 90 words.
CURRENT STATE:\n'''+json.dumps(state)+'\nPAST EDIT OUTCOMES:\n'+json.dumps(history[-5:])+'\nTRAINING TRACES:\n'+json.dumps(traces)
        messages=[{'role':'system','content':'Reflect on measured failures and propose only a supported, scoped process change as JSON.'},{'role':'user','content':prompt}]
        candidate=None;attempts=[];no_edit=False
        for attempt in range(2):
            rec=b.batch([messages],640,f'reflect/{r}/{attempt}')[0];card=parse(rec['raw'])
            cleaned=re.sub(r'<think>.*?</think>','',rec['raw'],flags=re.S)
            no_edit=bool(re.fullmatch(r'\s*(?:```(?:json)?\s*)?\{\s*\}\s*(?:```)?\s*',cleaned))
            reason=None if no_edit else validate(card,data['train'][:r*24]);attempts.append({'rejection':reason,'card':card,'no_edit':no_edit})
            save(PRIVATE/f'reflection-{r}-{attempt}.json',rec)
            if no_edit:break
            if not reason:candidate={'cards':state['cards']+[card]};break
            messages.extend([{'role':'assistant','content':rec['raw']},{'role':'user','content':'Rejected: '+reason+'. Repair once using observable conditions, or return {}.'}])
        trial={'round':r,'cases_seen':r*24,'attempts':attempts,'accepted':False,'no_edit':no_edit,'training_before':metrics(before,cases)}
        if candidate:
            after=execute(b,cases,'rxrsi',candidate,f'train-after-{r}');trial['training_after']=metrics(after,cases)
            pnew=metrics(execute(b,data['proposal'],'rxrsi',candidate,f'proposal-{r}'),data['proposal'])
            gnew=metrics(execute(b,data['guard'],'rxrsi',candidate,f'guard-{r}'),data['guard'])
            trial.update(candidate_proposal=pnew,candidate_guard=gnew)
            trial['accepted']=pnew['promotion_score']>pm['promotion_score'] and gnew['drug_micro_f1']>=gm['drug_micro_f1'] and gnew['core_order_micro_f1']>=gm['core_order_micro_f1']
            history.append({'card':candidate['cards'][-1],'accepted':trial['accepted'],
              'proposal_delta':pnew['promotion_score']-pm['promotion_score'],'guard_drug_delta':gnew['drug_micro_f1']-gm['drug_micro_f1'],
              'guard_core4_delta':gnew['core_order_micro_f1']-gm['core_order_micro_f1']})
            if trial['accepted']:state=candidate;pm=pnew;gm=gnew
        else:history.append({'round':r,'outcome':'explicit_no_edit' if no_edit else 'no valid supported edit','rejections':[a['rejection'] for a in attempts]})
        trial.update(state=state,proposal=pm,guard=gm);rounds.append(trial)
        write_learning(rounds,state,False)
        print(json.dumps({'round':r,'accepted':trial['accepted'],'retained':len(state['cards'])}),flush=True)
    write_learning(rounds,state,True)
    frozen={'state':state,'state_sha256':digest(state),'actor_sha256':sha(HERE/'actor.py'),
      'evidence_sha256':sha(HERE/'evidence.py'),'common_sha256':sha(HERE/'common.py'),'time':time.time(),
      'selection_used_test_labels':False,'earlier_literal_schema_test_scores_seen':True,'new_test_inference_started':False}
    save(PRIVATE/'test_freeze.json',frozen)
    save(HERE/'test_freeze_scope.json',{**frozen,'state':{'cards':[public_card(c) for c in state['cards']]},
      'executable_state_location':'restricted local test_freeze.json'})
if __name__=='__main__':main()
