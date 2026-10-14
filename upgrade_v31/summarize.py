"""Summarize completed audited seeds without selecting new checkpoints.

Patient bootstrap intervals are descriptive and conditional on observed seeds.
All individual predictions and patient identifiers remain in restricted storage.
"""
import hashlib,json
from collections import defaultdict
from pathlib import Path
import numpy as np
from audit_learning import CORE,PRIVATE,transform,verify_rows,sha
HERE=Path(__file__).resolve().parent
VIEWS=('ranked','permuted','reversed')
BASE='base-50d427756c6b1b2fe0c0a10f67fbda1fc8e82c1b'

def arrays(pred,cases):
    """Retain per-patient sufficient counts and per-admission set F1."""
    counts=[];visit=[];groups=defaultdict(list)
    for i,(orders,c) in enumerate(zip(pred,cases)):
        drug={o['drug_name'] for o in orders};gold={o['drug_name'] for o in c['gold']}
        order={tuple(o.get(f) for f in CORE) for o in orders if all(o.get(f) is not None for f in CORE)}
        target={tuple(o.get(f) for f in CORE) for o in c['gold'] if all(o.get(f) is not None for f in CORE)}
        count=[len(drug&gold),len(drug),len(gold),len(order&target),len(order),len(target)]
        counts.append(count);visit.append([2*count[j]/(count[j+1]+count[j+2]) if count[j+1]+count[j+2] else 1. for j in (0,3)])
        groups[c['subject_hash']].append(i)
    visit=np.asarray(visit);counts=np.asarray(counts)
    keys=sorted(groups)
    return {'counts':np.array([counts[groups[k]].sum(0) for k in keys]),'patient':np.array([visit[groups[k]].mean(0) for k in keys]),'visit':visit,'keys':keys}

def micro(counts):
    """Accept arbitrary leading axes, with six sufficient counts last."""
    return np.stack([2*counts[...,j]/np.maximum(1,counts[...,j+1]+counts[...,j+2]) for j in (0,3)],axis=-1)

def stats(values):
    values=np.asarray(values,dtype=float)
    return {'mean':float(values.mean()),'seed_sd':float(values.std(ddof=1)) if len(values)>1 else None}

def delta(first,second,draws=4000):
    """Matched seed x patient arrays; resample the same patients for every seed."""
    ap=np.array([x['patient'] for x in first]);bp=np.array([x['patient'] for x in second])
    ac=np.array([x['counts'] for x in first]);bc=np.array([x['counts'] for x in second])
    assert ap.shape==bp.shape and ac.shape==bc.shape
    point_patient=(ap-bp).mean(axis=(0,1));point_micro=(micro(ac.sum(1))-micro(bc.sum(1))).mean(0)
    rng=np.random.default_rng(31031);patient_draws=[];micro_draws=[]
    for start in range(0,draws,100):
        indices=rng.integers(0,ap.shape[1],size=(min(100,draws-start),ap.shape[1]))
        patient_draws.extend((ap-bp).mean(0)[indices].mean(1))
        micro_draws.extend((micro(ac[:,indices].sum(2))-micro(bc[:,indices].sum(2))).mean(0))
    out={}
    for j,name in enumerate(('drug','core_order')):
        out[name]={'patient_f1_difference':float(point_patient[j]),'patient_f1_ci95':np.quantile(np.array(patient_draws)[:,j],[.025,.975]).tolist(),
                   'micro_f1_difference':float(point_micro[j]),'micro_f1_ci95':np.quantile(np.array(micro_draws)[:,j],[.025,.975]).tolist()}
    return out

def transitions(current,previous):
    """A fix/regression is strictly higher/lower admission F1, not clinical safety."""
    difference=current['visit']-previous['visit'];out={}
    for j,name in enumerate(('drug','core_order')):
        d=difference[:,j];out[name]={'improved':int((d>1e-12).sum()),'regressed':int((d< -1e-12).sum()),'unchanged':int((abs(d)<=1e-12).sum()),'admissions':len(d)}
    return out

def main():
    data=json.loads((PRIVATE/'cases.json').read_text());cases=data['guard'];protocol=json.loads((HERE/'protocol.json').read_text());records={};sources={}
    for seed in protocol['seeds']:
        path=HERE/f'results/audit-seed{seed}.json'
        if not path.exists():continue
        audit=json.loads(path.read_text())
        if audit['status']!='passed':continue
        assert audit['auditor_sha256']==sha(HERE/'audit_learning.py')
        assert audit['source_public_snapshot_sha256']==sha(HERE/f'results/seed{seed}.json')
        folder=PRIVATE/f'seed{seed}';values={};summary={}
        assert set(audit['guard'])=={'base'}|{f'{arm}-round{r}' for arm in protocol['arms'] for r in (1,2,3)}
        for name,view_results in audit['guard'].items():
            values[name]={};summary[name]=view_results;version=BASE if name=='base' else sha(folder/name/'adapter/adapters.safetensors')
            assert set(view_results)==set(VIEWS)
            for view in VIEWS:
                cs=[transform(c,view) for c in cases];rows=json.loads((folder/f'{name}-guard-{view}.json').read_text())
                a=arrays(verify_rows(rows,cs,version),cs);values[name][view]=a
                np.testing.assert_allclose(micro(a['counts'].sum(0)),[view_results[view]['drug_micro_f1'],view_results[view]['core_order_micro_f1']],atol=1e-12,rtol=0)
                np.testing.assert_allclose(a['patient'].mean(0),[view_results[view]['patient_drug_f1'],view_results[view]['patient_order_f1']],atol=1e-12,rtol=0)
        for k in (8,20):
            name=f'original_rank_top{k}';a=arrays([list(c['catalogue'].values())[:k] for c in cases],cases)
            values[name]={v:a for v in VIEWS};summary[name]={v:audit['direct_controls'][name] for v in VIEWS}
        selected={arm:('base' if z['round']==0 else f'{arm}-round{z["round"]}') for arm,z in audit['frozen_selection']['arms'].items()}
        accepted={arm:['base']+[('base' if z['active_round']==0 else f'{arm}-round{z["active_round"]}') for z in audit['arms'][arm]] for arm in protocol['arms']}
        records[seed]={'values':values,'summary':summary,'selected':selected,'accepted':accepted,'audit':audit}
        sources[str(seed)]={'audit_sha256':sha(path),'public_state_sha256':sha(HERE/f'results/seed{seed}.json')}
    out={'status':'complete' if len(records)==3 else 'partial','seeds':list(records),'split':'reused_guard','test_inference':False,'analysis_sha256':sha(Path(__file__)),'sources':sources,
         'interval_scope':'4,000 matched patient-cluster bootstrap draws, seed31031; average seed effects, then condition on observed seeds. No multiplicity adjustment; descriptive exploratory intervals. Different seeds also change experience order.',
         'fix_definition':'Higher admission-level drug/core-order set F1 than previous raw/accepted round; not a clinical safety judgement. Equal empty sets score1 in patient F1; micro F1 uses total counts.',
         'endpoints':{},'curves':{},'fix_regress':{},'position_invariance':{}}
    if records:
        reference=next(iter(records.values()))['values']['base']['ranked']['keys']
        assert all(z['values']['base']['ranked']['keys']==reference for z in records.values())
        out.update(guard_admissions=len(cases),guard_patients=len(reference))
        def name(z,method,endpoint,r=None):
            if method not in protocol['arms']:return method
            if endpoint=='selected':return z['selected'][method]
            if endpoint=='final':return f'{method}-round3'
            return z['accepted'][method][r] if endpoint=='accepted' else ('base' if r==0 else f'{method}-round{r}')
        metrics=('drug_micro_f1','core_order_micro_f1','patient_drug_f1','patient_order_f1','empty_fraction','mean_predicted_drugs','display_prefix_fraction','original_rank_prefix_fraction')
        def aggregate(method,endpoint,view,r=None):
            rows=[z['summary'][name(z,method,endpoint,r)][view] for z in records.values()]
            return {m:stats([row[m] for row in rows]) for m in metrics if all(row.get(m) is not None for row in rows)}
        comparisons=[('permuted_uniform','ranked_uniform'),('permuted_own_error','permuted_uniform'),('permuted_own_error','permuted_shuffled_error'),('permuted_own_error','original_rank_top8'),('permuted_own_error','base')]
        for endpoint in ('selected','final'):
            out['endpoints'][endpoint]={}
            for view in VIEWS:
                methods={m:aggregate(m,endpoint,view) for m in protocol['arms']+['base','original_rank_top8','original_rank_top20']}
                contrasts={}
                for a,b in comparisons:
                    contrasts[a+'_minus_'+b]=delta([z['values'][name(z,a,endpoint)][view] for z in records.values()],[z['values'][name(z,b,endpoint)][view] for z in records.values()])
                out['endpoints'][endpoint][view]={'methods':methods,'contrasts':contrasts}
        for arm in protocol['arms']:
            out['curves'][arm]={kind:{view:[aggregate(arm,kind,view,r) for r in range(4)] for view in VIEWS} for kind in ('raw','accepted')}
        for seed,z in records.items():
            out['fix_regress'][str(seed)]={arm:{kind:{view:[transitions(z['values'][name(z,arm,kind,r)][view],z['values'][name(z,arm,kind,r-1)][view]) for r in (1,2,3)] for view in VIEWS} for kind in ('raw','accepted')} for arm in protocol['arms']}
            out['position_invariance'][str(seed)]=z['audit']['view_comparisons']
    path=HERE/'results/guard_summary.json';tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(out,indent=2)+'\n');tmp.replace(path)
    print(json.dumps({'status':out['status'],'audited_seeds':out['seeds'],'test_inference':False}))

if __name__=='__main__':main()
