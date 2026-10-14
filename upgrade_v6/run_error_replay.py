"""Use the actual pre-update GT error ledger to prioritize supervised replay.

Development revision r2 retains r1 results. Same 40k cases and frozen features;
validation chooses error weighting, order-memory mode and output threshold.
"""
import copy,json,time
import numpy as np
import joblib
from run_evolution import HERE,PRIVATE,neighbors,synthesize,selected
from rx_agent import score,hash_data

def run():
    start=time.time();bundle=joblib.load(PRIVATE/'evaluation_bundle.joblib')
    base=joblib.load(PRIVATE/'agent_40000.joblib');truth=bundle['truth'];parts=bundle['parts']
    config={'revision':'v6-r2-error-replay','weights':[0,.25,1.0],'order_modes':['global','similar_case'],
            'thresholds':[.1,.15,.2,.25,.3,.4,.5],
            'objective':'equal drug/core-order F1','split':'training feedback only; validation selects; developmental test',
            'r1_retained':True}
    (HERE/'results/error_replay_protocol.json').write_text(json.dumps(config,indent=2)+'\n')
    errors={r['case_key']:r for r in map(json.loads,(PRIVATE/'training_error_ledger.jsonl').read_text().splitlines())}
    difficulty=[]
    for h in parts['train'].hadm_id:
        r=errors.get(hash_data(str(h)))
        difficulty.append(0 if r is None else min(2.,(len(r['missed_drugs'])+len(r['extra_drugs'])+len(r['field_errors']))/max(1,len(r['reference_orders']))))
    difficulty=np.array(difficulty);classes=base['classes']
    y=np.array([[c in {o['drug_name'] for o in row} for c in classes] for row in truth['train']],dtype=np.float32)
    x={s:base['vectorizer'].transform(bundle['text'][s]) for s in parts}
    ni,wi=neighbors(x['val'],x['train']);best=-1;winner=None;winner_model=None;grid=[]
    for strength in config['weights']:
        model=copy.deepcopy(base['model'])
        if strength:
            weights=1+strength*difficulty
            for j,estimator in enumerate(model.estimators_):estimator.fit(x['train'],y[:,j],sample_weight=weights)
        p=model.predict_proba(x['val'])
        for mode in config['order_modes']:
            candidates=synthesize(p,classes,base['memory'],ni,wi,conditional=mode=='similar_case')
            for threshold in config['thresholds']:
                val=score(selected(candidates,threshold),truth['val'])
                row={'error_weight':strength,'order_mode':mode,'threshold':threshold,'validation':val}
                grid.append(row)
                if val['promotion_score']>best:
                    best=val['promotion_score'];winner=row;winner_model=copy.deepcopy(model)
        print(json.dumps({'replay_strength':strength,'best_validation_so_far':best}),flush=True)
    selection={'winner':winner,'grid':grid,'feedback_cases':len(errors),
               'training_error_ledger_sha256':__import__('hashlib').sha256((PRIVATE/'training_error_ledger.jsonl').read_bytes()).hexdigest()}
    (HERE/'results/error_replay_selection.json').write_text(json.dumps(selection,indent=2)+'\n')
    nt,wt=neighbors(x['test'],x['train']);p=winner_model.predict_proba(x['test'])
    candidates=synthesize(p,classes,base['memory'],nt,wt,conditional=winner['order_mode']=='similar_case')
    pred=selected(candidates,winner['threshold']);test=score(pred,truth['test'])
    agent={**base,'model':winner_model,'threshold':winner['threshold'],'order_mode':winner['order_mode'],'r2_selection':winner}
    joblib.dump(agent,PRIVATE/'rxrsi_active.joblib');joblib.dump(pred,PRIVATE/'r2_test_predictions.joblib')
    report={'run_id':'RxRSI-v6-error-replay-r2','winner':winner,'test':test,'feedback_cases':len(errors),
            'elapsed_seconds':time.time()-start,'limits':['r2 development revision after inspecting r1 failures; not confirmation.',
            'Error-weighted supervised replay changes the prescription policy, not the frozen LLM weights.',
            'All candidate grids and the zero-weight control are retained; best test score is never selected.']}
    (HERE/'results/error_replay_results.json').write_text(json.dumps(report,indent=2)+'\n')
    # Regenerate the pilot from the now-frozen active policy, not from held-out labels.
    for s in ['val','test']:
        path=PRIVATE/f'{s}_inputs.jsonl';rows=[json.loads(r) for r in path.read_text().splitlines()]
        nn,ww=neighbors(x[s][:20],x['train']);p=winner_model.predict_proba(x[s][:20])
        candidates=synthesize(p,classes,base['memory'],nn,ww,conditional=winner['order_mode']=='similar_case')
        for row,orders in zip(rows,candidates):
            row['candidate_orders']={f'O{j+1}':o for j,o in enumerate(orders[:12])}
            row['policy_selected_ids']=[k for k,o in row['candidate_orders'].items() if o['selection_score']>=winner['threshold']]
        path.write_text(''.join(json.dumps(r)+'\n' for r in rows))
    print(json.dumps(report),flush=True)

if __name__=='__main__':run()
