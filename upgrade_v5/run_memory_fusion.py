"""Validate whether the growing memory helps the stronger static ranker.

The fixed weights below are chosen before inspecting this experiment's test
results. A zero weight explicitly disables memory in the delivered policy.
"""
import json,sys
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
from run_rankers import HERE,ROOT,PRIVATE,residual_query,top,take,text_features,score,paired_f1_delta_ci

WEIGHTS=[0,.1,.25,.5,1.0]

def run():
    frame=pd.read_parquet(ROOT/'prismatic-v4/cohort.parquet')
    parts={s:take(frame,s,4000) for s in ['val','test']}
    gold={s:[set(x) for x in p.atc4_codes] for s,p in parts.items()}
    classes=json.loads((HERE/'results/ranker_memory_results.json').read_text())['classes']
    m=joblib.load(PRIVATE/'experience_memory.joblib')
    active=next(v for v in m['ledger'].versions if v['version']==m['ledger'].active)
    n=active['memory_size'];beta=active['beta']; scores={}
    for s in ['val','test']:
        x=m['base_vectorizer'].transform(text_features(parts[s])); base=m['base_model'].predict_proba(x)
        scores[s]=base+(beta*residual_query(x,m['memory_vectors'][:n],m['memory_residuals'][:n]) if n else 0)
    av=np.load(PRIVATE/'anchor_val_scores.npy'); at=np.load(PRIVATE/'anchor_test_scores.npy')
    grid={str(w):score(gold['val'],top((1-w)*av+w*scores['val']),classes)['micro_f1_at_5'] for w in WEIGHTS}
    weight=max(WEIGHTS,key=lambda w:grid[str(w)])
    selection={'memory_weights':WEIGHTS,'validation_grid':grid,'selected_memory_weight':weight,
               'memory_version':active['version'],'memory_admissions':n,'beta':beta,
               'rule':'validation only; ties prefer less memory'}
    (HERE/'results/memory_fusion_selection.json').write_text(json.dumps(selection,indent=2)+'\n')
    fused=(1-weight)*at+weight*scores['test'];fv=(1-weight)*av+weight*scores['val']
    report={'selection':selection,'test':score(gold['test'],top(fused),classes),
            'paired_fused_minus_static':paired_f1_delta_ci(parts['test'],gold['test'],top(at),top(fused),classes)}
    (HERE/'results/memory_fusion_results.json').write_text(json.dumps(report,indent=2)+'\n')
    np.save(PRIVATE/'fused_test_scores.npy',fused);np.save(PRIVATE/'fused_val_scores.npy',fv)
    for s,p in [('val',fv),('test',fused)]:
        original=PRIVATE/f'{s}_anchor.json'; static=PRIVATE/f'{s}_static_anchor.json'
        if not static.exists():static.write_text(original.read_text())
        source=PRIVATE/'val_labels.jsonl' if s=='val' else ROOT/'prismatic-v4/llm_labels.jsonl'
        rows=[json.loads(x) for x in source.read_text().splitlines()]
        loc={str(h):i for i,h in enumerate(parts[s].hadm_id)}
        out={r['case_id']:[{'atc4':classes[j],'score':float(p[loc[r['hadm_id']],j])} for j in top(p[[loc[r['hadm_id']]]])[0]] for r in rows}
        original.write_text(json.dumps(out))
    print(json.dumps(report),flush=True)

if __name__=='__main__':run()
