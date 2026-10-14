"""A factorial of memory gates on immutable, independently audited base fits."""
import argparse,copy,hashlib,json,os,sys,time
from pathlib import Path
import joblib,numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;V29=ROOT/'upgrade_v29';V27=ROOT/'upgrade_v27'
sys.path[:0]=[str(ROOT),str(HERE),str(V29),str(V27)]
from upgrade_v27.control_features import features
from upgrade_v27.method_runtime import flatten,truths,metrics
from upgrade_v27.rule_memory import feature_labels
from upgrade_v29.programs import apply,context,candidate,verify,digest
from upgrade_v29.audit import probabilities
from gates import check,rebase,promote,split_witness
from proposer import propose
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v30';SOURCE=PRIVATE.parent/'prismatic-v29';COHORT=PRIVATE.parent/'prismatic-v27'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,z):
    p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(z,indent=2)+'\n');tmp.replace(p)
def sources():
    paths=[HERE/f for f in ['run.py','gates.py','proposer.py']]+[V29/f for f in ['programs.py','audit.py']]+[V27/f for f in ['control_features.py','method_runtime.py','rule_memory.py']]+[ROOT/'upgrade_v8/public_client.py']
    return {str(p.relative_to(ROOT)):sha(p) for p in paths}
def arms(protocol):
    return [('raw_policy',None,0,0),('calibrated_policy',None,0,0)]+[(f'{method}_C{c}P{p}',method,c,p) for method in protocol['factorial']['methods'] for c in [0,1] for p in [0,1]]
def main(panel,seed):
    protocol=json.loads((HERE/'protocol.json').read_text());assert panel in protocol['panels'] and seed in protocol['seeds']
    os.environ['RXRSI_PUBLIC_COST_CAP_USD']=str(protocol['cumulative_successful_api_response_cap_usd'])
    probe=json.loads((HERE/'results/runtime_probe.json').read_text());assert probe['status']=='passed' and probe['source_sha256']==sources()
    source_report=V29/f'results/{panel}-seed{seed}.json';source_audit=V29/f'results/{panel}-audit-seed{seed}.json'
    original=json.loads(source_report.read_text());audit=json.loads(source_audit.read_text())
    assert original['status']=='selection_frozen' and audit['status']=='passed' and audit['source_report_sha256']==sha(source_report) and audit['auditor_sha256']==sha(V29/'audit.py')
    assert all(sha(ROOT/f)==h for f,h in original['lock']['source_sha256'].items())
    bundle=COHORT/(panel+'-models.joblib');assert sha(bundle)==original['lock']['bundle_sha256']
    folder=PRIVATE/f'{panel}-seed{seed}';folder.mkdir(parents=True,exist_ok=True);out=HERE/f'results/{panel}-seed{seed}.json'
    lock={'panel':panel,'seed':seed,'protocol_sha256':sha(HERE/'protocol.json'),'source_sha256':sources(),'v29_report_sha256':sha(source_report),'v29_audit_sha256':sha(source_audit),'bundle_sha256':sha(bundle)}
    if (folder/'lock.json').exists():assert json.loads((folder/'lock.json').read_text())==lock
    else:save(folder/'lock.json',lock)
    if out.exists() and json.loads(out.read_text())['status']=='selection_frozen':return
    b=joblib.load(bundle);source=joblib.load(COHORT/'visits.joblib');cases={s:flatten(b['data'][s]) for s in ['train','proposal','guard']}
    x={s:features(z,b['sizes']) for s,z in cases.items()};y=truths(cases['train'],b['medications']);people=np.array([z['subject_hash'] for z in cases['train']]);labels=feature_labels(source['vocab'],b['medications'])
    configurations=arms(protocol);memories={a:[] for a,_,_,_ in configurations};best={};rounds=[];all_seen=set();roles={}
    for r in range(1,6):
        src=SOURCE/f'{panel}-seed{seed}/round{r}';part=folder/f'round{r}';part.mkdir(exist_ok=True)
        ix=np.load(src/'fit_members.npy');wi=np.load(src/'witness_members.npy');ai,bi=split_witness(people[wi],seed,r);aidx=wi[ai];bidx=wi[bi]
        assert not set(people[wi])&set(people[ix]) and not all_seen&set(people[wi]);all_seen|=set(people[wi])
        roles[str(r)]={'edit_patients':sorted(set(people[aidx])),'confirmation_patients':sorted(set(people[bidx]))};save(folder/'witness_roles.json',roles)
        if (part/'complete.json').exists():
            row=json.loads((part/'complete.json').read_text());assert row['source_round_sha256']==sha(src/'complete.json')
            memories=json.loads((part/'memories.json').read_text());best=copy.deepcopy(row['best']);rounds.append(row);continue
        start=time.perf_counter();fits=json.loads((src/'fits.json').read_text());assert all(sha(src/f)==v for f,v in fits['model_sha256'].items())
        oof=np.load(src/'oof.npy');pval=np.load(src/'proposal.npy');wp=np.load(src/'witness.npy');ts=np.load(src/'thresholds.npy');raw=np.full(len(ts),fits['selection']['threshold'])
        reports={};contexts={}
        for arm,method,c,p in configurations:
            before=list(memories[arm]);receipt={'status':'no_proposal','model_calls':0};payload={};trials={};ops=[];eligible=[];unsupported=[];edits=[];compat={};confirm={};started=time.perf_counter();cached_context=False
            if method is not None:
                fit_check=check(before,x['train'][ix],oof,ts,y[ix],people[ix]);edit_check=check(before,x['train'][aidx],wp[ai],ts,y[aidx],people[aidx])
                basis=rebase(before,fit_check,edit_check,c);compat={'enabled':bool(c),'fit':fit_check,'edit':edit_check,'reset':bool(before and not basis),'starting_memory_sha256':digest(basis)}
                context_key=digest([basis,method=='greedy'])
                if context_key not in contexts:contexts[context_key]=context(basis,x['train'][ix],oof,ts,y[ix],people[ix],labels,b['medications'],expanded=method=='greedy')
                else:cached_context=True
                payload,pool,trials=contexts[context_key]
                if method=='greedy':ops=[{'operation':z['operation'],'rule':z['rule']} for z in pool[:4]]
                else:ops,receipt=propose(payload,seed,r,method,protocol)
                for index,op in enumerate(ops):
                    supported=candidate(op,basis,x['train'][ix],oof,ts,y[ix],people[ix])
                    if supported:eligible.append(supported)
                    else:unsupported.append({'index':index,'operation':op,'reason':'insufficient_actual_induction_support_or_gain'})
                edited,edits=verify(basis,eligible,x['train'][aidx],wp[ai],ts,y[aidx],people[aidx])
                confirmation=check(edited,x['train'][bidx],wp[bi],ts,y[bidx],people[bidx]);memories[arm]=promote(edited,confirmation,p)
                confirm={'enabled':bool(p),'check':confirmation,'candidate_memory_sha256':digest(edited),'reset':bool(edited and not memories[arm])}
            else:basis=[];edited=[]
            pred=apply(memories[arm],x['proposal'],pval,raw if arm=='raw_policy' else ts).astype(np.float32);m=metrics(pred,cases['proposal'],b,.5)
            if arm not in best or m['patient_jaccard']>best[arm]['proposal']['patient_jaccard']:best[arm]={'round':r,'proposal':m,'memory_sha256':digest(memories[arm])}
            evidence={'previous_memory':before,'compatibility':compat,'basis':basis,'payload':payload,'search':trials,'context_reused':cached_context,'receipt':receipt,'proposed_programs':ops,'eligible':eligible,'unsupported':unsupported,'edits':edits,'candidate_memory':edited,'confirmation':confirm,'memory':memories[arm]}
            save(part/(arm+'-evidence.json'),evidence)
            reports[arm]={'proposal':m,'memory_size':len(memories[arm]),'retained_conjunctions':sum(len(z['conditions'])==2 for z in memories[arm]),'memory_sha256':digest(memories[arm]),'compatibility_reset':compat.get('reset',False),'confirmation_reset':confirm.get('reset',False),'proposed_programs':len(ops),'eligible_programs':len(eligible),'accepted_edits_before_confirmation':sum(z['accepted'] for z in edits),'proposer_calls':receipt['model_calls'],'proposer_cost_usd':receipt.get('model_response',{}).get('cost_usd',0),'request_sha256':receipt.get('model_response',{}).get('request_sha256'),'search':trials,'context_reused':cached_context,'seconds':time.perf_counter()-started,'best_round':best[arm]['round']}
            print(json.dumps({'panel':panel,'seed':seed,'round':r,'arm':arm,'proposal_f1':m['patient_f1'],'rules':len(memories[arm]),'C_reset':compat.get('reset',False),'P_reset':confirm.get('reset',False)}),flush=True)
        row={'round':r,'fit_patients':len(set(people[ix])),'edit_patients':len(set(people[aidx])),'confirmation_patients':len(set(people[bidx])),'source_round_sha256':sha(src/'complete.json'),'fit_members_sha256':digest(ix.tolist()),'edit_members_sha256':digest(aidx.tolist()),'confirmation_members_sha256':digest(bidx.tolist()),'arms':reports,'best':copy.deepcopy(best),'elapsed_seconds':time.perf_counter()-start}
        save(part/'memories.json',memories);save(part/'complete.json',row);rounds.append(row);save(out,{'status':'training','lock':lock,'rounds':rounds,'test_inference':False})
    guards={};final_guards={};cache={}
    for arm,_,_,_ in configurations:
        for label,number,target in [('selected',best[arm]['round'],guards),('final',5,final_guards)]:
            src=SOURCE/f'{panel}-seed{seed}/round{number}';fits=json.loads((src/'fits.json').read_text())
            if number not in cache:cache[number]=probabilities(joblib.load(src/fits['base_file']),x['guard'])
            memory=json.loads((folder/f'round{number}/memories.json').read_text())[arm]
            threshold=np.full(len(b['medications']),fits['selection']['threshold']) if arm=='raw_policy' else np.load(src/'thresholds.npy')
            pred=apply(memory,x['guard'],cache[number],threshold).astype(np.float32);np.save(folder/f'{arm}-{label}-guard.npy',pred);target[arm]=metrics(pred,cases['guard'],b,.5)
    save(out,{'status':'selection_frozen','lock':lock,'rounds':rounds,'selections':best,'guard':guards,'final_guard':final_guards,'test_inference':False})
    print(json.dumps({'status':'selection_frozen','panel':panel,'seed':seed}),flush=True)
if __name__=='__main__':
    q=argparse.ArgumentParser();q.add_argument('panel',choices=['full','molecular']);q.add_argument('seed',type=int);a=q.parse_args();main(a.panel,a.seed)
