import unittest
from order_decoder import decode
class CompleteArrayDecoder(unittest.TestCase):
 def setUp(self):self.case={'catalogue':{'A1':{'drug_name':'one'},'A2':{'drug_name':'two'}}}
 def test_complete_array(self):
  r=decode('["A1","A2","A1"]',self.case);self.assertEqual(r['order_ids'],['A1','A2']);self.assertTrue(r['decoder_repair'])
 def test_truncated_array_not_completed(self):self.assertTrue(decode('["A1","A',self.case)['invalid'])
 def test_unknown_id_not_selected(self):self.assertTrue(decode('["A3"]',self.case)['invalid'])
 def test_prose_not_interpreted_as_order(self):self.assertTrue(decode('Possible choices: ["A1"]',self.case)['invalid'])
 def test_canonical_unchanged(self):
  r=decode('{"order_ids":["A1"]}',self.case);self.assertFalse(r['decoder_repair']);self.assertEqual(r['order_ids'],['A1'])
 def test_valid_empty_array(self):
  r=decode('[]',self.case);self.assertFalse(r['invalid']);self.assertEqual(r['orders'],[])
if __name__=='__main__':unittest.main()
