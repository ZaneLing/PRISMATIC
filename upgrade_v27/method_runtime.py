"""Common input hiding, set metrics, and pinned author-model execution."""
import copy,json,random,time
from pathlib import Path
import numpy as np,torch
from torch.nn import functional as F
from author_cores import armr,safedrug
HERE=Path(__file__).resolve().parent
THRESHOLDS=[.1,.2,.3,.4,.5,.6]

def flatten(patients):
    out=[]
    for group,p in enumerate(patients):
        for visit,v in enumerate(p['visits']):out.append({'patient':group,'subject_hash':p['subject_hash'],'visit':visit,'case_id':v['case_id'],'gold':v['gold'],'source':p['visits']})
    return out
def prefix(case):
    history=[[list(c) for c in v['codes']] for v in case['source'][:case['visit']+1]]
    history[-1][2]=[]
    return history
def truths(cases,meds):
    ci={c:i for i,c in enumerate(meds)};y=np.zeros((len(cases),len(meds)),dtype=np.float32)
    for i,c in enumerate(cases):
        for name in c['gold']:
            if name in ci:y[i,ci[name]]=1
    return y
def metrics(prob,cases,bundle,threshold=.5):
    pred=prob>=threshold;y=truths(cases,bundle['medications']).astype(bool)
    tp=(pred&y).sum(1);pn=pred.sum(1);gn=np.array([len(c['gold']) for c in cases]);den=pn+gn
    f=np.divide(2*tp,den,out=np.ones(len(tp)),where=den>0);union=den-tp;j=np.divide(tp,union,out=np.ones(len(tp)),where=union>0)
    groups=np.array([c['patient'] for c in cases]);n=groups.max()+1;counts=np.bincount(groups,minlength=n)
    pavg=lambda values:float(np.mean(np.bincount(groups,weights=values,minlength=n)/counts))
    ddi_pairs=all_pairs=covered_pairs=0;covered=set(bundle['ddi_covered_indices'])
    for row in pred:
        ix=np.flatnonzero(row);all_pairs+=len(ix)*(len(ix)-1)//2;ddi_pairs+=float(bundle['ddi'][np.ix_(ix,ix)].sum()/2)
        c=sum(i in covered for i in ix);covered_pairs+=c*(c-1)//2
    return {'patients':int(n),'visits':len(cases),'patient_f1':pavg(f),'patient_jaccard':pavg(j),'micro_f1':float(2*tp.sum()/max(1,den.sum())),
      'micro_precision':float(tp.sum()/max(1,pn.sum())),'micro_recall':float(tp.sum()/max(1,gn.sum())),
      'mean_medications':float(pn.mean()),'empty_prediction_fraction':float(np.mean(pn==0)),'empty_target_fraction':float(np.mean(gn==0)),
      'known_graph_pair_rate_all_predictions':float(ddi_pairs/max(1,all_pairs)),'ddi_source_covered_pair_fraction':covered_pairs/max(1,all_pairs),
      'known_graph_pair_rate_covered_pairs':float(ddi_pairs/max(1,covered_pairs)),'ddi_note':'Research graph relations; missing edges/classes are not proof of clinical safety.'}
def select(prob,cases,bundle):
    options=[{'threshold':t,'metrics':metrics(prob,cases,bundle,t)} for t in THRESHOLDS]
    return max(options,key=lambda x:x['metrics']['patient_jaccard'])
def make_model(name,bundle,device):
    if name=='ARMR':return armr().MyNet(256,tuple(bundle['sizes']),3,torch.tensor(bundle['ehr'],device=device),torch.tensor(bundle['ddi'],device=device)).to(device)
    core=safedrug()
    if name=='GAMENet':return core.GAMENet(tuple(bundle['sizes']),bundle['ehr'],bundle['ddi'],emb_dim=64,device=device)
    assert name=='SafeDrug' and 'mpnn_graphs' in bundle
    core.MolecularGraphNeuralNetwork.pad=sparse_molecular_pad
    model=core.SafeDrugModel(tuple(bundle['sizes']),bundle['ddi'],bundle['substructure_mask'],bundle['mpnn_graphs'],bundle['n_fingerprints'],bundle['average_projection'],emb_dim=64,device=device)
    # The released encoder is not registered in model.parameters()/the optimizer.
    # Preserve its exact forward values and registered-parameter gradients while
    # avoiding useless repeated backward passes through those fixed parameters.
    fixed=model.MPNN_emb.detach();del model.MPNN_emb;model.register_buffer('MPNN_emb',fixed)
    return model
def sparse_molecular_pad(self,matrices,pad_value):
    """Algebra-equivalent block diagonal adjacency, without quadratic storage."""
    assert pad_value==0
    coordinates=[];values=[];offset=0
    for matrix in matrices:
        nz=matrix.nonzero().T;coordinates.append(nz+offset);values.append(matrix[nz[0],nz[1]])
        assert matrix.shape[0]==matrix.shape[1];offset+=matrix.shape[0]
    return torch.sparse_coo_tensor(torch.cat(coordinates,1),torch.cat(values),(offset,offset),device=self.device).coalesce()
def armr_input(cases,sizes,device):
    length=max(c['visit']+1 for c in cases);arrays=[np.zeros((len(cases),length,n),dtype=np.float32) for n in sizes]
    for i,c in enumerate(cases):
        for j,visit in enumerate(reversed(prefix(c))):
            for k,ids in enumerate(visit):arrays[k][i,j,ids]=1
    return [torch.from_numpy(x).to(device) for x in arrays]
def batches(cases,rng=None,batch_size=32):
    # Exact-length buckets prevent zero-padding from inventing visit embeddings.
    groups={}
    for i,c in enumerate(cases):groups.setdefault(c['visit'],[]).append(i)
    out=[]
    for group in groups.values():
        if rng is not None:rng.shuffle(group)
        out.extend([group[i:i+batch_size] for i in range(0,len(group),batch_size)])
    if rng is not None:rng.shuffle(out)
    return out
def predict(model,name,cases,bundle,device):
    model.eval();output=np.zeros((len(cases),len(bundle['medications'])),dtype=np.float32)
    with torch.no_grad():
        for ix in batches(cases,None,64 if name=='ARMR' else 1):
            if name=='ARMR':logits=model(*armr_input([cases[i] for i in ix],bundle['sizes'],device))
            else:
                result=model(prefix(cases[ix[0]]));logits=result[0] if isinstance(result,tuple) else result
            values=logits.sigmoid().cpu().numpy();assert np.isfinite(values).all();output[ix]=values
    return output
def loss_for(model,name,cases,targets,bundle,device,temperature,rng):
    if name=='ARMR':
        logits=model(*armr_input(cases,bundle['sizes'],device));y=torch.as_tensor(targets,device=device)
        p=logits.sigmoid();mask=y.unsqueeze(2)*(1-y).unsqueeze(1)
        hinge=(F.relu(1-(p.unsqueeze(2)-p.unsqueeze(1)))*mask).sum((1,2))/mask.sum((1,2)).clamp(min=1)
        return .7*F.binary_cross_entropy_with_logits(logits,y)+.3*hinge.mean()
    logits,ddi_loss=model(prefix(cases[0]));y=torch.as_tensor(targets,device=device)
    margin=torch.full(y.shape,-1,dtype=torch.long,device=device);positive=np.flatnonzero(targets[0]);margin[0,:len(positive)]=torch.as_tensor(positive,device=device)
    alpha=.9 if name=='GAMENet' else .95;supervised=alpha*F.binary_cross_entropy_with_logits(logits,y)+(1-alpha)*F.multilabel_margin_loss(logits.sigmoid(),margin)
    ix=np.flatnonzero(logits.detach().sigmoid().cpu().numpy()[0]>=.5);rate=float(bundle['ddi'][np.ix_(ix,ix)].sum()/max(1,len(ix)*(len(ix)-1)))
    if name=='GAMENet':return ddi_loss if rate>.05 and rng.random()<np.exp((.05-rate)/temperature) else supervised
    beta=1. if rate<=.06 else max(0.,1-(rate-.06)/.05)
    return beta*supervised+(1-beta)*ddi_loss
