"""Non-generative recovery of a complete string array with missing delimiters.

Never extracts IDs from prose or invents a missing item. The original order
compiler still checks catalogue membership. This is an engineering replay,
not a learned prescription rule.
"""
import json,re
from actor import compile_raw

def recover(raw, case):
    original=compile_raw(raw,case)
    if not original['invalid']:return original,False
    match=re.fullmatch(r'\s*(?:```(?:json)?\s*)?\{\s*"order_ids"\s*:\s*\[(.*)',raw,re.S)
    if not match:return original,False
    body=re.sub(r'\s*```\s*$','',match.group(1)).strip()
    if body.endswith(']'):body=body[:-1].rstrip()
    if body.endswith(','):body=body[:-1].rstrip()
    try:items=json.loads('['+body+']')
    except ValueError:return original,False
    if not isinstance(items,list) or not all(isinstance(x,str) for x in items):return original,False
    return compile_raw(json.dumps({'order_ids':items}),case),True
