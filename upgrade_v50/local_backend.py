"""Local MLX only, deterministic cached batched generation with receipts."""
import os,time,json
os.environ.setdefault('TOKENIZERS_PARALLELISM','false')
from common import *
class Backend:
    def __init__(self,name='qwen'):
        from mlx_lm import load
        self.name=name;self.path=MODEL_PATHS[name]
        print('Hashing local weights: '+name,flush=True)
        self.model_hash=digest({p.name:sha(p) for p in sorted(self.path.glob('*.safetensors'))})
        print('Loading local model: '+name,flush=True)
        self.model,self.tok=load(str(self.path))
        print('Model loaded: '+name,flush=True)
        self.cache=PRIVATE/'generation';self.cache.mkdir(exist_ok=True)
        self.prefix={}
    def batch(self,messages,cap=128,tag='infer'):
        from mlx_lm import batch_generate
        from mlx_lm.sample_utils import make_sampler
        from mlx_lm.models.cache import trim_prompt_cache
        records=[None]*len(messages);pending=[]
        for i,msg in enumerate(messages):
            sig=digest([self.model_hash,msg,cap,'greedy-v1']);path=self.cache/(sig+'.json')
            if path.exists():records[i]=json.loads(path.read_text())
            else:pending.append((i,msg,path,sig))
        for lo in range(0,len(pending),8):
            chunk=pending[lo:lo+8]
            prompts=[self.tok.encode(x[1]) if isinstance(x[1],str) else self.tok.apply_chat_template(x[1],tokenize=True,add_generation_prompt=True,return_dict=False) for x in chunk]
            caches=[];remaining=[];keys=[];reused=[]
            for (_,msg,_,_),prompt in zip(chunk,prompts):
                k=digest(msg[:2]) if isinstance(msg,list) and len(msg)>=2 else None
                keys.append(k);old=self.prefix.get(k) if k else None;n=0;cache=None
                if old:
                    tokens,cache=old
                    for aa,bb in zip(tokens,prompt[:-1]):
                        if aa!=bb:break
                        n+=1
                    offset=int(cache[0].offset)
                    n=min(n,offset)
                    trim_prompt_cache(cache,offset-n)
                caches.append(cache);remaining.append(prompt[n:]);reused.append(n)
            start=time.monotonic()
            response=batch_generate(self.model,self.tok,remaining,prompt_caches=caches,max_tokens=cap,sampler=make_sampler(temp=0),
              prefill_batch_size=2,completion_batch_size=8,prefill_step_size=256,return_prompt_caches=True,return_token_ids=True)
            elapsed=time.monotonic()-start
            for (i,msg,path,sig),prompt,raw,k,n,cache,ids in zip(chunk,prompts,response.texts,keys,reused,response.caches,response.token_ids):
                if k:self.prefix[k]=(prompt+ids,cache)
                rec={'raw':raw,'input_tokens':len(prompt),'output_tokens':len(self.tok.encode(raw,add_special_tokens=False)),
                  'reused_prefix_tokens':n,'cap':cap,'batch_seconds_per_case':elapsed/len(chunk),'signature':sig,'model_sha256':self.model_hash,'api_cost_usd':0}
                save(path,rec);records[i]=rec
                with (PRIVATE/'local_usage.jsonl').open('a') as f:f.write(json.dumps({k:v for k,v in rec.items() if k!='raw'})+'\n')
            print(json.dumps({'model':self.name,'stage':tag,'completed':min(lo+8,len(pending)),'total':len(pending),'seconds':round(elapsed,2)}),flush=True)
            while len(self.prefix)>16:self.prefix.pop(next(iter(self.prefix)))
        return records
