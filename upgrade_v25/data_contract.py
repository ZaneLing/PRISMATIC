"""Native eICU order identities and explicit missing attributes."""
import hashlib,json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v25'
FIELDS=('drug_code','route','dosage','frequency')

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def norm(value):
    if value is None:return None
    value=re.sub(r'\s+',' ',str(value).strip().lower())
    return value or None
def order(row):return {'drug_code':'hicl:'+str(int(row['hicl'])),'route':norm(row['routeadmin']),'dosage':norm(row['dosage']),'frequency':norm(row['frequency'])}
def key(value):return tuple(value.get(k) for k in FIELDS)
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()
def save(path,value):
    path=Path(path);temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(value,indent=2)+'\n');temp.replace(path)
