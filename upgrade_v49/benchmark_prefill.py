"""Check engine throughput and exact intermediate-output parity on development inputs."""
import json,time
from common import *
from local_backend import Backend
from actor import run
import mlx_lm

def main():
    b=Backend();data=load_cases();cases=data['proposal'][:16]
    reference=json.loads((PRIVATE/'proposal-base.json').read_text())['rows'][:16]
    original=mlx_lm.batch_generate
    def tuned(*args,**kwargs):
        kwargs['prefill_batch_size']=8
        return original(*args,**kwargs)
    mlx_lm.batch_generate=tuned
    b.cache=PRIVATE/'prefill8-parity';b.cache.mkdir(exist_ok=True)
    start=time.monotonic();rows=run(b,cases,'rxrsi',{'cards':[]},'prefill8-parity')
    save(PRIVATE/'prefill8-parity-rows.json',rows)
    result={'cases':len(cases),'seconds':time.monotonic()-start,'prefill_batch_size':8,
      'exact_plan_matches':sum(x['plan']==y['plan'] for x,y in zip(rows,reference)),
      'exact_assessment_matches':sum(x['assessment']==y['assessment'] for x,y in zip(rows,reference)),
      'exact_final_matches':sum(x['raw']==y['raw'] for x,y in zip(rows,reference)),
      'same_orders':sum(x['orders']==y['orders'] for x,y in zip(rows,reference)),
      'model_sha256':b.model_hash,'api_cost_usd':0}
    save(HERE/'results/prefill_parity.json',result);print(json.dumps(result))
if __name__=='__main__':main()
