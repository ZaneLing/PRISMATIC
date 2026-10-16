import unittest
from evidence45 import entity_groups, homeopathic, identity_matches
from obligations import contract_checks


class ProductScopeTests(unittest.TestCase):
    def test_metadata_not_retained_by_old_reader_is_decisive(self):
        label = {'openfda': {'generic_name': ['FERROUS SULFATE'], 'product_type': ['HUMAN OTC DRUG']},
                 'spl_unclassified_section': ['This homeopathic product has not been evaluated for safety.']}
        self.assertTrue(homeopathic(label))
        self.assertFalse(homeopathic({'openfda': label['openfda']}))

    def test_otc_alone_does_not_exclude_conventional_product(self):
        self.assertFalse(homeopathic({'openfda': {'product_type': ['HUMAN OTC DRUG']}}))

    def test_extra_active_ingredient_rejects_combination_match(self):
        source = {'openfda': {'substance_name': ['ALPHA HYDROCHLORIDE', 'BETA']}}
        self.assertTrue(identity_matches(['alpha', 'beta'], source))
        source['openfda']['substance_name'].append('GAMMA')
        self.assertFalse(identity_matches(['alpha', 'beta'], source))

    def test_shared_component_keeps_both_roles(self):
        case = {'dialogue': 'Which combination?', 'options': ['alpha-beta', 'alpha-gamma']}
        plan = {'entities': [{'name': name, 'input_quote': option, 'option': letter}
                            for letter, option in zip('AB', case['options']) for name in option.split('-')]}
        groups = entity_groups(case, plan, {})
        self.assertEqual({x['option'] for x in groups if x['name'] == 'alpha'}, {'A', 'B'})
        self.assertEqual(sum(x['scope'] == 'combination' for x in groups), 2)

    def test_replacement_is_not_combination(self):
        case = {'dialogue': 'Choose an action.', 'options': ['replace alpha with beta']}
        plan = {'entities': [{'name': n, 'input_quote': case['options'][0], 'option': 'A'} for n in ['alpha', 'beta']]}
        self.assertFalse(any(x['scope'] == 'combination' for x in entity_groups(case, plan, {})))

    def test_option_prose_is_not_patient_observation(self):
        case = {'dialogue': 'The patient receives transfusions.', 'options': ['The patient has dialysis.']}
        assessment = {'decisive_claims': [{'patient_quote': case['options'][0], 'scope': 'combination', 'evidence_id': 'E1', 'source_quote': 'A component is indicated.'}]}
        evidence = {'excerpts': [{'evidence_id': 'E1', 'quote': 'A component is indicated.', 'product_scope': 'component'}]}
        result = contract_checks(assessment, case, evidence)['claims'][0]
        self.assertFalse(result['patient_bound'])
        self.assertTrue(result['source_bound'])
        self.assertTrue(result['combination_scope_mismatch'])


if __name__ == '__main__':
    unittest.main()
