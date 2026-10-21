import unittest
from runtime_decoder import decode
class RuntimeDecoder(unittest.TestCase):
 def test_complete_mixed_ids_preserve_known_only(self):
  c={'catalogue':{'O1':{'drug_code':'hicl:1'}}};r=decode('{"order_ids":["O1","made_up"]}',c)
  self.assertEqual(r['order_ids'],['O1']);self.assertEqual(r['invalid_ids'],1);self.assertTrue(r['invalid'])
 def test_no_truncation_recovery(self):
  self.assertEqual(decode('{"order_ids":["O1"',{'catalogue':{'O1':{}}})['orders'],[])
 def test_complete_fence_only(self):
  c={'catalogue':{'O1':{'drug_code':'hicl:1'}}}
  self.assertEqual(decode('```json\n["O1"]\n```',c)['order_ids'],['O1'])
  self.assertEqual(decode('```json\n["O1"]',c)['orders'],[])
if __name__=='__main__':unittest.main()
