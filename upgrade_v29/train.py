"""Five-round isolated-witness program-memory study; development evaluation only."""
import argparse,hashlib,json,os,sys,time
from pathlib import Path
import joblib,numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;V27=ROOT/'upgrade_v27'
sys.path.insert(0,str(V27))
from control_features import features
from method_runtime import flatten,truths,select,metrics
from train_rule_agent import fit,predict
from rule_memory import feature_labels
from programs import apply,calibrate,context,candidate,verify,digest
from proposer import propose
from partition import partitions
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v29';SOURCE=PRIVATE.parent/'prismatic-v27'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
    tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(x,indent=2)+'\n');tmp.replace(p)
def model_save(p,x):
    tmp=p.with_suffix('.tmp');joblib.dump(x,tmp,compress=3);tmp.replace(p)
def sources():
    paths=[HERE/f for f in ['train.py','programs.py','proposer.py','partition.py']]+[V27/f for f in ['control_features.py','method_runtime.py','train_rule_agent.py','rule_memory.py']]
    return {str(p.relative_to(ROOT)):sha(p) for p in paths}

def main(panel,seed):
    protocol=json.loads((HERE/'protocol.json').read_text());assert panel in protocol['panels'] and seed in protocol['seeds']
    os.environ['RXRSI_PUBLIC_COST_CAP_USD']=str(protocol['cumulative_successful_api_response_cap_usd'])
    probe=json.loads((HERE/'results/runtime_probe.json').read_text());assert probe['status']=='passed' and probe['source_sha256']==sources()
    path=SOURCE/(panel+'-models.joblib');resources=json.loads((V27/'results/model_resource_manifest.json').read_text());assert sha(path)==resources['panels'][panel]['bundle_sha256']
    b=joblib.load(path);source=joblib.load(SOURCE/'visits.joblib');folder=PRIVATE/f'{panel}-seed{seed}';folder.mkdir(parents=True,exist_ok=True);out=HERE/f'results/{panel}-seed{seed}.json'
    lock={'panel':panel,'seed':seed,'protocol_sha256':sha(HERE/'protocol.json'),'bundle_sha256':sha(path),'source_sha256':sources()}
    if (folder/'lock.json').exists():assert json.loads((folder/'lock.json').read_text())==lock
    else:save(folder/'lock.json',lock)
    if out.exists() and json.loads(out.read_text())['status']=='selection_frozen':return
    cases={s:flatten(b['data'][s]) for s in ['train','proposal','guard']};x={s:features(c,b['sizes']) for s,c in cases.items()};y=truths(cases['train'],b['medications'])
    people=np.array([c['subject_hash'] for c in cases['train']]);roles=partitions(people,seed);save(folder/'roles.json',roles)
    fit_set=set(roles['fit_patients']);witness_set=set(roles['witness_patients']);assert fit_set.isdisjoint(witness_set) and fit_set|witness_set==set(people)
    witness_seen=set();memories={a:[] for a in protocol['arms']};rounds=[];best={};labels=feature_labels(source['vocab'],b['medications'])
    save(out,{'status':'training','lock':lock,'rounds':[],'test_inference':False})
    for number,fraction in enumerate(protocol['rounds'],1):
        exposed=set(roles['fit_patients'][:int(np.ceil(len(fit_set)*fraction))]);witness=set(roles['witness_batches'][number-1]);assert not witness_seen&witness;witness_seen|=witness
        ix=np.flatnonzero(np.isin(people,list(exposed)));wi=np.flatnonzero(np.isin(people,list(witness)));assert set(people[ix]).isdisjoint(witness_set)
        part=folder/f'round{number}';part.mkdir(exist_ok=True)
        if (part/'complete.json').exists():
            row=json.loads((part/'complete.json').read_text());assert row['fit_members_sha256']==digest(ix.tolist()) and row['witness_members_sha256']==digest(wi.tolist())
            memories=json.loads((part/'memories.json').read_text());best=row['best'];rounds.append(row);continue
        start=time.perf_counter()
        if not (part/'fits.json').exists():
            options=[];best_score=-1;chosen=None;selected_prob=None
            for c in [.1,1.,10.]:
                f=part/f'C{c}.joblib'
                if f.exists():models=joblib.load(f)
                else:models=fit(x['train'][ix],y[ix],c,folder,f'round{number}-C{c}');model_save(f,models)
                prob=predict(models,x['proposal']);choice={'C':c,**select(prob,cases['proposal'],b)};options.append(choice)
                if choice['metrics']['patient_jaccard']>best_score:best_score=choice['metrics']['patient_jaccard'];chosen=choice;selected_prob=prob
            base_file=f"C{chosen['C']}.joblib";models=joblib.load(part/base_file);oof=np.zeros((len(ix),len(b['medications'])),dtype=float)
            folds=np.array([roles['folds'][p] for p in people[ix]])
            for f in range(3):
                kept=ix[folds!=f];held=np.flatnonzero(folds==f);model_path=part/f'fold{f}.joblib'
                assert set(people[kept]).isdisjoint(set(people[ix[held]])) and set(people[kept]).isdisjoint(witness_set)
                if model_path.exists():fold_model=joblib.load(model_path)
                else:fold_model=fit(x['train'][kept],y[kept],chosen['C'],folder,f'round{number}-fold{f}');model_save(model_path,fold_model)
                oof[held]=predict(fold_model,x['train'][ix[held]])
            np.save(part/'oof.npy',oof);np.save(part/'proposal.npy',selected_prob);np.save(part/'witness.npy',predict(models,x['train'][wi]));np.save(part/'fit_members.npy',ix);np.save(part/'witness_members.npy',wi)
            thresholds,calibration=calibrate(oof,y[ix],people[ix],chosen['threshold']);np.save(part/'thresholds.npy',thresholds)
            fits={'selection':chosen,'C_trials':options,'base_file':base_file,'calibration':calibration,
              'model_sha256':{p.name:sha(p) for p in sorted(part.glob('*.joblib'))},'policy_witness_patient_overlap':0,'crossfit_patient_overlap':0}
            save(part/'fits.json',fits)
        fits=json.loads((part/'fits.json').read_text());assert all(sha(part/f)==h for f,h in fits['model_sha256'].items())
        oof=np.load(part/'oof.npy');pval=np.load(part/'proposal.npy');wp=np.load(part/'witness.npy');ts=np.load(part/'thresholds.npy');raw=np.full(len(ts),fits['selection']['threshold'])
        reports={};own_ops=[];own_receipt={};own_support=[]
        for arm in protocol['arms']:
            previous=list(memories[arm]);receipt={'status':'no_proposal','model_calls':0};ops=[];eligible=[];unsupported=[];journal=[];payload={};trials={}
            if arm not in ['raw_policy','calibrated_policy']:
                arm_start=time.perf_counter()
                if arm=='matched_proposals_no_witness':
                    ops=own_ops;eligible=own_support;receipt={'status':'matched_proposals','model_calls':0,'own_response_sha256':digest(own_receipt)}
                else:
                    payload,pool,trials=context(previous,x['train'][ix],oof,ts,y[ix],people[ix],labels,b['medications'],expanded=arm in ['greedy_conditional_memory','random_conditional_memory'])
                    if arm=='greedy_conditional_memory':ops=[{'operation':z['operation'],'rule':z['rule']} for z in pool[:4]]
                    elif arm=='random_conditional_memory':
                        indices=np.random.default_rng(seed+number).choice(len(pool),min(4,len(pool)),replace=False);ops=[{'operation':pool[i]['operation'],'rule':pool[i]['rule']} for i in indices]
                    else:ops,receipt=propose(payload,seed,number,arm,protocol)
                    for index,op in enumerate(ops):
                        supported=candidate(op,previous,x['train'][ix],oof,ts,y[ix],people[ix])
                        if supported:eligible.append(supported)
                        else:unsupported.append({'index':index,'reason':'insufficient_actual_induction_support_or_gain','operation':op})
                    if arm=='own_error_program_agent':own_ops=ops;own_receipt=receipt;own_support=eligible
                memories[arm],journal=verify(previous,eligible,x['train'][wi],wp,ts,y[wi],people[wi],gate=arm!='matched_proposals_no_witness')
                proposal_seconds=time.perf_counter()-arm_start
            else:proposal_seconds=0.
            pred=apply(memories[arm],x['proposal'],pval,raw if arm=='raw_policy' else ts).astype(np.float32);m=metrics(pred,cases['proposal'],b,.5)
            if arm not in best or m['patient_jaccard']>best[arm]['proposal']['patient_jaccard']:best[arm]={'round':number,'proposal':m,'memory_sha256':digest(memories[arm])}
            save(part/(arm+'-evidence.json'),{'payload':payload,'search':trials,'receipt':receipt,'proposed_programs':ops,'eligible':eligible,'unsupported':unsupported,'edits':journal,'memory':memories[arm]})
            reports[arm]={'proposal':m,'memory_size':len(memories[arm]),'memory_sha256':digest(memories[arm]),'proposed_programs':len(ops),'eligible_programs':len(eligible),
              'accepted_edits':sum(z['accepted'] for z in journal),'accepted_operations':[z for z in journal if z['accepted']],
              'proposer_calls':receipt['model_calls'],'proposer_cost_usd':receipt.get('model_response',{}).get('cost_usd',0),'proposer_status':receipt['status'],
              'search':trials,'proposal_seconds':proposal_seconds,'best_round':best[arm]['round']}
            print(json.dumps({'panel':panel,'seed':seed,'round':number,'arm':arm,'proposal_f1':m['patient_f1'],'rules':len(memories[arm])}),flush=True)
        row={'round':number,'policy_fit_patients':len(exposed),'fresh_witness_patients':len(witness),'total_exposed_patients':len(exposed)+len(witness_seen),
          'fit_visits':len(ix),'witness_visits':len(wi),'fit_members_sha256':digest(ix.tolist()),'witness_members_sha256':digest(wi.tolist()),
          'model_sha256':fits['model_sha256'],'shared_selection':fits['selection'],'thresholds_sha256':sha(part/'thresholds.npy'),
          'calibrated_classes':int(np.sum(ts!=raw)),'arms':reports,'best':best,'elapsed_seconds':time.perf_counter()-start}
        save(part/'memories.json',memories);save(part/'complete.json',row);rounds.append(row);save(out,{'status':'training','lock':lock,'rounds':rounds,'test_inference':False})
    guards={}
    for arm,choice in best.items():
        part=folder/f"round{choice['round']}";fits=json.loads((part/'fits.json').read_text());models=joblib.load(part/fits['base_file']);prob=predict(models,x['guard']);memory=json.loads((part/'memories.json').read_text())[arm]
        thresholds=np.full(len(b['medications']),fits['selection']['threshold']) if arm=='raw_policy' else np.load(part/'thresholds.npy')
        pred=apply(memory,x['guard'],prob,thresholds).astype(np.float32);np.save(folder/(arm+'-guard.npy'),pred);guards[arm]=metrics(pred,cases['guard'],b,.5)
    save(out,{'status':'selection_frozen','lock':lock,'rounds':rounds,'selections':best,'guard':guards,'test_inference':False,
      'partition':{'policy_fit_patients':len(fit_set),'witness_patients':len(witness_set),'witness_batches':[len(z) for z in roles['witness_batches']],'any_policy_witness_patient_overlap':0}})
    print(json.dumps({'status':'selection_frozen','panel':panel,'seed':seed}),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('panel',choices=['full','molecular']);p.add_argument('seed',type=int);a=p.parse_args();main(a.panel,a.seed)
