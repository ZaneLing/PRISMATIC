"""Exact positional binary decisions; every listed candidate has one outcome."""
import json,re

def parse_mask(text,catalogue):
    try:
        d=json.loads(text);mask=d['include']
        if not isinstance(mask,list) or len(mask)!=len(catalogue):raise ValueError()
        if any(type(v) is not int or v not in (0,1) for v in mask):raise ValueError()
    except (ValueError,TypeError,KeyError):
        return {'orders':[],'status':'invalid_json','problems':[]}
    return {'orders':[o for o,v in zip(catalogue.values(),mask) if v], 'status':'valid','problems':[]}

def compile_model_selection(raw,catalogue):
    text=raw.strip();strict=parse_mask(text,catalogue)
    clean=re.sub(r'^<think>\s*</think>\s*','',text,count=1)
    return {**parse_mask(clean,catalogue),'raw_strict_status':strict['status'],'empty_reasoning_envelope_removed':clean!=text}

def bind_cached_output(row,case):
    return {**row,**compile_model_selection(row['raw'],case['catalogue']),'case_id':case['case_id']}
