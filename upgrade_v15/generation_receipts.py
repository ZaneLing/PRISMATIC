"""Post-study repair: deduplicated generation plus immutable case-bound receipts."""
import hashlib,json
from pathlib import Path

def digest(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def atomic(path,obj):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(obj,indent=2)+'\n');tmp.replace(path)

def infer_with_receipts(cases,version,root,generate,bind,max_tokens=128):
    """generate sees distinct prompts only; bind maps the same raw text per case."""
    root=Path(root);raw_dir=root/'raw';receipts=root/'cases';raw_dir.mkdir(parents=True,exist_ok=True);receipts.mkdir(exist_ok=True)
    groups={};raws={}
    for c in cases:
        sig=digest([version,c['messages'],max_tokens]);groups.setdefault(sig,[]).append(c)
    pending=[]
    for sig,group in groups.items():
        p=raw_dir/(sig+'.json')
        if p.exists():
            row=json.loads(p.read_text());assert row['generation_signature']==sig and row['adapter_sha256']==version;raws[sig]=row
        else:pending.append((sig,group[0]))
    for lo in range(0,len(pending),32):
        chunk=pending[lo:lo+32];outputs=generate([c for _,c in chunk]);assert len(outputs)==len(chunk)
        for (sig,_),output in zip(chunk,outputs):
            assert isinstance(output['raw'],str)
            row={**output,'generation_signature':sig,'adapter_sha256':version};atomic(raw_dir/(sig+'.json'),row);raws[sig]=row
    out=[]
    for c in cases:
        sig=digest([version,c['messages'],max_tokens]);record=bind(raws[sig],c)
        assert record['case_id']==c['case_id']
        key=digest([sig,c['case_id'],list(c['catalogue'].items())]);path=receipts/(key+'.json')
        record.update(case_receipt_key=key)
        if path.exists():assert json.loads(path.read_text())==record,'Immutable case receipt mismatch'
        else:atomic(path,record)
        out.append({**record,'case_receipt_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    return out
