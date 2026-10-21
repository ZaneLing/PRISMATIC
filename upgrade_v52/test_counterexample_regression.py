"""Regression: removing one true and one false drug must expose the lost target."""
import unittest
from common52 import *
from learn import propose
from learn_refined import propose_refined
class CounterexampleRegression(unittest.TestCase):
 def test_component_harm_can_be_hidden_by_total_loss(self):
  a=dict(drug_code='hicl:1',route='r',dosage='d',frequency='f');b=dict(a,drug_code='hicl:2');cases=[];pred=[]
  for i in range(8):
   c=dict(case_id=str(i),context=dict(categories=['renal' if i<2 else 'cardiovascular'],prior_orders=[],available_labs=[{}] if i<6 else []),catalogue={'O1':a,'O2':b},evidence=dict(drug_support={},order_support={'O1':0,'O2':0},probabilities={'hicl:1':0,'hicl:2':0}),gold=[a] if i<2 else [])
   cases.append(c);pred.append([a,b] if i<6 else [])
  old=propose(cases,pred,[]);new=propose_refined(cases,pred,[])
  wanted=lambda x:x['card']['when']=='labs_present' and x['card']['unless']==['dx:renal']
  self.assertFalse(any(wanted(x) for x in old))
  retained=[x for x in new if wanted(x)];self.assertEqual(len(retained),1)
  self.assertEqual(retained[0]['empirical_harmful_exceptions'],2)
  self.assertEqual(retained[0]['training_delta'][0],0)
  self.assertLess(retained[0]['training_delta'][1],0)
if __name__=='__main__':unittest.main()
