"""Stronger proposer receives aggregate counts only; never patient rows or traces."""
import json,re,time,urllib.request,urllib.error
from pathlib import Path
from common import PRIVATE,HERE,ROOT,save,digest
from policy import PROCEDURES,SCOPES,REPAIRABLE,PROBLEM_SCOPES
MODEL='anthropic/claude-sonnet-4.6'
LEDGER=PRIVATE.parent/'api_proposer_usage.jsonl'

def propose(packet,state,history,tag,repair=None):
 # Explicit allowlist: no examples, drug names, case IDs, clinical values, or free-text prior cards.
 stats={'cases':packet['cases'],'all_case_root_counts':packet['all_case_root_counts'],'by_observable_context':{g:{k:v for k,v in row.items() if k=='cases' or k in REPAIRABLE} for g,row in packet['by_observable_context'].items()}}
 assert isinstance(stats['cases'],int)
 assert set(stats['all_case_root_counts'])<=set(REPAIRABLE)
 assert all(isinstance(v,(int,float)) for v in stats['all_case_root_counts'].values())
 assert all(k in (SCOPES|PROBLEM_SCOPES) and all(isinstance(v,(int,float)) for v in row.values()) for k,row in stats['by_observable_context'].items())
 state_schema=[{k:c[k] for k in ['operator','when','unless']} for c in state['cards']]
 payload={'training_statistics':stats,'count_units':'Error values are DRUG/ORDER/FACT INSTANCES, not patients. Group cases are admission counts; groups overlap.',
 'available_input_types':['demographics','prior_order_records','available_lab_name_value_unit'],'clinical_diagnoses_available':False,
 'current_state_structure':state_schema,'edit_history':history,'operators':PROCEDURES,'scopes':sorted(SCOPES|set(stats['by_observable_context'])),'root_operator_contract':{k:sorted(v) for k,v in REPAIRABLE.items()}}
 if repair:payload['repair_proposal_and_error']=repair
 system='''You propose bounded executable improvements to RxRSIAgent from aggregate LOCAL training error counts. You receive no patient records. The actor predicts recorded NEW/CHANGED medication orders in hours 6-12 from information recorded by admission+6h. The complete provided input is already visible to the actor. Candidate recall and final drug selection are different stages. Candidate omission can ONLY be addressed by candidate_wide48 or candidate_retrieval48. The classifier vocabulary is 128 raw names; candidate_wide48 widens top24 to top48. candidate_retrieval48 keeps the 24 originals and adds up to 24 drugs recalled from 16 training neighbours, excluding same-patient retrieval. ranked_draft exposes the existing supervised classifier's top8 as a draft for the LLM to review; it does not train a new model or force the final output. The source templates and all weights remain fixed. fact_all repeats already visible facts at a checker and adds NO new patient information. Do not infer that selection errors are caused by insufficient fact checking. Missing evidence is not evidence of clinical contraindication; do not require a separate label quotation for every selected drug when the tool returns only two excerpts. Do not assume this repairs unavailable drugs. If no labels or symptoms exist, evidence alone cannot prove an indication. Current groups identify test availability, NOT diagnoses or abnormal results. Do not invent causal explanations from marginal counts. Do not convert counts of missed drugs into counts of patients. Missing labs is NOT absent prior orders and does not by itself invalidate case retrieval. Prior therapy can be renewed with identical fields; do not require a dose/route change to count a recorded target. Only propose general procedural instructions; no drug-name or dosing commands.
Propose up to TWO different skills. FIRST address candidate_omission if nonzero; SECOND address selection_omission or extra_drugs. Use only listed scopes, with executable unless exclusions when justified by the operator (do not invent clinical contraindications). Prefer broad evidence-supported applicability over arbitrary exclusions. Use previous effects and outcome feedback to avoid repeated failed changes. Return JSON with proposals array. Each object has root_cause (testable hypothesis, not proven cause), cluster (a STRING exactly equal to one listed root, not an object), operator, when (one scope), unless (scope list), instruction (<=90 words), counterexample (general observable exception/limitation, no training case IDs). Return an empty array with a reason only if no supported proposal exists. A proposal is retained only after measurable training and development benefit. Do not promise a gain.'''
 if repair:system+=' Repair only the specified failed proposal; return a single proposal object, not an array.'
 request={'model':MODEL,'messages':[{'role':'system','content':system},{'role':'user','content':json.dumps(payload,sort_keys=True)}],'max_tokens':1600,'temperature':0}
 receipt_key=digest(request);cache=PRIVATE/('cloud-'+receipt_key+'.json')
 if cache.exists():return json.loads(cache.read_text())
 spent=sum(json.loads(x).get('cost_usd',0) for x in LEDGER.read_text().splitlines()) if LEDGER.exists() else 0
 # $0.25 reservation/call exceeds the current model price upper bound for these small aggregate prompts.
 if spent+.25>10:raise RuntimeError('Paid budget guard reached')
 key=None
 for p in (Path.home()/'Desktop/PRISMATIC').glob('*.md'):
  if 'OPENROUTER' not in p.name.upper():continue
  m=re.search(r'sk-or-v1-[A-Za-z0-9]+',p.read_text()+' '+p.name)
  if m:key=m.group(0);break
 if not key:raise RuntimeError('Local credential unavailable; no path or credential printed')
 req=urllib.request.Request('https://openrouter.ai/api/v1/chat/completions',data=json.dumps(request).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},method='POST')
 try:
  with urllib.request.urlopen(req,timeout=120) as response:d=json.load(response)
 except urllib.error.HTTPError as e:raise RuntimeError('Provider HTTP status '+str(e.code)) from None
 usage=d.get('usage',{});cost=usage.get('cost');cost=float(cost) if cost is not None else usage.get('prompt_tokens',0)*.000003+usage.get('completion_tokens',0)*.000015
 raw=d['choices'][0]['message'].get('content') or ''
 out={'raw':raw,'model':MODEL,'usage':usage,'cost_usd':cost,'cost_source':'provider' if usage.get('cost') is not None else 'catalogue_estimate','aggregate_request_sha256':receipt_key,'patient_rows_sent':0,'case_ids_sent':0}
 save(cache,out)
 with LEDGER.open('a') as f:f.write(json.dumps({k:v for k,v in out.items() if k!='raw'})+'\n')
 save(PRIVATE/('request-audit-'+receipt_key+'.json'),{'payload':payload,'patient_records':False})
 print(json.dumps({'stage':tag,'proposer':MODEL,'cost_usd':cost,'aggregate_only':True}),flush=True)
 return out
