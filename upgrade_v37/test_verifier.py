import unittest
from agent37 import verify_applicability,parse_answer
from evidence37 import active_cards,config
class TestMechanisms(unittest.TestCase):
 def test_threshold_deactivation(self):
  text='The eGFR is 65 mL/min.';q='Avoid if eGFR is less than 30 mL/min.';e={'excerpts':[{'evidence_id':'E1','quote':q}]};x={'applicability':[{'parameter':'egfr','patient_value':65,'patient_quote':text,'operator':'lt','threshold':30,'evidence_id':'E1','rule_quote':q}]};r=verify_applicability(x,e,text);self.assertFalse(r[0]['condition_satisfied']);x['applicability'][0]['operator']='gt';self.assertEqual(verify_applicability(x,e,text)[0]['status'],'unverified_comparison')
 def test_unobserved_patient_value(self):
  q='Avoid if age is under 18 years.';x={'applicability':[{'parameter':'age','patient_value':17,'patient_quote':'A 40-year-old patient.','operator':'lt','threshold':18,'evidence_id':'E1','rule_quote':q}]};self.assertEqual(verify_applicability(x,{'excerpts':[{'evidence_id':'E1','quote':q}]},'A 40-year-old patient.')[0]['status'],'unverified_comparison')
 def test_scope_exclusion(self):
  c={'name':'renal','trigger_any':['renal_context'],'exclude_any':['hepatic_context'],'retrieval_patch':{'variants':3}};self.assertEqual(active_cards({'cards':[c]},['hepatic_context','renal_context']),[]);self.assertEqual(len(active_cards({'cards':[c]},['renal_context'])),1);self.assertEqual(config([c])['variants'],3)
 def test_multi_answer_not_forced_single(self):
  self.assertEqual(parse_answer('{"final":["B","A"]}',4,True)[0],['A','B']);self.assertIsNone(parse_answer('{"final":["B","A"]}',4,False)[0]);self.assertIsNone(parse_answer('{"final":["A","A"]}',4,True)[0])
if __name__=='__main__':unittest.main()
