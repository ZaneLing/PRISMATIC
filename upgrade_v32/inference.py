"""Local zero-prefix conditional scoring with immutable prompt and case receipts."""
import gc,hashlib,json,time
from pathlib import Path
import numpy as np
import mlx.core as mx
from mlx_lm import load
from decision_loss import logits_at_decisions
def digest(z):return hashlib.sha256(json.dumps(z,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save_once(p,z):
    p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():assert json.loads(p.read_text())==z,'Immutable inference receipt changed'
    else:
        temp=p.with_suffix('.tmp');temp.write_text(json.dumps(z,indent=2)+'\n');temp.replace(p)
def signature(c,version,source_signature,config):return digest([version,source_signature,c['messages'],'all_zero_include20',config])
def encode(tok,c,config):
    # Gold fields are deliberately absent from this operation.
    messages=c['messages'];sequence=tok.apply_chat_template(messages+[{'role':'assistant','content':json.dumps({'include':[0]*20})}],tokenize=True,return_dict=False);prompt=tok.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,return_dict=False)
    assert sequence[:len(prompt)]==prompt;positions=[len(prompt)+i for i in config['decision_offsets']];assert len(positions)==20 and all(sequence[i]==config['zero_token_id'] for i in positions)
    return sequence[:-1],positions
class Scorer:
    def __init__(self,model_path,adapter,version,root,config,source_signature):
        self.model_path=model_path;self.adapter=adapter;self.version=version;self.root=Path(root);self.config=config;self.source_signature=source_signature;self.loaded=[]
    def close(self):self.loaded.clear();gc.collect();mx.clear_cache()
    def score(self,cases,binding_name):
        groups={}
        for c in cases:groups.setdefault(signature(c,self.version,self.source_signature,self.config),c)
        pending=[(s,c) for s,c in groups.items() if not (self.root/'raw'/f'{s}.json').exists()]
        if pending and not self.loaded:self.loaded.extend(load(str(self.model_path),adapter_path=str(self.adapter) if self.adapter else None))
        for start in range(0,len(pending),4):
            chunk=pending[start:start+4];model,tok=self.loaded;encoded=[encode(tok,c,self.config) for _,c in chunk];length=max(len(tokens) for tokens,_ in encoded);pad=tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
            inputs=mx.array([tokens+[pad]*(length-len(tokens)) for tokens,_ in encoded],dtype=mx.int32);positions=mx.array([pos for _,pos in encoded],dtype=mx.int32);begin=time.perf_counter();logits=logits_at_decisions(model,inputs,positions,self.config['zero_token_id'],self.config['one_token_id']);prob=mx.softmax(logits,axis=-1)[:,:,1];mx.eval(prob);values=np.asarray(prob,dtype=float);elapsed=time.perf_counter()-begin
            assert values.shape==(len(chunk),20) and np.isfinite(values).all() and ((values>=0)&(values<=1)).all()
            for ((s,c),(tokens,pos),p) in zip(chunk,encoded,values):save_once(self.root/'raw'/f'{s}.json',{'signature':s,'state_version':self.version,'inference_source_signature':self.source_signature,'prompt_sha256':digest(c['messages']),'conditional_probabilities':p.tolist(),'input_tokens':len(tokens),'decision_positions':pos,'actual_batch_size':len(chunk),'seconds_per_unique_prompt':elapsed/len(chunk)})
            print(json.dumps({'score_state':self.version[:12],'binding':binding_name,'new_unique_prompts_completed':start+len(chunk),'new_unique_prompts_total':len(pending)}),flush=True);del logits,prob,inputs,positions;mx.clear_cache()
        rows=[]
        for c in cases:
            s=signature(c,self.version,self.source_signature,self.config);path=self.root/'raw'/f'{s}.json';raw=json.loads(path.read_text());assert raw['signature']==s and raw['state_version']==self.version and raw['inference_source_signature']==self.source_signature and raw['prompt_sha256']==digest(c['messages'])
            rows.append({'case_id':c['case_id'],'subject_hash':c['subject_hash'],'signature':s,'raw_sha256':sha(path),'conditional_probabilities':raw['conditional_probabilities']})
        save_once(self.root/'bindings'/f'{binding_name}.json',rows);return np.asarray([r['conditional_probabilities'] for r in rows],dtype=float)
