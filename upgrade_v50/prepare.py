"""Reuse the audited evaluation cohorts; prepare 144 different training admissions."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import json,sys,shutil,joblib,numpy as np
from common import *
sys.path.insert(0,str(ROOT/'upgrade_v21'))
from run_comparison import text_view
def main():
    previous=PRIVATE.parent/'prismatic-v49';PRIVATE.mkdir(exist_ok=True)
    data=json.loads((previous/'cases.json').read_text());source=json.loads((SOURCE/'cases.json').read_text())
    bundle=joblib.load(SOURCE/'data.joblib');run=joblib.load(SOURCE/'run_seed_42.joblib');classes=bundle['classes']
    ix=slice(144,288);x=run['x']['train'][ix];prob=run['models'][40000].predict_proba(x)
    names=[sorted(classes[j] for j in np.argsort(-p)[:24]) for p in prob];orders=run['tools'][40000].compile(names,x,conditional=True)
    data['train']=[{**c,'input':text_view(c),'catalogue':{f'A{j+1}':{f:o.get(f) for f in FIELDS} for j,o in enumerate(row)}} for c,row in zip(source['train'][ix],orders)]
    groups={s:{c['subject_hash'] for c in rows} for s,rows in data.items()}
    pairs=[(a,b) for i,a in enumerate(groups) for b in list(groups)[i+1:]]
    assert all(not groups[a]&groups[b] for a,b in pairs)
    save(PRIVATE/'cases.json',data)
    for name in ['flame-initial-seed.json','semantic_embeddings.json']:shutil.copy2(previous/name,PRIVATE/name)
    save(HERE/'results/preparation.json',{'case_counts':{s:len(v) for s,v in data.items()},
      'new_training_source_positions':[144,288],'overlap_with_prior_144_training_admissions':0,
      'patient_split_disjoint':True,'member_sha256':{s:digest([c['case_id'] for c in v]) for s,v in data.items()},
      'source_cases_sha256':sha(SOURCE/'cases.json'),'shared_tool_sha256':sha(SOURCE/'run_seed_42.joblib'),
      'data_sha256':sha(PRIVATE/'cases.json'),'test_history':'Historically exposed; earlier literal-schema test results were observed before this repair. No test label enters the learner.',
      'candidate_space_and_tool_unchanged':True,'external_patient_requests':0})
    print('Prepared', {s:len(v) for s,v in data.items()})
if __name__=='__main__':main()
