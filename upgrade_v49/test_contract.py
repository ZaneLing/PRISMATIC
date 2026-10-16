"""Guard against target leakage, optimistic denominators, and silent fallbacks."""
import unittest
from common import *
from actor import view,compile_raw,check_facts
from experiment import validate_card
class Contract(unittest.TestCase):
    def case(self):
        o={'drug_name':'example','route':'po','dose_value':'1','dose_unit':'mg','frequency_per_24h':None}
        return {'case_id':'synthetic','input':'age_decade 50 ; lab example 3','context':{'available_labs':[],'recorded_prior_orders':[]},
                'catalogue':{'A1':o},'gold':[{**o,'drug_name':'UNSEEN_GOLD_SENTINEL'}]}
    def test_no_gold_enters_prompt(self):self.assertNotIn('UNSEEN_GOLD_SENTINEL',view(self.case()))
    def test_invalid_never_defaults_to_popular_drugs(self):
        r=compile_raw('No output',self.case());self.assertTrue(r['invalid']);self.assertEqual(r['orders'],[])
    def test_bad_id_cannot_erase_valid_id(self):
        r=compile_raw('{"order_ids":["A1","invalid",[],"A1"]}',self.case());self.assertEqual(r['order_ids'],['A1']);self.assertEqual(r['invalid_ids'],2)
    def test_oov_stays_in_denominator(self):
        c=self.case();r={'case_id':c['case_id'],**compile_raw('{"order_ids":["A1"]}',c)}
        m=metrics([r],[c]);self.assertEqual(m['drug_recall'],0);self.assertEqual(m['core_gold_orders'],1);self.assertEqual(m['catalogue_drug_recall_ceiling'],0)
    def test_unknown_frequency_not_scored_as_match(self):
        c=self.case();c['gold']=[c['catalogue']['A1']];r={'case_id':c['case_id'],**compile_raw('{"order_ids":["A1"]}',c)}
        m=metrics([r],[c]);self.assertEqual(m['core_order_micro_f1'],1);self.assertEqual(m['core5_gt_field_coverage'],0)
    def test_invented_patient_quote_rejected(self):
        q=check_facts(self.case(),'{"facts":[{"quote":"dialysis"},{"quote":"age_decade 50"}]}')
        self.assertEqual(q['verified_input_quotes'],['age_decade 50']);self.assertEqual(q['rejected_quotes'],1)
    def test_future_reference_cannot_be_rule_condition(self):
        card={'root_cause':'training discrepancy','condition':'prior_orders_present','instruction':'Select a prior medication if the gold standard includes it.','counterexample':'No prior orders.'}
        self.assertEqual(validate_card(card),'unobservable_reference_predicate')
    def test_training_feedback_may_be_discussed_in_root_only(self):
        card={'root_cause':'GT discrepancy motivates checking duplicated routes','condition':'prior_orders_present','instruction':'Compare available order routes before selecting a duplicate.','counterexample':'Distinct routes may serve distinct documented purposes.'}
        self.assertIsNone(validate_card(card))
if __name__=='__main__':unittest.main()
