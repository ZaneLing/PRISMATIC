"""Real same-case baselines and time-input sensitivity; private case outputs."""
from __future__ import annotations
import json,sys,time,hashlib
from pathlib import Path
from collections import Counter
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.multiclass import OneVsRestClassifier

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'upgrade_v3'))
from run_atc4_methods import take,score,retrieve_vote,paired_f1_delta_ci,text_features
from build_atc4_cohort import ROOT
from build_protocol_data import sha

def run():
    started=time.time(); private=ROOT/'prismatic-v4'
    config=json.loads((HERE/'protocol.json').read_text())
    frame=pd.read_parquet(private/'cohort.parquet')
    parts={s:take(frame,s,n) for s,n in [('train',40000),('val',4000),('test',4000)]}
    sets={s:set(p.subject_id) for s,p in parts.items()}
    assert not (sets['train']&sets['val'] or sets['train']&sets['test'] or sets['val']&sets['test'])
    gold={s:[set(x) for x in p.atc4_codes] for s,p in parts.items()}
    classes=[c for c,n in Counter(c for row in gold['train'] for c in row).most_common(80)]
    yi={c:i for i,c in enumerate(classes)}
    y=np.array([[c in row for c in classes] for row in gold['train']],dtype=np.float32)
    results={}; predictions={}; sample_counts={}
    test=parts['test']; mapped=np.array([bool(x) for x in gold['test']])
    masks={'all_admissions':np.ones(len(test),dtype=bool),'at_least_one_mapped_label':mapped}
    def metrics(pred):
        return {name:score([g for g,k in zip(gold['test'],mask) if k],pred[mask],classes) for name,mask in masks.items()}
    for view in ['admission_proxy','home_meds_only','no_patient_text']:
        texts={s:(text_features(p) if view=='admission_proxy' else
                  ('home medicines '+p.home_meds.fillna('').astype(str).str.lower()).tolist()
                  if view=='home_meds_only' else ['no patient text']*len(p)) for s,p in parts.items()}
        vec=TfidfVectorizer(min_df=3,max_features=12000,ngram_range=(1,2),token_pattern=r'(?u)\b\w+\b',sublinear_tf=True)
        x={};x['train']=vec.fit_transform(texts['train'])
        for s in ['val','test']:x[s]=vec.transform(texts[s])
        pop=np.tile(np.arange(5),(len(test),1))
        retrieval=retrieve_vote(x['test'],x['train'],y,30,5)
        results[view]={'prevalence':metrics(pop),'case_retrieval':metrics(retrieval),'direct_sgd':{}}
        for seed in config['classical_seeds']:
            model=OneVsRestClassifier(SGDClassifier(loss='log_loss',alpha=1e-5,max_iter=50,tol=1e-3,random_state=seed),n_jobs=1)
            model.fit(x['train'],y)
            pred=np.argsort(-model.predict_proba(x['test']),axis=1,kind='stable')[:,:5]
            results[view]['direct_sgd'][str(seed)]=metrics(pred)
            if view=='admission_proxy' and seed==42:
                predictions['direct_sgd']=pred
        if view=='admission_proxy':
            predictions.update(prevalence=pop,case_retrieval=retrieval)
            # Prepare fixed, nested 50-case input file; raw test labels are kept in a separate file.
            pilot=take(frame,'test',50)
            xp=vec.transform(text_features(pilot))
            sims=(xp@x['train'].T).toarray()
            nearest=np.argsort(-sims,axis=1,kind='stable')[:,:3]
            import duckdb
            con=duckdb.connect();con.register('train_ids',parts['train'][['hadm_id']])
            names=con.execute('''WITH n AS (SELECT atc4,drug,COUNT(*) AS n FROM read_parquet(?)
              JOIN train_ids USING(hadm_id) WHERE atc4 IS NOT NULL GROUP BY 1,2)
              SELECT atc4,drug FROM n QUALIFY ROW_NUMBER() OVER(PARTITION BY atc4 ORDER BY n DESC,drug)=1''',
              [str(private/'mapped_orders.parquet')]).fetchall();con.close()
            names=dict(names); inputs=[]; labels=[]
            for i,row in pilot.iterrows():
                inputs.append({'case_id':str(i),'chiefcomplaint':str(row.chiefcomplaint or ''),
                    'acuity':str(row.acuity or ''),'home_meds':str(row.home_meds or ''),
                    'availability':'triage assumed; home medication charttime bounded, storetime unavailable',
                    'candidates':[{'atc4':c,'example_name':names.get(c,'unknown')} for c in classes],
                    'retrieved_cases':[{'chiefcomplaint':str(parts['train'].iloc[j].chiefcomplaint or ''),
                        'acuity':str(parts['train'].iloc[j].acuity or ''),
                        'home_meds':str(parts['train'].iloc[j].home_meds or ''),
                        'historical_codes':sorted(gold['train'][j]),'similarity':float(sims[i,j])} for j in nearest[i]]})
                labels.append({'case_id':str(i),'subject_id':str(row.subject_id),'hadm_id':str(row.hadm_id),
                    'codes':list(row.atc4_codes),'raw_orders':int(row.raw_orders),'mapped_orders':int(row.mapped_orders)})
            for name,rows in [('llm_inputs',inputs),('llm_labels',labels)]:
                (private/(name+'.jsonl')).write_text(''.join(json.dumps(r)+'\n' for r in rows))
            # Subset baseline predictions aligned by admission, not by row order.
            loc={str(h):i for i,h in enumerate(test.hadm_id)}
            indices=[loc[str(h)] for h in pilot.hadm_id]
            pilot_base={k:score([set(l['codes']) for l in labels],v[indices],classes) for k,v in predictions.items()}
        print(json.dumps({'completed_input_view':view}),flush=True)
    np.savez_compressed(private/'baseline_predictions.npz',**predictions)
    report={'run_id':'E01-v4-baselines-r1','protocol_sha256':sha(HERE/'protocol.json'),
      'cohort_sha256':sha(private/'cohort.parquet'),'sample_sizes':{k:len(v) for k,v in parts.items()},
      'sample_patients':{k:len(v) for k,v in sets.items()},'classes':classes,
      'split_member_sha256':{k:hashlib.sha256('\n'.join(sorted(p.hadm_id.astype(str))).encode()).hexdigest() for k,p in parts.items()},
      'test_label_status':{'no_recorded_order':int(test.raw_orders.eq(0).sum()),
         'orders_but_unmapped':int((test.raw_orders.gt(0)&test.mapped_orders.eq(0)).sum()),
         'at_least_one_mapped':int(mapped.sum())},
      'metrics':results,'same_50_case_baselines':pilot_base,
      'paired_direct_seed42_minus_retrieval':paired_f1_delta_ci(test,gold['test'],predictions['case_retrieval'],predictions['direct_sgd'],classes),
      'elapsed_seconds':round(time.time()-started,2),
      'limits':['Developmental test, not unseen confirmation.','Observed-label overlap is coverage biased, not clinical appropriateness.',
                'No patient text is an information-ablation control, not a clinical decision system.']}
    (HERE/'results/protocol_method_results.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

if __name__=='__main__':print(json.dumps(run(),indent=2))
