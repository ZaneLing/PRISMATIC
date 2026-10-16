"""Freeze learning, gates and independent transfer before root-guided updates."""
import json,re,urllib.request,random
from datetime import datetime,timezone
import pyarrow.parquet as pq
from common37 import ROOT,HERE,RUN,LOCAL,MODEL,save,sha,digest,ledger_total

def norm(s):return ' '.join(re.findall('[a-z0-9]+',s.lower()))
def main():
 assert not (HERE/'protocol.json').exists(),'Do not overwrite an established protocol'
 url='https://huggingface.co/datasets/TIM0927/MedPIC-Bench/resolve/9ef6db4f13865b14fc2e6be3f94dcfaf3a0cf983/questions.json'
 with urllib.request.urlopen(url,timeout=30) as r:raw=r.read()
 (RUN/'medpic_source.json').write_bytes(raw);source=json.loads(raw);assert isinstance(source,list) and len(source)==467
 medpic=[]
 for row in source:
  opts=row['options'];letters=sorted(opts);answers=sorted(row['answer']);assert all(a in letters for a in answers)
  medpic.append({'id':row['instance_id'],'dialogue':row['patient_vignette']+'\n'+row['question'],'options':[opts[k] for k in letters],'gold':answers,'multiple':True,'family':row['benchmark_task_family'],'dimension':row['taxonomy_reasoning_operation'],'question_only':row['question']})
 d=json.loads((LOCAL/'data.json').read_text());m36=json.loads((LOCAL.parent/'rxrsi-v36/data.json').read_text());prior=json.loads((LOCAL.parent/'rxrsi-v34/independent_medqa.json').read_text());exclude={norm(c['dialogue']) for cs in [*d['parts'].values(),d['transfer'],*m36.values(),prior,medpic] for c in cs}
 medqa=[]
 for rr in pq.read_table(LOCAL.parent/'rxrsi-v36/medqa_train.parquet').to_pylist():
  row=rr['data'];q=row['Question'];n=norm(q)
  if n in exclude:continue
  exclude.add(n)
  if not re.search(r'\b(medicat\w*|drug\w*|dos(?:e|age|ing)|treat\w*|therap\w*|contraindicat\w*|adverse|prescri\w*|pharmaco\w*)\b',q,re.I):continue
  if re.search(r'\b(image|shown|figure|photograph)\b',q,re.I):continue
  opts=[row['Options'][k] for k in sorted(row['Options'])]
  medqa.append({'id':'medqa_train_'+digest(q),'dialogue':q,'options':opts,'gold':row['Correct Option'],'multiple':False,'family':'medqa_train'})
 medqa.sort(key=lambda c:digest(['rx37-train',c['id']]));trainmed=medqa[:200];rxtrain=sorted(d['parts']['train'],key=lambda c:digest(['rx37-train',c['id']]))[:200]
 #400 cases, each round50 RxSafe +50 MedQA; no option-identity statistics are learned.
 train=[]
 for k in range(4):
  batch=rxtrain[k*50:(k+1)*50]+trainmed[k*50:(k+1)*50];random.Random(370+k).shuffle(batch);train+=batch
 data={'train':train,'proposal_rx':d['parts']['proposal'],'guard_rx':d['parts']['guard'],'proposal_med':m36['proposal'],'guard_med':m36['guard'],'test_rx':d['parts']['test'],'test_qa':d['transfer'],'test_independent':medpic};save(RUN/'data.json',data)
 proto={'created_utc':datetime.now(timezone.utc).isoformat(),'model':MODEL,'ledger_start_usd':ledger_total(),'max_incremental_usd':35,'data_sha256':sha(RUN/'data.json'),'sizes':{k:len(v) for k,v in data.items()},'membership':{k:digest([c['id'] for c in v]) for k,v in data.items()},'training':'400 mixed cases,4 rounds of100.200 RxSafe from original train625 and200 MedQA train not in previous development or test. No calibration, drug-frequency or name-to-answer memory.','changes':'Automatically proposed scoped procedural cards and bounded retrieval configurations; actor weights and code fixed. Root ledger includes trace-based hypotheses, counterexamples, local intervention results and rejected gates.','gates':'First paired training probes:at least2 net corrections,no invalid increase. Then proposal RxSafe190 and MedQA120:neither loses correct answers and total strictly improves; then guard RxSafe197 and MedQA120:neither loses and total strictly improves. Failure retains incumbent. Four-round trajectory freezes before independent/main inference.','candidate_limit_per_round':2,'output_allowance':4608,'calls_per_case':3,'independent':{'source':url,'dataset':'TIM0927/MedPIC-Bench','revision':'9ef6db4f13865b14fc2e6be3f94dcfaf3a0cf983','license':'CC-BY-4.0','sha256':sha(RUN/'medpic_source.json'),'n':467,'primary':'Exact-set accuracy on all467; paired/counterfactual metrics if unambiguous grouping is recoverable. Multi-answer task is not coerced to single choice.','public_schema_example_exposure':['SS-HF-HFREF-001'],'selection_feedback':False,'rounds':'Evaluate0,1,2,3,4 only after learning frozen; no best-independent-test checkpoint selection.'},'shortcut_controls':['No learned identity priors or direct case-answer retrieval in procedural memory','Option permutation with answer remapping','Patient-context ablation on a fixed independent subset','Independent patient-condition-change task; separate guideline-following and counterfactual scores'],'history':'RxSafe/RxQA repeatedly observed; earlier MedQA proposal120 used, guard120 not previously inferred. MedPIC new task, one public schema example seen.','clinical_scope':'Choice agreement and mechanistic applicability tests, not validated clinical prescribing.','not_guaranteed':'Target to exceed strongest executed method; no mandated positive result.'};save(HERE/'protocol.json',proto)
 print(json.dumps({'sizes':proto['sizes'],'medqa_eligible':len(medqa),'independent_families':{f:sum(c['family']==f for c in medpic) for f in set(c['family'] for c in medpic)},'id_patterns':[c['id'] for c in medpic[-8:]],'ledger_start':proto['ledger_start_usd']}))
if __name__=='__main__':main()
