"""Prepare a shared, frozen order catalogue. Never send source rows to APIs."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import json,sys,collections
import joblib,numpy as np
from common import *
sys.path.insert(0,str(ROOT/'upgrade_v21'))
from run_comparison import text_view
def main():
    protocol=json.loads((HERE/'protocol.json').read_text());PRIVATE.mkdir(parents=True,exist_ok=True)
    lock=PRIVATE/'protocol_lock.json'
    if lock.exists():assert json.loads(lock.read_text())['sha256']==digest(protocol)
    else:save(lock,{'sha256':digest(protocol),'test_labels_used_for_selection':False})
    bundle=joblib.load(SOURCE/'data.joblib');run=joblib.load(SOURCE/'run_seed_42.joblib')
    data=json.loads((SOURCE/'cases.json').read_text());classes=bundle['classes'];output={}
    # Fixed first indices are deterministic hashes in the source cohort, not selected for outcome.
    indices={'train':list(range(72)),'proposal':list(range(48)),'guard':list(range(64)),'test':list(range(len(data['test'])))}
    for split,ix in indices.items():
        x=run['x'][split][ix]
        probs=run['models'][40000].predict_proba(x) if split=='train' else run['probs'][40000][split][ix]
        names=[sorted(classes[j] for j in np.argsort(-p)[:24]) for p in probs]
        compiled=run['tools'][40000].compile(names,x,conditional=True)
        output[split]=[]
        for i,orders in zip(ix,compiled):
            c=data[split][i]
            output[split].append({**c,'input':text_view(c),
              'catalogue':{f'A{j+1}':{f:o.get(f) for f in FIELDS} for j,o in enumerate(orders)}})
    save(PRIVATE/'cases.json',output)
    save(HERE/'results/preparation.json',{'protocol_sha256':digest(protocol),
      'source_cases_sha256':sha(SOURCE/'cases.json'),'shared_tool_sha256':sha(SOURCE/'run_seed_42.joblib'),
      'case_counts':{s:len(x) for s,x in output.items()},'split_member_sha256':{s:digest([c['case_id'] for c in x]) for s,x in output.items()},
      'patient_split_disjoint':all(not {c['subject_hash'] for c in output[a]}&{c['subject_hash'] for c in output[b]} for a,b in [('train','proposal'),('train','guard'),('train','test'),('proposal','guard'),('proposal','test'),('guard','test')]),
      'candidate_drugs':24,'vocabulary':128,'raw_patient_data_exported':False})
    print('Prepared', {s:len(x) for s,x in output.items()},flush=True)
if __name__=='__main__':main()
