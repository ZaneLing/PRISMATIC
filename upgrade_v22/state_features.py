"""Numerical state features fitted only on the initial training contexts."""
from collections import Counter,defaultdict
import math
import numpy as np
from sklearn.feature_extraction import DictVectorizer
from sklearn.preprocessing import normalize

def finite(value):
    try:
        v=float(value)
        return v if math.isfinite(v) else None
    except (ValueError,TypeError):return None

class NumericState:
    def __init__(self,initial):
        names=Counter(o['drug_name'] for c in initial for o in c['context']['recorded_prior_orders'])
        labs=Counter((str(o['itemid']),str(o['unit'])) for c in initial for o in c['context']['available_labs'])
        self.names=set(n for n,_ in sorted(names.items(),key=lambda x:(-x[1],x[0]))[:512])
        self.labs=set(n for n,_ in sorted(labs.items(),key=lambda x:(-x[1],x[0]))[:64])
        values=defaultdict(list)
        for c in initial:
            _,nums=self.raw(c)
            for k,v in nums.items():values[k].append(v)
        self.scale={}
        for k,v in values.items():
            if len(v)<30:continue
            low,med,high=np.quantile(v,[.05,.5,.95]);self.scale[k]=(float(med),float(max(high-low,abs(med)*.1,1e-3)))
        self.vectorizer=DictVectorizer(sparse=True,dtype=np.float32)
        self.vectorizer.fit([self.features(c) for c in initial])

    def raw(self,c):
        v=c['context'];cats={'gender:'+str(v['gender']):1.,'age_decade:'+str(v['age_decade']):1.,
            'prior_count':len(v['recorded_prior_orders'])/24,'lab_count':len(v['available_labs'])/32}
        nums={};seen=set()
        for o in v['recorded_prior_orders']:
            n=o['drug_name']
            if n not in self.names:continue
            cats['prior:'+n]=1.;cats['route:'+n+':'+str(o['route'])]=1.
            if n in seen:continue
            seen.add(n)
            for field,unit in [('dose_value',o['dose_unit']),('frequency_per_24h','per24h')]:
                value=finite(o[field])
                if value is not None:nums['prior:'+n+':'+field+':'+str(unit)]=value
        for o in v['available_labs']:
            k=(str(o['itemid']),str(o['unit']))
            if k in self.labs:
                value=finite(o['value'])
                if value is not None:nums['lab:'+k[0]+':'+k[1]]=value
        return cats,nums

    def features(self,c):
        cats,nums=self.raw(c)
        for k,v in nums.items():
            if k in self.scale:
                median,spread=self.scale[k];cats['observed:'+k]=1.;cats['value:'+k]=float(np.clip((v-median)/spread,-3,3))
        return cats

    def transform(self,cases):return normalize(self.vectorizer.transform([self.features(c) for c in cases]),copy=False)
