"""Frozen candidate-tool controls; choose top-k only on the guard set."""
import argparse,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'upgrade_v7'))
from rx_agent import score
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v9'

def run(freeze_only):
    data=json.loads((PRIVATE/'cases.json').read_text());choices=[]
    for k in [2,3,5,8,10,12,15,20]:
        pred=[list(c['catalogue'].values())[:k] for c in data['guard']]
        choices.append({'top_k':k,'guard':score(pred,[c['gold'] for c in data['guard']])})
    selected=max(choices,key=lambda v:v['guard']['promotion_score'])['top_k']
    frozen={'selected_top_k':selected,'guard_candidates':choices,'test_feedback_used':False}
    (HERE/'results/tool_control_selection.json').write_text(json.dumps(frozen,indent=2)+'\n')
    if freeze_only:return
    assert (HERE/'results/frozen_selection.json').exists(),'Finish both model-selection arms before test scoring.'
    results={}
    for name,k in [('all_20_candidate_tools',20),('guard_selected_top_k_tools',selected)]:
        preds=[list(c['catalogue'].values())[:k] for c in data['test']]
        results[name]=score(preds,[c['gold'] for c in data['test']])
        (PRIVATE/(name+'-test.json')).write_text(json.dumps(preds)+'\n')
    (HERE/'results/tool_control_results.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--freeze-only',action='store_true');a=p.parse_args();run(a.freeze_only)
