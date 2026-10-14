"""Fit a predeclared numeric-state pilot, selecting without any test data."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1');os.environ.setdefault('OMP_NUM_THREADS','1');os.environ.setdefault('VECLIB_MAXIMUM_THREADS','1')
import hashlib,json,sys,time
from pathlib import Path
import joblib,numpy as np
from scipy.sparse import hstack
from sklearn.preprocessing import normalize
from sklearn.linear_model import SGDClassifier
from sklearn.multiclass import OneVsRestClassifier
from state_features import NumericState
HERE=Path(__file__).resolve().parent;PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v22';SOURCE=PRIVATE.parent/'prismatic-v21'
sys.path.insert(0,str(HERE.parent/'upgrade_v7'))
from rx_agent import score,hash_data

def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')

def main():
    started=time.time();PRIVATE.mkdir(exist_ok=True);(HERE/'results').mkdir(exist_ok=True)
    protocol=json.loads((HERE/'protocol.json').read_text());lock=PRIVATE/'protocol_lock.json'
    if lock.exists():assert json.loads(lock.read_text())['sha256']==hash_data(protocol)
    else:save(lock,{'sha256':hash_data(protocol),'test_used':False})
    data=json.loads((SOURCE/'cases.json').read_text());data={s:data[s] for s in ['train','proposal','guard']}
    # Existing models hold precomputed test features but this runner neither
    # evaluates them nor loads the v21 test prediction/score reports.
    b=joblib.load(SOURCE/'data.joblib');classes=b['classes'];truth={s:b['truth'][s] for s in data};del b
    base=joblib.load(SOURCE/'run_seed_42.joblib');tool=base['tools'][40000];word={s:base['x'][s] for s in data};del base
    typed=NumericState(data['train'][:8000]);tx={s:typed.transform(v) for s,v in data.items()}
    matrices={'typed_state':tx,'word_plus_typed_state':{s:normalize(hstack([word[s],tx[s]],format='csr'),copy=False) for s in data}}
    ys=[{o['drug_name'] for o in row} for row in truth['train']];y=np.array([[c in names for c in classes] for names in ys],dtype=np.float32)
    candidates=[];best=None
    def compile_top(p,split,conditional=True):
        rank=np.argsort(-p,axis=1,kind='stable')[:,:20]
        orders=tool.compile([[classes[j] for j in row] for row in rank],word[split],conditional)
        return orders,np.take_along_axis(p,rank,axis=1)
    def select(rows,probs,t):return [[o for o,p in zip(row,pv) if p>=t] for row,pv in zip(rows,probs)]
    for view,mat in matrices.items():
        for alpha in [1e-6,1e-5,1e-4]:
            model=OneVsRestClassifier(SGDClassifier(loss='log_loss',alpha=alpha,max_iter=60,tol=.001,random_state=42),n_jobs=1)
            model.fit(mat['train'],y);p=model.predict_proba(mat['proposal']);rows,rankp=compile_top(p,'proposal')
            for threshold in protocol['thresholds']:
                metrics=score(select(rows,rankp,threshold),truth['proposal']);state={'view':view,'alpha':alpha,'threshold':threshold}
                candidates.append({'state':state,'proposal':metrics})
                if best is None or metrics['promotion_score']>best['proposal']['promotion_score']:best={'state':state,'proposal':metrics};best_model=model
            print(json.dumps({'view':view,'alpha':alpha,'best_proposal_composite':best['proposal']['promotion_score']}),flush=True)
    save(HERE/'results/frozen_candidate.json',{'candidate':best,'candidates':candidates,'test_used':False})
    state=best['state'];p=best_model.predict_proba(matrices[state['view']]['guard']);rows,rankp=compile_top(p,'guard');pred=select(rows,rankp,state['threshold'])
    gm=score(pred,truth['guard'])
    control=joblib.load(SOURCE/'strong_seed_42.joblib');families=control['families'];prob={}
    for view in ['word','char']:
        model,mats=control['models'][families[view][1]];prob[view]=model.predict_proba(mats['guard'])
    choice=families['word_char_ensemble'];weight=choice[1];rows,rankp=compile_top(weight*prob['word']+(1-weight)*prob['char'],'guard',choice[3]);cpred=select(rows,rankp,choice[2]);cm=score(cpred,truth['guard'])
    passed=gm['promotion_score']>cm['promotion_score'] and all(gm[k]>=cm[k]-.002 for k in ['drug_micro_f1','core_order_micro_f1'])
    joblib.dump({'model':best_model,'state':state,'numeric_features':typed,'predictions':pred,'control_predictions':cpred,'classes':classes},PRIVATE/'pilot.joblib')
    report={'status':'complete_development_only','test_used':False,'seed':42,'selected':best,'candidate_guard':gm,'strong_control_guard':cm,'passes_declared_guard_rule':passed,
      'learned_numeric_dimensions':len(typed.scale),'typed_feature_count':len(typed.vectorizer.feature_names_),
      'policy_sha256':hash_data([m.coef_.tolist() for m in best_model.estimators_]),'numeric_state_sha256':hash_data(typed.scale),
      'protocol_sha256':hash_data(protocol),'seconds':time.time()-started,'limits':'Development pilot, not a test win, not a recursive-update experiment; order tools fixed. No new clinical context or future data added.'}
    save(HERE/'results/development_results.json',report);print(json.dumps(report),flush=True)

if __name__=='__main__':main()
