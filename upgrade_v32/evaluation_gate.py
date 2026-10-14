"""Prevent evaluation from reading guard data before all registered choices freeze."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v32'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(split):
    assert split in ['proposal','guard'];pending=[];proof={};audit=HERE/'results/training_audit.json'
    if not audit.exists():pending.append('all_four_training_audits')
    else:
        z=json.loads(audit.read_text())
        if z.get('status')!='passed' or z['auditor_sha256']!=sha(HERE/'audit_training.py') or set(z['arms'])!=set(json.loads((HERE/'protocol.json').read_text())['arms']):pending.append('current_training_audit')
        else:
            proof['training_audit_sha256']=sha(audit)
            for arm,r in z['arms'].items():
                if sha(PRIVATE/arm/'training_complete.json')!=r['training_receipt_sha256'] or sha(PRIVATE/arm/'adapter/adapters.safetensors')!=r['adapter_sha256']:pending.append('changed_training_artifact:'+arm)
    if split=='guard':
        frozen=PRIVATE/'frozen_thresholds.json';selected=HERE/'results/proposal_summary.json';recount=HERE/'results/proposal_audit.json';parent=PRIVATE.parent/'prismatic-v31/seed42/frozen_selection.json'
        for name,p in [('frozen_thresholds',frozen),('proposal_summary',selected),('proposal_audit',recount),('v31_seed42_frozen_selection',parent)]:
            if not p.exists():pending.append(name)
            else:proof[name+'_sha256']=sha(p)
        if recount.exists() and selected.exists():
            z=json.loads(recount.read_text())
            if z.get('status')!='passed' or z['summary_sha256']!=sha(selected) or z['auditor_sha256']!=sha(HERE/'audit_evaluation.py') or frozen.exists() and z['frozen_thresholds_sha256']!=sha(frozen):pending.append('current_proposal_audit')
        if frozen.exists() and selected.exists():
            z=json.loads(frozen.read_text());r=json.loads(selected.read_text())
            if z['proposal_summary_sha256']!=sha(selected) or z['selection']!=r['selected_thresholds'] or z['guard_inference_preceded_selection']:pending.append('current_frozen_thresholds')
        if parent.exists():
            z=json.loads(parent.read_text())
            if not z.get('all_arms_complete') or z.get('guard_generation_preceded_selection'):pending.append('parent_selection_incomplete')
    return {'status':'open' if not pending else 'closed','pending':pending,'proof':proof}
if __name__=='__main__':
    import sys;print(json.dumps(check(sys.argv[1]),indent=2))
