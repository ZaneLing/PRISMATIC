"""Development-only capacity diagnostics; never select using test errors."""
import json,sys
from pathlib import Path
import joblib
HERE=Path(__file__).resolve().parent;PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v21'
sys.path.insert(0,str(HERE.parent/'upgrade_v7'))
from rx_agent import CORE,key

def main():
    b=joblib.load(PRIVATE/'data.joblib');r=joblib.load(PRIVATE/'run_seed_42.joblib')
    data=json.loads((PRIVATE/'cases.json').read_text());vocabulary=set(b['classes'])
    # Inspect only proposal labels for the subsequent intervention design.
    gold=b['truth']['proposal'];tool=r['tools'][40000];templates={}
    for name,default in tool.memory.defaults.items():
        templates[name]={key(default)}|{tuple(t[:4]) for t in tool.labels.get(name,[])}
    targets=known=joint=joint_reachable=oracle_drugs=oracle_orders=overlap=0
    unobserved_context=0
    for c,orders in zip(data['proposal'],gold):
        names={o['drug_name'] for o in orders};available=names&vocabulary
        complete={key(o) for o in orders if all(o.get(f) is not None for f in CORE)}
        matching={t for t in complete if t[0] in vocabulary and t in templates.get(t[0],set())}
        targets+=len(names);known+=len(available);joint+=len(complete);joint_reachable+=len(matching)
        oracle_drugs+=min(20,len(available));oracle_orders+=min(20,len({t[0] for t in matching}))
        prior={o['drug_name'] for o in c['context']['recorded_prior_orders']};overlap+=len(names&prior)
        unobserved_context+=int(not c['context']['recorded_prior_orders'] and not c['context']['available_labs'])
    report={'split':'proposal only','test_used':False,'cases':len(gold),'gold_drug_instances':targets,'vocabulary_known_drugs':known,'vocabulary_recall_ceiling':known/targets,
      'complete_gold_order_instances':joint,'reachable_joint_tuples_in_default_or_conditional_library':joint_reachable,'joint_tuple_coverage':joint_reachable/joint,
      'drug_oracle_micro_f1_with_perfect_gt_selection':2*oracle_drugs/(oracle_drugs+targets),
      'order_oracle_micro_f1_with_perfect_gt_selection':2*oracle_orders/(oracle_orders+joint),
      'target_drugs_already_in_prior_context':overlap,'prior_context_target_fraction':overlap/targets,
      'cases_without_prior_orders_and_labs':unobserved_context,'full_data_conditional_tool_drugs':len(tool.models),
      'oracle_warning':'Diagnostic support ceilings use proposal ground truth and perfect selection; they are not attained model results and cannot appear as a method row.',
      'next_intervention_scope':'Representation of numeric labs and prior orders, and conditional joint-template support; keep the present evaluation unchanged. Subsequent studies on this test are exploratory and need new confirmation.'}
    (HERE/'results/development_capacity_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)

if __name__=='__main__':main()
