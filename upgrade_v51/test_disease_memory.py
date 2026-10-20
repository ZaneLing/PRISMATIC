import copy,unittest
from disease_memory import diagnostic_scopes,patient_facts
class TimedDiseaseRouting(unittest.TestCase):
 def case(self):return {'input':'gender F age_decade 50','context':{'hours_since_admission':6,'recorded_prior_orders':[{'drug_name':'example'}],'available_labs':[]}}
 def problem(self,category='renal',hour=4,status='documented'):return {'category':category,'recorded_hours_since_admission':hour,'status':status}
 def test_multiple_documented_categories(self):
  c=self.case();c['context']['available_problems']=[self.problem(),self.problem('cardiovascular')]
  self.assertEqual(diagnostic_scopes(c),{'diagnosis_renal','diagnosis_cardiovascular'})
 def test_future_problem_excluded(self):
  c=self.case();c['context']['available_problems']=[self.problem(hour=7)];self.assertFalse(diagnostic_scopes(c));self.assertEqual(patient_facts(c),[c['input']])
 def test_no_timestamp_no_scope(self):
  c=self.case();p=self.problem();p.pop('recorded_hours_since_admission');c['context']['available_problems']=[p];self.assertFalse(diagnostic_scopes(c))
 def test_uncertain_problem_not_confirmed(self):
  c=self.case();c['context']['available_problems']=[self.problem(status='suspected')];self.assertFalse(diagnostic_scopes(c))
 def test_nonfinite_time_excluded(self):
  c=self.case();c['context']['available_problems']=[self.problem(hour=float('nan'))];self.assertFalse(diagnostic_scopes(c))
 def test_drugs_and_discharge_codes_do_not_create_disease(self):
  c=self.case();c['discharge_diagnoses']=['renal failure'];self.assertFalse(diagnostic_scopes(c))
 def test_facts_are_idempotent_and_explicit(self):
  c=self.case();c['context']['available_problems']=[self.problem()];facts=patient_facts(c);c['input']=' ; '.join(facts);self.assertEqual(patient_facts(c),facts);self.assertIn('documented_predecision_problem_category renal',facts)
if __name__=='__main__':unittest.main()
