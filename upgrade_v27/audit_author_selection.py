"""Reload the selected real author checkpoint and reproduce development scores."""
import argparse,hashlib,json
from pathlib import Path
import joblib,numpy as np,torch
from method_runtime import make_model,predict,flatten,prefix
from evaluation_metrics import score,compare
HERE=Path(__file__).resolve().parent;PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v27'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(panel,method,seed):
    file=HERE/f'results/{panel}-{method}-seed{seed}.json';z=json.loads(file.read_text());assert z['status']=='selection_frozen' and len(z['epochs'])==50
    lock=z['lock'];assert all(sha(HERE/f)==h for f,h in lock['source_sha256'].items())
    assert sha(HERE/'training_addendum.json')==lock['training_protocol_sha256']
    b=joblib.load(PRIVATE/(panel+'-models.joblib'));source=joblib.load(PRIVATE/'visits.joblib')
    assert sha(PRIVATE/(panel+'-models.joblib'))==lock['resource_bundle_sha256']
    folder=PRIVATE/f'{panel}-{method}-seed{seed}';assert sha(folder/'best.pt')==z['best_model_sha256']
    chosen=max(z['epochs'],key=lambda row:row['proposal']['metrics']['patient_jaccard'])
    assert chosen['epoch']==z['selection']['epoch'] and chosen['proposal']['threshold']==z['selection']['threshold']
    device=torch.device(lock['device']);torch.set_num_threads(1)
    model=make_model(method,b,device);state=torch.load(folder/'best.pt',map_location=device,weights_only=False)
    assert state['lock']==lock and state['selection']==z['selection'];model.load_state_dict(state['model'])
    vocab=source['vocab'];indexes={k:{s:i for i,s in enumerate(vocab[k])} for k in ['diagnoses','procedures']};mi={s:i for i,s in enumerate(b['medications'])};results={}
    for split in ['proposal','guard']:
        cases=flatten(b['data'][split]);gold=[];people=[];row=0
        for p in source['data'][split]:
            history=[]
            for visit in p['visits']:
                history.append([[indexes[k].get(s,len(indexes[k])) for s in visit[k]] for k in ['diagnoses','procedures']]+[[mi[s] for s in visit['medications'] if s in mi]])
                expected=[[list(c) for c in h] for h in history];expected[-1][2]=[]
                assert prefix(cases[row])==expected and cases[row]['case_id']==visit['case_id'] and cases[row]['subject_hash']==p['subject_hash']
                gold.append(set(visit['medications']) if panel=='full' else set(visit['medications'])&set(mi));people.append(p['subject_hash']);row+=1
        probability=predict(model,method,cases,b,device);t=z['selection']['threshold']
        if split=='proposal':
            options=[]
            for threshold in [.1,.2,.3,.4,.5,.6]:
                metrics,_,_=score(probability>=threshold,gold,people,b['medications'],b['ddi'],b['ddi_covered_indices']);options.append((threshold,metrics))
            winner=max(options,key=lambda item:item[1]['patient_jaccard']);assert winner[0]==t;compare(z['selection']['metrics'],winner[1])
        else:
            saved=np.load(folder/'guard_probabilities.npy');np.testing.assert_allclose(probability,saved,atol=1e-6,rtol=1e-5);assert np.array_equal(probability>=t,saved>=t)
            metrics,_,_=score(probability>=t,gold,people,b['medications'],b['ddi'],b['ddi_covered_indices']);compare(z['guard'],metrics)
        results[split]={'status':'passed','visits':len(gold),'patients':len(set(people)),'selected_metrics':metrics if split=='guard' else winner[1]}
    result={'status':'passed','panel':panel,'method':method,'seed':seed,'source_report_sha256':sha(file),'checkpoint_sha256':sha(folder/'best.pt'),
      'source_sha256':{f:sha(HERE/f) for f in ['audit_author_selection.py','evaluation_metrics.py']},'test_inference':False,'splits':results,
      'scope':'Raw-source input/target reconstruction; selected checkpoint reload and exact threshold decisions; independent development metrics. Historical epoch ranking uses retained logs, not a rerun of all historical checkpoints.'}
    (HERE/f'results/{panel}-{method}-selection-audit-seed{seed}.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':'passed','panel':panel,'method':method,'seed':seed}),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('panel',choices=['full','molecular']);p.add_argument('method',choices=['ARMR','GAMENet','SafeDrug']);p.add_argument('seed',type=int);a=p.parse_args();main(a.panel,a.method,a.seed)
