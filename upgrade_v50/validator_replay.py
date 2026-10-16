"""Replay proposal validation without modifying frozen decisions or predictions."""
import collections,json
from common import *
from proposal_validation_v2 import validate,DOSE

def main():
    d=json.loads((PRIVATE/'learning.json').read_text());data=load_cases();out=[]
    for r in d['rounds'][1:]:
        for i,a in enumerate(r['attempts']):
            if not a.get('card'):continue
            c=a['card'];new=validate(c,data['train'][:r['cases_seen']])
            out.append({'round':r['round'],'attempt':i,'card_sha256':digest(c),'recorded_rejection':a['rejection'],
             'corrected_rejection':new,'numeric_dose_in_instruction':bool(DOSE.search(c.get('instruction',''))),
             'numeric_dose_in_counterexample':bool(DOSE.search(c.get('counterexample','')))})
    save(HERE/'results/validator_replay.json',{'complete':True,'attempts':out,
       'recorded_dispositions':dict(collections.Counter(x['recorded_rejection'] or 'valid_candidate' for x in out)),
       'corrected_dispositions':dict(collections.Counter(x['corrected_rejection'] or 'valid_candidate' for x in out)),
       'frozen_learning_state_modified':False,'new_actor_calls':0,'claim':'Corrected rejection feedback only; no new learned state or performance gain.'})
    print(json.dumps(out,indent=2))

if __name__=='__main__':main()
