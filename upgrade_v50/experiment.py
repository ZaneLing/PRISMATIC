"""Shared cached execution and observable-rule validation; learning lives in learn.py."""
import json,re
from common import *
from actor import run
def execute(b,cases,method,state,tag):
    path=PRIVATE/(tag.replace('/','_')+'.json')
    sig=digest([b.model_hash,method,state,[c['case_id'] for c in cases],sha(HERE/'actor.py'),sha(HERE/'evidence.py')])
    if path.exists():
        d=json.loads(path.read_text())
        if d['signature']==sig:return d['rows']
    rows=run(b,cases,method,state,tag)
    save(path,{'signature':sig,'rows':rows});return rows
def validate_card(x):
    if not all(isinstance(x.get(k),str) and x[k] for k in ['root_cause','condition','instruction','counterexample']):return 'invalid_or_absent_scoped_rule'
    if x['condition'] not in ['always','labs_present','labs_missing','prior_orders_present','prior_orders_missing']:return 'unknown_observable_condition'
    executable=x['instruction']+' '+x['counterexample']
    if re.search(r'\b(?:gold(?:[- ]standard)?|ground[- ]?truth|gt|reference(?:[- ]standard)?|correct answer|target (?:drug|medication|prescription))\b',executable,re.I):return 'unobservable_reference_predicate'
    if len(x['instruction'].split())>120:return 'instruction_too_long'
    return None
