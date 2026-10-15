import json
import tempfile
import unittest
from pathlib import Path
from rxrsiagent import RxRSIAgent, LabelIndex


class Contracts(unittest.TestCase):
    def setUp(self):
        self.agent = RxRSIAgent()
        self.order = dict(ingredient_id='drug-x', indication='documented-purpose',
                          dose=1, dose_unit='mg', route='oral', frequency='daily', duration='defined')

    def test_complete_is_not_clinical_clearance(self):
        r = self.agent.assess({'allergy_ingredient_ids': []}, [self.order])
        self.assertEqual(r['status'], 'structurally_complete')
        self.assertEqual(r['clinical_safety'], 'not_assessed')
        self.assertTrue(all(d['status'] == 'not_assessed' for d in r['clinical_domains']))

    def test_unknown_allergy_and_missing_frequency_are_visible(self):
        r = self.agent.assess({}, [dict(self.order, frequency=None)])
        codes = {x['code'] for x in r['issues']}
        self.assertTrue({'allergy_status_missing', 'missing_frequency'} <= codes)

    def test_recorded_allergy_and_duplicate(self):
        r = self.agent.assess({'allergy_ingredient_ids': ['drug-x']}, [self.order, self.order])
        codes = {x['code'] for x in r['issues']}
        self.assertTrue({'recorded_ingredient_allergy', 'potential_duplicate_ingredient'} <= codes)

    def test_iv_and_adjunct_require_evidence(self):
        r = self.agent.assess({}, [dict(self.order, route='IV', role='adjunct')])
        codes = {x['code'] for x in r['issues']}
        self.assertTrue({'iv_mode_missing', 'missing_preparation_evidence',
                         'missing_administration_rate_evidence', 'adjunct_purpose_missing'} <= codes)

    def test_invalid_dose(self):
        for dose in [-1, 0, float('nan'), float('inf'), True, 'one']:
            with self.subTest(dose=dose):
                r = self.agent.assess({}, [dict(self.order, dose=dose)])
                self.assertIn('dose_not_positive_finite_number', {x['code'] for x in r['issues']})

    def test_actors_cannot_return_invalid_option(self):
        agent = RxRSIAgent(actor=lambda context: {'final': 'Z'})
        self.assertEqual(agent.run('fictional', ['a', 'b'])['status'], 'invalid_output')

    def test_absent_actor_does_not_predict(self):
        self.assertEqual(self.agent.run('fictional')['status'], 'needs_actor')

    def test_invalid_order_container(self):
        self.assertEqual(self.agent.assess({}, 'not a list')['status'], 'invalid_order_container')

    def test_empty_orders_and_invalid_identity_are_visible(self):
        r = self.agent.assess({}, [])
        self.assertIn('empty_order_set_requires_justification', {x['code'] for x in r['issues']})
        r = self.agent.assess({'allergy_ingredient_ids': 'drug-x'},
                              [dict(self.order, ingredient_id=['drug-x'])])
        self.assertTrue({'invalid_allergy_list', 'invalid_ingredient_id'} <= {x['code'] for x in r['issues']})

    def test_selected_memory_reaches_actor(self):
        seen = []
        agent = RxRSIAgent(actor=lambda context: seen.append(context) or {'final': 'A'})
        self.assertEqual(agent.run('fictional', ['a', 'b'])['status'], 'completed')
        self.assertEqual(seen[0]['skill_memory']['sha256'], agent.profile['skill_sha256'])
        self.assertTrue(seen[0]['skill_memory']['text'])
        self.assertEqual(seen[0]['skill_memory']['authority'], 'experience_not_clinical_guidance')

    def test_test_experience_cannot_enter_memory(self):
        record = dict(split='test', scope='task', source_hashes=['sha'], trigger='condition',
                      action='review', counterexamples=['exception'], authority='experience_not_clinical_guidance')
        self.assertFalse(self.agent.admit_memory(record)['accepted'])
        record['split'] = 'train'
        self.assertTrue(self.agent.admit_memory(record)['accepted'])
        record['authority'] = 'clinical_rule'
        self.assertFalse(self.agent.admit_memory(record)['accepted'])

    def test_question_mentions_and_dosage_sections(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'labels.json'
            quote = 'Fictional product instructions for the synthetic unit test only.'
            p.write_text(json.dumps({'x': {'status': 'matched', 'label': {'id': 'fixture-label',
                'openfda': {'generic_name': ['fictionaldrug']}, 'dosage_and_administration': [quote]}}}))
            index = LabelIndex(p)
            r = index.query('What is the frequency of fictionaldrug?', ['daily', 'weekly'])
            self.assertEqual(r['label_ids'], ['fixture-label'])
            self.assertEqual(r['excerpts'][0]['quote'], quote)
            self.assertEqual(r['clinical_safety'], 'not_assessed')
            self.assertEqual(index.query('fictionaldrugextra')['label_ids'], [])
            self.assertEqual(index.query('unlisted medicine')['status'], 'not_assessed')


if __name__ == '__main__':
    unittest.main()
