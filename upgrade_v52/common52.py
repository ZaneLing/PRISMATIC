import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v52'
SOURCE=PRIVATE.parent/'prismatic-v25'
FIELDS=('drug_code','route','dosage','frequency')
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def save(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');t.replace(p)
def key(o):return tuple(o.get(f) for f in FIELDS)
def uniq(orders):return list({key(o):o for o in orders}.values())
def counts(pred,gold):
 a={o['drug_code'] for o in pred};b={o['drug_code'] for o in gold}
 p={key(o) for o in pred if all(o.get(f) is not None for f in FIELDS)};g={key(o) for o in gold if all(o.get(f) is not None for f in FIELDS)}
 return [len(b-a),len(a-b),len(p^g),len(a&b),len(a),len(b),len(p&g),len(p),len(g)]
def metrics(pred,cases):
 n=[sum(x) for x in zip(*(counts(p,c['gold']) for p,c in zip(pred,cases)))];N=len(cases)
 return dict(cases=N,missed_drugs_per_patient=n[0]/max(1,N),extra_drugs_per_patient=n[1]/max(1,N),joint_errors_per_patient=n[2]/max(1,N),drug_f1=2*n[3]/max(1,n[4]+n[5]),joint_f1=2*n[6]/max(1,n[7]+n[8]),recall=n[3]/max(1,n[5]),precision=n[3]/max(1,n[4]),counts=n,empty_fraction=sum(not p for p in pred)/max(1,N),target_complete_field_coverage=n[8]/max(1,sum(len(c['gold']) for c in cases)))
