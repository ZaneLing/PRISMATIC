"""Instrumented local reflection: observed-fact scope is an executable patch.

The researcher supplies a bounded configuration interface, not the chosen
patch. A local model proposes a conditional patch from actual training traces;
the existing proposal/guard gates retain or reject it. No parameter fitting.
"""
import json,time,re
from common import *
from experiment import execute,validate_card
from local_backend import Backend
def main():
    b=Backend();data=load_cases();training=json.loads((PRIVATE/'training-stream-2.json').read_text())
    state={'cards':[]};pm=metrics(execute(b,data['proposal'],'rxrsi',state,'scope-proposal-base'),data['proposal']);gm=metrics(execute(b,data['guard'],'rxrsi',state,'scope-guard-base'),data['guard'])
    rounds=[{'round':0,'cases_seen':0,'state':state,'proposal':pm,'guard':gm,'accepted':False}]
    for r in range(1,4):
        cases=training[(r-1)*24:r*24];before=execute(b,cases,'rxrsi',state,f'scope-train-before-{r}')
        traces=[];profiles=[]
        for c,row in zip(cases,before):
            gt={o['drug_name'] for o in c['gold']};pred={o['drug_name'] for o in row['orders']}
            if gt==pred:continue
            traces.append({'context':c['input'],'catalogue':c['catalogue'],'reference_orders':c['gold'],'predicted_orders':row['orders'],
              'plan':row['plan'],'assessment':row['assessment'],'checked_fact_count':len(row['checks']['verified_input_quotes']),
              'observed_fact_count':len(c['input'].split(' ; ')),'verified_facts':row['checks']['verified_input_quotes'],
              'reference_drugs_absent_from_catalogue':len(gt-{o['drug_name'] for o in c['catalogue'].values()})})
            selected=' '.join(row['checks']['verified_input_quotes'])
            profiles.append({'example':len(profiles)+1,'observed_fact_count':len(c['input'].split(' ; ')),
              'checked_fact_count':len(row['checks']['verified_input_quotes']),
              'has_labs':bool(c['context']['available_labs']),'has_prior_orders':bool(c['context']['recorded_prior_orders']),
              'missed_targets':len(gt-pred),'extra_predictions':len(pred-gt),
              'missed_targets_named_in_unselected_observations':sum(n in c['input'] and n not in selected for n in gt-pred),
              'missed_targets_outside_catalogue':len((gt-pred)-{o['drug_name'] for o in c['catalogue'].values()}),
              'selected_fact_ids':parse(row['plan']).get('facts',[])})
        save(PRIVATE/f'scope-trace-profiles-{r}.json',{'traces':traces,'profiles':profiles})
        prompt='''Analyze these mechanically counted TRAINING trace profiles to identify a repeated workflow error and propose one bounded process update. Drug names and exact reference prescriptions are deliberately absent to prevent memorized drug-action rules. Available facts are observed input fields; selecting only three for verification might omit relevant observations, but this is a hypothesis to test. Reference-derived counts are feedback only and are NEVER runtime conditions. You may propose a procedural card, or fact_scope="all_observed", making every actually observed input field available to the assessment checker. This adds no inferred findings. The alternative is fact_scope="selected" (unchanged tool). Choose based on profiles; more facts need not improve results. Return {} if no supported edit exists. Return JSON {"root_cause":"a general workflow hypothesis","condition":"always|labs_present|labs_missing|prior_orders_present|prior_orders_missing","instruction":"short procedure under 90 words, using ONLY observable inputs","counterexample":"observable circumstance where this procedure should not apply","fact_scope":"selected|all_observed"}. Do not mention reference labels, GT, future outcomes or a correct answer in the instruction/counterexample. Do not invent any drug-specific rule, dose or treatment.\nCURRENT STATE:\n'''+json.dumps(state)+'\nTRAINING PROFILES:\n'+json.dumps(profiles)
        history=[];candidate=None;attempts=[]
        for attempt in range(2):
            rec=b.batch([[{'role':'system','content':'Return a supported process update as strict JSON only.'},{'role':'user','content':prompt}]+history],512,f'scope/reflect-{r}-{attempt}')[0]
            card=parse(rec['raw']);reason=validate_card(card)
            if not reason and card.get('fact_scope') not in ['selected','all_observed']:reason='unsupported_tool_configuration'
            if not reason:
                wording=(card['instruction']+' '+card['counterexample']).lower()
                drug_terms=set()
                for c in cases:
                    for o in c['catalogue'].values():
                        term=re.sub(r'\([^)]*\)','',o['drug_name'].lower())
                        words=re.findall(r'[a-z]+',term)
                        if words and len(words[0])>=4:drug_terms.add(words[0])
                if any(re.search(r'\b'+re.escape(t)+r'\b',wording) for t in drug_terms):reason='named_drug_rule_in_procedural_update'
                if re.search(r'\b\d+(?:\.\d+)?\s*(?:mg|mcg|ml|units|liters)\b',wording):reason='unsupported_dose_rule'
            attempts.append({'rejection':reason,'card':card})
            save(PRIVATE/f'scope-reflection-{r}-{attempt}.json',rec)
            if not reason:candidate={'cards':state['cards']+[card]};break
            history.extend([{'role':'assistant','content':rec['raw']},{'role':'user','content':'Rejected: '+reason+'. Repair once using only observable runtime conditions, or return {}.'}])
        trial={'round':r,'cases_seen':r*24,'attempts':attempts,'accepted':False,'training_before':metrics(before,cases)}
        if candidate:
            after=execute(b,cases,'rxrsi',candidate,f'scope-train-after-{r}');trial['training_after']=metrics(after,cases)
            pnew=metrics(execute(b,data['proposal'],'rxrsi',candidate,f'scope-proposal-{r}'),data['proposal'])
            gnew=metrics(execute(b,data['guard'],'rxrsi',candidate,f'scope-guard-{r}'),data['guard'])
            trial.update(candidate_proposal=pnew,candidate_guard=gnew)
            trial['accepted']=pnew['promotion_score']>pm['promotion_score'] and gnew['drug_micro_f1']>=gm['drug_micro_f1'] and gnew['core_order_micro_f1']>=gm['core_order_micro_f1']
            if trial['accepted']:state=candidate;pm=pnew;gm=gnew
        trial.update(state=state,proposal=pm,guard=gm);rounds.append(trial)
        save(HERE/'results/learning_scope.json',{'complete':False,'rounds':rounds,'selected_state':state})
        print(json.dumps({'scope_round':r,'retained':len(state['cards']),'accepted':trial['accepted']}),flush=True)
    save(HERE/'results/learning_scope.json',{'complete':True,'rounds':rounds,'selected_state':state})
    save(HERE/'test_freeze_scope.json',{'state':state,'state_sha256':digest(state),'actor_sha256':sha(HERE/'actor.py'),
      'evidence_sha256':sha(HERE/'evidence.py'),'selection_used_test_labels':False,'time':time.time(),'initial_test_inference_started_but_scores_unread':True})
if __name__=='__main__':main()
