"""Freeze a new medication-management development cohort from public training data."""
import json,re,sys,urllib.request
from datetime import datetime,timezone
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parent.parent;HERE=ROOT/'upgrade_v36';sys.path.insert(0,str(ROOT/'upgrade_v35'))
from common import LOCAL,sha,digest,save,ledger_total
RUN=LOCAL.parent/'rxrsi-v36';RUN.mkdir(exist_ok=True)

def main():
 p=RUN/'medqa_train.parquet'
 url='https://huggingface.co/datasets/openlifescienceai/medqa/resolve/refs%2Fconvert%2Fparquet/default/train/0000.parquet'
 if not p.exists():
  with urllib.request.urlopen(url,timeout=60) as r:p.write_bytes(r.read())
 data=json.loads((LOCAL/'data.json').read_text());prior=[c for cs in list(data['parts'].values())+[data['transfer']] for c in cs]+json.loads((LOCAL.parent/'rxrsi-v34/independent_medqa.json').read_text())
 normalize=lambda s:' '.join(re.findall('[a-z0-9]+',s.lower()))
 excluded={normalize(c['dialogue']) for c in prior};candidates=[];seen=set();overlap=0
 for row in pd.read_parquet(p).to_dict('records'):
  d=row['data'];q=d['Question'];options=d['Options'];key=normalize(q)
  if key in excluded:overlap+=1;continue
  if key in seen:continue
  seen.add(key)
  # Select on INPUT only, emphasizing medication decisions with action-statement options.
  if not re.search(r'\b(medicat\w*|drug\w*|dos(?:e|age|ing)|treat\w*|therap\w*|contraindicat\w*|adverse|prescri\w*|pharmaco\w*)\b',q,re.I):continue
  vals=[options[k] for k in sorted(options)]
  if max(len(o.split()) for o in vals)<=6:continue
  candidates.append({'id':'medqa_train_'+digest(q),'dialogue':q,'options':vals,'gold':d['Correct Option'],'type':'medication_management_train'})
 ordered=sorted(candidates,key=lambda c:digest(['rx35-followup36',c['id']]))
 assert len(ordered)>=240
 parts={'proposal':ordered[:120],'guard':ordered[120:240]}
 save(RUN/'data.json',parts)
 protocol={'created_utc':datetime.now(timezone.utc).isoformat(),'purpose':'Independent training-source development for longer treatment/action questions; RxQA labels excluded from new selection.',
  'source':'https://huggingface.co/datasets/openlifescienceai/medqa','author_source':'https://github.com/jind11/MedQA','source_revision':'153e61cdd129eb79d3c27f82cdf3bc5e018c11b0','mirror_disclosure':'Public re-upload; not an author-hosted copy. Parquet hash binds exact downloaded content.',
  'parquet_sha256':sha(p),'source_train_rows':10178,'eligible':len(candidates),'excluded_exact_overlap':overlap,
  'selection':'Input medication/treatment keyword + an option longer than6 whitespace words; hash order; first120 proposal,next120 guard. No labels/difficulty/model outputs selected membership.',
  'membership':{k:digest([c['id'] for c in cs]) for k,cs in parts.items()},'new_dev_n':240,
  'candidates':['static_v35','full_section_context'],'tokens':'Same3 calls x1536 output cap; report input tokens separately. Conditional application to long action options only; short medication-name branch and frozen numeric calibrator unchanged.',
  'gate':'Strictly improve correct count on120 proposal then120 guard versus static workflow, no additional invalids; freeze before RxQA rerun. If fail, do not select by RxQA outcome.',
  'prior_test_exposure':'Aggregate v35 RxQA score199/300 is known; no per-item RxQA errors/answers inspected to design/select this intervention. Repeated main benchmark remains exploratory.',
  'ledger_start_usd':ledger_total(),'max_incremental_usd':10,'model':'deepseek/deepseek-v4.1-flash'}
 save(HERE/'protocol.json',protocol);print(json.dumps({k:protocol[k] for k in ['eligible','excluded_exact_overlap','new_dev_n','ledger_start_usd']}))
 # Stop the prior experiment's billing window before subsequent calls.
 save(ROOT/'upgrade_v35/results/billing_close.json',{'closed_utc':datetime.now(timezone.utc).isoformat(),'ledger_total_usd':ledger_total()})
if __name__=='__main__':main()
