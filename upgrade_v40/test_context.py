import unittest
from agent40 import expanded_features
from evidence37 import active_cards
class TestContextPatch(unittest.TestCase):
 def test_empty_state_matches_base(self):
  from evidence37 import features
  c={'dialogue':'A 50-year-old patient has eGFR of 20.','options':['A','B']};p={'entities':[]}
  self.assertEqual(expanded_features(c,p,{'cards':[]}),features(c,p))
 def test_phrase_patch_routes_without_drug_prior(self):
  c={'dialogue':'The patient presents at 12 weeks gestation.','options':['A','B']};p={'entities':[]};card={'name':'timing','trigger_any':['pregnancy_context'],'exclude_any':[],'trigger_terms':{'pregnancy_context':['weeks gestation']}}
  self.assertNotIn('pregnancy_context',expanded_features(c,p,{'cards':[]}))
  f=expanded_features(c,p,{'cards':[card]});self.assertIn('pregnancy_context',f);self.assertEqual(len(active_cards({'cards':[card]},f)),1)
  other=dict(c,dialogue='The patient reports weakness.');self.assertNotIn('pregnancy_context',expanded_features(other,p,{'cards':[card]}))
 def test_exclusion_still_applies_after_patch(self):
  c={'dialogue':'At 12 weeks gestation with renal disease.','options':['A','B']};card={'trigger_any':['pregnancy_context'],'exclude_any':['renal_context'],'trigger_terms':{'pregnancy_context':['weeks gestation']}};self.assertEqual(active_cards({'cards':[card]},expanded_features(c,{'entities':[]},{'cards':[card]})),[])
if __name__=='__main__':unittest.main()
