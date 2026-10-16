"""Publish public-benchmark answer letters only, without case/source text."""
import sys,json,random
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(ROOT/'upgrade_v37'))
from common37 import RUN as BASE_RUN,digest,sha,save
HERE=ROOT/'upgrade_v44';RUN=BASE_RUN.parent/'rxrsi-v44'
def target(c):return sorted(c['gold']) if isinstance(c['gold'],list) else [c['gold']]
def main():
 data=json.loads((BASE_RUN/'data.json').read_text());states=json.loads((HERE/'results/learning.json').read_text())['rounds'];state=states[-1]['state'];assert all(s['state']==state for s in states),'Export must be expanded if retained states differ';out=[];counts={}
 def add(cs,split,ds,condition,maps=None):
  correct=0
  for c in cs:
   r=json.loads((RUN/'runs'/digest(state)/split/(digest(c['id'])+'.json')).read_text());g=target(c);correct+=r['prediction']==g;row={'dataset':ds,'condition':condition,'case_id':c['id'],'gold':g,'prediction':r['prediction'],'state_sha256':digest(state)}
   if c.get('group_id'):row['scenario_group_id']=c['group_id']
   if maps:row['new_index_to_original_index']=maps[c['id']]
   out.append(row)
  counts[ds+'/'+condition]={'n':len(cs),'correct':correct}
 for k,ds in [('test_rx','RxSafe988'),('test_qa','RxQA300'),('test_independent','MedPIC467')]:add(data[k],k,ds,'original')
 ip=json.loads((ROOT/'upgrade_v37/independent_protocol.json').read_text());by={c['id']:c for c in data['test_independent']};sub=[by[i] for i in ip['shortcut_ids']];perm=[];maps={}
 for c in sub:
  ix=list(range(len(c['options'])));random.Random(digest(['permutation',c['id']])).shuffle(ix)
  if ix==list(range(len(ix))):ix=ix[1:]+ix[:1]
  maps[c['id']]=ix;perm.append(dict(c,gold=sorted(chr(65+ix.index(ord(z)-65)) for z in target(c))))
 add(perm,'test_shortcut_permuted','MedPIC467','permuted',maps);add(sub,'test_shortcut_no_patient','MedPIC467','no_patient')
 p=HERE/'results/public_predictions.jsonl';p.write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in out));assert len(out)==sum(len(data[k]) for k in ['test_rx','test_qa','test_independent'])+2*len(sub)
 audit=json.loads((HERE/'results/audit.json').read_text());ind=json.loads((HERE/'results/independent.json').read_text())
 for key,split in [('RxSafe988/original','test_rx'),('RxQA300/original','test_qa')]:assert counts[key]['correct']==audit['methods'][split]['final']['correct']
 assert counts['MedPIC467/original']['correct']==ind['trajectory'][-1]['metrics']['correct']
 save(HERE/'results/public_prediction_manifest.json',{'status':'recounted','rows':len(out),'sha256':sha(p),'counts':counts,'source':'Public RxSafe/RxQA/MedPIC only; no restricted EHR data','fields':'IDs, answer letters, condition, state hash and permutation mapping only; no patient/source prose or provider receipts','initial_and_rounds':'All retained states are identical; these predictions serve rounds0-4 without claiming independent replication.','exporter_sha256':sha(__file__)})
 print(json.dumps(counts))
if __name__=='__main__':main()
