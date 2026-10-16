"""Predeclared component diagnostic; no test-selected checkpoint or repair."""
import copy,json,time
from common import *
import actor
from audit_results import paired
from local_backend import Backend

def declare():
    p=HERE/'component_protocol.json'
    if p.exists():return
    assert not (HERE/'results/comparison.json').exists(), 'Declare before reading a full-test score'
    cases=sorted(load_cases()['test'],key=lambda c:digest(['component-4916',c['case_id']]))[:128]
    frozen=json.loads((HERE/'test_freeze_scope.json').read_text())
    save(PRIVATE/'component-test-members.json',[c['case_id'] for c in cases])
    save(p,{'declared_unix':time.time(),'cases':128,'selection':'lowest SHA256(component-4916, case_id); independent of labels',
      'member_sha256':digest([c['case_id'] for c in cases]),'retained_state_sha256':frozen['state_sha256'],
      'arms':['initial','retained','instruction_only','fact_scope_only'],
      'interventions':{'instruction_only':'keep the retained card text and trigger; reset fact_scope to selected',
        'fact_scope_only':'keep the retained executable fact_scope and trigger; suppress skills() text'},
      'output_caps':[128,128,96],'selection_from_results':False,
      'limits':['small exploratory component diagnostic','same historically exposed MIMIC test source','not clinical-safety validation']})

def main():
    protocol=json.loads((HERE/'component_protocol.json').read_text());data=load_cases()
    ids=json.loads((PRIVATE/'component-test-members.json').read_text());pool={c['case_id']:c for c in data['test']}
    cases=[pool[i] for i in ids];assert digest(ids)==protocol['member_sha256']
    state=json.loads((HERE/'test_freeze_scope.json').read_text())['state'];assert digest(state)==protocol['retained_state_sha256']
    b=Backend();raw={};summary={};prior={}
    for name,suffix in [('initial','base'),('retained','selected')]:
        saved=json.loads((PRIVATE/f'qwen-test-rxrsi_{suffix}.json').read_text())['rows']
        byid={r['case_id']:r for r in saved};prior[name]=[byid[i] for i in ids]
    # Fresh per-batch caches keep all arms on the same case/chunk schedule.
    # Reusing a full-cohort response would mix different original batch layouts.
    namespace=PRIVATE/'component-controlled-generation'/str(time.time_ns())
    original_batch=b.batch
    def controlled(messages,cap=128,tag='infer'):
        b.cache=namespace/tag.replace('/','_');b.cache.mkdir(parents=True,exist_ok=True)
        return original_batch(messages,cap,tag)
    b.batch=controlled
    raw['initial']=actor.run(b,cases,'rxrsi',{'cards':[]},'component/initial')
    raw['retained']=actor.run(b,cases,'rxrsi',state,'component/retained')
    instruction=copy.deepcopy(state)
    for card in instruction['cards']:card['fact_scope']='selected'
    raw['instruction_only']=actor.run(b,cases,'rxrsi',instruction,'component/instruction')
    original=actor.skills
    try:
        actor.skills=lambda c,s:''
        raw['fact_scope_only']=actor.run(b,cases,'rxrsi',state,'component/fact-scope')
    finally:actor.skills=original
    for name,rows in raw.items():
        for row in rows:row['component_intervention']=name
        save(PRIVATE/f'component-{name}.json',{'rows':rows})
        summary[name]={'metrics':metrics(rows,cases),'paired_to_initial':paired(cases,raw['initial'],rows),
          'mean_checked_facts':sum(len(r.get('checks',{}).get('verified_input_quotes',[])) for r in rows)/len(rows)}
    save(HERE/'results/component_ablation.json',{'complete':True,'cases':len(cases),'arms':summary,
      'cached_full_cohort_to_fresh_replay':{name:paired(cases,prior[name],raw[name]) for name in prior},
      'fixed_case_order_and_chunks':True,'fresh_per_batch_generation':True,
      'selection_from_results':False,'api_cost_usd':0,'protocol_sha256':sha(HERE/'component_protocol.json')})
if __name__=='__main__':
    import sys
    declare() if '--declare' in sys.argv else main()
