"""Concrete failure-path checks for product identity, route, citations and math."""
import unittest
from evidence import LabelTool,routes
from workflow import verify,arithmetic
from common import HERE,save
class Tests(unittest.TestCase):
 def test_single_ingredient_rejects_combination(self):
  tool=object.__new__(LabelTool)
  label={'openfda':{'brand_name':['Combo'],'generic_name':['AMLODIPINE AND BENAZEPRIL'],'substance_name':['AMLODIPINE','BENAZEPRIL']}}
  self.assertFalse(tool.identity_ok('amlodipine',label));self.assertTrue(tool.identity_ok('Combo',label))
 def test_salt_identity_retained(self):
  tool=object.__new__(LabelTool);self.assertTrue(tool.identity_ok('clindamycin',{'openfda':{'generic_name':['CLINDAMYCIN HYDROCHLORIDE'],'substance_name':['CLINDAMYCIN HYDROCHLORIDE']}}))
 def test_route_requires_recognized_form(self):
  self.assertEqual(routes('nasal spray'),['nasal']);self.assertEqual(routes('route unspecified'),[])
 def test_quote_must_be_exact(self):
  ev={'excerpts':[{'evidence_id':'E1','quote':'The original prescribed interval is weekly.'}]}
  report={'options':[{'option':'A','citations':[{'evidence_id':'E1','quote':'The original prescribed interval is daily.'}]}]}
  self.assertEqual(verify(report,ev,'')['invalid_checks'],1)
 def test_quote_unknown_source(self):
  report={'options':[{'citations':[{'evidence_id':'missing','quote':'long enough quote'}]}]}
  self.assertEqual(verify(report,{'excerpts':[]},'')['invalid_checks'],1)
 def test_arithmetic_source_binding(self):
  item={'expression':'500 / 5','inputs':[{'value':500,'source':'input','quote':'500 mg in 5 mL'},{'value':5,'source':'input','quote':'500 mg in 5 mL'}]}
  good=verify({'calculations':[item]},{'excerpts':[]},'500 mg in 5 mL');self.assertEqual(good['checks'][0]['result'],100)
  item['expression']='500 / 50';self.assertEqual(verify({'calculations':[item]},{'excerpts':[]},'500 mg in 5 mL')['invalid_checks'],1)
 def test_no_code_execution(self):
  for expr in ['__import__("os")','2**1000000','x+1','float("inf")']:
   with self.assertRaises(ValueError):arithmetic(expr)
 def test_no_zero_division_result(self):
  self.assertEqual(verify({'calculations':[{'expression':'1/0','inputs':[]}]},{'excerpts':[]},'')['invalid_checks'],1)
if __name__=='__main__':
 result=unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
 save(HERE/'results/tool_tests.json',{'status':'passed' if result.wasSuccessful() else 'failed','tests':result.testsRun,'scope':'Synthetic failure-path software tests, not clinical safety accuracy.'})
 if not result.wasSuccessful():raise SystemExit(1)
