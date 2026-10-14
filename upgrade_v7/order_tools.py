"""Trainable order-completion tool: preserve a joint template, condition on context."""
from collections import Counter,defaultdict
import numpy as np
from sklearn.linear_model import SGDClassifier
from rx_agent import FIELDS,key,OrderMemory

class ConditionalOrderTool:
    def __init__(self,orders,x,seed=42):
        self.memory=OrderMemory(orders);self.models={};self.labels={};self.support={}
        groups=defaultdict(list)
        for i,row in enumerate(orders):
            for order in row:groups[order['drug_name']].append((i,key(order,FIELDS)))
        for name,records in groups.items():
            counts=Counter(k for _,k in records)
            labels=[k for k,n in counts.most_common(8) if n>=10]
            if len(records)<80 or len(labels)<2:continue
            index={k:j for j,k in enumerate(labels)}
            ix=[i for i,k in records if k in index];y=[index[k] for i,k in records if k in index]
            clf=SGDClassifier(loss='log_loss',alpha=1e-4,max_iter=40,tol=1e-3,random_state=seed)
            clf.fit(x[ix],y)
            self.models[name]=clf;self.labels[name]=labels;self.support[name]=len(ix)

    def compile(self,names,x,conditional=True):
        result=[self.memory.synthesize(row,conditional=False) for row in names]
        if not conditional:return result
        positions=defaultdict(list)
        for i,row in enumerate(names):
            for j,name in enumerate(row):
                if name in self.models:positions[name].append((i,j))
        for name,loc in positions.items():
            p=self.models[name].predict(x[[i for i,j in loc]])
            for (i,j),label in zip(loc,p):
                result[i][j].update(dict(zip(FIELDS,self.labels[name][int(label)])))
                result[i][j]['provenance']='context_conditioned_joint_order_tool'
        return result
