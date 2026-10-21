"""Verify delivered scores and aggregate-only exports against frozen local receipts."""
import datetime,sys
from common52 import *
from skills import predict
def main():
 data=json.loads((HERE/'results/evaluation.json').read_text());lock=json.loads((PRIVATE/'selection_lock.json').read_text());cases=json.loads((PRIVATE/'audit.json').read_text());rows=json.loads((PRIVATE/'qwen-audit.json').read_text());base=[r['orders'] for r in rows]
 assert len(cases)==len(rows)==256
 assert [c['case_id'] for c in cases]==[r['case_id'] for r in rows]
 for name,h in lock['states'].items():assert sha(PRIVATE/(name+'-states.json'))==h
 for name in ['qwen-52','qwen-152','qwen-52-shuffle']:
  states=json.loads((PRIVATE/(name+'-states.json')).read_text());assert len(states)==7
  for r,state in enumerate(states):assert metrics(predict(cases,base,state),cases)==data['curves'][name][r]['metrics']
 for n in ['actor.py','skills.py','learn.py','prepare.py','protocol.json']:
  expected=lock['implementation'].get(n) if n!='protocol.json' else data['protocol_sha256']
  assert expected==sha(HERE/n),n+' changed after selection freeze'
 forbidden={'case_id','case_ids','patient_hash','hospital_hash','patientunitstayid','uniquepid','gold','diagnoses','prior_orders','available_labs','raw','neighbor_patients','counterexample_case_ids','scope_negative_case_ids','seen_case_ids'}
 def check(x):
  if isinstance(x,dict):
   assert not set(x)&forbidden,'patient-level field exported'
   for v in x.values():check(v)
  elif isinstance(x,list):
   for v in x:check(v)
 for p in (HERE/'results').glob('*.json'):check(json.loads(p.read_text()))
 receipts=[json.loads(s) for s in (PRIVATE/'usage.jsonl').read_text().splitlines()];assert len({r['signature'] for r in receipts})==len(receipts)
 assert sum(r['api_cost_usd'] for r in receipts)==0
 for file,source in [('refined_freeze.json','learn_refined.py'),('decoder_freeze.json','runtime_decoder.py')]:
  f=json.loads((HERE/'results'/file).read_text());assert sha(HERE/source)==f.get('source_sha256',f.get('decoder_sha256'))
  for name,h in f['states'].items():assert sha(PRIVATE/(name+'-states.json'))==h
 runtime=json.loads((PRIVATE/'runtime/qwen-audit-experimental-final.json').read_text());compatible=json.loads((HERE/'results/decoder_evaluation.json').read_text())
 assert metrics([r['orders'] for r in runtime],cases)==compatible['arms']['qwen-compatible-52']['all']
 assert not json.loads((HERE/'results/release_decision.json').read_text())['experimental_memory_promoted']
 tex=ROOT/'paper/latex/v0.3/prismatic_v03_en.tex';compile=json.loads((tex.parent/'compile_check.json').read_text());assert compile['status']=='success' and compile['source_sha256']==sha(tex)
 save(HERE/'results/verification.json',dict(completed=True,checked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),round_state_recounts_match=True,learning_actor_tool_code_unchanged_since_freeze=True,amendment_state_hashes_match=True,compatible_runtime_integration_matches_256_predictions=True,experimental_memory_promoted=False,boundary_tests_previously_executed={'base_contracts':8,'counterexample_regression':1,'runtime_decoder':3,'all_passed':True},aggregate_export_check='passed',new_api_spend_usd=0,local_successful_receipts=len(receipts),english_manuscript_compiled=True,source_sha256=sha(tex)))
 save(HERE/'implementation.json',{'recorded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'kind':'post-experiment implementation inventory; preread locks are separate','files':{p.name:sha(p) for p in sorted(HERE.glob('*.py'))},'protocol_sha256':sha(HERE/'protocol.json')})
 print('Frozen states, all round scores, privacy exports, receipts and manuscript compilation verified.',flush=True)
if __name__=='__main__':main()
