"""Run actual pinned forward/backward cores on synthetic, non-patient inputs."""
import hashlib,json,time
from pathlib import Path
import numpy as np,torch
from author_cores import armr,safedrug,ROOT,SAFE,sha

HERE=Path(__file__).resolve().parent
def main():
    torch.manual_seed(42);torch.set_num_threads(1);report={}
    sizes=(12,9,8);ehr=np.eye(8,dtype=np.float32);ddi=np.zeros((8,8),dtype=np.float32)
    # Synthetic graph edges are for an execution probe only, never a study DDI resource.
    for i in range(7):ehr[i,i+1]=ehr[i+1,i]=1
    ddi[0,1]=ddi[1,0]=1
    model=armr().MyNet(16,sizes,3,torch.tensor(ehr),torch.tensor(ddi));model.train()
    start=time.perf_counter();d=(torch.rand(4,5,12)>.7).float();p=(torch.rand(4,5,9)>.7).float();m=(torch.rand(4,5,8)>.8).float();m[:,0,:]=0
    out=model(d,p,m);loss=torch.nn.functional.binary_cross_entropy_with_logits(out,torch.zeros_like(out));loss.backward()
    assert out.shape==(4,8) and torch.isfinite(out).all()
    gradients=[x.grad for x in model.parameters() if x.grad is not None]
    assert gradients and all(torch.isfinite(g).all() for g in gradients)
    report['ARMR_2025']={'forward_backward':'passed','shape':list(out.shape),'seconds':time.perf_counter()-start,'parameters':sum(x.numel() for x in model.parameters())}
    core=safedrug();sequence=[[[0,1],[0],[0,2]],[[2,3],[1,2],[]]]
    model=core.GAMENet(sizes,ehr,ddi,emb_dim=16);model.eval();out=model(sequence);assert out.shape==(1,8) and torch.isfinite(out).all()
    # Verify this core cannot read the current visit's medication label field.
    changed=[[v[0],v[1],list(v[2])] for v in sequence];changed[-1][2]=[1,3,6]
    assert torch.equal(out,model(changed));out.sum().backward()
    report['GAMENet']={'forward_backward':'passed','current_target_field_invariance':'passed','shape':list(out.shape)}
    molecules=json.loads((ROOT/'v27-molecules/atc4_molecules.json').read_text());classes=sorted(molecules)[:8]
    sample={c:[molecules[c][0]['smiles']] for c in classes}
    graphs,nfp,projection=core.buildMPNN(sample,dict(enumerate(classes)),device='cpu')
    assert len(graphs)==8 and np.allclose(projection.sum(1),1)
    # Identity substructure mask only tests the forward contract; full BRICS
    # resources must be built for all classes before a SafeDrug experiment.
    model=core.SafeDrugModel(sizes,ddi,np.eye(8,dtype=np.float32),graphs,nfp,projection,emb_dim=16,device=torch.device('cpu'));model.eval()
    out,ddi_loss=model(sequence);assert out.shape==(1,8) and torch.isfinite(out).all();(out.sum()+ddi_loss).backward()
    report['SafeDrug']={'forward_backward':'passed','shape':list(out.shape),'real_public_molecules':len(graphs),
       'substructure_mask':'Synthetic identity mask used ONLY for dependency probe; not a trained/evaluated method',
       'study_ready':False}
    paths=[ROOT/'ARMR2025/code/net_mynet.py',SAFE/'src/models.py',SAFE/'src/layers.py',SAFE/'src/util.py']
    report={'status':'complete','purpose':'Execution readiness, no clinical/patient performance measured','models':report,
      'source_sha256':{str(p):sha(p) for p in paths},'versions':{'torch':torch.__version__},'restricted_records_loaded':False}
    (HERE/'results/author_core_probe.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)

if __name__=='__main__':main()
