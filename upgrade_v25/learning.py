"""Typed native-code state, explicit order tuples and matched policy updates."""
import math,re,time
from collections import Counter,defaultdict
import numpy as np,joblib
from scipy.special import expit
from sklearn.feature_extraction import DictVectorizer
from sklearn.preprocessing import normalize
from sklearn.linear_model import SGDClassifier
from sklearn.neighbors import NearestNeighbors
from data_contract import FIELDS,key,digest

def dump(value,path):
    temporary=path.with_suffix(path.suffix+'.tmp');joblib.dump(value,temporary);temporary.replace(path)

def counts(pred,gold):
    a={o['drug_code'] for o in pred};b={o['drug_code'] for o in gold}
    p={key(o) for o in pred if all(o.get(f) is not None for f in FIELDS)}
    g={key(o) for o in gold if all(o.get(f) is not None for f in FIELDS)}
    return [len(a&b),len(a),len(b),len(p&g),len(p),len(g)]

def score(pred,gold):
    assert len(pred)==len(gold)
    a=np.asarray([counts(p,g) for p,g in zip(pred,gold)]);n=a.sum(0);d=2*n[0]/max(1,n[1]+n[2]);o=2*n[3]/max(1,n[4]+n[5])
    return {'cases':len(gold),'drug_micro_f1':float(d),'core_order_micro_f1':float(o),'promotion_score':float((d+o)/2),
      'drug_precision':float(n[0]/max(1,n[1])),'drug_recall':float(n[0]/max(1,n[2])),
      'empty_fraction':float(np.mean([not p for p in pred])),'mean_predicted_drugs':float(n[1]/max(1,len(gold))),
      'complete_predicted_orders':int(n[4]),'complete_gold_orders':int(n[5]),
      'predicted_order_completion':float(n[4]/max(1,sum(len(p) for p in pred))),
      'empty_decision_agreement':float(np.mean([(not p)==(not g) for p,g in zip(pred,gold)]))}

def text(c):
    x=c['context'];lines=['gender '+str(x['gender']),'age decade '+str(x['age_decade'])]
    for o in x['prior_orders']:lines.append('prior '+' '.join(str(o.get(f) or 'unknown') for f in ['drug_code','drug_name','route','dosage','frequency']))
    for o in x['available_labs']:lines.append('lab '+o['name']+' '+str(o['value'])+' '+o['unit'])
    return '\n'.join(lines)

class NumericState:
    def __init__(self,initial):
        codes=Counter(o['drug_code'] for c in initial for o in c['context']['prior_orders'] if o['drug_code'])
        labs=Counter((o['name'],o['unit']) for c in initial for o in c['context']['available_labs'])
        self.codes=set(k for k,_ in sorted(codes.items(),key=lambda x:(-x[1],x[0]))[:512]);self.labs=set(k for k,_ in sorted(labs.items(),key=lambda x:(-x[1],x[0]))[:64])
        values=defaultdict(list)
        for c in initial:
            for k,v in self.raw(c)[1].items():values[k].append(v)
        self.scales={}
        for k,v in values.items():
            if len(v)>=30:
                lo,med,hi=np.quantile(v,[.05,.5,.95]);self.scales[k]=(float(med),float(max(hi-lo,abs(med)*.1,1e-3)))
        self.vectorizer=DictVectorizer(dtype=np.float32);self.vectorizer.fit([self.features(c) for c in initial])
    def raw(self,c):
        x=c['context'];cats={'gender:'+str(x['gender']):1.,'age:'+str(x['age_decade']):1.,'prior_count':len(x['prior_orders'])/24,'lab_count':len(x['available_labs'])/32};nums={};seen=set()
        for o in x['prior_orders']:
            code=o['drug_code']
            if code not in self.codes:continue
            cats['prior:'+code]=1.;cats['route:'+code+':'+str(o['route'])]=1.;cats['frequency:'+code+':'+str(o['frequency'])]=1.
            if code in seen:continue
            seen.add(code);match=re.fullmatch(r'\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*([^\d]*)',o['dosage'] or '')
            if match:
                value=float(match.group(1))
                if math.isfinite(value):nums['dose:'+code+':'+match.group(2).strip()]=value
        for o in x['available_labs']:
            if (o['name'],o['unit']) in self.labs:nums['lab:'+o['name']+':'+o['unit']]=o['value']
        return cats,nums
    def features(self,c):
        cats,nums=self.raw(c)
        for k,v in nums.items():
            if k in self.scales:
                med,spread=self.scales[k];cats['observed:'+k]=1.;cats['value:'+k]=float(np.clip((v-med)/spread,-3,3))
        return cats
    def transform(self,cases):return normalize(self.vectorizer.transform([self.features(c) for c in cases]),copy=False)

class Policy:
    def __init__(self,x,y,weights,seed):
        start=time.perf_counter();coef=[];bias=[];self.iterations=[]
        for j in range(y.shape[1]):
            assert set(np.unique(y[:,j]))=={0,1}
            m=SGDClassifier(loss='log_loss',alpha=1e-5,max_iter=60,tol=None,random_state=seed)
            m.fit(x,y[:,j],sample_weight=weights);assert m.n_iter_==60
            coef.append(m.coef_[0]);bias.append(m.intercept_[0]);self.iterations.append(int(m.n_iter_))
        self.coef_=np.asarray(coef);self.intercept_=np.asarray(bias)
        assert np.isfinite(self.coef_).all() and np.isfinite(self.intercept_).all()
        self.sha256=digest([self.coef_.tolist(),self.intercept_.tolist()]);self.training_seconds=time.perf_counter()-start
    def predict_proba(self,x):return expit(x@self.coef_.T+self.intercept_)

class OrderTool:
    def __init__(self,truth,x,seed):
        self.membership_sha256=digest(truth);self.defaults={};self.models={};self.labels={};groups=defaultdict(list)
        for i,orders in enumerate(truth):
            for o in orders:groups[o['drug_code']].append((i,key(o)))
        for code,records in groups.items():
            freq=Counter(k for _,k in records);self.defaults[code]=dict(zip(FIELDS,freq.most_common(1)[0][0]))
            labels=[k for k,n in freq.most_common(8) if n>=10]
            if len(records)<80 or len(labels)<2:continue
            indexes={k:j for j,k in enumerate(labels)};selected=[(i,indexes[k]) for i,k in records if k in indexes]
            m=SGDClassifier(loss='log_loss',alpha=1e-4,max_iter=40,tol=1e-3,random_state=seed)
            m.fit(x[[i for i,_ in selected]],[j for _,j in selected]);self.models[code]=m;self.labels[code]=labels
    def compile(self,names,x,conditional=True):
        out=[[self.defaults[n].copy() for n in row] for row in names]
        if conditional:
            locations=defaultdict(list)
            for i,row in enumerate(names):
                for j,n in enumerate(row):
                    if n in self.models:locations[n].append((i,j))
            for n,loc in locations.items():
                labels=self.models[n].predict(x[[i for i,j in loc]])
                for (i,j),label in zip(loc,labels):out[i][j]=dict(zip(FIELDS,self.labels[n][int(label)]))
        return out

def ranked_rows(p,tool,x,classes,conditional=True):
    ix=np.argsort(-p,axis=1,kind='stable')[:,:20]
    return tool.compile([[classes[j] for j in row] for row in ix],x,conditional),np.take_along_axis(p,ix,axis=1)
def choose(rows,probs,threshold):return [[o for o,p in zip(row,values) if p>=threshold] for row,values in zip(rows,probs)]
def feedback_weights(p,y,threshold):
    ranked=np.argsort(-p,axis=1,kind='stable')[:,:20];weights=[]
    for row,target,ix in zip(p,y,ranked):
        pred={int(j) for j in ix if row[j]>=threshold};gold=set(np.flatnonzero(target));den=len(pred)+len(gold)
        quality=2*len(pred&gold)/den if den else 1.;weights.append(1+3*(1-quality))
    return np.asarray(weights)
def retrieval_probs(train,y,queries):
    search=NearestNeighbors(n_neighbors=30,metric='cosine',algorithm='brute',n_jobs=1).fit(train);out=[]
    for start in range(0,queries.shape[0],128):
        distances,ix=search.kneighbors(queries[start:start+128]);w=np.maximum(0,1-distances);w[w.sum(1)==0]=1
        out.append((y[ix]*w[:,:,None]).sum(1)/w.sum(1)[:,None])
    return np.concatenate(out)
