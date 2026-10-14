"""Train real author architectures; freeze development selection without testing."""
import argparse,hashlib,json,os,subprocess,sys,time
from pathlib import Path
import joblib,numpy as np,torch
from method_runtime import flatten,truths,make_model,predict,select,batches,loss_for,metrics
HERE=Path(__file__).resolve().parent;PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v27'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
    tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(x,indent=2)+'\n');tmp.replace(p)
def checkpoint(p,x):
    tmp=p.with_suffix('.tmp');torch.save(x,tmp);tmp.replace(p)
def main(panel,name,seed):
    protocol=json.loads((HERE/'training_addendum.json').read_text());resources=json.loads((HERE/'results/model_resource_manifest.json').read_text())
    assert seed in protocol['seeds'] and name in ['ARMR','GAMENet','SafeDrug'] and (name!='SafeDrug' or panel=='molecular')
    assert sha(PRIVATE/(panel+'-models.joblib'))==resources['panels'][panel]['bundle_sha256']
    probe=json.loads((HERE/'results/training_runtime_probe.json').read_text())
    assert probe['status']=='passed' and probe['runtime_sha256']==sha(HERE/'method_runtime.py')
    if name=='ARMR':
        while not (HERE.parent/'upgrade_v26/results/summary.json').exists():
            live=subprocess.check_output(['ps','-axo','command'],text=True)
            if not any('python -u upgrade_v26/run_diagnostic.py' in line for line in live.splitlines()):raise RuntimeError('Qwen diagnostic stopped before audit; GPU training stays gated.')
            time.sleep(30)
        assert torch.backends.mps.is_available(),'No silent device substitution; run equivalence audit before changing device.'
    device=torch.device('mps' if name=='ARMR' else 'cpu');torch.set_num_threads(1);torch.manual_seed(seed);rng=np.random.default_rng(seed)
    bundle=joblib.load(PRIVATE/(panel+'-models.joblib'));parts={s:flatten(bundle['data'][s]) for s in ['train','proposal','guard']}
    train=parts['train'];target=truths(train,bundle['medications']);folder=PRIVATE/f'{panel}-{name}-seed{seed}';folder.mkdir(exist_ok=True)
    out=HERE/f'results/{panel}-{name}-seed{seed}.json'
    lock={'training_protocol_sha256':sha(HERE/'training_addendum.json'),'implementation_notes_sha256':sha(HERE/'implementation_notes.json'),'runtime_probe_sha256':sha(HERE/'results/training_runtime_probe.json'),'resource_bundle_sha256':sha(PRIVATE/(panel+'-models.joblib')),
       'source_sha256':{f:sha(HERE/f) for f in ['train_author.py','method_runtime.py','author_cores.py']},'device':str(device),'seed':seed,'method':name,'panel':panel}
    if (folder/'execution_lock.json').exists():assert json.loads((folder/'execution_lock.json').read_text())==lock
    else:save(folder/'execution_lock.json',lock)
    model=make_model(name,bundle,device);options={'lr':.0002,'eps':1e-5,'weight_decay':1e-6} if name=='ARMR' else {'lr':.0005}
    optimizer=torch.optim.Adam(model.parameters(),**options);start_epoch=0;best=-1;rows=[];best_choice=None;steps=0
    if (folder/'last.pt').exists():
        state=torch.load(folder/'last.pt',map_location=device,weights_only=False);model.load_state_dict(state['model']);optimizer.load_state_dict(state['optimizer'])
        torch.set_rng_state(state['torch_rng'].cpu());rng.bit_generator.state=state['numpy_rng'];start_epoch=state['epoch'];best=state['best'];best_choice=state['best_choice'];rows=state['rows'];steps=state['steps']
        if device.type=='mps':torch.mps.set_rng_state(state['mps_rng'].cpu())
    save(out,{'status':'training','lock':lock,'epochs':rows,'parameters':sum(p.numel() for p in model.parameters()),'test_inference':False})
    print(json.dumps({'status':'training','panel':panel,'method':name,'seed':seed,'start_epoch':start_epoch}),flush=True)
    for epoch in range(start_epoch,50):
        model.train();start=time.perf_counter();loss_total=0.;order=batches(train,rng,32 if name=='ARMR' else 1)
        for batch_index,ix in enumerate(order):
            optimizer.zero_grad(set_to_none=True)
            loss=loss_for(model,name,[train[i] for i in ix],target[ix],bundle,device,.85*(.85**epoch),rng)
            assert torch.isfinite(loss);loss.backward();optimizer.step();loss_total+=float(loss.detach().cpu())*len(ix);steps+=1
            if (batch_index+1)%500==0:
                print(json.dumps({'epoch':epoch+1,'batches_complete':batch_index+1,'batches_total':len(order),'seconds':time.perf_counter()-start}),flush=True)
        training_seconds=time.perf_counter()-start;prob=predict(model,name,parts['proposal'],bundle,device);choice=select(prob,parts['proposal'],bundle)
        selected=choice['metrics']['patient_jaccard']>best
        if selected:
            best=choice['metrics']['patient_jaccard'];best_choice={'epoch':epoch+1,**choice}
            checkpoint(folder/'best.pt',{'model':model.state_dict(),'selection':best_choice,'lock':lock})
        row={'epoch':epoch+1,'train_loss':loss_total/len(train),'training_seconds':training_seconds,'cumulative_optimizer_steps':steps,
          'cumulative_visit_exposures':(epoch+1)*len(train),'proposal':choice,'checkpoint_selected':selected,'best_epoch':best_choice['epoch']}
        rows.append(row)
        state={'model':model.state_dict(),'optimizer':optimizer.state_dict(),'epoch':epoch+1,'best':best,'best_choice':best_choice,'rows':rows,'steps':steps,'torch_rng':torch.get_rng_state(),'numpy_rng':rng.bit_generator.state}
        if device.type=='mps':state['mps_rng']=torch.mps.get_rng_state()
        checkpoint(folder/'last.pt',state)
        save(out,{'status':'training','lock':lock,'epochs':rows,'parameters':sum(p.numel() for p in model.parameters()),'test_inference':False})
        print(json.dumps({'panel':panel,'method':name,'seed':seed,**row}),flush=True)
    state=torch.load(folder/'best.pt',map_location=device,weights_only=False);model.load_state_dict(state['model']);guard=predict(model,name,parts['guard'],bundle,device)
    np.save(folder/'guard_probabilities.npy',guard)
    save(out,{'status':'selection_frozen','lock':lock,'epochs':rows,'parameters':sum(p.numel() for p in model.parameters()),'selection':best_choice,
       'best_model_sha256':sha(folder/'best.pt'),'guard':metrics(guard,parts['guard'],bundle,best_choice['threshold']),'test_inference':False})
    print(json.dumps({'status':'selection_frozen','panel':panel,'method':name,'seed':seed,'selection':best_choice}),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('panel',choices=['full','molecular']);p.add_argument('method',choices=['ARMR','GAMENet','SafeDrug']);p.add_argument('seed',type=int);a=p.parse_args();main(a.panel,a.method,a.seed)
