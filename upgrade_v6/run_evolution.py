"""Execute automatic ground-truth order evaluation and real policy/memory updates."""
import json,sys,time
from pathlib import Path
from collections import Counter
import duckdb,joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.multiclass import OneVsRestClassifier
from rx_agent import record_order,key,FIELDS,OrderMemory,score,error_feedback,hash_data

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'upgrade_v3'))
from run_atc4_methods import take,text_features
ROOT=Path.home()/'Desktop/MedTreeBench/dataset/restricted'
PRIVATE=ROOT/'prismatic-v6'

def neighbors(xq,xt):
    idx=[];weights=[]
    for lo in range(0,xq.shape[0],64):
        sim=(xq[lo:lo+64]@xt.T).toarray();ix=np.argpartition(-sim,29,axis=1)[:,:30]
        idx.extend(ix);weights.extend(np.take_along_axis(sim,ix,axis=1))
    return np.array(idx),np.array(weights)

def synthesize(probabilities,classes,memory,nn,ww,conditional=True):
    result=[];ranks=np.argsort(-probabilities,axis=1,kind='stable')[:,:20]
    for i,rank in enumerate(ranks):
        names=[classes[j] for j in rank]
        orders=memory.synthesize(names,nn[i],ww[i],conditional)
        for order,j in zip(orders,rank):order['selection_score']=float(probabilities[i,j])
        result.append(orders)
    return result

def selected(orders,threshold):return [[o for o in row if o['selection_score']>=threshold] for row in orders]

def run():
    start=time.time();PRIVATE.mkdir(exist_ok=True);(HERE/'results').mkdir(exist_ok=True)
    config=json.loads((HERE/'protocol.json').read_text())
    frame=pd.read_parquet(ROOT/'prismatic-v4/cohort.parquet')
    parts={s:take(frame,s,n) for s,n in [('train',40000),('val',4000),('test',4000)]}
    patient={s:set(p.subject_id) for s,p in parts.items()}
    assert not (patient['train']&patient['val'] or patient['train']&patient['test'] or patient['val']&patient['test'])
    con=duckdb.connect();members=pd.concat([p[['hadm_id']] for p in parts.values()]);con.register('members',members)
    rows=con.execute('select hadm_id,drug_key,route,dose_val_rx,dose_unit_rx,doses_per_24_hrs from read_parquet(?) join members using(hadm_id)',
         [str(ROOT/'prismatic-v4/mapped_orders.parquet')]).fetchdf();con.close()
    by_hadm={}
    for row in rows.to_dict('records'):
        order=record_order(row)
        if order['drug_name'] is None:continue
        by_hadm.setdefault(str(row['hadm_id']),{})[key(order,FIELDS)]=order
    truth={s:[list(by_hadm.get(str(h),{}).values()) for h in p.hadm_id] for s,p in parts.items()}
    base_counts=Counter(n for episode in truth['train'][:8000] for n in {o['drug_name'] for o in episode})
    classes=[n for n,c in base_counts.most_common(128)]
    ys=[{o['drug_name'] for o in row} for row in truth['train']]
    y=np.array([[c in row for c in classes] for row in ys],dtype=np.float32)
    texts={s:text_features(p) for s,p in parts.items()}
    vec=TfidfVectorizer(min_df=3,max_features=16000,ngram_range=(1,2),token_pattern=r'(?u)\b\w+\b',sublinear_tf=True)
    vec.fit(texts['train'][:8000]);x={s:vec.transform(t) for s,t in texts.items()}
    versions=[];best=-1;active=None;previous_model=None;previous_memory=None;previous_threshold=.2;previous_n=0
    feedback_path=PRIVATE/'training_error_ledger.jsonl';feedback_path.write_text('')
    test_cache={};val_cache={};model_cache={}
    for n in config['training_checkpoints']:
        # Before observing the new block, use the previous policy to expose errors.
        errors=Counter()
        if previous_model is not None:
            p=previous_model.predict_proba(x['train'][previous_n:n]);ranks=np.argsort(-p,axis=1)[:,:20]
            with feedback_path.open('a') as f:
                for offset,rank in enumerate(ranks):
                    names=[classes[j] for j in rank if p[offset,j]>=previous_threshold]
                    draft=previous_memory.synthesize(names,conditional=False)
                    feedback=error_feedback(draft,truth['train'][previous_n+offset],'train')
                    for field in ['missed_drugs','extra_drugs','field_errors']:errors[field]+=len(feedback[field])
                    f.write(json.dumps({'case_key':hash_data(str(parts['train'].iloc[previous_n+offset].hadm_id)),
                       'policy_training_cases':previous_n,'split':'train',**feedback})+'\n')
        model=OneVsRestClassifier(SGDClassifier(loss='log_loss',alpha=1e-5,max_iter=60,tol=1e-3,random_state=42),n_jobs=1)
        model.fit(x['train'][:n],y[:n]);memory=OrderMemory(truth['train'][:n])
        nv,wv=neighbors(x['val'],x['train'][:n]);pv=model.predict_proba(x['val'])
        candidates=synthesize(pv,classes,memory,nv,wv)
        grid={str(t):score(selected(candidates,t),truth['val']) for t in config['thresholds']}
        threshold=max(config['thresholds'],key=lambda t:grid[str(t)]['promotion_score'])
        val=grid[str(threshold)];promoted=val['promotion_score']>best
        if promoted:best=val['promotion_score'];active=n
        version={'training_cases':n,'threshold':threshold,'validation':val,'promoted':promoted,
                 'active_training_cases':active,'new_block_errors_before_update':dict(errors),
                 'training_member_sha256':hash_data(list(parts['train'].hadm_id.astype(str)[:n])),
                 'threshold_grid':{k:v['promotion_score'] for k,v in grid.items()}}
        versions.append(version);val_cache[n]=selected(candidates,threshold)
        # Store test predictions without scoring them until validation selections are frozen.
        nt,wt=neighbors(x['test'],x['train'][:n]);pt=model.predict_proba(x['test'])
        tc=synthesize(pt,classes,memory,nt,wt);test_cache[n]=selected(tc,threshold)
        joblib.dump({'model':model,'memory':memory,'classes':classes,'vectorizer':vec,
                     'threshold':threshold,'train_vectors':x['train'][:n],'version':version},PRIVATE/f'agent_{n}.joblib')
        if n==40000:
            global_orders=synthesize(pt,classes,memory,nt,wt,conditional=False)
            global_val=synthesize(pv,classes,memory,nv,wv,conditional=False)
            global_grid={str(t):score(selected(global_val,t),truth['val'])['promotion_score'] for t in config['thresholds']}
            global_t=max(config['thresholds'],key=lambda t:global_grid[str(t)])
            global_test=selected(global_orders,global_t)
        previous_model=model;previous_memory=memory;previous_n=n;previous_threshold=threshold
        print(json.dumps({'training_cases':n,'validation':val,'promoted':promoted}),flush=True)
    selection={'protocol_sha256':hash_data(config),'versions':versions,'active_training_cases':active,
               'global_template_ablation':{'threshold':global_t,'validation_grid':global_grid}}
    (HERE/'results/frozen_selection.json').write_text(json.dumps(selection,indent=2)+'\n')
    growth=[{**{k:v for k,v in ver.items() if k!='threshold_grid'},'test':score(test_cache[ver['training_cases']],truth['test'])} for ver in versions]
    # kNN baseline uses the identical name vocabulary, prefix, full-field memory and threshold search.
    train_indicator=y;retrieval_scores={}
    for s in ['val','test']:
        ni,wi=neighbors(x[s],x['train']);p=np.zeros((len(parts[s]),len(classes)))
        for i in range(len(p)):p[i]=(wi[i,:,None]*train_indicator[ni[i]]).sum(0)/max(1e-9,wi[i].sum())
        retrieval_scores[s]=synthesize(p,classes,previous_memory,ni,wi)
    rg={str(t):score(selected(retrieval_scores['val'],t),truth['val'])['promotion_score'] for t in config['thresholds']}
    rt=max(config['thresholds'],key=lambda t:rg[str(t)])
    metrics={'retrieval_40k':score(selected(retrieval_scores['test'],rt),truth['test']),
       'static_8k':score(test_cache[8000],truth['test']),
       'full_data_global_templates':score(global_test,truth['test']),
       'rxrsi_promoted':score(test_cache[active],truth['test'])}
    coverage={s:sum(o['drug_name'] in classes for row in truth[s] for o in row)/max(1,sum(map(len,truth[s]))) for s in parts}
    report={'run_id':'RxRSI-v6-order-evolution-r1','samples':{s:len(p) for s,p in parts.items()},
      'vocabulary_size':len(classes),'vocabulary_order_coverage':coverage,'growth':growth,'metrics':metrics,
      'active_training_cases':active,'no_human_review_required':True,'elapsed_seconds':time.time()-start,
      'limits':['Developmental test, not confirmatory.','Raw-name order space differs from ATC benchmarks.',
        'Core order = name, route, dose string and dose unit; missing GT fields are excluded and coverage reported.',
        'Saline presence is observed occurrence, not fluid purpose or appropriateness.',
        'This run updates a supervised policy and case/template memory; it does not fine-tune LLM weights.']}
    (HERE/'results/order_evolution_results.json').write_text(json.dumps(report,indent=2)+'\n')
    joblib.dump({'predictions':test_cache,'truth':truth,'parts':parts,'classes':classes,
      'active_training_cases':active,'text':texts},PRIVATE/'evaluation_bundle.joblib')
    # Compile inputs for an actual local LLM planning pilot without access to test GT.
    for s in ['val','test']:
        rows=[];labels=[];agent=joblib.load(PRIVATE/f'agent_{active}.joblib')
        nn,ww=neighbors(x[s][:20],agent['train_vectors']);prob=agent['model'].predict_proba(x[s][:20])
        candidates=synthesize(prob,classes,agent['memory'],nn,ww)
        for i in range(20):
            catalogue={f'O{j+1}':o for j,o in enumerate(candidates[i][:12])}
            evidence={'chief_complaint':str(parts[s].iloc[i].chiefcomplaint or ''),
                      'acuity':str(parts[s].iloc[i].acuity or ''),'home_medications':str(parts[s].iloc[i].home_meds or '')}
            rows.append({'case_id':str(i),'patient':evidence,'candidate_orders':catalogue,
                  'policy_selected_ids':[k for k,o in catalogue.items() if o['selection_score']>=agent['threshold']],
                  'episode_memory':[{'case_summary':texts['train'][int(j)],'recorded_orders':truth['train'][int(j)]} for j in nn[i,:2]]})
            labels.append({'case_id':str(i),'orders':truth[s][i]})
        (PRIVATE/f'{s}_inputs.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
        (PRIVATE/f'{s}_labels.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in labels))
    print(json.dumps({'metrics':metrics,'active_training_cases':active,'elapsed_seconds':time.time()-start}),flush=True)

if __name__=='__main__':run()
