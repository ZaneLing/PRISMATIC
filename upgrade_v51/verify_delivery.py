"""Validate completed aggregate deliverables against restricted frozen records."""
import datetime,json,hashlib,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v51'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 for name in ['learning.json','trajectory.json','cloud/learning.json','cloud/trajectory.json','cloud/controls_transfer.json','mechanism_audit.json','decoder_replay.json']:
  assert read(HERE/'results'/name)['complete'],name
 old=read(PRIVATE/'local_before_schema_fix/trajectory.json');now=read(HERE/'results/trajectory.json')
 assert [r['metrics'] for r in old['trajectory']]==[r['metrics'] for r in now['trajectory']]
 local=read(PRIVATE/'cases.json');groups={k:{c['subject_hash'] for c in cs} for k,cs in local.items()}
 assert all(not groups[a]&groups[b] for a in groups for b in groups if a<b)
 cloud=read(PRIVATE/'cloud/learning.json');curve=read(HERE/'results/cloud/trajectory.json')
 assert len(cloud['rounds'])==len(curve['trajectory'])==4
 assert [r['cases_seen'] for r in curve['trajectory']]==[0,24,48,72]
 assert [r['retained'] for r in cloud['rounds']]==[r['retained'] for r in curve['trajectory']]
 assert not read(PRIVATE/'cloud/freeze.json')['selection_used_audit']
 cost=read(HERE/'results/cost.json');receipts=[json.loads(x) for x in (PRIVATE/'api_proposer_usage.jsonl').read_text().splitlines()]
 assert abs(cost['api_cost_usd']-sum(r['cost_usd'] for r in receipts))<1e-10 and cost['api_cost_usd']<=10
 assert all(r['patient_rows_sent']==0 and r['case_ids_sent']==0 for r in receipts)
 forbidden={'case_id','subject_hash','hadm_id','subject_id','observed_input','recorded_training_orders','available_labs','recorded_prior_orders'}
 def validate_keys(obj):
  if isinstance(obj,dict):
   assert not forbidden&obj.keys(), 'Patient-field key in aggregate export'
   for value in obj.values():validate_keys(value)
  elif isinstance(obj,list):
   for value in obj:validate_keys(value)
 for p in (HERE/'results').rglob('*.json'):validate_keys(read(p))
 for p in (PRIVATE/'cloud').glob('request-audit-*.json'):validate_keys(read(p)['payload'])
 test=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(HERE),'-p','test_*.py'],capture_output=True,text=True)
 assert test.returncode==0,test.stderr
 tex=ROOT/'paper/latex/v0.3/prismatic_v03_en.tex';comp=read(tex.parent/'compile_check.json')
 assert comp['status']=='success' and comp['source_sha256']==sha(tex)
 manifest={'recorded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'stage':'post-execution source inventory, not preregistration','files':{str(p.relative_to(ROOT)):sha(p) for p in sorted(HERE.glob('*.py'))},'api_cost_usd':cost['api_cost_usd'],'private_patient_exports':0}
 (HERE/'implementation.json').write_text(json.dumps(manifest,indent=2)+'\n')
 result={'complete':True,'local_schema_replay_metrics_identical':True,'patient_disjoint':True,'rounds':3,'distinct_reflection_admissions':72,'audit_admissions':48,'audit_selects_updates':False,'aggregate_export_field_check':'passed','api_receipts':len(receipts),'api_spend_usd':cost['api_cost_usd'],'boundary_tests':test.stderr.strip(),'built_in_latex_compilation':'success','source_sha256':sha(tex)}
 (HERE/'results/verification.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k!='boundary_tests'},indent=2))
if __name__=='__main__':main()
