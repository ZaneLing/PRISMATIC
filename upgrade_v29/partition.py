"""Label-independent patient roles and disjoint, single-round witness batches."""
import hashlib
import numpy as np
def h(s):return int(hashlib.sha256(s.encode()).hexdigest(),16)
def partitions(people,seed):
    unique=sorted(set(map(str,people)),key=lambda p:h(f'v29|{seed}|role|{p}'))
    n=int(np.floor(.8*len(unique)));fit=unique[:n];witness=unique[n:]
    fit=sorted(fit,key=lambda p:h(f'v29|{seed}|fit-order|{p}'))
    witness=sorted(witness,key=lambda p:h(f'v29|{seed}|witness-order|{p}'))
    batches=[list(map(str,b)) for b in np.array_split(witness,5)]
    return {'fit_patients':fit,'witness_patients':witness,'witness_batches':batches,
      'folds':{p:h(f'v29|{seed}|fold|{p}')%3 for p in fit}}
