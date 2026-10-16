import json,unittest
from unittest.mock import patch
import actor44
from runtime import RobustEvidence
from evidence37 import EvidenceTool
class RuntimeTests(unittest.TestCase):
 def test_valid_focus_is_unchanged(self):
  plan={'focus':'renal dosing'};expected={'excerpts':[]};tool=RobustEvidence.__new__(RobustEvidence)
  with patch.object(EvidenceTool,'query',return_value=expected) as parent:
   self.assertIs(tool.query({},plan),expected);self.assertIs(parent.call_args[0][1],plan)
 def test_list_focus_is_normalized_without_mutating_plan(self):
  plan={'focus':['renal','dosing',None]};tool=RobustEvidence.__new__(RobustEvidence)
  with patch.object(EvidenceTool,'query',return_value={'excerpts':[]}) as parent:
   got=tool.query({},plan);self.assertEqual(parent.call_args[0][1]['focus'],'renal dosing');self.assertEqual(plan['focus'],['renal','dosing',None]);self.assertEqual(got['schema_repairs'],['focus_list_to_text'])
 def test_task_schema_is_explicit_and_uses_three_calls(self):
  class Labels:
   def query(self,*args):return {'products':[],'excerpts':[],'flags':[]}
  for multiple in [False,True]:
   agent=actor44.Agent44.__new__(actor44.Agent44);agent.state={'cards':[]};agent.labels=Labels();prompts=[]
   def fake(prompt,role,max_tokens=1536):
    prompts.append((role,prompt));return {'raw':json.dumps({'focus':'dosing','facts':[],'entities':[]} if role=='plan' else {'options':[]} if role=='assess' else {'final':['A']})}
   with patch.object(actor44,'call',side_effect=fake):r=agent.solve({'id':'synthetic','dialogue':'A patient asks about treatment.','options':['A','B'],'multiple':multiple})
   self.assertEqual(len(prompts),3);self.assertEqual(r['prediction'],['A'])
   if multiple:self.assertNotIn('"draft":"one option letter"',prompts[1][1]);self.assertNotIn('"final":"one option letter"',prompts[2][1])
   else:self.assertTrue(prompts[1][1].startswith(actor44.ASSESS37));self.assertTrue(prompts[2][1].startswith(actor44.FINAL37))
if __name__=='__main__':unittest.main()
