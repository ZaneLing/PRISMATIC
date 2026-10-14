"""Validation-selected rankers and frozen-base train-only residual memory growth.

All patient text, membership, fitted models and predictions stay under restricted/.
Public outputs contain aggregate scores, hashes, configurations and run timings.
"""
import hashlib, json, sys, time
from pathlib import Path
from collections import Counter
import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.multiclass import OneVsRestClassifier

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/'upgrade_v3'))
from run_atc4_methods import take, text_features, score, paired_f1_delta_ci
from core import digest, ExperienceLedger
ROOT = Path.home()/'Desktop/MedTreeBench/dataset/restricted'
PRIVATE = ROOT/'prismatic-v5'

def top(scores):
    return np.argsort(-scores, axis=1, kind='stable')[:, :5]

def fit(x, y, alpha):
    model = OneVsRestClassifier(SGDClassifier(loss='log_loss', alpha=alpha,
                    max_iter=50, tol=1e-3, random_state=42), n_jobs=1)
    model.fit(x, y)
    return model

def residual_query(query, memory, residuals, neighbors=30):
    result = np.zeros((query.shape[0], residuals.shape[1]), dtype=np.float32)
    for lo in range(0, len(result), 64):
        sim = (query[lo:lo+64] @ memory.T).toarray()
        k = min(neighbors, memory.shape[0])
        idx = np.argpartition(-sim, k-1, axis=1)[:, :k]
        w = np.take_along_axis(sim, idx, axis=1)
        for i in range(len(sim)):
            result[lo+i] = (w[i, :, None] * residuals[idx[i]]).sum(0) / max(1e-8, w[i].sum())
    return result

def run():
    start = time.time(); PRIVATE.mkdir(exist_ok=True); (HERE/'results').mkdir(exist_ok=True)
    config = json.loads((HERE/'protocol.json').read_text())
    frame = pd.read_parquet(ROOT/'prismatic-v4/cohort.parquet')
    parts = {s: take(frame, s, n) for s,n in [('train',40000),('val',4000),('test',4000)]}
    patients = {s:set(p.subject_id) for s,p in parts.items()}
    assert not (patients['train'] & patients['val'] or patients['train'] & patients['test'] or patients['val'] & patients['test'])
    gold = {s:[set(row) for row in p.atc4_codes] for s,p in parts.items()}
    classes = [c for c,n in Counter(c for row in gold['train'] for c in row).most_common(80)]
    y = np.array([[c in row for c in classes] for row in gold['train']], dtype=np.float32)
    texts = {s:text_features(p) for s,p in parts.items()}
    metric = lambda s,p: score(gold[s], top(p), classes)['micro_f1_at_5']
    models = {}; validation = {}; vectors = {}; matrices = {}; selected = {}
    for view in ['word', 'char']:
        vec = (TfidfVectorizer(min_df=3, max_features=12000, ngram_range=(1,2),
                   token_pattern=r'(?u)\b\w+\b', sublinear_tf=True) if view=='word' else
               TfidfVectorizer(min_df=3, max_features=24000, analyzer='char_wb', ngram_range=(3,5), sublinear_tf=True))
        x = {'train':vec.fit_transform(texts['train'])}
        x['val'] = vec.transform(texts['val'])
        vectors[view] = vec; matrices[view] = x
        best = None
        for alpha in config['ranker_alphas']:
            key = f'{view}-{alpha}'
            model = fit(x['train'], y, alpha); p = model.predict_proba(x['val'])
            validation[key] = metric('val',p)
            models[key] = model
            if best is None or validation[key] > validation[best]: best=key
            np.save(PRIVATE/f'val-{key}.npy', p)
            print(json.dumps({'ranker':key,'validation_f1':validation[key]}),flush=True)
        selected[view] = best
    wp = np.load(PRIVATE/f"val-{selected['word']}.npy")
    cp = np.load(PRIVATE/f"val-{selected['char']}.npy")
    choices = [(validation[selected['word']],1.0),(validation[selected['char']],0.0)]
    for w in config['word_char_weights']:
        validation[f'ensemble-word-{w}'] = metric('val',w*wp+(1-w)*cp)
        choices.append((validation[f'ensemble-word-{w}'],w))
    _, weight = max(choices, key=lambda z:z[0])
    # Freeze all main ranker choices before computing any new test score.
    frozen = {'protocol_sha256':hashlib.sha256((HERE/'protocol.json').read_bytes()).hexdigest(),
              'selected':selected,'word_weight':weight,'validation_grid':validation,
              'membership_sha256':{s:digest(sorted(p.hadm_id.astype(str))) for s,p in parts.items()}}
    (HERE/'results/ranker_selection.json').write_text(json.dumps(frozen,indent=2)+'\n')
    # Frozen-base learning: keep whole patients in base vs experience portions of train.
    ordered_subjects = sorted(patients['train'],key=lambda x:digest(str(x)))
    counts=parts['train'].subject_id.value_counts(); base_ids=set(); n=0
    for sid in ordered_subjects:
        if n>=8000: break
        base_ids.add(sid);n+=int(counts[sid])
    base=np.flatnonzero(parts['train'].subject_id.isin(base_ids).to_numpy())
    memory=np.flatnonzero(~parts['train'].subject_id.isin(base_ids).to_numpy())
    bvec=TfidfVectorizer(min_df=3,max_features=12000,ngram_range=(1,2),token_pattern=r'(?u)\b\w+\b',sublinear_tf=True)
    bx=bvec.fit_transform([texts['train'][i] for i in base]); bm=fit(bx,y[base],1e-5)
    mx=bvec.transform([texts['train'][i] for i in memory]); residual=y[memory]-bm.predict_proba(mx)
    vx=bvec.transform(texts['val']); base_val=bm.predict_proba(vx)
    ledger=ExperienceLedger(); baseline_val=metric('val',base_val)
    ledger.checkpoint(baseline_val,{'beta':0.0,'memory_size':0})
    stages=[]; old=0
    for requested in config['memory_checkpoints']:
        size=min(requested,len(memory))
        for i in range(old,size):
            j=memory[i]
            ledger.append({'case_key':digest(str(parts['train'].iloc[j].hadm_id)), 'split':'train',
                           'observed_label_sha256':digest(sorted(gold['train'][j])),
                           'feedback_kind':'historical_record_not_clinician_rating'})
        old=size
        correction=residual_query(vx,mx[:size],residual[:size])
        grid={str(b):metric('val',base_val+b*correction) for b in config['memory_beta']}
        beta=max(config['memory_beta'],key=lambda b:grid[str(b)])
        v=ledger.checkpoint(grid[str(beta)],{'beta':beta,'memory_size':size,'validation_beta_grid':grid})
        stages.append(v)
        print(json.dumps({'memory_cases':size,'beta':beta,'validation_f1':grid[str(beta)],'promoted':v['promoted']}),flush=True)
    (HERE/'results/memory_selection.json').write_text(json.dumps({'base_admissions':len(base),
          'base_patients':len(base_ids),'memory_admissions':len(memory),'versions':ledger.versions,
          'active_version':ledger.active,'scope':config['growth_scope']},indent=2)+'\n')
    # Test evaluation starts after both selection files have been written.
    test_scores={}; val_scores={}
    for view,key in selected.items():
        test_scores[view]=models[key].predict_proba(vectors[view].transform(texts['test']))
        val_scores[view]=np.load(PRIVATE/f'val-{key}.npy')
    anchor=weight*test_scores['word']+(1-weight)*test_scores['char']
    anchor_val=weight*wp+(1-weight)*cp
    tx=bvec.transform(texts['test']); base_test=bm.predict_proba(tx)
    growth=[{'memory_size':0,'beta':0.0,'validation_f1':baseline_val,'test':score(gold['test'],top(base_test),classes)}]
    active_test=base_test; active_val=base_val
    for v in stages:
        size=v['memory_size']; beta=v['beta']
        p=base_test+beta*residual_query(tx,mx[:size],residual[:size])
        if v['promoted']: active_test=p
        growth.append({**v,'test':score(gold['test'],top(p),classes),
                       'promoted_policy_test':score(gold['test'],top(active_test),classes)})
    predictions={'selected_word':top(test_scores['word']),'selected_char':top(test_scores['char']),
                 'validation_selected_anchor':top(anchor),'frozen_base_8k':top(base_test),
                 'promoted_residual_memory':top(active_test)}
    baseline=dict(np.load(ROOT/'prismatic-v4/baseline_predictions.npz'))
    metrics={name:score(gold['test'],p,classes) for name,p in predictions.items()}
    np.savez_compressed(PRIVATE/'ranker_predictions.npz',**predictions)
    np.save(PRIVATE/'anchor_test_scores.npy',anchor);np.save(PRIVATE/'anchor_val_scores.npy',anchor_val)
    joblib.dump({'models':{v:models[k] for v,k in selected.items()},'vectors':vectors,'word_weight':weight,
                 'classes':classes},PRIVATE/'selected_anchor.joblib')
    joblib.dump({'base_vectorizer':bvec,'base_model':bm,'memory_vectors':mx,'memory_residuals':residual,
                 'ledger':ledger,'memory_indices':memory,'base_indices':base},PRIVATE/'experience_memory.joblib')
    report={'run_id':'E01-v5-rankers-memory-r1','selection':frozen,'classes':classes,'metrics':metrics,
            'growth':growth,'paired_anchor_minus_v4_sgd':paired_f1_delta_ci(parts['test'],gold['test'],baseline['direct_sgd'],top(anchor),classes),
            'paired_memory_minus_frozen_base':paired_f1_delta_ci(parts['test'],gold['test'],top(base_test),top(active_test),classes),
            'elapsed_seconds':round(time.time()-start,2),'limits':[config['confirmation'],config['growth_scope'],
            'Residual memory updates no LLM weights; labels are observed behavior, not verified indication.',
            'No saline/infusion indication outcome is established by the ATC experiment.']}
    (HERE/'results/ranker_memory_results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'final_metrics':metrics,'elapsed':report['elapsed_seconds']}),flush=True)
    # Same training retrieval for LLM validation; test uses immutable v4 inputs.
    samples=take(frame,'val',50); loc={str(h):i for i,h in enumerate(parts['val'].hadm_id)}
    inputs=[json.loads(s) for s in (ROOT/'prismatic-v4/llm_inputs.jsonl').read_text().splitlines()]
    candidate_names=inputs[0]['candidates']
    sims=(vectors['word'].transform(text_features(samples)) @ matrices['word']['train'].T).toarray()
    nearest=np.argsort(-sims,axis=1,kind='stable')[:,:3]
    val_cases=[]; val_labels=[]
    for i,row in samples.iterrows():
        val_cases.append({'case_id':str(i),'chiefcomplaint':str(row.chiefcomplaint or ''),
           'acuity':str(row.acuity or ''),'home_meds':str(row.home_meds or ''),
           'availability':inputs[0]['availability'],'candidates':candidate_names,
           'retrieved_cases':[{'chiefcomplaint':str(parts['train'].iloc[j].chiefcomplaint or ''),
             'acuity':str(parts['train'].iloc[j].acuity or ''),'home_meds':str(parts['train'].iloc[j].home_meds or ''),
             'historical_codes':sorted(gold['train'][j]),'similarity':float(sims[i,j])} for j in nearest[i]]})
        val_labels.append({'case_id':str(i),'subject_id':str(row.subject_id),'hadm_id':str(row.hadm_id),'codes':list(row.atc4_codes)})
    for name,rows in [('val_inputs',val_cases),('val_labels',val_labels)]:
        (PRIVATE/f'{name}.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
    for split, rows, p in [('val',val_labels,anchor_val),('test',[json.loads(s) for s in (ROOT/'prismatic-v4/llm_labels.jsonl').read_text().splitlines()],anchor)]:
        loc={str(h):i for i,h in enumerate(parts[split].hadm_id)}
        out={r['case_id']:[{'atc4':classes[j],'score':float(p[loc[r['hadm_id']],j])} for j in top(p[[loc[r['hadm_id']]]])[0]] for r in rows}
        (PRIVATE/f'{split}_anchor.json').write_text(json.dumps(out))

if __name__=='__main__':run()
