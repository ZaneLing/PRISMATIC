"""Declare compatible decoder, replay development and refit gates before audit metrics."""
import datetime
from common52 import *
from runtime_decoder import decode
from learn import learn
def replay(name,split):
 cs=json.loads((PRIVATE/(split+'.json')).read_text());old=json.loads((PRIVATE/(name+'-'+split+'.json')).read_text());rows=[]
 for c,r in zip(cs,old):
  assert c['case_id']==r['case_id'];rows.append({**r,**decode(r['receipt']['raw'],c)})
 save(PRIVATE/(name+'-compatible-'+split+'.json'),rows)
 return {'cases':len(rows),'nonempty_restored':sum(not a['orders'] and bool(b['orders']) for a,b in zip(old,rows)),'changed_rows':sum(a['orders']!=b['orders'] for a,b in zip(old,rows))}
if __name__=='__main__':
 assert not (HERE/'results/evaluation.json').exists(),'Pre-audit-metric development replay required'
 info={s:replay('qwen',s) for s in ['reflection','proposal','guard']}
 for seed in [52,152]:learn(seed,backbone='qwen-compatible')
 learn(52,shuffle=True,backbone='qwen-compatible')
 names=['qwen-compatible-52','qwen-compatible-152','qwen-compatible-52-shuffle']
 save(HERE/'results/decoder_freeze.json',{'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'development_replay':info,'decoder_sha256':sha(HERE/'runtime_decoder.py'),'states':{n:sha(PRIVATE/(n+'-states.json')) for n in names},'original_results_preserved':True,'original_audit_generation_already_started':True,'audit_metrics_observed':False,'reason':'Whole-output rejection of complete JSON containing some unknown identifiers discards other valid orders. Keep only verified IDs and log invalid IDs; accept a complete fenced wrapper; do not recover truncated structures.','classification':'researcher runtime repair; gates rerun under same decoder for all splits, not counted as RSI'})
