"""Pinned GAMENet graph/readout with an explicitly adapted single-visit text input.

No discharge codes, fabricated diagnoses, or zero substitute DDI graph. Dynamic
loading preserves author code locally; a forward-equivalence check guards the
batched single-visit computation. This is not a faithful longitudinal reproduction.
"""
from __future__ import annotations
import ast,hashlib,json,re,sys,time,copy,subprocess
from pathlib import Path
from collections import Counter
import numpy as np,pandas as pd,torch
from torch.nn import functional as F
from build_protocol_data import ROOT,sha
from run_protocol_methods import take,score
from build_graph_resources import RES

HERE=Path(__file__).resolve().parent

def load_author_model(repo):
    env={}
    for name,keep in [('layers.py',{'GraphConvolution'}),('models.py',{'GCN','GAMENet'})]:
        tree=ast.parse((repo/'code'/name).read_text())
        nodes=[n for n in tree.body if (isinstance(n,ast.ClassDef) and n.name in keep) or
            (isinstance(n,(ast.Import,ast.ImportFrom)) and not (isinstance(n,ast.ImportFrom) and n.module in {'dnc','layers'}))]
        exec(compile(ast.Module(body=nodes,type_ignores=[]),str(repo/'code'/name),'exec'),env)
    return env['GAMENet']

def encode(parts):
    raw={s:[('chief '+str(r.chiefcomplaint or '')+' acuity '+str(r.acuity or ''),str(r.home_meds or '')) for r in p.itertuples()] for s,p in parts.items()}
    voc=[]
    for channel in range(2):
        freq=Counter(t for row in raw['train'] for t in re.findall(r'\w+',row[channel].lower()))
        voc.append({t:i+1 for i,(t,n) in enumerate(freq.most_common(6000))})
    encoded={s:[[([voc[c].get(t,0) for t in re.findall(r'\w+',row[c].lower())][:128] or [0]) for c in range(2)] for row in rows] for s,rows in raw.items()}
    return encoded,[len(v)+1 for v in voc]

def batch_forward(model,rows):
    means=[]
    for channel in range(2):
        seq=[r[channel] for r in rows];length=max(map(len,seq))
        ids=torch.zeros((len(seq),length),dtype=torch.long);mask=torch.zeros_like(ids,dtype=torch.float32)
        for i,row in enumerate(seq):ids[i,:len(row)]=torch.tensor(row);mask[i,:len(row)]=1
        emb=model.dropout(model.embeddings[channel](ids))
        means.append((emb*mask.unsqueeze(-1)).sum(1)/mask.sum(1).unsqueeze(-1))
    outs=[model.encoders[c](means[c].unsqueeze(1))[0][:,0] for c in range(2)]
    query=model.query(torch.cat(outs,dim=-1))
    memory=model.ehr_gcn()-model.ddi_gcn()*model.inter
    fact=F.softmax(query@memory.T,dim=-1)@memory
    logits=model.output(torch.cat([query,fact,fact],dim=-1))
    prob=torch.sigmoid(logits)
    penalty=((prob.unsqueeze(2)*prob.unsqueeze(1))*model.tensor_ddi_adj).mean()
    return logits,penalty

def run():
    torch.set_num_threads(2);torch.set_num_interop_threads(1)
    config={'id':'E01-GAMENet-admission-text-r1','seeds':[17,42,73],'epochs':5,'batch_size':64,'embedding_dim':64,
       'optimizer':'Adam','lr':0.001,'ddi_penalty_weight':0.1,'input_channels':['chief complaint + acuity','home medication text'],
       'max_tokens_per_channel':128,'vocab_per_channel':6000,'history':'single visit; no previous-visit read',
       'ddi':'all author-linked TWOSIDES pairs, class aggregation; differs from original selected-side-effect graph'}
    (HERE/'graph_protocol.json').write_text(json.dumps(config,indent=2)+'\n')
    frame=pd.read_parquet(ROOT/'prismatic-v4/cohort.parquet')
    parts={s:take(frame,s,n) for s,n in [('train',40000),('val',4000),('test',4000)]}
    enc,sizes=encode(parts)
    classes=json.loads((HERE/'results/protocol_method_results.json').read_text())['classes']
    truth={s:[set(x) for x in p.atc4_codes] for s,p in parts.items()}
    y=torch.tensor([[c in g for c in classes] for g in truth['train']],dtype=torch.float32)
    graphs=np.load(RES/'atc4_graphs.npz');assert graphs['ddi'].sum()>0
    repo=Path('/tmp/prismatic-gamenet');Model=load_author_model(repo)
    results=[];t=time.time()
    def predict(model,rows):
        model.eval();vals=[]
        with torch.no_grad():
            for lo in range(0,len(rows),128):
                v,_=batch_forward(model,rows[lo:lo+128]);vals.append(np.argsort(-v.numpy(),axis=1,kind='stable')[:,:5])
        return np.concatenate(vals)
    for seed in config['seeds']:
        torch.manual_seed(seed);rng=np.random.default_rng(seed)
        model=Model(tuple(sizes+[len(classes)]),graphs['ehr'],graphs['ddi'],emb_dim=64,device=torch.device('cpu'))
        model.eval()
        with torch.no_grad():
            batched,_=batch_forward(model,enc['train'][:4])
            original=torch.cat([model([[r[0],r[1],[]]]) for r in enc['train'][:4]])
            err=float((batched-original).abs().max())
        assert err<1e-5,err
        opt=torch.optim.Adam(model.parameters(),lr=.001);best=-1;best_state=None;history=[]
        for epoch in range(5):
            model.train();order=rng.permutation(len(y));losses=[]
            for lo in range(0,len(order),64):
                idx=order[lo:lo+64];logits,penalty=batch_forward(model,[enc['train'][i] for i in idx])
                loss=F.binary_cross_entropy_with_logits(logits,y[idx])+.1*penalty
                opt.zero_grad();loss.backward();opt.step();losses.append(float(loss.detach()))
            pred=predict(model,enc['val']);metric=score(truth['val'],pred,classes)['micro_f1_at_5']
            history.append({'epoch':epoch+1,'train_loss':float(np.mean(losses)),'val_micro_f1_at5':metric})
            if metric>best:best=metric;best_state=copy.deepcopy(model.state_dict())
            print(json.dumps({'method':'GAMENet_text_adaptation','seed':seed,'epoch':epoch+1,'val_f1':metric}),flush=True)
        model.load_state_dict(best_state);pred=predict(model,enc['test'])
        np.save(ROOT/f'prismatic-v4/gamenet_predictions_seed{seed}.npy',pred)
        torch.save(best_state,ROOT/f'prismatic-v4/gamenet_weights_seed{seed}.pt')
        results.append({'seed':seed,'forward_max_error':err,'validation_history':history,'best_val':best,'test':score(truth['test'],pred,classes)})
    pilot=take(frame,'test',50);loc={h:i for i,h in enumerate(parts['test'].hadm_id)}
    pilot_pred=np.load(ROOT/'prismatic-v4/gamenet_predictions_seed42.npy')[[loc[h] for h in pilot.hadm_id]]
    report={'run_id':config['id'],'author_commit':subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip(),
        'source_models_sha256':sha(repo/'code/models.py'),'protocol_sha256':sha(HERE/'graph_protocol.json'),
        'cohort_sha256':sha(ROOT/'prismatic-v4/cohort.parquet'),'runs':results,'elapsed_seconds':round(time.time()-t,2),
        'same_50_case_seed42':score([set(x) for x in pilot.atc4_codes],pilot_pred,classes),
        'status':'executed independent admission-text/single-visit adaptation; not original-paper reproduction',
        'limits':['Text token channels replace diagnosis/procedure codes; cannot be called faithful GAMENet.',
          'No longitudinal dynamic-memory read for single-visit inputs.',
          'Adam/BCE plus fixed DDI penalty and batched training differ from original training schedule.',
          'Graph coverage and all-pair construction are disclosed in graph_resource_audit.json.',
          'Validation F1 was still increasing at the five-epoch budget boundary; this is a short development run, not a converged competitive reproduction.']}
    (HERE/'results/gamenet_adaptation_results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':run()
