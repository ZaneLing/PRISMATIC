import copy
import unittest
from rxrsiagent.clinical_metrics import score


class ClinicalMetrics(unittest.TestCase):
    def setUp(self):
        self.bundle = {'status': 'adjudicated', 'arm_id': 'blinded-A',
            'references': [{'case_id': 'synthetic-1', 'requirements': [
                {'id': 'goal-1', 'domain': 'therapeutic_goal', 'applicable': True, 'critical': True},
                {'id': 'followup', 'domain': 'monitoring', 'applicable': True, 'critical': False}]}],
            'outputs': [{'case_id': 'synthetic-1', 'order_ids': ['order-a']}],
            'reviews': [{'case_id': 'synthetic-1', 'requirements': {'goal-1': True, 'followup': False},
                         'major_error': False, 'unnecessary_orders': {'order-a': False}}]}

    def test_known_omission_is_not_hidden(self):
        r = score(self.bundle)
        self.assertEqual(r['domains']['monitoring']['pass_rate_among_rated'], 0)
        self.assertEqual(r['domains']['therapeutic_goal']['pass_rate_among_rated'], 1)

    def test_missing_review_is_unknown(self):
        self.bundle['reviews'] = []
        r = score(self.bundle)
        self.assertIsNone(r['major_error_cases']['event_rate_among_rated'])
        self.assertEqual(r['domains']['therapeutic_goal']['assessment_coverage'], 0)

    def test_empty_order_set_is_not_perfect_appropriateness(self):
        self.bundle['outputs'][0]['order_ids'] = []
        self.bundle['reviews'][0]['unnecessary_orders'] = {}
        r = score(self.bundle)
        self.assertIsNone(r['unnecessary_orders']['event_rate_among_rated'])
        self.assertEqual(r['order_action_coverage'], 0)

    def test_unknown_critical_cannot_be_called_safe(self):
        self.bundle['reviews'][0]['requirements']['goal-1'] = None
        with self.assertRaises(ValueError): score(self.bundle)

    def test_case_or_order_inventory_cannot_change(self):
        b = copy.deepcopy(self.bundle)
        b['outputs'] = []
        with self.assertRaises(ValueError): score(b)
        self.bundle['reviews'][0]['unnecessary_orders']['invented'] = True
        with self.assertRaises(ValueError): score(self.bundle)

    def test_non_applicable_is_not_a_success(self):
        self.bundle['references'][0]['requirements'][1]['applicable'] = False
        self.bundle['reviews'][0]['requirements']['followup'] = None
        r = score(self.bundle)
        self.assertNotIn('monitoring', r['domains'])

    def test_incomplete_annotation_cannot_generate_final_results(self):
        self.bundle['status'] = 'awaiting_reviews'
        with self.assertRaises(ValueError): score(self.bundle)


if __name__ == '__main__':
    unittest.main()
