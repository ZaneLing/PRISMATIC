"""Post hoc engineering replay on every frozen state and all LLM controls."""
import json
from common import *
from learn import evaluated
from order_decoder import repair_rows
from audit_results import paired

def main():
 cs=load_cases()['audit'];out={}
 targets={'qwen_initial':('cloud','audit-round-0'),'qwen_retained':('cloud','audit-final'),
 'qwen_static_bundle':('cloud','audit-static-repairs'),'qwen_static_draft':('cloud','audit-static-ranked-draft'),
 'llama_initial':('cloud','llama-audit-initial'),'llama_transferred':('cloud','llama-audit-selected')}
 for name,(folder,tag) in targets.items():
  rows=json.loads((PRIVATE/folder/(tag+'.json')).read_text())['rows'];repaired=repair_rows(rows)
  out[name]={'original':evaluated(rows,cs),'replayed':evaluated(repaired,cs),'recovered_outputs':sum(r['decoder_repair'] for r in repaired),'paired':paired(cs,rows,repaired)}
  save(PRIVATE/'decoder-replay'/f'{name}.json',{'rows':repaired,'source_sha256':sha(PRIVATE/folder/(tag+'.json'))})
 trajectories={}
 for name,folder,public in [('local','',HERE/'results/trajectory.json'),('aggregate','cloud',HERE/'results/cloud/trajectory.json')]:
  curve=json.loads(public.read_text());learning=json.loads((PRIVATE/folder/'learning.json').read_text());seen={};rr=[]
  for r in learning['rounds']:
   h=digest(r['state'])
   if h not in seen:
    rows=json.loads((PRIVATE/folder/f'audit-round-{r["round"]}.json').read_text())['rows'];seen[h]=repair_rows(rows)
   rr.append({'round':r['round'],'cases_seen':r['cases_seen'],'retained':r['retained'],'metrics':evaluated(seen[h],cs)})
  trajectories[name]=rr
 result={'complete':True,'post_hoc':True,'changes_learned_state':False,'gates_replayed':False,'additional_llm_calls':0,'test_selects_state':False,'methods':out,'trajectories':trajectories,'limitations':'Complete JSON-array wrapper repair only. No completion of truncated identifiers, no new drug selection, no RSI attribution; original learning gates and original scores remain the primary frozen experiment.'}
 save(HERE/'results/decoder_replay.json',result)
 print(json.dumps({n:{'recovered':v['recovered_outputs'],'drug_f1':v['replayed']['drug_micro_f1'],'core4_f1':v['replayed']['core_order_micro_f1']} for n,v in out.items()},indent=2))
if __name__=='__main__':main()
