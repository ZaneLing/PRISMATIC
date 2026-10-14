import unittest
from rx_agent import record_order,score,error_feedback,OrderMemory,compile_selection

def order(name='example',dose='1',route='po',frequency=None):
    return {'drug_name':name,'dose_value':dose,'dose_unit':'mg','route':route,'frequency_per_24h':frequency}

class RxContracts(unittest.TestCase):
    def test_gt_exact_order_matches(self):
        r=score([[order()]],[[order()]])
        self.assertEqual(r['drug_micro_f1'],1);self.assertEqual(r['core_order_micro_f1'],1)
    def test_wrong_dose_not_rewarded_as_complete_order(self):
        r=score([[order(dose='2')]],[[order()]])
        self.assertEqual(r['drug_micro_f1'],1);self.assertEqual(r['core_order_micro_f1'],0)
    def test_missing_gt_field_excluded_from_field_denominator(self):
        r=score([[order(frequency='3')]],[[order(frequency=None)]])
        self.assertEqual(r['known_fields_scored'],3)
    def test_test_feedback_rejected(self):
        with self.assertRaises(ValueError):error_feedback([],[],split='test')
    def test_train_feedback_identifies_omission_and_dose(self):
        f=error_feedback([order(dose='2')],[order(),order('other')],'train')
        self.assertEqual(f['missed_drugs'],['other']);self.assertEqual(f['field_errors'][0]['field'],'dose_value')
    def test_joint_template_not_independent_field_mix(self):
        m=OrderMemory([[order(dose='1',route='po')],[order(dose='2',route='iv')]])
        p=m.synthesize(['example'],[1],[1.])[0]
        self.assertEqual((p['dose_value'],p['route']),('2','iv'));self.assertIsNone(p['fluid_purpose'])
    def test_compiler_salvages_valid_tool_reference(self):
        r=compile_selection('{"order_ids":["O1","fake"]}',{'O1':order()})
        self.assertEqual(r['orders'],[order()]);self.assertEqual(r['status'],'partial_repair')

if __name__=='__main__':unittest.main()
