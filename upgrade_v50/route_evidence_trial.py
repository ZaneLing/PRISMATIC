"""Exploratory paired development test of label-route eligibility only."""
import time
from common import *
from local_backend import Backend
from audit_results import paired
import actor
import route_evidence

def main():
    protocol = json.loads((HERE/'route_evidence_protocol.json').read_text())
    cases = load_cases()['proposal']; assert digest([c['case_id'] for c in cases]) == protocol['member_sha256']
    b = Backend(); original_batch = b.batch
    namespace = PRIVATE/'route-trial-generation'/str(time.time_ns())
    def controlled(messages, cap=128, tag='infer'):
        b.cache = namespace/tag.replace('/', '_'); b.cache.mkdir(parents=True, exist_ok=True)
        return original_batch(messages, cap, tag)
    b.batch = controlled
    baseline = actor.run(b, cases, 'rxrsi', {'cards': []}, 'route-trial/baseline')
    original = actor.retrieve
    try:
        actor.retrieve = route_evidence.retrieve
        filtered = actor.run(b, cases, 'rxrsi', {'cards': []}, 'route-trial/filtered')
    finally:
        actor.retrieve = original
    save(PRIVATE/'route-evidence-trial.json', {'baseline': baseline, 'filtered': filtered})
    illustrative=[]
    for direction in ['improved','regressed']:
        pool=[]
        for c,a,r in zip(cases,baseline,filtered):
            before=score([a['orders']],[c['gold']])['drug_micro_f1']
            after=score([r['orders']],[c['gold']])['drug_micro_f1']
            if (after>before if direction=='improved' else after<before):
                pool.append((digest(c['case_id']),c,a,r,before,after))
        for _,c,a,r,before,after in sorted(pool,key=lambda x:x[0])[:2]:
            illustrative.append({'category':direction,'case_id':c['case_id'],
                'available_context':c['context'],'reference':c['gold'],
                'before':a['orders'],'after':r['orders'],
                'evidence_before':a['evidence'],'evidence_after':r['evidence'],
                'drug_f1_before':before,'drug_f1_after':after})
    private_text='# Route-evidence cases / 说明书途径实验病例\n\n'
    private_text+='Restricted development examples. Reference agreement is not clinical appropriateness. / 受限开发病例；GT一致性不等于临床适宜性。\n'
    for i,c in enumerate(illustrative,1):
        private_text+=f'\n## {i}. '+c['category']+'\n\n```json\n'+json.dumps(c,ensure_ascii=False,indent=2)+'\n```\n'
    (PRIVATE/'ROUTE_CASE_STUDIES.bilingual.md').write_text(private_text)
    save(HERE/'results/route_evidence_trial.json', {
        'complete': True, 'cases': len(cases), 'split': 'proposal',
        'baseline': metrics(baseline, cases), 'route_filtered': metrics(filtered, cases),
        'paired': paired(cases, baseline, filtered),
        'evidence_changed_cases': sum(a['evidence'] != b['evidence'] for a,b in zip(baseline, filtered)),
        'plan_changed_cases': sum(a['plan'] != b['plan'] for a,b in zip(baseline, filtered)),
        'private_case_studies': len(illustrative),
        'protocol_sha256': sha(HERE/'route_evidence_protocol.json'),
        'selected_for_main_table': False, 'autonomous_rsi_update': False,
        'limits': 'Exploratory researcher tool repair on reused development cases; source contents and input length may change; not clinical safety validation.'})
    print('Finished paired route-evidence development experiment')

if __name__ == '__main__': main()
