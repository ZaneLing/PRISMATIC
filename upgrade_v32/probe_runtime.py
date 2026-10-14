"""Check decision-target alignment, blinding, gradients and real projection equivalence."""
import gc,json,sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import mlx.core as mx
import mlx.nn as nn
from mlx.utils import tree_flatten
from mlx_lm import load
from decision_loss import inputs_and_labels,logits_at_decisions,decision_loss
from run_training import HERE,PRIVATE,MODEL,sha,sources,save
class Body(nn.Module):
    def __init__(self):super().__init__();self.embed=nn.Embedding(17,8)
    def __call__(self,inputs):return mx.cumsum(self.embed(inputs),axis=1)
class Toy(nn.Module):
    def __init__(self):super().__init__();self.model=Body();self.lm_head=nn.Linear(8,17);self.args=SimpleNamespace(tie_word_embeddings=False)
    def __call__(self,inputs):return self.lm_head(self.model(inputs))
def main():
    mx.random.seed(42);toy=Toy();offsets=list(range(20));row=[9,3]+[5,9]*10+[2,0,0];batch=mx.array([row,row]);lengths=mx.array([[2,23],[2,23]])
    x,y,pos=inputs_and_labels(batch,lengths,offsets,5,9,'zero');changed=batch.at[0,7].add(-4);x2,y2,_=inputs_and_labels(changed,lengths,offsets,5,9,'zero');assert bool(mx.all(x==x2)) and bool(mx.any(y!=y2)) and bool(mx.all(x[:,:2]==batch[:,:2]))
    teacher,_,_=inputs_and_labels(batch,lengths,offsets,5,9,'teacher');assert bool(mx.any(teacher!=x))
    full=toy(x);gathered=mx.take_along_axis(full,(pos-1)[:,:,None],axis=1)[:,:,mx.array([5,9])];narrow=logits_at_decisions(toy,x,pos,5,9);assert float(mx.max(mx.abs(gathered-narrow)).item())<1e-5
    for prefix in ['teacher','zero']:
        for weight in [1.,3.9875311720698257]:
            loss,count=decision_loss(toy,batch,lengths,offsets,5,9,prefix,weight);assert count.item()==40 and bool(mx.isfinite(loss))
    fn=lambda m:decision_loss(m,batch,lengths,offsets,5,9,'zero',1.)[0];_,gradient=nn.value_and_grad(toy,fn)(toy);flat=tree_flatten(gradient);assert flat and all(bool(mx.all(mx.isfinite(v))) for _,v in flat) and any(bool(mx.any(v!=0)) for _,v in flat)
    _,other=nn.value_and_grad(toy,lambda m:decision_loss(m,changed,lengths,offsets,5,9,'zero',1.)[0])(toy);assert any(bool(mx.any(v!=dict(tree_flatten(other))[k])) for k,v in flat)
    padded=batch.at[:,24].add(6);assert abs(decision_loss(toy,batch,lengths,offsets,5,9,'zero')[0].item()-decision_loss(toy,padded,lengths,offsets,5,9,'zero')[0].item())<1e-7
    del toy;gc.collect();mx.clear_cache()
    original=json.loads((HERE.parent/'upgrade_v31/results/data_audit.json').read_text());assert all(sha(MODEL/name)==h for name,h in original['model_files_sha256'].items());config=json.loads((PRIVATE/'decision_config.json').read_text());checks=[]
    for name,adapter in [('base',None),('original_failed_adapter',str(PRIVATE.parent/'prismatic-v31/seed42/permuted_uniform-round1/adapter'))]:
        model,tok=load(str(MODEL),adapter_path=adapter);messages=[{'role':'system','content':'Synthetic binary-decision probe; no clinical records.'},{'role':'user','content':'Return20 binary decisions.'}];target={'include':[0,1]*10};sequence=tok.apply_chat_template(messages+[{'role':'assistant','content':json.dumps(target)}],return_dict=False);prompt=tok.apply_chat_template(messages,add_generation_prompt=True,return_dict=False);assert sequence[:len(prompt)]==prompt
        b=mx.array([sequence]);length=mx.array([[len(prompt),len(sequence)]]);indices=[j for j in range(len(prompt),len(sequence)) if sequence[j] in [config['zero_token_id'],config['one_token_id']]];assert [j-len(prompt) for j in indices]==config['decision_offsets']
        for prefix in ['teacher','zero']:
            inputs,labels,pos=inputs_and_labels(b,length,config['decision_offsets'],config['zero_token_id'],config['one_token_id'],prefix);full=model(inputs);wide=mx.take_along_axis(full,(pos-1)[:,:,None],axis=1)[:,:,mx.array([config['zero_token_id'],config['one_token_id']])].astype(mx.float32);narrow=logits_at_decisions(model,inputs,pos,config['zero_token_id'],config['one_token_id']);p1=mx.softmax(wide,axis=-1);p2=mx.softmax(narrow,axis=-1);mx.eval(p1,p2);difference=float(mx.max(mx.abs(p1-p2)).item());assert difference<=.002,(name,prefix,difference)
            checks.append({'state':name,'prefix':prefix,'max_binary_probability_delta':difference,'predeclared_runtime_tolerance':.002});del full,wide,narrow,p1,p2;mx.clear_cache()
        del model,tok;gc.collect();mx.clear_cache()
    result={'status':'passed','source_sha256':sources(),'probe_sha256':sha(Path(__file__)),'model_files_sha256':original['model_files_sha256'],'synthetic_checks':['exact20decision_alignment','zero_prefix_label_blindness','prompt_tokens_unchanged','teacher_prefix_control_changes','binary_projection_equivalence','finite_loss_and_gradients','labels_change_loss_gradients','padding_does_not_change_loss','target_counter_counts_decisions_not_weight_mass'],'real_synthetic_projection_checks':checks,'clinical_model_generations':0,'clinical_fits':0,'api_calls':0,'guard_or_test_reads':False}
    save(HERE/'results/runtime_probe.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':main()
