"""Safety-relevant contract checks, including invented evidence and silent nulls."""
import unittest
from jsonschema import Draft202012Validator,ValidationError
from order_protocol import normalize,review,schema

class ContractTests(unittest.TestCase):
    def test_unknowns_remain_unknown(self):
        b=normalize({'orders':[{'drug_name':'sodium chloride','evidence_ids':['E1']}]})
        Draft202012Validator(schema()).validate(b)
        self.assertIsNone(b['orders'][0]['rate_ml_h'])
        r=review(b,{'E1'})
        self.assertIn('fluid_information_missing',[x['kind'] for x in r['findings']])
        self.assertEqual(r['status'],'needs_information')
    def test_retrieval_is_not_patient_evidence(self):
        b=normalize({'orders':[{'drug_name':'example','evidence_ids':['R1']}]})
        self.assertIn('invalid_evidence_reference',[x['kind'] for x in review(b,{'E1'})['findings']])
    def test_negative_or_boolean_dose_rejected(self):
        for value in [-1,True]:
            b=normalize({'orders':[{'dose_value':value}]})
            with self.assertRaises(ValidationError):Draft202012Validator(schema()).validate(b)
    def test_duplicates_reviewed(self):
        b=normalize({'orders':[{'ingredient_id':'example:1'},{'ingredient_id':'example:1'}]})
        self.assertIn('duplicate_ingredient',[x['kind'] for x in review(b,set())['findings']])
    def test_empty_is_abstention_not_safety(self):
        r=review(normalize({'orders':[]}),set())
        self.assertEqual(r['status'],'abstained');self.assertFalse(r['clinically_validated'])
    def test_unknown_fields_not_silently_dropped(self):
        with self.assertRaises(ValueError):normalize({'orders':[{'administration_approved':True}]})
    def test_wrong_atc_granularity_not_guessed(self):
        b=normalize({'orders':[{'atc4':'N02BE01'}]})
        self.assertIsNone(b['orders'][0]['atc4'])
        self.assertIn('unresolved_atc4:N02BE01',b['orders'][0]['uncertainty'])

if __name__=='__main__':unittest.main()
