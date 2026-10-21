"""Outcome decomposition and condition/exception audit after selection freezes."""
from common52 import *
from skills import *
def roots(cases,pred):
 out=dict(target_drugs=0,outside_catalogue=0,available_but_missed=0,correct_drug_without_complete_joint_hit=0,extra_drugs=0,complete_target_orders=0,complete_target_order_hits=0)
 for c,pp in zip(cases,pred):
  g={o['drug_code'] for o in c['gold']};p={o['drug_code'] for o in pp};cat={o['drug_code'] for o in c['catalogue'].values()};gp={key(o) for o in c['gold'] if all(o.get(f) for f in FIELDS)};pr={key(o) for o in pp if all(o.get(f) for f in FIELDS)}
  out['target_drugs']+=len(g);out['outside_catalogue']+=len(g-cat);out['available_but_missed']+=len((g&cat)-p);out['extra_drugs']+=len(p-g);out['complete_target_orders']+=len(gp);out['complete_target_order_hits']+=len(gp&pr)
  out['correct_drug_without_complete_joint_hit']+=sum(n in g&p and not any(k[0]==n for k in gp&pr) and any(k[0]==n for k in gp) for n in g)
 return out
def main():
 e=json.loads((HERE/'results/evaluation.json').read_text());cases=json.loads((PRIVATE/'audit.json').read_text());pred=json.loads((PRIVATE/'audit_predictions.json').read_text());base=pred['fixed_qwen'];final=pred['qwen-52'];state=json.loads((PRIVATE/'qwen-52-states.json').read_text())[-1]
 d=dict(recovered_correct_drugs=0,lost_correct_drugs=0,removed_extra_drugs=0,added_extra_drugs=0,recovered_complete_joint_targets=0,lost_complete_joint_targets=0,removed_extra_joint_tuples=0,added_extra_joint_tuples=0)
 for c,a,b in zip(cases,base,final):
  g={o['drug_code'] for o in c['gold']};aa={o['drug_code'] for o in a};bb={o['drug_code'] for o in b};gt={key(o) for o in c['gold'] if all(o.get(f) for f in FIELDS)};pa={key(o) for o in a if all(o.get(f) for f in FIELDS)};pb={key(o) for o in b if all(o.get(f) for f in FIELDS)}
  for k,v in [('recovered_correct_drugs',len((bb-aa)&g)),('lost_correct_drugs',len((aa-bb)&g)),('removed_extra_drugs',len((aa-bb)-g)),('added_extra_drugs',len((bb-aa)-g)),('recovered_complete_joint_targets',len((pb-pa)&gt)),('lost_complete_joint_targets',len((pa-pb)&gt)),('removed_extra_joint_tuples',len((pa-pb)-gt)),('added_extra_joint_tuples',len((pb-pa)-gt))]:d[k]+=v
 bycard=[];current=base
 for card in state:
  after=predict(cases,current,[card]);active=sum(applies(c,card) for c in cases);changed=sum({key(o) for o in a}!={key(o) for o in b} for a,b in zip(current,after));before_m=metrics(current,cases);after_m=metrics(after,cases)
  bycard.append(dict(card=card,active_patients=active,changed_patients=changed,error_count_delta=[after_m['counts'][i]-before_m['counts'][i] for i in range(3)]));current=after
 assert current==final
 result={'initial_roots':roots(cases,base),'final_roots':roots(cases,final),'transition':d,'card_interventions':bycard,'all_three_primary_errors_strictly_decreased':all(e['arms']['qwen-52']['all'][k]<e['arms']['fixed_qwen']['all'][k] for k in ['missed_drugs_per_patient','extra_drugs_per_patient','joint_errors_per_patient']),'generated_new_operator_code':False,'changed_backbone_weights':False,'changed_update_algorithm':False,'teacher_proposed_prose_reflections':False,'automatically_selected_executable_conditions':True}
 save(HERE/'results/mechanisms.json',result);print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()
