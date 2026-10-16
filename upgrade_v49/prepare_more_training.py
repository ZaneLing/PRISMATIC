"""A fresh 72-case training stream for the instrumented updater."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import json,sys,joblib,numpy as np
from common import *
sys.path.insert(0,str(ROOT/'upgrade_v21'))
from run_comparison import text_view
def main():
    data=json.loads((SOURCE/'cases.json').read_text());bundle=joblib.load(SOURCE/'data.joblib');run=joblib.load(SOURCE/'run_seed_42.joblib')
    x=run['x']['train'][72:144];prob=run['models'][40000].predict_proba(x);classes=bundle['classes']
    names=[sorted(classes[j] for j in np.argsort(-p)[:24]) for p in prob];orders=run['tools'][40000].compile(names,x,conditional=True)
    cases=[]
    for c,row in zip(data['train'][72:144],orders):cases.append({**c,'input':text_view(c),'catalogue':{f'A{j+1}':{f:o.get(f) for f in FIELDS} for j,o in enumerate(row)}})
    save(PRIVATE/'training-stream-2.json',cases)
    assert not {c['case_id'] for c in cases}&{c['case_id'] for c in load_cases()['train']}
    save(HERE/'results/additional_training.json',{'new_cases':72,'overlap_with_initial_72':0,'member_sha256':digest([c['case_id'] for c in cases]),'test_feedback':False})
if __name__=='__main__':main()
