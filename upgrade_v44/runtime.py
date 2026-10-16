"""Declared post-freeze schema repair; valid focus strings are unchanged."""
from actor44 import Agent44
from evidence37 import EvidenceTool
class RobustEvidence(EvidenceTool):
 def query(self,c,plan,policy=None):
  focus=plan.get('focus','')
  if isinstance(focus,str):return super().query(c,plan,policy)
  normalized=' '.join(x for x in focus if isinstance(x,str)) if isinstance(focus,list) else ''
  out=super().query(c,dict(plan,focus=normalized),policy)
  out['schema_repairs']=['focus_list_to_text' if isinstance(focus,list) else 'unsupported_focus_to_empty']
  return out
class RuntimeAgent(Agent44):
 def __init__(self,state=None):
  super().__init__(state);self.labels=RobustEvidence()
