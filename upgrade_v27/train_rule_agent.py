"""Matched case-growth policy fits and executable rule-memory evolution."""
import argparse,hashlib,json,os,time,warnings
from pathlib import Path
import joblib,numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.exceptions import ConvergenceWarning
from control_features import features
from method_runtime import flatten,truths,select,metrics
from rule_memory import apply,induce,verify_edits,feature_labels,digest
from rule_proposer import propose
HERE=Path(__file__).resolve().parent;PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v27'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
    tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(x,indent=2)+'\n');tmp.replace(p)
def atomic_model(p,x):
    tmp=p.with_suffix('.tmp');joblib.dump(x,tmp);tmp.replace(p)
def predict(models,x):return np.column_stack([np.full(x.shape[0],m) if isinstance(m,float) else m.predict_proba(x)[:,1] for m in models])
def fit(x,y,c,folder,label):
    start=time.perf_counter();models=[];iterations=[]
    for j in range(y.shape[1]):
        target=y[:,j]
        if target.min()==target.max():models.append(float(target.mean()));iterations.append(0);continue
        model=LogisticRegression(C=c,solver='liblinear',max_iter=1000,tol=.0001,random_state=42)
        with warnings.catch_warnings():
            warnings.simplefilter('error',ConvergenceWarning);model.fit(x,target)
        models.append(model);iterations.append(int(model.n_iter_.max()))
    event={'fit':label,'visits':x.shape[0],'C':c,'seconds':time.perf_counter()-start,'max_class_iterations':max(iterations),'convergence_warnings':0}
    with (folder/'fit_events.jsonl').open('a') as stream:stream.write(json.dumps(event)+'\n')
    print(json.dumps(event),flush=True);return models
def integer_hash(value):return int(hashlib.sha256(value.encode()).hexdigest(),16)

def main(panel,seed):
    protocol=json.loads((HERE/'rsi_addendum.json').read_text());assert panel in protocol['panels'] and seed in protocol['seeds']
    os.environ['RXRSI_PUBLIC_COST_CAP_USD']=str(protocol['cumulative_successful_api_response_cap_usd'])
    resources=json.loads((HERE/'results/model_resource_manifest.json').read_text());bundle_path=PRIVATE/(panel+'-models.joblib')
    assert sha(bundle_path)==resources['panels'][panel]['bundle_sha256'];b=joblib.load(bundle_path);source=joblib.load(PRIVATE/'visits.joblib')
    lock={'protocol_sha256':sha(HERE/'rsi_addendum.json'),'bundle_sha256':sha(bundle_path),'seed':seed,'panel':panel,
      'sources':{f:sha(HERE/f) for f in ['train_rule_agent.py','rule_memory.py','rule_proposer.py','control_features.py','method_runtime.py']}}
    probe=json.loads((HERE/'results/rsi_runtime_probe.json').read_text());assert probe['status']=='passed'
    assert all(sha(HERE/f)==value for f,value in probe['source_sha256'].items())
    folder=PRIVATE/f'{panel}-rsi-seed{seed}';folder.mkdir(exist_ok=True);out=HERE/f'results/{panel}-rsi-seed{seed}.json'
    if (folder/'lock.json').exists():assert json.loads((folder/'lock.json').read_text())==lock
    else:save(folder/'lock.json',lock)
    if out.exists():
        old=json.loads(out.read_text());assert old['lock']==lock
        if old['status']=='selection_frozen':return
    else:save(out,{'status':'training','lock':lock,'rounds':[],'test_inference':False})
    cases={s:flatten(b['data'][s]) for s in ['train','proposal','guard']};x={s:features(c,b['sizes']) for s,c in cases.items()};target=truths(cases['train'],b['medications'])
    people=np.array([c['subject_hash'] for c in cases['train']]);unique=sorted(set(people),key=lambda s:integer_hash(str(seed)+'|order|'+s));labels=feature_labels(source['vocab'],b['medications'])
    assert len(labels)==x['train'].shape[1]
    folds=np.array([integer_hash(str(seed)+'|fold|'+s)%3 for s in people]);witness=np.array([integer_hash(str(seed)+'|witness|'+s)%5==0 for s in people])
    memories={a:[] for a in protocol['arms']};rounds=[];best={}
    for round_number,fraction in enumerate(protocol['rounds'],1):
        seen=set(unique[:int(np.ceil(len(unique)*fraction))]);ix=np.flatnonzero(np.isin(people,list(seen)));part=folder/f'round{round_number}';part.mkdir(exist_ok=True)
        if (part/'complete.json').exists():
            row=json.loads((part/'complete.json').read_text());assert row['members_sha256']==digest(ix.tolist());memories=json.loads((part/'memories.json').read_text());best=row['best'];rounds.append(row);continue
        start=time.perf_counter()
        if not (part/'fits_complete.json').exists():
            choices=[];best_score=-1;models=None;chosen=None;proposal_prob=None
            for c in [.1,1.,10.]:
                path=part/f'C{c}.joblib'
                if path.exists():model=joblib.load(path)
                else:model=fit(x['train'][ix],target[ix],c,folder,f'round{round_number}-C{c}');atomic_model(path,model)
                probability=predict(model,x['proposal']);choice={'C':c,**select(probability,cases['proposal'],b)};choices.append(choice)
                if choice['metrics']['patient_jaccard']>best_score:best_score=choice['metrics']['patient_jaccard'];models=model;chosen=choice;proposal_prob=probability
            atomic_model(part/'base.joblib',models);np.save(part/'proposal.npy',proposal_prob)
            oof=np.zeros((len(ix),b['sizes'][2]),dtype=np.float64)
            for fold in range(3):
                fit_ix=ix[folds[ix]!=fold];test_ix=np.flatnonzero(folds[ix]==fold);fold_path=part/f'oof{fold}.npy'
                assert set(people[fit_ix]).isdisjoint(set(people[ix[test_ix]]))
                if fold_path.exists():prob=np.load(fold_path)
                else:
                    model=fit(x['train'][fit_ix],target[fit_ix],chosen['C'],folder,f'round{round_number}-fold{fold}');prob=predict(model,x['train'][ix[test_ix]]);np.save(fold_path,prob)
                assert prob.shape==(len(test_ix),b['sizes'][2]);oof[test_ix]=prob
            np.save(part/'oof.npy',oof);np.save(part/'members.npy',ix)
            save(part/'fits_complete.json',{'selection':chosen,'C_trials':choices,'crossfit_patient_overlap':0,'members_sha256':digest(ix.tolist()),'base_sha256':sha(part/'base.joblib')})
        fits=json.loads((part/'fits_complete.json').read_text());assert fits['members_sha256']==digest(ix.tolist())
        oof=np.load(part/'oof.npy');pval=np.load(part/'proposal.npy');threshold=fits['selection']['threshold'];induction=~witness[ix];check=witness[ix]
        assert len(np.unique(people[ix[check]]))>=5 and len(np.unique(people[ix[induction]]))>=20
        arm_reports={};own_candidates=[];own_edits=[]
        for arm in protocol['arms']:
            previous=list(memories[arm]);receipt={'status':'no_proposal','model_calls':0};candidates=[];selected=[];journal=[]
            if arm!='uniform_policy':
                if arm=='matched_proposals_without_witness_gate':candidates=own_candidates;selected=own_edits
                else:
                    candidates=induce(previous,x['train'][ix[induction]],oof[induction],target[ix[induction]],people[ix[induction]],threshold,labels,b['medications'])
                    if arm=='greedy_error_rules':selected=[c['id'] for c in candidates[:4]]
                    elif arm=='random_candidate_rules':
                        rng=np.random.default_rng(seed+round_number);selected=[candidates[i]['id'] for i in rng.choice(len(candidates),min(4,len(candidates)),replace=False)]
                    else:selected,receipt=propose(candidates,previous,seed,round_number,arm,protocol)
                    if arm=='own_error_rule_agent':own_candidates=candidates;own_edits=selected
                memories[arm],journal=verify_edits(previous,candidates,selected,x['train'][ix[check]],oof[check],target[ix[check]],people[ix[check]],threshold,gate=arm!='matched_proposals_without_witness_gate')
            proposed=apply(memories[arm],x['proposal'],pval,threshold).astype(np.float32);m=metrics(proposed,cases['proposal'],b,.5)
            if arm not in best or m['patient_jaccard']>best[arm]['proposal']['patient_jaccard']:
                best[arm]={'round':round_number,'proposal':m,'threshold':threshold,'memory_sha256':digest(memories[arm])}
            save(part/(arm+'-evidence.json'),{'candidates':candidates,'selected':selected,'receipt':receipt,'edits':journal,'memory':memories[arm]})
            arm_reports[arm]={'proposal':m,'candidates':len(candidates),'proposed_edits':len(selected),'accepted_edits':sum(z['accepted'] for z in journal),
               'memory_size':len(memories[arm]),'memory_sha256':digest(memories[arm]),'proposal_status':receipt['status'],'proposer_calls':receipt['model_calls'],
               'proposer_cost_usd':receipt.get('model_response',{}).get('cost_usd',0),'best_round':best[arm]['round'],
               'accepted_operations':[{'operation':z['candidate']['operation'],'rule':z['candidate']['rule'],'witness_before':z['witness_before'],'witness_after':z['witness_after']} for z in journal if z['accepted']]}
            print(json.dumps({'round':round_number,'panel':panel,'seed':seed,'arm':arm,'proposal_f1':m['patient_f1'],'rules':len(memories[arm])}),flush=True)
        row={'round':round_number,'training_patients':len(seen),'training_visits':len(ix),'members_sha256':digest(ix.tolist()),'base_model_sha256':fits['base_sha256'],
          'shared_policy_selection':fits['selection'],'arms':arm_reports,'best':best,'elapsed_this_attempt_seconds':time.perf_counter()-start}
        save(part/'memories.json',memories);save(part/'complete.json',row);rounds.append(row)
        save(out,{'status':'training','lock':lock,'rounds':rounds,'test_inference':False})
    guards={}
    for arm,choice in best.items():
        part=folder/f"round{choice['round']}";model=joblib.load(part/'base.joblib');p=predict(model,x['guard']);memory=json.loads((part/'memories.json').read_text())[arm]
        assert digest(memory)==choice['memory_sha256'];pred=apply(memory,x['guard'],p,choice['threshold']).astype(np.float32)
        np.save(folder/(arm+'-guard.npy'),pred);guards[arm]=metrics(pred,cases['guard'],b,.5)
    fit_events=[json.loads(line) for line in (folder/'fit_events.jsonl').read_text().splitlines()]
    save(out,{'status':'selection_frozen','lock':lock,'rounds':rounds,'selections':best,'guard':guards,'fit_events':fit_events,'test_inference':False})
    print(json.dumps({'status':'selection_frozen','panel':panel,'seed':seed}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('panel',choices=['full','molecular']);p.add_argument('seed',type=int);a=p.parse_args();main(a.panel,a.seed)
