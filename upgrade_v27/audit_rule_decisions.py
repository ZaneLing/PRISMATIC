"""Recount completed rule rounds with scalar reductions independent of BLAS."""
import hashlib,json,math
from pathlib import Path
import joblib,numpy as np
from control_features import features
from method_runtime import flatten
HERE=Path(__file__).resolve().parent;PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v27'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def score(pred,target,people):
    scores={}
    for p,y,person in zip(pred,target,people):
        ps=set(np.flatnonzero(p));ys=set(np.flatnonzero(y));tp=len(ps&ys)
        f=2*tp/(len(ps)+len(ys)) if ps or ys else 1.;j=tp/len(ps|ys) if ps or ys else 1.
        scores.setdefault(person,[]).append((f,j))
    return {name:math.fsum(math.fsum(z[k] for z in values)/len(values) for values in scores.values())/len(scores) for k,name in enumerate(['patient_f1','patient_jaccard'])}
def apply(memory,x,prob,threshold):
    result=prob>=threshold
    for r in memory:
        present=x[:,r['feature_index']].toarray().ravel()!=0;p=prob[:,r['drug_index']]
        mask=present&(p>=threshold-.15)&(p<threshold) if r['action']=='include' else present&(p>=threshold)&(p<=threshold+.15)
        result[mask,r['drug_index']]=r['action']=='include'
    return result
def integer(value):return int(hashlib.sha256(value.encode()).hexdigest(),16)
def main():
    result={'status':'partial','panels':{},'warning_investigation':'Scalar math.fsum patient/visit recount, without BLAS dot products; warnings are not converted into failed model scores.'}
    for panel in ['full','molecular']:
        b=joblib.load(PRIVATE/(panel+'-models.joblib'));cases=flatten(b['data']['train']);x=features(cases,b['sizes']);people=np.array([c['subject_hash'] for c in cases]);ci={c:i for i,c in enumerate(b['medications'])}
        y=np.zeros((len(cases),b['sizes'][2]),dtype=bool)
        for i,c in enumerate(cases):y[i,[ci[a] for a in c['gold'] if a in ci]]=True
        result['panels'][panel]={}
        for seed in [42,137,2026]:
            folder=PRIVATE/f'{panel}-rsi-seed{seed}'
            if not (folder/'lock.json').exists():continue
            lock=json.loads((folder/'lock.json').read_text());assert sha(PRIVATE/(panel+'-models.joblib'))==lock['bundle_sha256']
            assert all(sha(HERE/f)==h for f,h in lock['sources'].items())
            states={};audits=[]
            for part in sorted(folder.glob('round*'),key=lambda p:int(p.name[5:])):
                if not (part/'complete.json').exists():continue
                row=json.loads((part/'complete.json').read_text());memories=json.loads((part/'memories.json').read_text());ix=np.load(part/'members.npy');p=np.load(part/'oof.npy')
                assert p.shape==(len(ix),len(ci)) and np.isfinite(p).all() and p.min()>=0 and p.max()<=1
                assert hashlib.sha256(json.dumps(ix.tolist(),sort_keys=True).encode()).hexdigest()==row['members_sha256']
                witness=np.array([integer(str(seed)+'|witness|'+s)%5==0 for s in people[ix]]);xx=x[ix[witness]];pp=p[witness];yy=y[ix[witness]];gg=people[ix[witness]];threshold=row['shared_policy_selection']['threshold']
                checked=accepted=0;maximum=0.
                for arm in row['arms']:
                    evidence=json.loads((part/(arm+'-evidence.json')).read_text());state=states.get(arm,[])
                    for item in evidence['edits']:
                        checked+=1;candidate=item['candidate']
                        proposal=[r for r in state if r['id']!=candidate['rule']['id']] if candidate['operation']=='DELETE' else (state+[candidate['rule']] if len(state)<20 and not any(r['id']==candidate['rule']['id'] for r in state) else list(state))
                        before=apply(state,xx,pp,threshold);after=apply(proposal,xx,pp,threshold);old=score(before,yy,gg);new=score(after,yy,gg)
                        for key,z in [('witness_before',old),('witness_after',new)]:
                            for metric,v in z.items():
                                recorded=item[key][metric];assert math.isfinite(recorded) and abs(recorded-v)<1e-12;maximum=max(maximum,abs(recorded-v))
                        changed=np.any(before!=after,axis=1);n=len(set(gg[changed]));assert n==item['affected_witness_patients']
                        # Use scalar deltas, with exact no-change equality handled
                        # explicitly, to detect floating-point gate sign changes.
                        f_delta=new['patient_f1']-old['patient_f1'];j_delta=new['patient_jaccard']-old['patient_jaccard']
                        decision=state!=proposal and (not item['gate_enabled'] or (n>=5 and f_delta>0 and j_delta>=0))
                        assert decision==item['accepted'],f'Gate mismatch: {panel} seed{seed} round{row["round"]} {arm}'
                        if decision:state=proposal;accepted+=1
                    assert state==memories[arm];states[arm]=state
                    for candidate in evidence['candidates']:assert np.isfinite(candidate['induction_jaccard_gain']) and candidate['induction_jaccard_gain']>0
                audits.append({'round':row['round'],'decisions':checked,'accepted':accepted,'max_scalar_vs_recorded_metric_delta':maximum,'finite_oof_probabilities':'passed','scalar_gate_and_memory_reconstruction':'passed'})
            result['panels'][panel][str(seed)]={'completed_rounds_audited':len(audits),'rounds':audits}
    if all(len(s)==3 and all(v['completed_rounds_audited']==5 for v in s.values()) for s in result['panels'].values()):result['status']='complete'
    result['scope']='Witness decision/memory arithmetic only. Independent cross-fitting/source/proposal and final prediction audits remain required before v27 test interpretation.'
    (HERE/'results/rule_decision_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)

if __name__=='__main__':main()
