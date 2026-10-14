import unittest
from core import parse_codes, clinical_review, ExperienceLedger

class Contracts(unittest.TestCase):
    def test_partial_invalid_does_not_erase_valid(self):
        r=parse_codes('{"codes":["A01AA","invented","A01AA"]}',{'A01AA'})
        self.assertEqual(r['codes'],['A01AA']);self.assertFalse(r['raw_valid'])
    def test_truncation_recovers_prior(self):
        r=parse_codes('{"codes":[',{'A01AA'},['A01AA'])
        self.assertEqual(r['codes'],['A01AA']);self.assertFalse(r['raw_valid'])
    def test_real_abstention_not_forced_to_five(self):
        self.assertEqual(parse_codes('{"codes":[]}',{'A01AA'},['A01AA'])['codes'],[])
    def test_unknown_preserves_prediction_but_never_authorizes(self):
        r=clinical_review(['A01AA'])
        self.assertEqual(r['historical_candidates'],['A01AA'])
        self.assertFalse(r['clinical_clearance']);self.assertEqual(r['executable_orders'],[])
    def test_unverified_contradiction_not_accepted(self):
        r=clinical_review(['A01AA'],[{'code':'A01AA','verdict':'contradicted','evidence_id':'fake'}])
        self.assertEqual(r['clinical_items'][0]['clinical_status'],'needs_information')
    def test_verified_contradiction_blocks_clinical_item_only(self):
        r=clinical_review(['A01AA'],[{'code':'A01AA','verdict':'contradicted','evidence_id':'E1'}],['E1'])
        self.assertEqual(r['clinical_items'][0]['clinical_status'],'blocked')
        self.assertEqual(r['historical_candidates'],['A01AA'])
    def test_test_feedback_rejected(self):
        for split in ['val','test','unreviewed']:
            with self.assertRaises(ValueError):ExperienceLedger().append({'split':split,'case_key':'a'})
    def test_validation_gate_rolls_back_and_replays(self):
        led=ExperienceLedger();led.append({'split':'train','case_key':'a'})
        a=led.checkpoint(.4,{'beta':0});b=led.checkpoint(.3,{'beta':1})
        self.assertTrue(a['promoted']);self.assertFalse(b['promoted']);self.assertEqual(led.active,a['version'])
        replay=ExperienceLedger();replay.append({'split':'train','case_key':'a'})
        self.assertEqual(replay.checkpoint(.4,{'beta':0})['version'],a['version'])

if __name__=='__main__':unittest.main()
