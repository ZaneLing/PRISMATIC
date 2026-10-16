"""Compact, typed updater context; public training roles remain executable checks."""
import collections,json
NARROW=('dose_question','interaction_question','renal_context','hepatic_context','pregnancy_context','explicit_route','conditional_question')
def build(base,roots,samples,state,history,attempt,by,seen,bounds):
 alias={c['id']:'T'+str(i+1).zfill(4) for i,c in enumerate(seen)};inverse={v:k for k,v in alias.items()}
 scores=collections.Counter(f for r in roots for f in r['root'].get('trigger_features',[]) if f in NARROW)
 order=sorted(scores,key=lambda x:(-scores[x],x));focus=order[attempt%len(order)] if order else 'conditional_question'
 selected=[r for r in roots if focus in r['root'].get('trigger_features',[])][:6];selected_ids={r['case_id'] for r in selected}
 # Existing detector features and root hypotheses are visibly separate.
 candidates=[x for x in samples if focus in x['features'] or x['id'] in selected_ids]
 errors=[x for x in candidates if not x['success']];success=[x for x in candidates if x['success']]
 errors.sort(key=lambda x:(x['id'] not in selected_ids,x['id']));success.sort(key=lambda x:x['id'])
 def brief(x):
  c=next(c for c in seen if c['id']==x['id']);return {'id':alias[x['id']],'observed_features':x['features'],'input':c['dialogue'][:1800],'focus':x['question_summary'],'role':'success' if x['success'] else 'failure'}
 recent=[{k:t.get(k) for k in ('round','attempt','rejection','probe','schema_errors','regression_root_hypotheses')} for t in history[-2:]]
 def remap(o):
  if isinstance(o,str):return alias.get(o,o)
  if isinstance(o,list):return [remap(x) for x in o]
  if isinstance(o,dict):return {k:remap(v) for k,v in o.items()}
  return o
 payload={'required_single_trigger':focus,'bounds':bounds,'current_state':state,'supported_roots':[{k:v for k,v in r.items() if k not in ('receipt','state_sha256')} for r in selected],'ALLOWED_FAILURE_SUPPORTS':[brief(x) for x in errors[:10]],'ALLOWED_SUCCESS_COUNTEREXAMPLES':[brief(x) for x in success[:10]],'ALLOWED_ROOT_IDS':[alias[r['case_id']] for r in selected],'recent_failures':recent}
 text=base+'\nUse the typed role pools below. Only Txxxx identifiers are allowed. A root-suggested condition may be missing from observed_features: that is a detector mismatch, not permission to pretend the feature is present. If the input really expresses the condition, propose trigger_terms with exact general phrases present in a failure and a success; otherwise choose another valid support. Choose no out-of-pool identifiers. Do not claim an ID was replaced unless the JSON value actually changes. Return null if two supported failures and two genuine successes cannot be found.\n'+json.dumps(remap(payload))
 return text,inverse,focus

def decode(card,inverse):
 if not isinstance(card,dict):return card
 out=dict(card)
 for k in ('support_ids','counterexample_ids','root_ids'):
  if isinstance(out.get(k),list):out[k]=[inverse.get(i,i) for i in out[k]]
 return out
