"""Gate the common frozen comparison; never starts generation or fitting."""
import hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT))
from upgrade_v27.test_gate import check as original_gate
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check():
    old=original_gate();pending=['v27: '+x for x in old['pending']];files={}
    def require(path,status):
        if not path.exists():pending.append(str(path.relative_to(ROOT))+': missing');return None
        z=json.loads(path.read_text())
        if z['status']!=status:pending.append(str(path.relative_to(ROOT))+': '+z['status']);return None
        files[str(path.relative_to(ROOT))]=sha(path);return z
    report=require(ROOT/'upgrade_v27/results/test_summary.json','executed_pending_independent_prediction_audit')
    audit=require(ROOT/'upgrade_v27/results/test_audit.json','passed')
    if report and audit:assert audit['source_report_sha256']==sha(ROOT/'upgrade_v27/results/test_summary.json')
    for version in (29,30):
        folder=ROOT/f'upgrade_v{version}'
        for panel in ('full','molecular'):
            for seed in (42,137,2026):
                path=folder/f'results/{panel}-seed{seed}.json';state=require(path,'selection_frozen')
                a=require(folder/f'results/{panel}-audit-seed{seed}.json','passed')
                if state:
                    assert len(state['rounds'])==5 and state['test_inference'] is False
                    assert sha(folder/'protocol.json')==state['lock']['protocol_sha256']
                    assert all(sha(ROOT/p)==h for p,h in state['lock']['source_sha256'].items())
                if state and a:assert a['source_report_sha256']==sha(path) and a['auditor_sha256']==sha(folder/'audit.py')
    return {'status':'open' if not pending else 'closed','pending':pending,'v27_selection_gate':old,'frozen_results_sha256':files}
if __name__=='__main__':
    z=check();print(json.dumps({'status':z['status'],'pending_count':len(z['pending']),'test_inference':False}))
