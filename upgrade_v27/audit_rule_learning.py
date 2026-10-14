"""Reconstruct frozen development trajectories from raw visits and saved artifacts.

Checks every reported candidate's actual induction effect, actual prompt fields,
round selection, and selected guard output. Candidate search completeness is
not asserted; full cross-fit reconstruction and witness-decision audits are
separate requirements. No test examples are evaluated.
"""
import argparse,hashlib,json,math
from pathlib import Path
import joblib,numpy as np
from audit_controls import reconstruct
from audit_rule_decisions import apply,integer
from evaluation_metrics import score,compare
HERE=Path(__file__).resolve().parent;PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v27'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x,unicode=False):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=not unicode).encode()).hexdigest()
def predict(models,x):return np.column_stack([np.full(x.shape[0],m) if isinstance(m,float) else m.predict_proba(x)[:,1] for m in models])
def save(p,x):
    tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(x,indent=2)+'\n');tmp.replace(p)

def main(panel,seed):
    original=json.loads((HERE/f'results/{panel}-rsi-seed{seed}.json').read_text());assert original['status']=='selection_frozen'
    lock=original['lock'];assert all(sha(HERE/f)==v for f,v in lock['sources'].items())
    assert sha(HERE/'rsi_addendum.json')==lock['protocol_sha256']
    source=joblib.load(PRIVATE/'visits.joblib');b=joblib.load(PRIVATE/(panel+'-models.joblib'));meds=b['medications'];assert sha(PRIVATE/(panel+'-models.joblib'))==lock['bundle_sha256']
    assert sha(PRIVATE/'visits.joblib')==json.loads((HERE/'results/cohort_manifest.json').read_text())['bundle_sha256']
    data={}
    for split in ['train','proposal','guard']:
        x,gold,_,people,_=reconstruct(source['data'][split],source['vocab'],meds)
        if panel=='molecular':gold=[g&set(meds) for g in gold]
        data[split]=(x,gold,people)
    labels=[]
    for name,values in [('current_diagnosis',source['vocab']['diagnoses']+['UNKNOWN']),('current_procedure',source['vocab']['procedures']+['UNKNOWN']),('prior_diagnosis',source['vocab']['diagnoses']+['UNKNOWN']),('prior_procedure',source['vocab']['procedures']+['UNKNOWN']),('last_visit_medication',meds),('prior_medication_history',meds)]:labels.extend(name+':'+s for s in values)
    folder=PRIVATE/f'{panel}-rsi-seed{seed}';states={};best={};rounds=[];guard={};private_scores={}
    for row in original['rounds']:
        r=row['round'];part=folder/f'round{r}';fits=json.loads((part/'fits_complete.json').read_text())
        assert sha(part/'base.joblib')==fits['base_sha256']==row['base_model_sha256']
        base=joblib.load(part/'base.joblib');proposal=predict(base,data['proposal'][0]);saved=np.load(part/'proposal.npy')
        np.testing.assert_allclose(proposal,saved,atol=1e-12,rtol=1e-12)
        options=[]
        for trial in fits['C_trials']:
            models=joblib.load(part/f"C{trial['C']}.joblib");prob=predict(models,data['proposal'][0]);choices=[]
            assert all(isinstance(m,float) or m.C==trial['C'] for m in models)
            for t in [.1,.2,.3,.4,.5,.6]:
                z,_,_=score(prob>=t,data['proposal'][1],data['proposal'][2],meds,b['ddi'],b['ddi_covered_indices']);choices.append((z['patient_jaccard'],t,z))
            winner=max(choices,key=lambda z:z[0]);assert trial['threshold']==winner[1];compare(trial['metrics'],winner[2]);options.append((winner[0],trial['C']))
        assert fits['selection']['C']==max(options,key=lambda z:z[0])[1]
        ix=np.load(part/'members.npy');oof=np.load(part/'oof.npy');witness=np.array([integer(str(seed)+'|witness|'+s)%5==0 for s in data['train'][2][ix]])
        induction=ix[~witness];xx=data['train'][0][induction];pp=oof[~witness];people=data['train'][2][induction];gold=[data['train'][1][i] for i in induction]
        y=np.array([[m in g for m in meds] for g in gold]);threshold=fits['selection']['threshold'];memories=json.loads((part/'memories.json').read_text());counts={}
        _,inverse,patient_counts=np.unique(people,return_inverse=True,return_counts=True);weights=1/(len(patient_counts)*patient_counts[inverse])
        top_features=set(np.lexsort((np.arange(xx.shape[1]),-np.asarray((xx>0).sum(0)).ravel()))[:128]);own_evidence=None
        for arm,report in row['arms'].items():
            evidence=json.loads((part/(arm+'-evidence.json')).read_text());previous=states.get(arm,[])
            # The no-witness intervention deliberately reuses own-agent proposals,
            # not candidates re-induced from its different accumulated memory.
            induction_memory=states.get('own_error_rule_agent_previous',[]) if arm=='matched_proposals_without_witness_gate' else previous
            before=apply(induction_memory,xx,pp,threshold);base_tp=(before&y).sum(1);base_union=before.sum(1)+y.sum(1)-base_tp
            base_j=np.divide(base_tp,base_union,out=np.ones(len(before)),where=base_union>0)
            max_gain_delta=0.
            for c in evidence['candidates']:
                rule=c['rule'];f=rule['feature_index'];d=rule['drug_index']
                assert rule['feature']==labels[f] and rule['drug']==meds[d]
                assert rule['id']==digest({k:v for k,v in rule.items() if k!='id'})[:20]
                if c['operation']=='ADD':assert f in top_features
                alternative=[q for q in induction_memory if q['id']!=rule['id']] if c['operation']=='DELETE' else induction_memory+[rule]
                after=apply(alternative,xx,pp,threshold);changed=np.any(before!=after,axis=1)
                assert int(changed.sum())==c['affected_visits'] and len(set(people[changed]))==c['affected_patients']
                assert c['affected_visits']>=30 and c['affected_patients']>=20
                tp=(after[changed]&y[changed]).sum(1);union=after[changed].sum(1)+y[changed].sum(1)-tp
                j=np.divide(tp,union,out=np.ones(len(tp)),where=union>0)
                gain=math.fsum(float(a-bb)*float(w) for a,bb,w in zip(j,base_j[changed],weights[changed]))
                assert gain>0 and abs(gain-c['induction_jaccard_gain'])<1e-12
                max_gain_delta=max(max_gain_delta,abs(gain-c['induction_jaccard_gain']))
            receipt=evidence['receipt']
            if arm in ['own_error_rule_agent','shuffled_evidence_rule_agent'] and evidence['candidates']:
                payload=receipt['aggregate_payload'];assert set(payload)=={'round','retained_rules','candidate_edits','decision_schema'}
                assert payload['round']==r and payload['retained_rules']==[{k:q[k] for k in ['id','feature','drug','action']} for q in previous]
                expected=[{'id':c['id'],'operation':c['operation'],'feature':c['rule']['feature'],'drug':c['rule']['drug'],'action':c['rule']['action'],**{k:c[k] for k in ['induction_jaccard_gain','affected_visits','affected_patients']}} for c in sorted(evidence['candidates'],key=lambda z:z['id'])]
                if arm=='shuffled_evidence_rule_agent':
                    order=np.random.default_rng(seed+1000*r).permutation(len(expected));old=[dict(z) for z in expected]
                    for i,j in enumerate(order):
                        for k in ['induction_jaccard_gain','affected_visits','affected_patients']:expected[i][k]=old[j][k]
                assert payload['candidate_edits']==expected and digest(payload,True)==receipt['aggregate_prompt_sha256']
                assert not receipt['model_response'].get('error') and receipt['model_calls']==1
                assert receipt['selected_ids']==evidence['selected']
            if arm=='own_error_rule_agent':states['own_error_rule_agent_previous']=previous;own_evidence=evidence
            if arm=='matched_proposals_without_witness_gate':assert evidence['candidates']==own_evidence['candidates'] and evidence['selected']==own_evidence['selected']
            assert memories[arm]==evidence['memory'] and digest(memories[arm])==report['memory_sha256'];states[arm]=memories[arm]
            pred=apply(memories[arm],data['proposal'][0],proposal,threshold)
            metrics,_,_=score(pred,data['proposal'][1],data['proposal'][2],meds,b['ddi'],b['ddi_covered_indices']);compare(report['proposal'],metrics)
            if arm not in best or metrics['patient_jaccard']>best[arm][1]:best[arm]=(r,metrics['patient_jaccard'])
            assert report['best_round']==best[arm][0]
            counts[arm]={'candidates_checked':len(evidence['candidates']),'maximum_induction_gain_delta':max_gain_delta,'proposal_metrics':metrics,'memory_size':len(memories[arm])}
        rounds.append({'round':r,'training_patients':row['training_patients'],'arms':counts})
        print(json.dumps({'panel':panel,'seed':seed,'round_audited':r}),flush=True)
    for arm,choice in original['selections'].items():
        assert choice['round']==best[arm][0];part=folder/f"round{choice['round']}";memory=json.loads((part/'memories.json').read_text())[arm]
        prob=predict(joblib.load(part/'base.joblib'),data['guard'][0]);pred=apply(memory,data['guard'][0],prob,choice['threshold'])
        np.testing.assert_array_equal(pred,np.load(folder/(arm+'-guard.npy')))
        z,patient,keys=score(pred,data['guard'][1],data['guard'][2],meds,b['ddi'],b['ddi_covered_indices']);compare(original['guard'][arm],z)
        guard[arm]=z;private_scores[arm]=patient
    np.savez(folder/'audited-guard-patient-scores.npz',people=np.array(keys),**private_scores)
    result={'status':'passed','panel':panel,'seed':seed,'source_report_sha256':sha(HERE/f'results/{panel}-rsi-seed{seed}.json'),
      'auditor_sources':{f:sha(HERE/f) for f in ['audit_rule_learning.py','evaluation_metrics.py','audit_controls.py','audit_rule_decisions.py']},
      'test_inference':False,'rounds':rounds,'guard':guard,'scope':'Raw-source feature reconstruction; actual candidate effects and aggregate prompt contents; saved-policy proposal/guard outputs, hyperparameter and round choices. Does not independently enumerate excluded candidates or assert clinical validity.'}
    save(HERE/f'results/{panel}-rsi-learning-audit-seed{seed}.json',result)
    print(json.dumps({'panel':panel,'seed':seed,'learning_audit':'passed'}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('panel',choices=['full','molecular']);p.add_argument('seed',type=int);a=p.parse_args();main(a.panel,a.seed)
