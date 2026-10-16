"""Controlled-batch development evidence removal; no checkpoint selection."""
import json,time
from common import *
from local_backend import Backend
import actor
from audit_results import paired

def main():
    b=Backend();data=load_cases();cases=data['proposal'];state={'cards':[]}
    cached=json.loads((PRIVATE/'proposal-base.json').read_text())['rows']
    save(HERE/'evidence_ablation_protocol.json',{'declared_unix':time.time(),'cases':48,'split':'fixed proposal set',
      'member_sha256':digest([c['case_id'] for c in cases]),'amendment':'Fresh paired batch layouts replace cached baseline comparison; retain metadata and remove only spans.',
      'timing':'Before this evidence-removal inference, after main Qwen test results; diagnostic only, never state selection.',
      'output_caps':[128,128,96],'fixed_case_order_and_chunks':True,'selection_from_results':False})
    namespace=PRIVATE/'evidence-controlled-generation'/str(time.time_ns());original_batch=b.batch
    def controlled(messages,cap=128,tag='infer'):
        b.cache=namespace/tag.replace('/','_');b.cache.mkdir(parents=True,exist_ok=True)
        return original_batch(messages,cap,tag)
    b.batch=controlled
    baseline=actor.run(b,cases,'rxrsi',state,'diagnostic/label')
    original=actor.retrieve
    try:
        actor.retrieve=lambda c,plan:{**original(c,plan),'spans':[]}
        rows=actor.run(b,cases,'rxrsi',state,'diagnostic/no-label')
    finally:actor.retrieve=original
    save(PRIVATE/'label-proposal-fresh.json',{'rows':baseline})
    save(PRIVATE/'no-label-proposal.json',{'rows':rows})
    save(HERE/'results/evidence_ablation.json',{'complete':True,'split':'proposal, 48 cases','baseline':metrics(baseline,cases),
      'without_label_excerpts':metrics(rows,cases),'paired':paired(cases,baseline,rows),'checkpoint_selected':False,
      'cached_to_fresh_no_edit_replay':paired(cases,cached,baseline),
      'fixed_case_order_and_chunks':True,'source_metadata_preserved':True,
      'protocol_sha256':sha(HERE/'evidence_ablation_protocol.json'),
      'limits':'Exploratory development intervention; changed source content and token count, not a same-token safety comparison'})
if __name__=='__main__':main()
