"""Independent native-code metrics, feedback replay and cluster contrasts."""
import json
import numpy as np,joblib
from data_contract import HERE,PRIVATE,FIELDS,sha,digest,save

def recount(pred,gold):
    a={o['drug_code'] for o in pred};b={o['drug_code'] for o in gold}
    p={tuple(o[f] for f in FIELDS) for o in pred if all(o.get(f) is not None for f in FIELDS)}
    g={tuple(o[f] for f in FIELDS) for o in gold if all(o.get(f) is not None for f in FIELDS)}
    return [len(a.intersection(b)),len(a),len(b),len(p.intersection(g)),len(p),len(g)]
def endpoints(matrix):
    x=np.asarray(matrix).sum(axis=0);return np.array([2*x[0]/max(1,x[1]+x[2]),2*x[3]/max(1,x[4]+x[5])])
def bootstrap(mats,groups):
    _,ix=np.unique(groups,return_inverse=True);n=int(ix.max()+1);names=list(mats);grouped=[]
    for name in names:
        a=np.zeros((n,6));np.add.at(a,ix,mats[name]);grouped.append(a)
    stacked=np.concatenate(grouped,axis=1);rng=np.random.default_rng(42)
    weights=np.asarray([np.bincount(rng.integers(0,n,n),minlength=n) for _ in range(2000)],dtype=np.float64)
    sums=(weights@stacked).reshape(2000,len(names),6)
    values=np.stack([2*sums[:,:,0]/np.maximum(1,sums[:,:,1]+sums[:,:,2]),2*sums[:,:,3]/np.maximum(1,sums[:,:,4]+sums[:,:,5])],axis=-1)
    return n,{name:values[:,j,:] for j,name in enumerate(names)}

def main():
    protocol=json.loads((HERE/'protocol.json').read_text());dev=joblib.load(PRIVATE/'development.joblib');test=joblib.load(PRIVATE/'sealed_evaluation.joblib')
    frozen=json.loads((HERE/'results/frozen_before_test.json').read_text());reports=[];audits=[];pairs={};curves={};strata={}
    classes=dev['classes'];case_ids=[c['case_id'] for c in test['cases']];empty=np.array([not g for g in test['truth']]);allowed=set(classes)
    for seed in protocol['seeds']:
        folder=PRIVATE/f'seed_{seed}';report=json.loads((HERE/f'results/test_seed_{seed}.json').read_text());assert report['status']=='complete'
        assert sha(HERE/f'results/selection_seed_{seed}.json')==frozen['selections_sha256'][str(seed)]==report['selection_sha256']
        selection=json.loads((HERE/f'results/selection_seed_{seed}.json').read_text());seq=joblib.load(folder/'case_order.joblib');weights={a:np.ones(40000) for a in protocol['arms']}
        for r,n in enumerate(protocol['round_sizes']):
            ix=seq[:n]
            if r:
                new=seq[protocol['round_sizes'][r-1]:n];f=joblib.load(folder/f'feedback_round_{r}.joblib');parent=joblib.load(folder/f['parent']['policy_file'])
                assert f['case_ids']==[dev['train']['cases'][i]['case_id'] for i in new]
                assert digest([parent.coef_.tolist(),parent.intercept_.tolist()])==f['parent']['policy_sha256']
                p=parent.predict_proba(dev['train']['x'][new]);assert np.allclose(p,f['preupdate_probabilities'],atol=1e-12,rtol=0)
                expected=[]
                for row,y in zip(p,dev['y'][new]):
                    pred={int(j) for j in np.argsort(-row,kind='stable')[:20] if row[j]>=f['parent']['threshold']};gold=set(np.flatnonzero(y));den=len(pred)+len(gold)
                    expected.append(1+3*(1-(2*len(pred&gold)/den if den else 1)))
                assert np.allclose(expected,f['weights'],atol=1e-12,rtol=0)
                weights['error_prioritized'][new]=f['weights'];weights['permuted_priority'][new]=f['weights'][f['permutation']]
            seen_truth=[dev['train']['truth'][i] for i in ix];seen={tuple(o[f] for f in FIELDS) for row in seen_truth for o in row};distributions=[]
            for arm in protocol['arms']:
                j=json.loads((HERE/f'results/journal_seed_{seed}_{arm}.json').read_text())[r];s=j['candidate'];model=joblib.load(folder/s['policy_file']);tool=joblib.load(folder/s['tool_file'])
                assert digest([model.coef_.tolist(),model.intercept_.tolist()])==s['policy_sha256'];assert model.iterations==[60]*len(classes)
                assert j['logical_training_case_exposures']==n*60*len(classes)
                assert j['training_membership_sha256']==digest([dev['train']['cases'][i]['case_id'] for i in ix])
                w=weights[arm][ix];w=w/w.mean();assert digest(w.tolist())==j['sample_weight_sha256']
                assert sha(folder/s['tool_file'])==s['tool_sha256'];assert tool.membership_sha256==digest(seen_truth)==j['tool_membership_sha256']
                assert all(tuple(v[f] for f in FIELDS) in seen for v in tool.defaults.values())
                assert all(tuple(v) in seen for rows in tool.labels.values() for v in rows)
                if arm!='uniform':distributions.append(np.sort(w))
            assert np.allclose(*distributions,atol=1e-12,rtol=0)
        static=joblib.load(folder/'static_controls.joblib')
        for name,m in static['static_models'].items():
            assert m.iterations==[60]*len(classes) and digest([m.coef_.tolist(),m.intercept_.tolist()])==selection['static_model_hashes'][name]
        saved=joblib.load(folder/'all_test_predictions.joblib');assert saved['case_ids']==case_ids;mats={}
        for name,pred in saved['predictions'].items():
            assert len(pred)==len(test['truth']);assert all(len(row)<=20 and len({o['drug_code'] for o in row})==len(row) and all(o['drug_code'] in allowed for o in row) for row in pred)
            a=np.asarray([recount(p,g) for p,g in zip(pred,test['truth'])]);mats[name]=a
            if '_round_' in name:
                prefix,r=name.rsplit('_round_',1);arm,kind=prefix.rsplit('_',1);m=report['accepted_curves' if kind=='active' else 'raw_curves'][arm][int(r)]['metrics']
            else:m=report['methods'][name]
            assert np.allclose(endpoints(a),[m['drug_micro_f1'],m['core_order_micro_f1']],atol=1e-12,rtol=0)
        final={k:mats[k] for k in report['methods']};patient_n,pboot=bootstrap(final,[c['patient_hash'] for c in test['cases']]);hospital_n,hboot=bootstrap(final,[c['hospital_hash'] for c in test['cases']])
        pairs[str(seed)]={}
        for left,right in [('error_prioritized','uniform'),('error_prioritized','permuted_priority'),('error_prioritized','word_char_ensemble'),('error_prioritized','error_priority_initial_tool'),('uniform','initial_state'),('uniform','word_char_ensemble')]:
            pairs[str(seed)][left+'__minus__'+right]={'drug_order_difference':(endpoints(final[left])-endpoints(final[right])).tolist(),
              'hospital_ci95':np.quantile(hboot[left]-hboot[right],[.025,.975],axis=0).tolist(),'patient_ci95':np.quantile(pboot[left]-pboot[right],[.025,.975],axis=0).tolist()}
        curves[str(seed)]={}
        for arm in protocol['arms']:
            curve=[];previous=None
            for r in range(5):
                a=mats[f'{arm}_active_round_{r}'];den=a[:,1]+a[:,2];quality=np.divide(2*a[:,0],den,out=np.ones(len(a)),where=den>0)
                delta=quality-previous if previous is not None else np.zeros(len(a));previous=quality
                curve.append({'round':r,'drug_f1':float(endpoints(a)[0]),'order_f1':float(endpoints(a)[1]),'drug_cases_improved':int((delta>1e-12).sum()),'drug_cases_regressed':int((delta< -1e-12).sum())})
            curves[str(seed)][arm]=curve
        strata[str(seed)]={k:{'zero_target_stays':int(empty.sum()),'nonempty_target_stays':int((~empty).sum()),
          'zero_target_false_nonempty_rate':float(np.mean(a[empty,1]>0)),'zero_target_mean_predicted_codes':float(a[empty,1].mean()),
          'nonempty_drug_order_f1':endpoints(a[~empty]).tolist()} for k,a in final.items()}
        audits.append({'seed':seed,'feedback_recomputed':True,'weight_distributions_equal':True,'epochs_exposures_verified':True,'seen_tool_labels_verified':True,'actual_parameter_hashes_recomputed':True,'all_prediction_recounts':'passed'})
        reports.append(report)
    methods={}
    for name in reports[0]['methods']:
        a=np.array([[r['methods'][name][k] for k in ['drug_micro_f1','core_order_micro_f1','empty_fraction','predicted_order_completion']] for r in reports])
        methods[name]={'drug_f1_mean':float(a[:,0].mean()),'drug_f1_sd':float(a[:,0].std(ddof=1)),'order_f1_mean':float(a[:,1].mean()),'order_f1_sd':float(a[:,1].std(ddof=1)),
          'empty_fraction':float(a[:,2].mean()),'predicted_order_completion':float(a[:,3].mean())}
    gold_sets=[{o['drug_code'] for o in g} for g in test['truth']]
    save(HERE/'results/summary.json',{'status':'complete','test_stays':len(test['truth']),'test_patients':patient_n,'test_hospitals':hospital_n,
      'zero_target_stays':int(empty.sum()),'test_drug_vocabulary_coverage':sum(len(g&allowed) for g in gold_sets)/sum(map(len,gold_sets)),
      'methods':methods,'accepted_curves':curves,'paired':pairs,'strata':strata,'audits':audits,
      'test_used_for_selection':False,'interval_note':'Paired hospital and patient cluster bootstrap2000 draws; descriptive, no multiplicity adjustment. Seeds vary order and optimizer jointly.',
      'claim_boundary':protocol['claim_boundary']})
    print(json.dumps({'status':'complete','methods':methods}),flush=True)

if __name__=='__main__':main()
