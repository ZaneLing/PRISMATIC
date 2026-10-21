"""Read the fresh audit only after all update streams have been frozen."""
import json,random,copy
from collections import Counter
import numpy as np
from common53 import *
from programs import *
from learn import load_development,templates
from clinical_checks import screen_case
from runtime import run_decoded
def summary(pred,cases):
    result=metrics(pred,cases)
    pairs=[joint_field_mismatch(p,c['gold']) for p,c in zip(pred,cases)]
    result['wrong_shared_tuples']=sum(x[0] for x in pairs)
    result['shared_reference_tuples']=sum(x[1] for x in pairs)
    result['joint_field_mismatch_rate']=sum(x[0] for x in pairs)/max(1,sum(x[1] for x in pairs))
    return result
def comparison(pred,base,cases,seed=5353):
    a=np.array([counts(p,c['gold']) for p,c in zip(pred,cases)],dtype=float)
    b=np.array([counts(p,c['gold']) for p,c in zip(base,cases)],dtype=float)
    d=a[:,:3]-b[:,:3];n=len(cases);rng=np.random.default_rng(seed)
    idx=rng.integers(0,n,(4000,n));boot=d[idx].mean(1)
    # 3 errors x 3 streams x 2 models x 2 template-bank designs; conservative family bound.
    upper=np.quantile(boot,1-.05/36,axis=0).tolist()
    aa=a[idx].sum(1);bb=b[idx].sum(1)
    fd=2*aa[:,3]/np.maximum(1,aa[:,4]+aa[:,5])-2*bb[:,3]/np.maximum(1,bb[:,4]+bb[:,5])
    return dict(error_delta=d.mean(0).tolist(),error_ci95=np.quantile(boot,[.025,.975],axis=0).T.tolist(),familywise_upper=upper,all_three_reliably_lower=all(x<0 for x in upper),drug_f1_delta_ci95=np.quantile(fd,[.025,.975]).tolist(),component_harmed_patients=int((d>0).any(1).sum()),omission_harmed_patients=int((d[:,0]>0).sum()),pareto_improved_patients=int(((d<=0).all(1)&(d<0).any(1)).sum()),changed_patients=sum(set(map(key,p))!=set(map(key,q)) for p,q in zip(pred,base)))
def replay(cases,base,seen,seenbase):
    """Nearest feedback correction, no induced condition/exception library.

    Same reflection templates (>=3 patients); nearest diagnosis-feature Jaccard,
    minimum0.5. Tie by fixed case hash. It can remove memorized extra identities,
    or add/replace a supported complete template. No query gold access.
    """
    palette={key(o) for o in templates(seen)};out=[]
    ff=[diagnosis_features(c) for c in seen]
    for c,p in zip(cases,base):
        f=diagnosis_features(c);rank=sorted(range(len(seen)),key=lambda i:(-len(f&ff[i])/max(1,len(f|ff[i])),seen[i]['case_id']))
        i=rank[0];sim=len(f&ff[i])/max(1,len(f|ff[i]));r=list(p)
        if sim>=.5:
            gold=seen[i]['gold'];gc={o['drug_code'] for o in gold};bc={o['drug_code'] for o in seenbase[i]}
            drop=bc-gc;r=[o for o in r if o['drug_code'] not in drop]
            for o in gold:
                if key(o) not in palette:continue
                r=[x for x in r if x['drug_code']!=o['drug_code']]+[o]
        out.append(uniq(r))
    return out
def main():
    lock=json.loads((PRIVATE/'learning_lock.json').read_text())
    assert not lock['audit_predictions_present']
    assert sha(HERE/'protocol.json')==lock['protocol']
    for name,h in lock['states'].items():assert sha(PRIVATE/name)==h
    cs=json.loads((PRIVATE/'audit.json').read_text());dev,db=load_development()
    states={str(s):json.loads((PRIVATE/(str(s)+'-states.json')).read_text()) for s in [53,153,253]}
    states['53-shuffled']=json.loads((PRIVATE/'53-shuffled-states.json').read_text())
    library_lock=json.loads((PRIVATE/'library_lock.json').read_text());assert not library_lock['audit_metrics_present']
    for name,h in library_lock['states'].items():
        assert sha(PRIVATE/'library'/name)==h
        states['library_'+name.replace('-states.json','')]=json.loads((PRIVATE/'library'/name).read_text())
    rows={};private={};trajectories={};decoding={}
    for model in ['qwen','llama']:
        rr=json.loads((PRIVATE/(model+'-audit.json')).read_text())
        assert len(rr)==len(cs)==256 and [r['case_id'] for r in rr]==[c['case_id'] for c in cs]
        base=[r['orders'] for r in rr];outputs={'fixed':base,'supervised_draft':[[c['catalogue'][i] for i in c['frozen_draft']] for c in cs], 'feedback_replay':replay(cs,base,dev['reflection'],db['reflection'])}
        outputs['contract_fallback']=[run_decoded(c,row,enable_fallback=True)['orders'] for c,row in zip(cs,rr)]
        decoding[model]=dict(cases=len(rr),syntax_failure=sum(x['syntax_failure'] for x in rr),any_unknown_ids=sum(x['invalid_ids']>0 for x in rr),empty_outputs=sum(not x['orders'] for x in rr),empty_with_nonempty_target=sum(not x['orders'] and bool(c['gold']) for x,c in zip(rr,cs)),output_cap_reached=sum(x['receipt']['output_tokens']>=256 for x in rr))
        trajectories[model]={}
        for stream,ss in states.items():
            seq=[]
            for roundno,state in enumerate(ss):
                pp=predict(cs,base,state)
                seq.append(dict(round=roundno,feedback=32*roundno,rules=len(state),exception_rules=sum(bool(s['unless']) for s in state),operations=dict(Counter(s['op'] for s in state)),metrics=summary(pp,cs)))
            outputs['rxrsi_'+stream]=predict(cs,base,ss[-1]);trajectories[model][stream]=seq
        old_templates=globals()['templates']
        library_keys={key(r['template']) for r in json.loads((PRIVATE/'training_joint_library.json').read_text())}
        globals()['templates']=lambda seen:[dict(zip(FIELDS,k)) for k in sorted({key(o) for c in seen for o in c['gold'] if all(o.get(f) for f in FIELDS)}&library_keys)]
        outputs['library_feedback_replay']=replay(cs,base,dev['reflection'],db['reflection'])
        globals()['templates']=old_templates
        outputs['unscoped_53']=predict(cs,base,states['53'][-1],True)
        rows[model]={}
        for name,pp in outputs.items():
            strata={}
            for multi in [False,True]:
                ix=[i for i,c in enumerate(cs) if (len(c['context']['categories'])>=2)==multi]
                strata['multiple_systems' if multi else 'one_system']=summary([pp[i] for i in ix],[cs[i] for i in ix])
            rows[model][name]=dict(metrics=summary(pp,cs),paired=comparison(pp,base,cs),strata=strata)
        private[model]=outputs
    # Reference ceilings and decomposition are computed only now.
    target=sum(len({o['drug_code'] for o in c['gold']}) for c in cs)
    reachable=sum(len({o['drug_code'] for o in c['gold']}&{o['drug_code'] for o in c['catalogue'].values()}) for c in cs)
    joint=sum(len({key(o) for o in c['gold'] if all(o.get(f) for f in FIELDS)}) for c in cs)
    reachablejoint=sum(len({key(o) for o in c['gold'] if all(o.get(f) for f in FIELDS)}&{key(o) for o in c['catalogue'].values()}) for c in cs)
    screenings=[r for c,p in zip(cs,private['qwen']['rxrsi_53']) for r in screen_case(c,p)]
    coverage=Counter(r['coverage'] for r in screenings);statuses=Counter(x['status'] for r in screenings for x in r['checks'])
    allpass=all(rows[m]['rxrsi_'+s]['paired']['all_three_reliably_lower'] for m in ['qwen','llama'] for s in ['53','153','253'])
    result=dict(protocol_sha256=sha(HERE/'protocol.json'),audit_cases=len(cs),metrics=rows,trajectories=trajectories,ceiling=dict(target_drugs=target,catalogue_target_drugs=reachable,target_complete_tuples=joint,catalogue_target_complete_tuples=reachablejoint),clinical_screening=dict(orders=len(screenings),coverage=dict(coverage),statuses=dict(statuses),clinical_annotations=0,overall_appropriateness_assessed=False),claim=dict(all_error_intervals_pass=allpass,clinical_review_complete=False,learned_empirical_exceptions=any(x['unless'] for ss in states.values() for x in ss[-1]),strong_hypothesis_supported=False,default_runtime_promotion=False),api_spend_usd=0)
    result['decoding']=decoding
    save(PRIVATE/'audit_outputs.json',private);save(HERE/'results/audit.json',result)
    usage=[json.loads(l) for l in (PRIVATE/'usage.jsonl').read_text().splitlines()]
    save(HERE/'results/compute.json',dict(new_calls=len(usage),input_tokens=sum(r['input_tokens'] for r in usage),output_tokens=sum(r['output_tokens'] for r in usage),amortized_batch_seconds=sum(r['seconds'] for r in usage),api_spend_usd=0,prior_current_budget_spend_usd=.085203,remaining_usd=9.914797,local_compute_priced=False))
    print(json.dumps({m:{n:{k:round(v,5) for k,v in r['metrics'].items() if k in ['drug_f1','joint_f1','missed_drugs_per_patient','extra_drugs_per_patient','joint_errors_per_patient']} for n,r in results.items()} for m,results in rows.items()},indent=2))
if __name__=='__main__':main()
