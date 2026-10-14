"""Independently reconstruct gates with scalar set scores; no gate implementation imports."""
import argparse,copy,hashlib,json,sys
from pathlib import Path
import joblib,numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;V29=ROOT/'upgrade_v29';V27=ROOT/'upgrade_v27';sys.path[:0]=[str(ROOT),str(V27)]
from upgrade_v29.audit import execute,change,agreement,probabilities
from upgrade_v27.audit_controls import reconstruct
from upgrade_v27.evaluation_metrics import score,compare
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v30';SOURCE=PRIVATE.parent/'prismatic-v29';COHORT=PRIVATE.parent/'prismatic-v27'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(z):return hashlib.sha256(json.dumps(z,sort_keys=True).encode()).hexdigest()
def save(p,z):
    p.parent.mkdir(exist_ok=True);tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(z,indent=2)+'\n');tmp.replace(p)
def check_state(memory,x,prob,thresholds,y,people):
    empty=execute([],x,prob,thresholds);pred=execute(memory,x,prob,thresholds);a=agreement(empty,y,people);b=agreement(pred,y,people);n=len(set(people[np.any(empty!=pred,axis=1)]))
    return {'memory_sha256':digest(memory),'empty':a,'memory':b,'affected_patients':n,'passed':n>=3 and b['patient_f1']-a['patient_f1']>1e-12 and b['patient_jaccard']-a['patient_jaccard']>=-1e-12}
def same(recorded,actual):
    for k,v in actual.items():
        if isinstance(v,dict):same(recorded[k],v)
        elif isinstance(v,float):assert abs(recorded[k]-v)<1e-12,(k,recorded[k],v)
        else:assert recorded[k]==v,(k,recorded[k],v)
def main(panel,seed):
    report=HERE/f'results/{panel}-seed{seed}.json';state=json.loads(report.read_text());assert state['status']=='selection_frozen';lock=state['lock'];folder=PRIVATE/f'{panel}-seed{seed}'
    assert lock['protocol_sha256']==sha(HERE/'protocol.json') and all(sha(ROOT/f)==v for f,v in lock['source_sha256'].items())
    source_report=V29/f'results/{panel}-seed{seed}.json';source_audit=V29/f'results/{panel}-audit-seed{seed}.json';old=json.loads(source_report.read_text());audited=json.loads(source_audit.read_text())
    assert sha(source_report)==lock['v29_report_sha256'] and sha(source_audit)==lock['v29_audit_sha256'] and audited['status']=='passed' and audited['source_report_sha256']==sha(source_report) and audited['auditor_sha256']==sha(V29/'audit.py')
    assert old['lock']['protocol_sha256']==sha(V29/'protocol.json') and all(sha(ROOT/f)==v for f,v in old['lock']['source_sha256'].items())
    assert sha(COHORT/(panel+'-models.joblib'))==lock['bundle_sha256'];b=joblib.load(COHORT/(panel+'-models.joblib'));source=joblib.load(COHORT/'visits.joblib');meds=b['medications']
    assert sha(COHORT/'visits.joblib')==json.loads((V27/'results/cohort_manifest.json').read_text())['bundle_sha256']
    data={}
    for split in ['train','proposal','guard']:
        x,gold,_,people,_=reconstruct(source['data'][split],source['vocab'],meds)
        if panel=='molecular':gold=[g&set(meds) for g in gold]
        data[split]=(x,gold,people)
    x,gold,people=data['train'];y=np.array([[m in g for m in meds] for g in gold]);best={};memories={};rounds=[];seen=set();guard_cache={}
    config=[('raw_policy',None,0,0),('calibrated_policy',None,0,0)]+[(f'{m}_C{c}P{p}',m,c,p) for m in ['greedy','own','shuffled'] for c in [0,1] for p in [0,1]]
    roles=json.loads((folder/'witness_roles.json').read_text())
    for row in state['rounds']:
        r=row['round'];src=SOURCE/f'{panel}-seed{seed}/round{r}';part=folder/f'round{r}';original=json.loads((src/'complete.json').read_text());assert sha(src/'complete.json')==row['source_round_sha256']==audited['rounds'][r-1]['round_source_sha256']
        assert row==json.loads((part/'complete.json').read_text());ix=np.load(src/'fit_members.npy');wi=np.load(src/'witness_members.npy')
        assert digest(ix.tolist())==original['fit_members_sha256']==row['fit_members_sha256'] and digest(wi.tolist())==original['witness_members_sha256']
        ordered=sorted(set(people[wi]),key=lambda p:hashlib.sha256(f'v30|{seed}|{r}|witness-split|{p}'.encode()).hexdigest());aset=set(ordered[:len(ordered)//2]);bset=set(ordered[len(ordered)//2:])
        aidx=wi[np.isin(people[wi],list(aset))];bidx=wi[np.isin(people[wi],list(bset))]
        assert not aset&bset and not (aset|bset)&set(people[ix]) and not (aset|bset)&seen;seen|=aset|bset
        assert digest(aidx.tolist())==row['edit_members_sha256'] and digest(bidx.tolist())==row['confirmation_members_sha256']
        assert sorted(aset)==roles[str(r)]['edit_patients'] and sorted(bset)==roles[str(r)]['confirmation_patients']
        assert row['edit_patients']==len(aset) and row['confirmation_patients']==len(bset)
        fits=json.loads((src/'fits.json').read_text());assert all(sha(src/f)==h for f,h in fits['model_sha256'].items())
        model=joblib.load(src/fits['base_file']);wp=probabilities(model,x[wi]);pval=probabilities(model,data['proposal'][0]);ts=np.load(src/'thresholds.npy')
        np.testing.assert_allclose(wp,np.load(src/'witness.npy'),atol=1e-12,rtol=1e-12);np.testing.assert_allclose(pval,np.load(src/'proposal.npy'),atol=1e-12,rtol=1e-12)
        folds=np.array([int(hashlib.sha256(f'v29|{seed}|fold|{p}'.encode()).hexdigest(),16)%3 for p in people[ix]]);oof=np.zeros((len(ix),len(meds)))
        for f in range(3):
            held=np.flatnonzero(folds==f);oof[held]=probabilities(joblib.load(src/f'fold{f}.joblib'),x[ix[held]])
        np.testing.assert_allclose(oof,np.load(src/'oof.npy'),atol=1e-12,rtol=1e-12)
        # Independently replay the source calibration to verify threshold bytes.
        expected_ts=np.full(len(meds),fits['selection']['threshold'])
        for event in fits['calibration']:assert expected_ts[event['drug_index']]==event['old_threshold'];expected_ts[event['drug_index']]=event['new_threshold']
        np.testing.assert_array_equal(expected_ts,ts);actual_memories=json.loads((part/'memories.json').read_text());arms={}
        ai=np.flatnonzero(np.isin(people[wi],list(aset)));bi=np.flatnonzero(np.isin(people[wi],list(bset)))
        for arm,method,c,p in config:
            prior=memories.get(arm,[]);e=json.loads((part/(arm+'-evidence.json')).read_text());assert e['previous_memory']==prior
            current=list(prior);decisions=0
            if method is not None:
                fcheck=check_state(prior,x[ix],oof,ts,y[ix],people[ix]);acheck=check_state(prior,x[aidx],wp[ai],ts,y[aidx],people[aidx]);same(e['compatibility']['fit'],fcheck);same(e['compatibility']['edit'],acheck)
                if c and not(fcheck['passed'] and acheck['passed']):current=[]
                assert e['compatibility']['enabled']==bool(c) and e['basis']==current and e['compatibility']['reset']==bool(prior and not current) and e['compatibility']['starting_memory_sha256']==digest(current)
                baseline=execute(current,x[ix],oof,ts);bm=agreement(baseline,y[ix],people[ix]);eligible=[];unsupported=[]
                for index,op in enumerate(e['proposed_programs']):
                    altered=execute(change(current,op),x[ix],oof,ts);changed=np.any(baseline!=altered,axis=1);gain=agreement(altered,y[ix],people[ix])['patient_jaccard']-bm['patient_jaccard'];visits=int(changed.sum());patients=len(set(people[ix][changed]))
                    if visits>=30 and patients>=20 and gain>1e-12:
                        eligible.append(op);logged=e['eligible'][len(eligible)-1];assert logged['operation']==op['operation'] and logged['rule']==op['rule'] and logged['affected_visits']==visits and logged['affected_patients']==patients and abs(logged['induction_jaccard_gain']-gain)<1e-12
                    else:unsupported.append(index)
                assert len(eligible)==len(e['eligible']) and unsupported==[z['index'] for z in e['unsupported']]
                if method!='greedy':
                    receipt=e['receipt'];shown=receipt['aggregate_payload'];assert set(shown)=={'allowed_features','focus_drugs','single_predicate_evidence','retained_rules','round'} and shown['round']==r and shown['retained_rules']==current
                    assert hashlib.sha256(json.dumps(shown,sort_keys=True,ensure_ascii=False).encode()).hexdigest()==receipt['aggregate_prompt_sha256']
                    for k in ['allowed_features','focus_drugs']:assert shown[k]==e['payload'][k]
                    expected=copy.deepcopy(e['payload']['single_predicate_evidence'])
                    if method=='shuffled':
                        original_e=copy.deepcopy(expected);order=np.random.default_rng(seed+1000*r).permutation(len(expected))
                        for i,j in enumerate(order):
                            for key in ['induction_jaccard_gain','affected_visits','affected_patients']:expected[i][key]=original_e[j][key]
                    assert shown['single_predicate_evidence']==expected and all(q['affected_visits']>=30 and q['affected_patients']>=20 for q in expected)
                    assert all(q['error_visits']>=30 and q['error_patients']>=20 for q in shown['focus_drugs'])
                    assert receipt['parsed_programs']==e['proposed_programs']
                    for op in e['proposed_programs']:
                        if op['operation']=='ADD':assert op['rule']['drug_index'] in {d['drug_index'] for d in shown['focus_drugs']} and all(v['feature_index'] in {f['feature_index'] for f in shown['allowed_features']} for v in op['rule']['conditions'])
                assert len(e['edits'])==len(eligible)
                for index,edit in enumerate(e['edits']):
                    assert edit['operation']==e['eligible'][index]
                    alternative=change(current,edit['operation']);before=execute(current,x[aidx],wp[ai],ts);after=execute(alternative,x[aidx],wp[ai],ts);m0=agreement(before,y[aidx],people[aidx]);m1=agreement(after,y[aidx],people[aidx]);affected=len(set(people[aidx][np.any(before!=after,axis=1)]))
                    same(edit['witness_before'],m0);same(edit['witness_after'],m1);yes=current!=alternative and affected>=3 and m1['patient_f1']-m0['patient_f1']>1e-12 and m1['patient_jaccard']-m0['patient_jaccard']>=-1e-12
                    assert edit['accepted']==yes and edit['affected_witness_patients']==affected and edit['gate_enabled'];assert edit['before_memory_sha256']==digest(current) and edit['proposed_memory_sha256']==digest(alternative)
                    if yes:current=alternative
                    decisions+=1
                assert current==e['candidate_memory'];confirmation=check_state(current,x[bidx],wp[bi],ts,y[bidx],people[bidx]);same(e['confirmation']['check'],confirmation)
                assert e['confirmation']['enabled']==bool(p) and e['confirmation']['candidate_memory_sha256']==digest(current)
                pre=list(current)
                if p and not confirmation['passed']:current=[]
                assert e['confirmation']['reset']==bool(pre and not current)
            assert current==e['memory']==actual_memories[arm];memories[arm]=current;logged=row['arms'][arm];assert logged['memory_sha256']==digest(current) and logged['memory_size']==len(current)
            assert logged['compatibility_reset']==e['compatibility'].get('reset',False) and logged['confirmation_reset']==e['confirmation'].get('reset',False)
            assert logged['accepted_edits_before_confirmation']==sum(z['accepted'] for z in e['edits'])
            threshold=np.full(len(meds),fits['selection']['threshold']) if arm=='raw_policy' else ts
            pred=execute(current,data['proposal'][0],pval,threshold);m,_,_=score(pred,data['proposal'][1],data['proposal'][2],meds,b['ddi'],b['ddi_covered_indices']);compare(logged['proposal'],m)
            if arm not in best or m['patient_jaccard']>best[arm][1]:best[arm]=(r,m['patient_jaccard'])
            assert logged['best_round']==best[arm][0]==row['best'][arm]['round']
            arms[arm]={'proposal':m,'memory_size':len(current),'retained_conjunctions':sum(len(q['conditions'])==2 for q in current),'edit_decisions_checked':decisions,'compatibility_reset':logged['compatibility_reset'],'confirmation_reset':logged['confirmation_reset']}
        rounds.append({'round':r,'edit_patients':len(aset),'confirmation_patients':len(bset),'patient_overlap':0,'source_round_sha256':sha(src/'complete.json'),'v30_round_sha256':sha(part/'complete.json'),'arms':arms})
        print(json.dumps({'panel':panel,'seed':seed,'round_audited':r}),flush=True)
    outputs={};patient_scores={};keys=None
    for endpoint,field in [('selected','guard'),('final','final_guard')]:
        outputs[endpoint]={}
        for arm,_,_,_ in config:
            assert state['selections'][arm]['round']==best[arm][0];number=best[arm][0] if endpoint=='selected' else 5;src=SOURCE/f'{panel}-seed{seed}/round{number}';fits=json.loads((src/'fits.json').read_text())
            if number not in guard_cache:guard_cache[number]=probabilities(joblib.load(src/fits['base_file']),data['guard'][0])
            memory=json.loads((folder/f'round{number}/memories.json').read_text())[arm];ts=np.full(len(meds),fits['selection']['threshold']) if arm=='raw_policy' else np.load(src/'thresholds.npy');pred=execute(memory,data['guard'][0],guard_cache[number],ts)
            np.testing.assert_array_equal(pred,np.load(folder/f'{arm}-{endpoint}-guard.npy'));m,a,keys=score(pred,data['guard'][1],data['guard'][2],meds,b['ddi'],b['ddi_covered_indices']);compare(state[field][arm],m);outputs[endpoint][arm]=m;patient_scores[endpoint+'__'+arm]=a
    np.savez(folder/'audited-guard-patient-scores.npz',people=np.array(keys),**patient_scores)
    result={'status':'passed','panel':panel,'seed':seed,'source_report_sha256':sha(report),'auditor_sha256':sha(Path(__file__)),'v29_audit_sha256':sha(source_audit),'rounds':rounds,'guard':outputs,'test_inference':False,'scope':'Independent raw-source features, hash-partitioned A/B patients, original-model probability reconstruction, actual induction supports and scalar whole-memory/edit/promotion decisions. Original source-model refits are inherited from locked v29 audits. Full greedy candidate ranking is not independently enumerated. No test inference.'}
    save(HERE/f'results/{panel}-audit-seed{seed}.json',result);print(json.dumps({'status':'passed','panel':panel,'seed':seed}),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('panel',choices=['full','molecular']);p.add_argument('seed',type=int);a=p.parse_args();main(a.panel,a.seed)
