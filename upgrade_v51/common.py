"""All case-level material is local to the credentialed restricted directory."""
import hashlib,json,re,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v51'
SOURCE=PRIVATE.parent/'prismatic-v21'
RESOURCES=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/resources'
MODELS=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/models'
MODEL_PATHS={'qwen':MODELS/'qwen3-4b-instruct-2507-4bit','llama':MODELS/'llama-3.2-3b-instruct-4bit','flame':MODELS/'flame-list-grpo-4bit'}
sys.path.insert(0,str(ROOT/'upgrade_v7'))
from rx_agent import score,FIELDS,CORE,key
def save(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');t.replace(p)
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()
def parse(raw):
    raw=re.sub(r'<think>.*?</think>','',raw,flags=re.S).strip()
    for i,c in enumerate(raw):
        if c=='{':
            try:
                x,end=json.JSONDecoder().raw_decode(raw[i:])
                if isinstance(x,dict):return x
            except ValueError:pass
    return {}
def metrics(rows,cases):
    assert len(rows)==len(cases)
    out=score([r['orders'] for r in rows],[c['gold'] for c in cases])
    hits=pred=gold=0;complete=total=0;reachable=target=0
    for r,c in zip(rows,cases):
        assert r['case_id']==c['case_id']
        a={key(o,FIELDS) for o in r['orders'] if all(o.get(f) is not None for f in FIELDS)}
        b={key(o,FIELDS) for o in c['gold'] if all(o.get(f) is not None for f in FIELDS)}
        hits+=len(a&b);pred+=len(a);gold+=len(b)
        complete+=len(b);total+=len({key(o,FIELDS) for o in c['gold']})
        gt={o['drug_name'] for o in c['gold']};target+=len(gt)
        reachable+=len(gt & {o['drug_name'] for o in c['catalogue'].values()})
    out.update(core5_micro_f1=2*hits/max(1,pred+gold),core5_gt_field_coverage=complete/max(1,total),
      invalid_fraction=sum(r['invalid'] for r in rows)/max(1,len(rows)),catalogue_drug_recall_ceiling=reachable/max(1,target),
      output_tokens=sum(r.get('output_tokens',0) for r in rows),input_tokens=sum(r.get('input_tokens',0) for r in rows),
      logical_calls=sum(r.get('logical_calls',0) for r in rows),api_cost_usd=0)
    return out
def condition(c,name):
    parts=[s.strip() for s in re.split(r'\s+and\s+|\s*&\s*',name)]
    if len(parts)>1:return len(parts)<=2 and all(condition(c,p) for p in parts)
    v=c['context']
    return {'always':True,'labs_present':bool(v['available_labs']),'labs_missing':not v['available_labs'],
            'prior_orders_present':bool(v['recorded_prior_orders']),'prior_orders_missing':not v['recorded_prior_orders']} .get(name,False)
def load_cases():return json.loads((PRIVATE/'cases.json').read_text())

# Source tools are unchanged; local module paths take precedence.
sys.path.append(str(ROOT / "upgrade_v50"))
