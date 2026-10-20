"""Training-only candidate expansion and explicit reachability audit; no remote data."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
import json,sys,collections,hashlib
from pathlib import Path
import joblib,numpy as np
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'upgrade_v51'
sys.path[:0]=[str(ROOT/'upgrade_v7'),str(ROOT/'upgrade_v21')]
from rx_agent import FIELDS
from run_comparison import text_view
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v51'
SOURCE=PRIVATE.parent/'prismatic-v21'
def save(p,d):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def main():
 data=json.loads((SOURCE/'cases.json').read_text());b=joblib.load(SOURCE/'data.joblib');r=joblib.load(SOURCE/'run_seed_42.joblib');vocab=set(b['classes']);tool=r['tools'][40000]
 old=json.loads((PRIVATE.parent/'prismatic-v50/cases.json').read_text());total=collections.Counter()
 for c in old['test']:
  g={o['drug_name'] for o in c['gold']};cat={o['drug_name'] for o in c['catalogue'].values()}
  total.update(gold=len(g),covered=len(g&cat),outside_vocabulary=len(g-vocab),inside_vocabulary_pruned=len((g&vocab)-cat))
 audit={'test_instances':dict(total),'vocabulary_recall':(total['gold']-total['outside_vocabulary'])/total['gold'],'top24_recall':total['covered']/total['gold'],
 'vocabulary_size':len(vocab),'vocabulary_source':'128 most frequent normalized raw names in initial 8000 training admissions','ranking_source':'OneVsRestClassifier fit on 40000 training admissions; highest 24 scores per case',
 'normalization':'lowercase/trimmed raw drug strings, NOT RxNorm ingredient identity; brand/formulation fragmentation remains','selection_uses_test_labels':False}
 save(HERE/'results/candidate_origin.json',audit);print(json.dumps(audit),flush=True)
 # Fixed positional selection before current inference; patient-disjoint by source design.
 # Both evaluation pools have been exposed to historical supervised research: exploratory only.
 specs={'train':('train',list(range(288,360))),'proposal':('proposal',list(range(96,120))),'guard':('guard',list(range(128,160))),'audit':('test',list(range(48)))}
 output={};trainpatients=np.array([c['subject_hash'] for c in data['train']]);xt=r['x']['train'];vnames=b['classes']
 for split,(src,ix) in specs.items():
  xx=r['x'][src][ix];pp=r['models'][40000].predict_proba(xx) if src=='train' else r['probs'][40000][src][ix]
  variants={k:[] for k in ['base24','wide48','retrieval48']};extras=[]
  for j,i in enumerate(ix):
   c=data[src][i];ranked=[vnames[k] for k in np.argsort(-pp[j])];sim=(xx[j]@xt.T).toarray().ravel();sim[trainpatients==c['subject_hash']]=-1
   near=np.argsort(-sim)[:16];votes=collections.Counter();support=collections.Counter()
   for n in near:
    if sim[n]<=0:continue
    for drug in {o['drug_name'] for o in data['train'][int(n)]['gold']}:votes[drug]+=float(sim[n]);support[drug]+=1
   retrieved=[n for n,_ in sorted(votes.items(),key=lambda kv:(-kv[1],kv[0])) if n in tool.memory.defaults]
   variants['base24'].append(sorted(ranked[:24]));variants['wide48'].append(sorted(ranked[:48]));hybrid=list(ranked[:24])
   for n in retrieved:
    if n not in hybrid:hybrid.append(n)
    if len(hybrid)==48:break
   variants['retrieval48'].append(sorted(hybrid));extras.append({'neighbor_drug_votes':dict(votes),'neighbor_drug_support':dict(support),'classifier_rank':ranked,'same_patient_neighbors_excluded':True})
  compiled={k:tool.compile(names,xx,conditional=True) for k,names in variants.items()};output[split]=[]
  for j,i in enumerate(ix):
   c=data[src][i];cats={k:{f'A{n+1}':{f:o.get(f) for f in FIELDS} for n,o in enumerate(rows[j])} for k,rows in compiled.items()}
   output[split].append({**c,'input':text_view(c),'catalogue':cats['base24'],'catalogues':cats,'retrieval_meta':extras[j]})
  print('prepared',split,len(output[split]),flush=True)
 groups={s:{c['subject_hash'] for c in rows} for s,rows in output.items()};assert all(not groups[a]&groups[z] for a in groups for z in groups if a<z)
 save(PRIVATE/'cases.json',output)
 reach={}
 for s,cs in output.items():
  den=sum(len({o['drug_name'] for o in c['gold']}) for c in cs)
  reach[s]={k:sum(len({o['drug_name'] for o in c['gold']}&{o['drug_name'] for o in c['catalogues'][k].values()}) for c in cs)/den for k in variants}
 save(HERE/'results/preparation.json',{'case_counts':{s:len(v) for s,v in output.items()},'selection':specs,'patient_disjoint':True,'candidate_recall':reach,'data_sha256':hashlib.sha256((PRIVATE/'cases.json').read_bytes()).hexdigest(),'test_status':'48-case historically exposed exploratory audit; no audit feedback to updater','supervised_prior':'All candidate variants and templates derive from same fixed 40000-admission training resource; train-case same-patient retrieval excluded, but these cases were in classifier training','diagnoses_available_at_runtime':False})
if __name__=='__main__':main()
