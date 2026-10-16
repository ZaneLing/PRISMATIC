"""Distinguish proposal, applicability, execution and predictive-effect failures."""
import collections,json
from common import *
def main():
    data=load_cases();learning=json.loads((PRIVATE/'learning.json').read_text());assert learning['complete']
    dispositions=collections.Counter();out=[]
    for r in learning['rounds'][1:]:
        for attempt in r['attempts']:dispositions[attempt.get('rejection') or ('explicit_no_edit' if attempt.get('no_edit') else 'valid_candidate')]+=1
        item={'round':r['round'],'accepted':r['accepted'],'cases_seen':r['cases_seen']}
        cards=[a['card'] for a in r['attempts'] if a.get('card') and not a['rejection']]
        if cards:
            card=cards[-1];item['condition']=card['condition'];item['scope']=card['fact_scope'];item['effects']={}
            for split,oldtag,newtag,cases in [
              ('training',f"train-before-{r['round']}",f"train-after-{r['round']}",data['train'][(r['round']-1)*24:r['round']*24]),
              ('proposal','proposal-base',f"proposal-{r['round']}",data['proposal']),
              ('guard','guard-base',f"guard-{r['round']}",data['guard'])]:
                paths=[PRIVATE/(tag+'.json') for tag in [oldtag,newtag]]
                if not all(p.exists() for p in paths):continue
                before,after=[json.loads(p.read_text())['rows'] for p in paths]
                assert all(c['case_id']==a['case_id']==b['case_id'] for c,a,b in zip(cases,before,after))
                item['effects'][split]={'cases':len(cases),'triggered':sum(condition(c,card['condition']) for c in cases),
                 'observed_fact_counts_when_triggered':dict(collections.Counter(len(c['input'].split(' ; ')) for c in cases if condition(c,card['condition']))),
                 'checked_fact_count_changed':sum(len(a['checks'].get('verified_input_quotes',[]))!=len(b['checks'].get('verified_input_quotes',[])) for a,b in zip(before,after)),
                 'plan_changed':sum(a['plan']!=b['plan'] for a,b in zip(before,after)),
                 'assessment_changed':sum(a['assessment']!=b['assessment'] for a,b in zip(before,after)),
                 'evidence_changed':sum(a['evidence']!=b['evidence'] for a,b in zip(before,after)),
                 'order_set_changed':sum({key(o,FIELDS) for o in a['orders']}!={key(o,FIELDS) for o in b['orders']} for a,b in zip(before,after)),
                 'before_drug_f1':metrics(before,cases)['drug_micro_f1'],'after_drug_f1':metrics(after,cases)['drug_micro_f1']}
        out.append(item)
    save(HERE/'results/learning_diagnostics.json',{'complete':True,'rounds':out,'attempt_dispositions':dict(dispositions),
       'retained_cards':len(learning['selected_state']['cards']),
       'interpretation':'Observable adapter traces; no clinical correctness or internal neural-circuit claim.',
       'ground_truth_is_training_feedback_only':True})
    print(json.dumps(out,indent=2))
if __name__=='__main__':main()
