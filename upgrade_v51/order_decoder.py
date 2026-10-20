"""Strict compatibility decoding; accepts complete arrays, never completes IDs.

The original study uses actor.compile_raw. Apply this adapter explicitly to a
saved or fresh final response; it does not change the learned state or invoke an
LLM. Only a complete JSON array of catalogue-valid string identifiers qualifies.
"""
import json
from actor import compile_raw

def decode(raw,case):
 result=compile_raw(raw,case)
 if not result['invalid']:return {**result,'decoder_repair':False}
 try:obj=json.loads(raw.strip())
 except (ValueError,TypeError):return {**result,'decoder_repair':False}
 if not isinstance(obj,list) or not all(isinstance(x,str) and x in case['catalogue'] for x in obj):
  return {**result,'decoder_repair':False}
 ids=list(dict.fromkeys(obj))
 return {'orders':[case['catalogue'][x] for x in ids],'order_ids':ids,'invalid':False,'invalid_ids':0,'decoder_repair':True}

def repair_rows(rows):
 return [{**r,**decode(r['raw'],{'catalogue':r['catalogue']})} for r in rows]

def run_with_compatible_output(backend,cases,method='rxrsi',state=None,tag=''):
 """Runtime adapter for fresh inference; identical calls and output allowance."""
 from actor import run
 return repair_rows(run(backend,cases,method,state,tag))
