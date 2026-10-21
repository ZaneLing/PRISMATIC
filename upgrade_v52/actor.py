"""Local-only frozen LLM actor; one consistent complete-JSON decoder."""
import argparse,json,sys,os,time
from common52 import *
os.environ.setdefault('TOKENIZERS_PARALLELISM','false')
MODELS=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/models'
PATHS={'qwen':MODELS/'qwen3-4b-instruct-2507-4bit','llama':MODELS/'llama-3.2-3b-instruct-4bit'}
TASK='''Retrospective research task: predict NEW or CHANGED medication orders entered during ICU hours6-12, using only information recorded by hour6. Prior orders are context, not automatically new targets. Recorded diagnoses can be provisional. The catalogue, draft and neighboring cases are statistical suggestions, not proof of indication. Select a coherent set of orders; select zero if no new order is expected. Do not invent missing diagnoses, allergies or order fields. For each drug choose the most appropriate joint route/dose/frequency template. Return ONLY a complete JSON object with key order_ids and a list of actual catalogue IDs. No prose.'''
def prompt(c):
 x=c['context'];lines=['Age decade: '+str(x['age_decade'])+'; gender: '+str(x['gender']),'Diagnoses entered by hour6: '+'; '.join(x['diagnoses']), 'Prior recorded orders:']
 lines.extend(' | '.join(str(o.get(f)) for f in ['drug_name','route','dosage','frequency','order_offset']) for o in x['prior_orders'])
 lines+=['Available labs:']+[str(o['name'])+' '+str(o['value'])+' '+str(o['unit']) for o in x['available_labs']]
 lines+=['Catalogue: ID | drug | route | dosage | frequency | supporting training neighbors']
 for oid,o in c['catalogue'].items():lines.append(oid+' | '+c['drug_names'][o['drug_code']]+' | '+' | '.join(str(o[f]) for f in FIELDS[1:])+' | '+str(c['evidence']['order_support'][oid]))
 lines+=['Frozen predictor draft IDs: '+json.dumps(c['frozen_draft']),'Choose the order IDs for this patient.']
 return [{'role':'system','content':TASK},{'role':'user','content':'\n'.join(lines)}]
def decode(raw,c):
 try:
  obj=json.loads(raw.strip());ids=obj.get('order_ids') if isinstance(obj,dict) else obj
  if not isinstance(ids,list) or not all(isinstance(x,str) and x in c['catalogue'] for x in ids):raise ValueError()
  ids=list(dict.fromkeys(ids));return {'order_ids':ids,'orders':[c['catalogue'][i] for i in ids],'invalid':False}
 except (ValueError,TypeError):return {'order_ids':[],'orders':[],'invalid':True}
def run(name,splits):
 from mlx_lm import load,batch_generate
 from mlx_lm.sample_utils import make_sampler
 path=PATHS[name];mh=digest({p.name:sha(p) for p in sorted(path.glob('*.safetensors'))})
 model,tok=load(str(path));cache=PRIVATE/'generation';cache.mkdir(exist_ok=True)
 for split in splits:
  cases=json.loads((PRIVATE/(split+'.json')).read_text())
  if name=='llama':cases=cases[:128]
  rows=[]
  for start in range(0,len(cases),8):
   chunk=cases[start:start+8];records=[None]*len(chunk);pending=[]
   for i,c in enumerate(chunk):
    msg=prompt(c);sig=digest([mh,msg,256,'v52-greedy-batch2-8']);f=cache/(sig+'.json')
    if f.exists():records[i]=json.loads(f.read_text())
    else:pending.append((i,msg,sig,f))
   if pending:
    pp=[tok.apply_chat_template(m,tokenize=True,add_generation_prompt=True,return_dict=False) for i,m,s,f in pending];t=time.monotonic()
    result=batch_generate(model,tok,pp,max_tokens=256,sampler=make_sampler(temp=0),prefill_batch_size=2,completion_batch_size=8,prefill_step_size=256)
    elapsed=time.monotonic()-t
    for (i,msg,sig,f),p,raw in zip(pending,pp,result.texts):
     rec=dict(raw=raw,input_tokens=len(p),output_tokens=len(tok.encode(raw,add_special_tokens=False)),seconds=elapsed/len(pending),model_sha256=mh,signature=sig,api_cost_usd=0)
     save(f,rec);records[i]=rec
     with (PRIVATE/'usage.jsonl').open('a') as out:out.write(json.dumps({k:v for k,v in rec.items() if k!='raw'})+'\n')
   for c,r in zip(chunk,records):rows.append(dict(case_id=c['case_id'],**decode(r['raw'],c),receipt=r))
   save(PRIVATE/(name+'-'+split+'.json'),rows)
   print(json.dumps(dict(model=name,split=split,done=len(rows),total=len(cases),invalid=sum(r['invalid'] for r in rows))),flush=True)
 if name=='qwen':save(PRIVATE/'actor_lock.json',{'implementation_sha256':sha(Path(__file__)),'model_sha256':mh})
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--model',default='qwen',choices=PATHS);p.add_argument('--splits',nargs='+',default=['reflection','proposal','guard','audit']);a=p.parse_args();run(a.model,a.splits)
