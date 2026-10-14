"""Synthetic evidence for label-free execution and independent witness behavior."""
import hashlib,json,inspect
from pathlib import Path
import numpy as np
from scipy import sparse
from rule_memory import apply,induce,verify_edits,agreement,digest
import rule_proposer

HERE=Path(__file__).resolve().parent
def main():
    groups=np.repeat(np.arange(200),2);condition=groups%2==0
    x=sparse.csr_matrix(np.column_stack([condition,np.ones(len(groups))]).astype(np.float32))
    p=np.tile([.4,.8],(len(groups),1));y=np.column_stack([condition,np.ones(len(groups))]).astype(bool)
    training=groups%5!=0;witness=~training
    candidates=induce([],x[training],p[training],y[training],groups[training],.5,['current_diagnosis:SYNTHETIC','generic_history:SYNTHETIC'],['SYNTHETIC_A','SYNTHETIC_B'])
    assert candidates and candidates[0]['rule']['feature_index']==0 and candidates[0]['rule']['drug_index']==0
    selected=[candidates[0]['id']]
    accepted,records=verify_edits([],candidates,selected,x[witness],p[witness],y[witness],groups[witness],.5)
    assert len(accepted)==1 and records[0]['accepted']
    pred=apply(accepted,x,p,.5);assert np.array_equal(pred,y)
    # Counterexample witnesses must reject the same candidate, even when
    # induction evidence was favorable. Labels cannot be supplied to apply.
    wrong=y[witness].copy();wrong[:,0]=False
    rejected,negative=verify_edits([],candidates,selected,x[witness],p[witness],wrong,groups[witness],.5)
    assert rejected==[] and not negative[0]['accepted']
    ablated,_=verify_edits([],candidates,selected,x[witness],p[witness],wrong,groups[witness],.5,gate=False)
    assert len(ablated)==1 and digest(accepted)==digest(ablated)
    assert list(inspect.signature(apply).parameters)==['memory','x','prob','threshold']
    before=p.copy();apply(accepted,x,p,.5);assert np.array_equal(before,p)
    original=rule_proposer.request;payloads=[]
    def fake_request(messages,*args,**kwargs):
        payloads.append(json.loads(messages[1]['content']));return {'raw':json.dumps({'edits':selected}),'cost_usd':0}
    rule_proposer.request=fake_request
    protocol=json.loads((HERE/'rsi_addendum.json').read_text())
    try:
        ids,receipt=rule_proposer.propose(candidates,[],42,1,'own_error_rule_agent',protocol);assert ids==selected and receipt['status']=='valid'
        rule_proposer.request=lambda *a,**kw:{'raw':'{"edits":["invented"]}','cost_usd':0}
        ids,receipt=rule_proposer.propose(candidates,[],42,1,'own_error_rule_agent',protocol);assert ids==[] and receipt['status']=='invalid_edit_response'
    finally:rule_proposer.request=original
    assert set(payloads[0])=={'round','retained_rules','candidate_edits','decision_schema'}
    assert all(set(r)=={'id','operation','feature','drug','action','induction_jaccard_gain','affected_visits','affected_patients'} for r in payloads[0]['candidate_edits'])
    report={'status':'passed','restricted_data_used':False,'external_api_calls':0,'synthetic_cases':len(groups),'synthetic_patients':200,
      'checks':['typed rule improves held-out synthetic witnesses','opposite witness labels reject the same edit','matched gate ablation applies the same proposal','runtime rule application has no target argument and leaves probabilities unchanged','unknown model-generated IDs rejected','external prompt contains only whitelisted aggregate descriptors'],
      'source_sha256':{f:hashlib.sha256((HERE/f).read_bytes()).hexdigest() for f in ['train_rule_agent.py','rule_memory.py','rule_proposer.py']},
      'scope':'Runtime correctness only; no clinical performance or RSI benefit measured.'}
    (HERE/'results/rsi_runtime_probe.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)

if __name__=='__main__':main()
