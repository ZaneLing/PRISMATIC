"""Reconstruct isolated witnesses, original models and executed rule effects.

No training helper or rule-runtime implementation is used to reproduce fits,
rule application, calibration gains or witness decisions. Full enumerated
candidate-pool ranking is not independently rerun; selected effects are.
"""
import argparse,hashlib,json,math,sys,warnings
from pathlib import Path
import joblib,numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.exceptions import ConvergenceWarning
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;sys.path.insert(0,str(ROOT/'upgrade_v27'))
from audit_controls import reconstruct
from evaluation_metrics import score,compare
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v29';SOURCE=PRIVATE.parent/'prismatic-v27'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()
def h(s):return int(hashlib.sha256(s.encode()).hexdigest(),16)
def save(p,x):
    t=p.with_suffix('.tmp');t.write_text(json.dumps(x,indent=2)+'\n');t.replace(p)
def probabilities(models,x):return np.column_stack([np.full(x.shape[0],m) if isinstance(m,float) else m.predict_proba(x)[:,1] for m in models])
def execute(memory,x,prob,thresholds):
    prediction=prob>=thresholds
    for r in memory:
        base={k:r[k] for k in ['drug_index','conditions','action']};assert r['id']==digest(base)[:20]
        assert len(r['conditions']) in [1,2] and any(c['present'] for c in r['conditions'])
        mask=np.ones(x.shape[0],dtype=bool)
        for c in r['conditions']:
            values=np.asarray(x[:,c['feature_index']].todense()).ravel();mask&=(values>0) if c['present'] else (values<=0)
        d=r['drug_index'];p=prob[:,d];t=thresholds[d]
        mask&=((p>=t-.15)&(p<t)) if r['action']=='include' else ((p>=t)&(p<=t+.15))
        prediction[mask,d]=r['action']=='include'
    return prediction
def change(memory,op):
    if op['operation']=='DELETE':return [r for r in memory if r['id']!=op['rule']['id']]
    return memory+[op['rule']] if len(memory)<20 and all(r['id']!=op['rule']['id'] for r in memory) else list(memory)
def agreement(pred,y,people):
    groups={}
    for p,t,person in zip(pred,y,people):
        ps=set(np.flatnonzero(p));ts=set(np.flatnonzero(t));intersection=len(ps&ts)
        groups.setdefault(person,[]).append((2*intersection/(len(ps)+len(ts)) if ps or ts else 1.,intersection/len(ps|ts) if ps or ts else 1.))
    return {name:math.fsum(math.fsum(z[i] for z in rows)/len(rows) for rows in groups.values())/len(groups) for i,name in enumerate(['patient_f1','patient_jaccard'])}
def reproduce(models,x,y,c):
    delta=0.
    for index,original in enumerate(models):
        target=y[:,index]
        if np.unique(target).size==1:assert isinstance(original,float) and original==target[0];continue
        model=LogisticRegression(C=c,solver='liblinear',max_iter=1000,tol=.0001,random_state=42)
        with warnings.catch_warnings():warnings.simplefilter('error',ConvergenceWarning);model.fit(x,target)
        for key in ['coef_','intercept_']:
            a=getattr(model,key);b=getattr(original,key);np.testing.assert_allclose(a,b,atol=1e-12,rtol=1e-12);delta=max(delta,float(np.max(np.abs(a-b))))
    return delta

def main(panel,seed):
    path=HERE/f'results/{panel}-seed{seed}.json';z=json.loads(path.read_text());assert z['status']=='selection_frozen';lock=z['lock']
    assert sha(HERE/'protocol.json')==lock['protocol_sha256'] and all(sha(ROOT/f)==v for f,v in lock['source_sha256'].items())
    folder=PRIVATE/f'{panel}-seed{seed}';cache=folder/'independent_audit';cache.mkdir(exist_ok=True)
    b=joblib.load(SOURCE/(panel+'-models.joblib'));assert sha(SOURCE/(panel+'-models.joblib'))==lock['bundle_sha256'];source=joblib.load(SOURCE/'visits.joblib');meds=b['medications']
    assert sha(SOURCE/'visits.joblib')==json.loads((ROOT/'upgrade_v27/results/cohort_manifest.json').read_text())['bundle_sha256']
    data={}
    for split in ['train','proposal','guard']:
        x,gold,_,people,_=reconstruct(source['data'][split],source['vocab'],meds)
        if panel=='molecular':gold=[g&set(meds) for g in gold]
        data[split]=(x,gold,people)
    x,gold,people=data['train'];y=np.array([[m in g for m in meds] for g in gold],dtype=np.float32)
    ranked=sorted(set(people),key=lambda p:h(f'v29|{seed}|role|{p}'));n=int(np.floor(.8*len(ranked)));fit=sorted(ranked[:n],key=lambda p:h(f'v29|{seed}|fit-order|{p}'));witness=sorted(ranked[n:],key=lambda p:h(f'v29|{seed}|witness-order|{p}'));batches=[list(a) for a in np.array_split(witness,5)]
    roles=json.loads((folder/'roles.json').read_text());assert fit==roles['fit_patients'] and witness==roles['witness_patients'] and batches==roles['witness_batches']
    assert set(fit).isdisjoint(witness);states={};best={};rounds=[];seen=set()
    for row in z['rounds']:
        r=row['round'];part=folder/f'round{r}';receipt=cache/f'round{r}.json';immutable=json.loads((part/'complete.json').read_text())
        ix=np.load(part/'fit_members.npy');wi=np.load(part/'witness_members.npy');expected=set(fit[:int(np.ceil(len(fit)*r/5))]);wb=set(batches[r-1])
        assert np.array_equal(ix,np.flatnonzero(np.isin(people,list(expected)))) and np.array_equal(wi,np.flatnonzero(np.isin(people,list(wb))))
        assert not set(people[ix])&set(witness) and not seen&wb;seen|=wb
        assert digest(ix.tolist())==row['fit_members_sha256'] and digest(wi.tolist())==row['witness_members_sha256']
        fits=json.loads((part/'fits.json').read_text());assert all(sha(part/f)==v for f,v in fits['model_sha256'].items())
        choice=max(fits['C_trials'],key=lambda v:v['metrics']['patient_jaccard']);assert choice==fits['selection']
        oof=np.load(part/'oof.npy');wp=np.load(part/'witness.npy');ts=np.load(part/'thresholds.npy');pval=np.load(part/'proposal.npy');memories=json.loads((part/'memories.json').read_text())
        if receipt.exists():
            cached=json.loads(receipt.read_text());assert cached['round_source_sha256']==sha(part/'complete.json') and cached['auditor_sha256']==sha(Path(__file__))
            rounds.append(cached);states=memories
            for arm,a in row['arms'].items():
                if arm not in best or a['proposal']['patient_jaccard']>best[arm][1]:best[arm]=(r,a['proposal']['patient_jaccard'])
            continue
        model=joblib.load(part/fits['base_file']);delta=reproduce(model,x[ix],y[ix],fits['selection']['C'])
        np.testing.assert_allclose(probabilities(model,x[wi]),wp,atol=1e-12,rtol=1e-12);np.testing.assert_allclose(probabilities(model,data['proposal'][0]),pval,atol=1e-12,rtol=1e-12)
        folds=np.array([h(f'v29|{seed}|fold|{p}')%3 for p in people[ix]])
        for fold in range(3):
            kept=ix[folds!=fold];held=np.flatnonzero(folds==fold);models=joblib.load(part/f'fold{fold}.joblib');assert set(people[kept]).isdisjoint(people[ix[held]])
            delta=max(delta,reproduce(models,x[kept],y[kept],fits['selection']['C']));np.testing.assert_allclose(probabilities(models,x[ix[held]]),oof[held],atol=1e-12,rtol=1e-12)
        # Recount every recorded coordinate edit using a separate set scorer.
        thresholds=np.full(len(meds),fits['selection']['threshold']);current=oof>=thresholds;old=agreement(current,y[ix],people[ix]);cal_delta=0.
        for event in fits['calibration']:
            d=event['drug_index'];assert thresholds[d]==event['old_threshold'];thresholds[d]=event['new_threshold'];current[:,d]=oof[:,d]>=thresholds[d]
            new=agreement(current,y[ix],people[ix]);gain=new['patient_jaccard']-old['patient_jaccard'];assert gain>0 and abs(gain-event['induction_jaccard_gain'])<1e-12
            cal_delta=max(cal_delta,abs(gain-event['induction_jaccard_gain']));old=new
        np.testing.assert_array_equal(thresholds,ts);assert sha(part/'thresholds.npy')==row['thresholds_sha256']
        arm_rows={};own_previous=None;own_evidence=None
        for arm,a in row['arms'].items():
            previous=states.get(arm,[]);evidence=json.loads((part/(arm+'-evidence.json')).read_text());receipt_data=evidence['receipt'];decision_count=0;max_gain=0.
            basis=own_previous if arm=='matched_proposals_no_witness' else previous
            before=execute(basis,x[ix],oof,ts);baseline=agreement(before,y[ix],people[ix])
            for op in evidence['eligible']:
                after=execute(change(basis,op),x[ix],oof,ts);changed=np.any(before!=after,axis=1);new=agreement(after,y[ix],people[ix]);gain=new['patient_jaccard']-baseline['patient_jaccard']
                assert int(changed.sum())==op['affected_visits'] and len(set(people[ix][changed]))==op['affected_patients'] and gain>1e-12
                assert abs(gain-op['induction_jaccard_gain'])<1e-12;max_gain=max(max_gain,abs(gain-op['induction_jaccard_gain']))
            if arm=='matched_proposals_no_witness':assert evidence['proposed_programs']==own_evidence['proposed_programs'] and evidence['eligible']==own_evidence['eligible']
            if arm in ['own_error_program_agent','shuffled_evidence_program_agent']:
                shown=receipt_data['aggregate_payload'];assert set(shown)=={'allowed_features','focus_drugs','single_predicate_evidence','retained_rules','round'} and shown['round']==r
                assert hashlib.sha256(json.dumps(shown,sort_keys=True,ensure_ascii=False).encode()).hexdigest()==receipt_data['aggregate_prompt_sha256']
                assert shown['retained_rules']==previous and shown['allowed_features']==evidence['payload']['allowed_features'] and shown['focus_drugs']==evidence['payload']['focus_drugs']
                assert all(c['affected_visits']>=30 and c['affected_patients']>=20 for c in shown['single_predicate_evidence'])
                expected=list(evidence['payload']['single_predicate_evidence'])
                if arm=='shuffled_evidence_program_agent':
                    original=[dict(q) for q in expected];order=np.random.default_rng(seed+1000*r).permutation(len(expected));expected=[dict(q) for q in expected]
                    for i,j in enumerate(order):
                        for k in ['induction_jaccard_gain','affected_visits','affected_patients']:expected[i][k]=original[j][k]
                assert shown['single_predicate_evidence']==expected
                for op in evidence['proposed_programs']:
                    if op['operation']=='ADD':
                        assert op['rule']['drug_index'] in {d['drug_index'] for d in shown['focus_drugs']}
                        assert all(c['feature_index'] in {f['feature_index'] for f in shown['allowed_features']} for c in op['rule']['conditions'])
            state=list(previous)
            for edit in evidence['edits']:
                op=edit['operation'];alternative=change(state,op);a0=execute(state,x[wi],wp,ts);a1=execute(alternative,x[wi],wp,ts)
                old=agreement(a0,y[wi],people[wi]);new=agreement(a1,y[wi],people[wi]);changed=len(set(people[wi][np.any(a0!=a1,axis=1)]))
                for recorded,actual in [(edit['witness_before'],old),(edit['witness_after'],new)]:
                    assert all(abs(recorded[k]-actual[k])<1e-12 for k in actual)
                assert changed==edit['affected_witness_patients'];yes=state!=alternative and (not edit['gate_enabled'] or (changed>=3 and new['patient_f1']-old['patient_f1']>1e-12 and new['patient_jaccard']-old['patient_jaccard']>=-1e-12))
                assert yes==edit['accepted'];decision_count+=1
                if yes:state=alternative
            assert state==memories[arm] and digest(state)==a['memory_sha256'];states[arm]=state
            if arm=='own_error_program_agent':own_previous=previous;own_evidence=evidence
            threshold=np.full(len(ts),fits['selection']['threshold']) if arm=='raw_policy' else ts
            pred=execute(state,data['proposal'][0],pval,threshold);m,_,_=score(pred,data['proposal'][1],data['proposal'][2],meds,b['ddi'],b['ddi_covered_indices']);compare(a['proposal'],m)
            if arm not in best or m['patient_jaccard']>best[arm][1]:best[arm]=(r,m['patient_jaccard'])
            assert a['best_round']==best[arm][0] and immutable['best'][arm]['round']==best[arm][0]
            arm_rows[arm]={'witness_decisions_checked':decision_count,'induction_gain_max_delta':max_gain,'proposal':m,'memory_size':len(state),'retained_conjunctions':sum(len(q['conditions'])==2 for q in state)}
        result={'round':r,'round_source_sha256':sha(part/'complete.json'),'auditor_sha256':sha(Path(__file__)),
          'fit_patient_count':row['policy_fit_patients'],'fresh_witness_patients':len(wb),'policy_witness_overlap':0,'prior_witness_overlap':0,
          'original_model_refits':4,'coefficient_max_abs_delta':delta,'calibration_gain_max_abs_delta':cal_delta,'arms':arm_rows}
        save(receipt,result);rounds.append(result);print(json.dumps({'panel':panel,'seed':seed,'round_audited':r,'model_delta':delta}),flush=True)
    guard={};patient_scores={};keys=None
    for arm,selection in z['selections'].items():
        assert selection['round']==best[arm][0];part=folder/f"round{selection['round']}";fits=json.loads((part/'fits.json').read_text());prob=probabilities(joblib.load(part/fits['base_file']),data['guard'][0]);memory=json.loads((part/'memories.json').read_text())[arm]
        ts=np.full(len(meds),fits['selection']['threshold']) if arm=='raw_policy' else np.load(part/'thresholds.npy')
        pred=execute(memory,data['guard'][0],prob,ts);np.testing.assert_array_equal(pred,np.load(folder/(arm+'-guard.npy')))
        m,p,keys=score(pred,data['guard'][1],data['guard'][2],meds,b['ddi'],b['ddi_covered_indices']);compare(z['guard'][arm],m);guard[arm]=m;patient_scores[arm]=p
    np.savez(folder/'audited-guard-patient-scores.npz',people=np.array(keys),**patient_scores)
    result={'status':'passed','panel':panel,'seed':seed,'source_report_sha256':sha(path),'auditor_sha256':sha(Path(__file__)),'rounds':rounds,'guard':guard,'test_inference':False,
      'scope':'Independent raw features and patient partition; selected base and all fold models freshly refit; predictions, actual calibration gains, eligible proposal effects, fresh-witness decisions and final guard outputs reconstructed. Full candidate search ranking and skipped calibration alternatives are not independently enumerated. Guard remains development evidence.'}
    save(HERE/f'results/{panel}-audit-seed{seed}.json',result);print(json.dumps({'status':'passed','panel':panel,'seed':seed}),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('panel',choices=['full','molecular']);p.add_argument('seed',type=int);a=p.parse_args();main(a.panel,a.seed)
