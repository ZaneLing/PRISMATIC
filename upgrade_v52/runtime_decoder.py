"""Compatible runtime compiler: retain known IDs in complete JSON; never infer IDs."""
import json,re
def decode(raw,c):
 text=raw.strip();fenced=False
 match=re.fullmatch(r'```(?:json)?\s*([\s\S]*?)\s*```',text,flags=re.I)
 if match:text=match.group(1);fenced=True
 try:
  obj=json.loads(text);ids=obj.get('order_ids') if isinstance(obj,dict) else obj
  if not isinstance(ids,list):raise ValueError()
 except (ValueError,TypeError):return dict(order_ids=[],orders=[],invalid=True,invalid_ids=0,syntax_failure=True,wrapper_removed=fenced)
 known=list(dict.fromkeys(x for x in ids if isinstance(x,str) and x in c['catalogue']))
 bad=sum(not isinstance(x,str) or x not in c['catalogue'] for x in ids)
 return dict(order_ids=known,orders=[c['catalogue'][i] for i in known],invalid=bool(bad),invalid_ids=bad,syntax_failure=False,wrapper_removed=fenced)
