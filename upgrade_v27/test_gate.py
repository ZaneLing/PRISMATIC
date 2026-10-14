"""Fail closed until every registered selection and development audit freezes."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check():
    pending=[];files={}
    def require(name,status):
        path=HERE/'results'/name
        if not path.exists():pending.append(name+': missing');return None
        z=json.loads(path.read_text())
        if z.get('status')!=status:pending.append(name+': '+str(z.get('status')));return None
        files[name]=sha(path);return z
    for name in ['cohort_audit.json','control_audit.json']:require(name,'passed')
    for panel in ['full','molecular']:
        require(panel+'-controls.json','selection_frozen')
        for seed in [42,137,2026]:
            rule=require(f'{panel}-rsi-seed{seed}.json','selection_frozen')
            cross=require(f'{panel}-rsi-crossfit-audit-seed{seed}.json','complete')
            learned=require(f'{panel}-rsi-learning-audit-seed{seed}.json','passed')
            if rule:
                assert len(rule['rounds'])==5 and not rule['test_inference']
                assert all(sha(HERE/f)==h for f,h in rule['lock']['sources'].items())
                assert sha(HERE/'rsi_addendum.json')==rule['lock']['protocol_sha256']
            if cross:assert len(cross['folds'])==15 and all(f['all_decision_boundaries_identical'] and f['patient_overlap']==0 for f in cross['folds'])
            if learned:
                assert learned['source_report_sha256']==sha(HERE/f'results/{panel}-rsi-seed{seed}.json')
                assert all(sha(HERE/f)==h for f,h in learned['auditor_sources'].items())
            for method in (['ARMR','GAMENet'] if panel=='full' else ['ARMR','GAMENet','SafeDrug']):
                name=f'{panel}-{method}-seed{seed}.json';z=require(name,'selection_frozen')
                a=require(f'{panel}-{method}-selection-audit-seed{seed}.json','passed')
                if z:
                    assert len(z['epochs'])==50 and not z['test_inference']
                    assert all(sha(HERE/f)==h for f,h in z['lock']['source_sha256'].items())
                if a:assert a['source_report_sha256']==sha(HERE/'results'/name)
    decisions=require('rule_decision_audit.json','complete')
    if decisions:assert all(len(s)==3 and all(z['completed_rounds_audited']==5 for z in s.values()) for s in decisions['panels'].values())
    return {'status':'open' if not pending else 'closed','pending':pending,'frozen_results_sha256':files,'test_inference':False}
if __name__=='__main__':
    z=check();print(json.dumps({'status':z['status'],'pending_items':len(z['pending']),'pending':z['pending']},indent=2))
