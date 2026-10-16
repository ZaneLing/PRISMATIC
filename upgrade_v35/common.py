import hashlib,json,os,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parent.parent
HERE=ROOT/'upgrade_v35'
sys.path.insert(0,str(ROOT/'upgrade_v8'))
from public_client import LOCAL,request,json_object,digest,ledger_total
RUN=LOCAL.parent/'rxrsi-v35';RUN.mkdir(exist_ok=True)
MODEL='deepseek/deepseek-v4.1-flash'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 t=p.with_suffix(f'.{os.getpid()}.tmp');t.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');t.replace(p)
def configure():
 p=HERE/'protocol.json'
 if not p.exists():
  save(p,{'created_utc':datetime.now(timezone.utc).isoformat(),'model':MODEL,'data_sha256':sha(LOCAL/'data.json'),
   'ledger_start_usd':ledger_total(),'max_incremental_usd':25,
   'primary_data':'Same historically observed RxSafe988 and RxQA300; exploratory repeated benchmark use, no test-driven edits within this experiment.',
   'development':'190 proposal,197 guard; select by proposal accuracy then require guard gain over matched three-call no-evidence control. No test outcome chooses configuration.',
   'arms':['no_evidence','old_evidence','verified_evidence'],
   'architecture':'Three calls: observable facts and queries; evidence assessment; executable quotation/arithmetic checks and final decision.',
   'equal_budget':'Three calls x1536 output cap for component/control arms. Native author workflows will use the same4608 total generated-token ceiling with80-call upper bound; this equal output-token allowance does not equate actual input cost or calls.',
   'external_sources':['https://open.fda.gov/apis/drug/label/','https://open.fda.gov/apis/drug/label/searchable-fields/'],
   'source_policy':'Existing frozen labels plus drug-name-only openFDA lookups for absent or route-mismatched products; persist every response. No gold or patient context sent to label service.',
   'source_cutoff':'20261016','test_adaptation':False,'restricted_data_sent':False,
   'engineering_target_pp':10,'target_is_not_observed_result':True})
 d=json.loads(p.read_text());assert d['data_sha256']==sha(LOCAL/'data.json')
 os.environ['RXRSI_PUBLIC_COST_CAP_USD']=str(d['ledger_start_usd']+d['max_incremental_usd'])
 return d
