"""Frozen-checkpoint logit diagnosis; no refitting, threshold selection or test reads."""
import gc,hashlib,json,math,sys,time
from pathlib import Path
import numpy as np
import mlx.core as mx
from mlx_lm import load
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;sys.path.insert(0,str(HERE))
from views import view,serialize
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v31'
MODEL=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/models/qwen3-4b-instruct-2507-4bit'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,z):
    p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(z,indent=2)+'\n');tmp.replace(p)
def auc(y,p):
    y=np.asarray(y,dtype=bool);p=np.asarray(p);n=int(y.sum());m=len(y)-n
    if not n or not m:return None
    order=np.argsort(p,kind='stable');ranks=np.empty(len(p),dtype=float);lo=0
    while lo<len(p):
        hi=lo+1
        while hi<len(p) and p[order[hi]]==p[order[lo]]:hi+=1
        ranks[order[lo:hi]]=(lo+1+hi)/2;lo=hi
    return float((ranks[y].sum()-n*(n+1)/2)/(n*m))
def summary(rows,prevalence):
    y=np.asarray([x for r in rows for x in r['target']],dtype=float);p=np.asarray([x for r in rows for x in r['probability_one']],dtype=float);q=np.clip(p,1e-12,1-1e-12)
    return {'examples':len(rows),'slots':len(y),'positive_slots':int(y.sum()),'positive_prevalence':float(y.mean()),'conditional_binary_bce':float(-(y*np.log(q)+(1-y)*np.log1p(-q)).mean()),'brier':float(np.mean((p-y)**2)),'auroc':auc(y,p),'mean_probability_one':float(p.mean()),'probability_one_sd':float(p.std()),'mean_probability_given_positive':float(p[y==1].mean()) if y.sum() else None,'mean_probability_given_negative':float(p[y==0].mean()) if (1-y).sum() else None,'fraction_at_or_above_half':float((p>=.5).mean()),'constant_training_prevalence_bce':float(-(y*np.log(prevalence)+(1-y)*np.log1p(-prevalence)).mean()),'mean_binary_token_mass':float(np.mean([x for r in rows for x in r['binary_token_mass']]))}
def main():
    start=time.time();protocol=HERE/'collapse_diagnostic_protocol.json';spec=json.loads(protocol.read_text());part=PRIVATE/'seed42/permuted_uniform-round1';adapter=part/'adapter'
    assert sha(adapter/'adapters.safetensors')==spec['frozen_adapter_sha256']
    audit=json.loads((HERE/'results/data_audit.json').read_text());assert sha(PRIVATE/'cases.json')==audit['prepared_sha256']
    training=[json.loads(line) for line in (part/'data/train.jsonl').read_text().splitlines()];targets=[json.loads(x['messages'][-1]['content'])['include'] for x in training]
    prevalence=sum(map(sum,targets))/(len(targets)*20);source=json.loads((PRIVATE/'cases.json').read_text())
    groups={'train_permuted':training[:32],**{f'proposal_{k}':[serialize(view(c,k)) for c in source['validation'][:32]] for k in ['ranked','permuted']}}
    frozen={'protocol_sha256':sha(protocol),'script_sha256':sha(Path(__file__)),'source_training_sha256':sha(part/'data/train.jsonl'),'source_cases_sha256':sha(PRIVATE/'cases.json'),'adapter_sha256':spec['frozen_adapter_sha256'],'model_files_sha256':audit['model_files_sha256']}
    directory=PRIVATE/'collapse-diagnostic';directory.mkdir(exist_ok=True);lock=directory/'lock.json'
    if lock.exists():assert json.loads(lock.read_text())==frozen
    else:save(lock,frozen)
    result={'status':'running','sources':frozen,'training_label_statistics':{'examples':len(targets),'positive_slots':sum(map(sum,targets)),'total_slots':len(targets)*20,'prevalence':prevalence,'zero_target_examples':sum(sum(y)==0 for y in targets),'positive_by_position':[sum(y[i] for y in targets) for i in range(20)]},'cached_proposal':{},'states':{},'new_test_or_guard_inference':False,'refits':0,'threshold_selection':False}
    for kind in ['ranked','permuted']:
        rows=json.loads((part/f'proposal-{kind}.json').read_text());masks=[]
        import re
        for r in rows:
            text=re.sub(r'^<think>\s*</think>\s*','',r['raw'].strip(),count=1);mask=json.loads(text)['include'];assert len(mask)==20 and all(type(v) is int and v in [0,1] for v in mask);assert r['orders']==[];masks.append(mask)
        result['cached_proposal'][kind]={'examples':len(rows),'valid_binary_masks':len(masks),'all_zero_masks':sum(sum(m)==0 for m in masks),'unique_raw_responses':len({r['raw'] for r in rows}),'prediction_file_sha256':sha(part/f'proposal-{kind}.json')}
    for state,adapter_path in [('frozen_base',None),('permuted_uniform_seed42_round1',str(adapter))]:
        model,tok=load(str(MODEL),adapter_path=adapter_path);zero=tok.encode('0',add_special_tokens=False);one=tok.encode('1',add_special_tokens=False);assert len(zero)==len(one)==1;bits=[zero[0],one[0]];result['states'][state]={}
        for group,examples in groups.items():
            result['states'][state][group]={}
            for context in spec['contexts']:
                records=[]
                for i,example in enumerate(examples):
                    messages=example['messages'];target=json.loads(messages[-1]['content'])['include'];path=directory/f'{state}-{group}-{context}-{i}.json'
                    if path.exists():record=json.loads(path.read_text());assert record['target']==target
                    else:
                        content=messages[-1]['content'] if context=='teacher_forced_ground_truth_prefix' else json.dumps({'include':[0]*20})
                        sequence=tok.apply_chat_template(messages[:-1]+[{'role':'assistant','content':content}],tokenize=True,return_dict=False)
                        prompt=tok.apply_chat_template(messages[:-1],tokenize=True,add_generation_prompt=True,return_dict=False);assert sequence[:len(prompt)]==prompt
                        positions=[j for j in range(len(prompt),len(sequence)) if sequence[j] in bits];assert len(positions)==20
                        expected=target if context=='teacher_forced_ground_truth_prefix' else [0]*20;assert [bits.index(sequence[j]) for j in positions]==expected
                        output=model(mx.array([sequence[:-1]],dtype=mx.int32));selected=output[0,mx.array([j-1 for j in positions])].astype(mx.float32);logp=selected-mx.logsumexp(selected,axis=-1,keepdims=True);pair=logp[:,mx.array(bits)];prob=mx.softmax(pair,axis=-1)[:,1];mass=mx.exp(pair).sum(axis=-1);mx.eval(prob,mass)
                        record={'index':i,'target':target,'probability_one':prob.tolist(),'binary_token_mass':mass.tolist(),'prompt_tokens':len(prompt),'decision_tokens':len(positions),'prompt_target_alignment_verified':True};save(path,record);del output,selected,logp,pair,prob,mass;mx.clear_cache()
                    records.append(record)
                result['states'][state][group][context]=summary(records,prevalence);print(json.dumps({'state':state,'group':group,'context':context,'complete':len(records)}),flush=True)
        del model,tok;gc.collect();mx.clear_cache()
    result['status']='executed';result['seconds']=time.time()-start;result['scope']='Post-observation diagnostic on32 training examples and32 proposal cases in two views, with fixed model states. Oracle-prefix likelihood is not deployable accuracy. No winner or threshold selected.'
    save(HERE/'results/collapse_diagnostic.json',result);print(json.dumps({'status':result['status'],'seconds':result['seconds']}),flush=True)
if __name__=='__main__':main()
