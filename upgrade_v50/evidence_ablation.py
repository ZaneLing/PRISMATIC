"""Development-only evidence removal diagnostic, never selects a test checkpoint."""
import json
from common import *
from local_backend import Backend
import actor
from audit_results import paired
def main():
    b=Backend();data=load_cases();cases=data['proposal'];state={'cards':[]}
    baseline=json.loads((PRIVATE/'proposal-base.json').read_text())['rows']
    actor.retrieve=lambda c,plan:{'candidate_drugs':len(c['catalogue']),'spans':[],
      'limits':'Controlled ablation: no external label excerpts provided. Absence of a label is not absence of an indication.'}
    rows=actor.run(b,cases,'rxrsi',state,'diagnostic/no-label');save(PRIVATE/'no-label-proposal.json',{'rows':rows})
    save(HERE/'results/evidence_ablation.json',{'split':'proposal, 48 cases','baseline':metrics(baseline,cases),
      'without_label_excerpts':metrics(rows,cases),'paired':paired(cases,baseline,rows),'checkpoint_selected':False,
      'limits':'Exploratory development intervention; changed information and token count, not a same-token safety comparison'})
if __name__=='__main__':main()
