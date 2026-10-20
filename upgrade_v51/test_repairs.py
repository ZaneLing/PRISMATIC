import unittest
from policy import validate,applies,config,effect_probe,scopes
class RepairTests(unittest.TestCase):
 def case(self):
  cat={'A1':{'drug_name':'example','route':'po'}}
  return {'case_id':'synthetic','input':'gender F','context':{'available_labs':[],'recorded_prior_orders':[]},'catalogue':cat,'catalogues':{'base24':cat,'wide48':dict(cat,A2={'drug_name':'second','route':'po'}),'retrieval48':cat},'retrieval_meta':{'neighbor_drug_votes':{}}}
 def card(self):return {'root_cause':'Truncation','cluster':'candidate_omission','operator':'candidate_wide48','when':'all','unless':[],'instruction':'Inspect newly retrieved candidates.','counterexample':'A prior 5 mg order is not by itself a new order.'}
 def test_numeric_observation_allowed(self):self.assertIsNone(validate(self.card(),[self.case()]))
 def test_numeric_action_rejected(self):
  x=self.card();x['instruction']='Administer 5 mg.';self.assertEqual(validate(x,[self.case()]),'unsupported_dose_instruction')
 def test_exception_executes(self):
  x=self.card();x['unless']=['no_observations'];self.assertFalse(applies(self.case(),x));self.assertEqual(config(self.case(),{'cards':[x]})['candidate'],'base24')
 def test_unknown_or_gt_scope_rejected(self):
  x=self.card();x['when']='GT_contains_drug';self.assertEqual(validate(x,[self.case()]),'unknown_scope')
 def test_old_noop_detected(self):
  x=self.card();x['operator']='fact_all';c=self.case();row={'checks':{'verified_input_quotes':['gender F']},'plan':'{}'}
  self.assertEqual(effect_probe([c],[row],{'cards':[]},{'cards':[x]})['effective_cases'],0)
 def test_real_candidate_effect(self):
  c=self.case();x=self.card();row={'checks':{'verified_input_quotes':[]},'plan':'{}'}
  self.assertEqual(effect_probe([c],[row],{'cards':[]},{'cards':[x]})['effective_cases'],1)
 def test_prior_drug_not_diagnosis(self):
  c=self.case();c['context']['recorded_prior_orders']=[{'drug_name':'insulin'}];self.assertNotIn('glucose_electrolyte_labs',scopes(c))
 def test_no_future_diagnosis_routing(self):
  c=self.case();c['discharge_diagnoses']=['renal failure'];self.assertNotIn('renal_labs',scopes(c))
 def test_explicit_lab_scope(self):
  c=self.case();c['context']['available_labs']=[{'name':'Creatinine','value':1}];self.assertIn('renal_labs',scopes(c))
 def test_ground_truth_cannot_change_actor_input(self):
  import copy
  from actor import view
  from policy import prepare_case,instructions
  c=self.case();c['gold']=[{'drug_name':'target-one'}];z=copy.deepcopy(c);z['gold']=[{'drug_name':'target-two'}];z['discharge_diagnoses']=['future renal disease']
  state={'cards':[self.card()]}
  self.assertEqual(view(prepare_case(c,state)),view(prepare_case(z,state)))
  self.assertEqual(config(c,state),config(z,state));self.assertEqual(instructions(c,state),instructions(z,state))
 def test_root_operator_mismatch_rejected(self):
  x=self.card();x['operator']='fact_all';self.assertEqual(validate(x,[self.case()]),'operator_cannot_repair_declared_root')
 def test_root_description_can_compare_stages(self):
  x=self.card();x['root_cause']='candidate_omission precedes selection_omission';self.assertIsNone(validate(x,[self.case()]))
 def test_temporal_rule_cannot_require_changed_dose(self):
  x=self.card();x.update(operator='temporal_reconcile',cluster='selection_omission',instruction='Only include orders that differ in dose.');self.assertEqual(validate(x,[self.case()]),'incorrect_temporal_rule_excludes_recorded_renewals')
 def test_single_proposal_wrapper_preserves_fields(self):
  from policy import normalize_card
  c=self.card();self.assertEqual(normalize_card({'proposals':[c]}),c)
 def test_multiple_wrapped_proposals_are_not_silently_selected(self):
  from policy import normalize_card
  d={'proposals':[self.card(),self.card()]};self.assertEqual(normalize_card(d),d)
 def test_documented_disease_routes_and_is_visible(self):
  from policy import prepare_case
  from actor import view
  c=self.case();c['context'].update(hours_since_admission=6,available_problems=[{'category':'renal','recorded_hours_since_admission':4,'status':'documented'}])
  x=self.card();x['when']='diagnosis_renal';self.assertIsNone(validate(x,[c]));self.assertTrue(applies(c,x));self.assertIn('documented_predecision_problem_category renal',view(prepare_case(c,{'cards':[x]})))
 def test_future_disease_cannot_activate_skill(self):
  c=self.case();c['context'].update(hours_since_admission=6,available_problems=[{'category':'renal','recorded_hours_since_admission':8,'status':'documented'}])
  x=self.card();x['when']='diagnosis_renal';self.assertFalse(applies(c,x));self.assertEqual(validate(x,[c]),'unknown_scope')
if __name__=='__main__':unittest.main()
