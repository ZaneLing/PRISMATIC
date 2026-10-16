"""Fuse released FLAME list-policy adapter, then quantize tensor by tensor.

No training, patient data, or base-model substitution. Conversion provenance
records the complete source hashes. Evaluation is list-policy transfer only;
the authors' separate classifier and patient embedding pipeline are not run.
"""
import json,shutil
from common import *
def main():
    import mlx.core as mx
    src=MODELS/'flame';base=src/'pi_list_sft';out=MODELS/'flame-list-grpo-4bit';out.mkdir(exist_ok=True)
    config=json.loads((base/'config.json').read_text());ac=json.loads((src/'pi_list/adapter_config.json').read_text())
    adapter=mx.load(str(src/'pi_list/adapter_model.safetensors'))
    source=json.loads((base/'model.safetensors.index.json').read_text())['weight_map']
    assert all((base/f).exists() for f in set(source.values())), 'Download incomplete'
    merged=0;index={};errors=[];used=set();total=0
    names=sorted(set(source.values()))
    for j,file in enumerate(names):
        weights=mx.load(str(base/file));dest={}
        for name,w in weights.items():
            prefix='base_model.model.'+name.removesuffix('.weight')
            ak=prefix+'.lora_A.weight';bk=prefix+'.lora_B.weight'
            if ak in adapter:
                assert bk in adapter and w.shape==(adapter[bk].shape[0],adapter[ak].shape[1])
                w=w+(adapter[bk]@adapter[ak]*(ac['lora_alpha']/ac['r'])).astype(w.dtype)
                used.update([ak,bk]);merged+=1
            if w.ndim==2 and w.shape[-1]%64==0:
                q,s,b=mx.quantize(w,group_size=64,bits=4)
                mx.eval(q,s,b)
                dest[name]=q;dest[name.removesuffix('.weight')+'.scales']=s;dest[name.removesuffix('.weight')+'.biases']=b
            else:mx.eval(w);dest[name]=w
        name=f'model-{j+1:05d}-of-{len(names):05d}.safetensors'
        mx.save_safetensors(str(out/name),dest,metadata={'format':'mlx'})
        for k,v in dest.items():index[k]=name;total+=v.nbytes
        del weights,dest;mx.clear_cache();print('converted shard',j+1,flush=True)
    assert used==set(adapter), 'Unmerged LoRA tensors: '+str(len(set(adapter)-used))
    config['quantization']={'group_size':64,'bits':4};config['quantization_config']=config['quantization']
    save(out/'config.json',config);save(out/'model.safetensors.index.json',{'metadata':{'total_size':total},'weight_map':index})
    for name in ['tokenizer.json','tokenizer_config.json','special_tokens_map.json']:shutil.copyfile(base/name,out/name)
    save(HERE/'results/flame_conversion.json',{'source_model':'cxfan/FLAME_ckpts','source_revision':'2dbdc8d5c31ab320e57b9e6b1a07683301b44dfc',
      'source_files':{str(p.relative_to(src)):sha(p) for p in [*(base/f for f in names),src/'pi_list/adapter_model.safetensors',src/'pi_list/adapter_config.json',base/'config.json']},
      'merged_linear_layers':merged,'unmerged_adapter_tensors':0,'quantization':'4-bit affine, group 64 after merge',
      'kind':'released trained list-policy transfer; full FLAME classifier/embedding pipeline not reproduced'})
if __name__=='__main__':main()
