"""Check scientifically material scoring and actual closed-gate behavior."""
import json,hashlib
from pathlib import Path
import numpy as np
from evaluation_metrics import score,paired
from test_gate import check
HERE=Path(__file__).resolve().parent
def main():
    pred=np.array([[1,0],[0,0],[0,1],[1,1]],dtype=bool);gold=[{'A','OOV'},set(),{'A'},{'A','B'}];people=['p1','p1','p2','p3']
    z,values,keys=score(pred,gold,people,['A','B'])
    assert abs(z['patient_f1']-11/18)<1e-12 and abs(z['patient_jaccard']-7/12)<1e-12
    assert z['micro_f1']==2*3/9 and z['micro_recall']==3/5 and z['empty_target_fraction']==.25
    assert z['strata']['zero_target']['patient_f1']==1 and z['strata']['nonzero_target']['patients']==3
    assert all(v['difference']==0 and v['patient_ci95']==[0.,0.] for v in paired(values,values).values())
    gate=check();assert gate['status']=='closed' and gate['pending']
    result={'status':'passed','synthetic_patient_averaging_oov_zero_target':'passed','identical_paired_difference':'passed',
      'actual_test_gate_status':gate['status'],'pending_prerequisites':len(gate['pending']),'test_inference':False,
      'source_sha256':{f:hashlib.sha256((HERE/f).read_bytes()).hexdigest() for f in ['evaluation_metrics.py','test_gate.py','evaluate_methods.py','audit_author_selection.py']}}
    (HERE/'results/evaluation_probe.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
if __name__=='__main__':main()
