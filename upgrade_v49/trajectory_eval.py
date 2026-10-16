"""Evaluate each already-frozen retained state; never choose a test-best state."""
import json
from common import *
from local_backend import Backend
from experiment import execute
from audit_results import paired
def main():
    data=load_cases();learning=json.loads((HERE/'results/learning_scope.json').read_text());assert learning['complete']
    freeze=json.loads((HERE/'test_freeze_scope.json').read_text());assert not freeze['selection_used_test_labels']
    b=Backend();curve=[];seen={};baseline=None
    for r in learning['rounds']:
        state=r['state'];sig=digest(state)
        if sig not in seen:seen[sig]=execute(b,data['test'],'rxrsi',state,f'qwen-trajectory-{r["round"]}')
        rows=seen[sig]
        if baseline is None:baseline=rows
        curve.append({'round':r['round'],'cases_seen':r['cases_seen'],'state_sha256':sig,'retained_cards':len(state['cards']),
          'metrics':metrics(rows,data['test']),'paired_to_initial':paired(data['test'],baseline,rows)})
    save(HERE/'results/round_curve.json',{'trajectory':curve,'unique_states':len(seen),'chosen_by_test':False,'complete':True})
if __name__=='__main__':main()
