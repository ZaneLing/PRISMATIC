"""Whole-memory checks and label-independent, patient-level witness roles."""
import hashlib
import numpy as np
from upgrade_v29.programs import apply,agreement,digest

def split_witness(people,seed,round_number):
    order=sorted(set(people),key=lambda p:hashlib.sha256(f'v30|{seed}|{round_number}|witness-split|{p}'.encode()).hexdigest())
    edit=set(order[:len(order)//2]);confirm=set(order[len(order)//2:])
    assert edit.isdisjoint(confirm) and edit|confirm==set(people)
    return np.flatnonzero(np.isin(people,list(edit))),np.flatnonzero(np.isin(people,list(confirm)))

def check(memory,x,prob,thresholds,y,people):
    empty=apply([],x,prob,thresholds);pred=apply(memory,x,prob,thresholds)
    before=agreement(empty,y,people);after=agreement(pred,y,people)
    affected=len(set(people[np.any(empty!=pred,axis=1)]))
    passed=affected>=3 and after['patient_f1']-before['patient_f1']>1e-12 and after['patient_jaccard']-before['patient_jaccard']>=-1e-12
    return {'memory_sha256':digest(memory),'empty':before,'memory':after,'affected_patients':affected,'passed':bool(passed)}

def rebase(previous,fit_check,edit_check,enabled):
    supported=fit_check['passed'] and edit_check['passed']
    return list(previous) if not enabled or supported else []

def promote(candidate,confirmation,enabled):
    return list(candidate) if not enabled or confirmation['passed'] else []
