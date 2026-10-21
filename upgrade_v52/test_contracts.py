import unittest,copy
from actor import decode
from skills import *
from learn import pareto
def fixture():
 o=dict(drug_code='hicl:1',route='r',dosage='d',frequency='f');other=dict(o,dosage='d2')
 return dict(context=dict(categories=['renal','cardiovascular'],prior_orders=[],available_labs=[]),catalogue={'O1':o,'O2':other},evidence=dict(drug_support={'hicl:1':5},order_support={'O1':1,'O2':4},probabilities={'hicl:1':.01}))
class Contracts(unittest.TestCase):
 def test_complete_array(self):
  c=fixture();self.assertFalse(decode('["O1"]',c)['invalid']);self.assertTrue(decode('["O1"',c)['invalid']);self.assertTrue(decode('["unknown"]',c)['invalid'])
 def test_target_inaccessible(self):
  c=fixture();a=operate(c,[],'recover_consensus');c['gold']=[dict(drug_code='secret')];self.assertEqual(a,operate(c,[],'recover_consensus'))
 def test_exception(self):
  c=fixture();s=[dict(when='dx:renal',unless=['dx:cardiovascular'],operator='recover_consensus')];self.assertEqual(execute(c,[],s),[]);self.assertTrue(execute(c,[],s,True))
 def test_contextual_joint(self):
  c=fixture();self.assertEqual(operate(c,[c['catalogue']['O1']],'contextual_order'),[c['catalogue']['O2']])
 def test_no_invented_fields(self):
  c=fixture();c['catalogue']['O2']['dosage']=None;self.assertEqual(operate(c,[],'recover_consensus'),[])
 def test_pareto(self):
  self.assertFalse(pareto([-5,1,-10]));self.assertFalse(pareto([0,0,0]));self.assertTrue(pareto([-1,0,-1]))
 def test_retained_prior_not_pruned(self):
  c=fixture();c['evidence']['drug_support']={};c['context']['prior_orders']=[c['catalogue']['O1']];self.assertEqual(operate(c,[c['catalogue']['O1']],'prune_unsupported'),[c['catalogue']['O1']])
 def test_reference_counts(self):
  c=fixture();self.assertEqual(counts([c['catalogue']['O1']],[c['catalogue']['O2']])[:3],[0,0,2])
if __name__=='__main__':unittest.main()
