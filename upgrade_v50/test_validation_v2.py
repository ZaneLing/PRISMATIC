import unittest
from proposal_validation_v2 import validate
class ValidationRegression(unittest.TestCase):
    def card(self):return {'root_cause':'Observed selection mismatch','condition':'always','instruction':'Check prior orders before selecting a duplicate.','counterexample':'A documented change of frequency can justify a new order.','fact_scope':'selected'}
    def cases(self):return [{'context':{'available_labs':[],'recorded_prior_orders':[]},'catalogue':{'A1':{'drug_name':'example'}}}]
    def test_observed_example_is_not_dose_instruction(self):
        c=self.card();c['counterexample']='A prior 5 mg order may have a documented frequency change.'
        self.assertIsNone(validate(c,self.cases()))
    def test_numeric_instruction_is_still_rejected(self):
        c=self.card();c['instruction']='Administer 5 mg.'
        self.assertEqual(validate(c,self.cases()),'unsupported_dose_instruction')
    def test_training_trace_is_not_general_exception(self):
        c=self.card();c['counterexample']='In T2 the previous 5 mg order was repeated.'
        self.assertEqual(validate(c,self.cases()),'case_specific_counterexample_requires_abstraction')
    def test_t2_clinical_term_is_not_a_trace_reference(self):
        c=self.card();c['counterexample']='T2-weighted imaging may support a different documented indication.'
        self.assertIsNone(validate(c,self.cases()))
if __name__=='__main__':unittest.main()
