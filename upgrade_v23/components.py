"""Exact-epoch weighted drug policies and common structured-order scoring."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
import joblib
from scipy.special import expit
from sklearn.linear_model import SGDClassifier
HERE=Path(__file__).resolve().parent;PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v23'
sys.path[:0]=[str(HERE.parent/'upgrade_v7'),str(HERE.parent/'upgrade_v22')]
from rx_agent import score,hash_data

def save(path,value):
    temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(value,indent=2)+'\n');temp.replace(path)

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def dump(value,path):
    temp=path.with_suffix(path.suffix+'.tmp');joblib.dump(value,temp);temp.replace(path)

class WeightedPolicy:
    def __init__(self,x,y,weights,seed,epochs=60):
        assert np.isfinite(weights).all() and (weights>0).all()
        coef=[];intercepts=[];self.iterations=[]
        for j in range(y.shape[1]):
            assert set(np.unique(y[:,j]))=={0,1}
            model=SGDClassifier(loss='log_loss',alpha=1e-5,max_iter=epochs,tol=None,random_state=seed)
            model.fit(x,y[:,j],sample_weight=weights)
            assert model.n_iter_==epochs
            coef.append(model.coef_[0]);intercepts.append(model.intercept_[0]);self.iterations.append(int(model.n_iter_))
        self.coef_=np.asarray(coef);self.intercept_=np.asarray(intercepts)
        assert np.isfinite(self.coef_).all() and np.isfinite(self.intercept_).all()
        self.sha256=hash_data([self.coef_.tolist(),self.intercept_.tolist()])

    def predict_proba(self,x):return expit(x@self.coef_.T+self.intercept_)

def drug_mask(p,threshold):
    rank=np.argsort(-p,axis=1,kind='stable')[:,:20];out=np.zeros(p.shape,dtype=bool)
    for i,row in enumerate(rank):out[i,row]=p[i,row]>=threshold
    return out

def feedback_weights(p,gold,threshold):
    chosen=drug_mask(p,threshold);truth=gold.astype(bool);hits=(chosen&truth).sum(1);denom=chosen.sum(1)+truth.sum(1)
    quality=np.divide(2*hits,denom,out=np.ones(len(gold),dtype=float),where=denom>0)
    return 1+3*(1-quality)

def compile_ranked(policy,tool,x,word,classes):
    p=policy.predict_proba(x);rank=np.argsort(-p,axis=1,kind='stable')[:,:20]
    rows=tool.compile([[classes[j] for j in row] for row in rank],word,True)
    return rows,np.take_along_axis(p,rank,axis=1)

def choose(rows,ranked,threshold):return [[o for o,p in zip(row,ps) if p>=threshold] for row,ps in zip(rows,ranked)]
