"""Audit pre-update feedback, matched weights/budgets and every test prediction."""
import json,sys
import joblib,numpy as np
from components import HERE,PRIVATE,hash_data,sha,save
sys.path.insert(0,str(HERE.parent/'upgrade_v9'))
from summarize import counts,scores

def main():
    protocol=json.loads((HERE/'protocol.json').read_text());dev=joblib.load(PRIVATE/'development.joblib');test=joblib.load(PRIVATE/'sealed_evaluation.joblib')
    frozen=json.loads((HERE/'results/frozen_before_test.json').read_text());summaries=[];budget_audits=[];rounds={};paired={}
    _,patient_ix=np.unique(test['parts'].subject_id.to_numpy(),return_inverse=True);npats=int(patient_ix.max()+1)
    for seed in protocol['seeds']:
        folder=PRIVATE/f'seed_{seed}';r=json.loads((HERE/f'results/test_seed_{seed}.json').read_text());assert r['status']=='complete'
        assert sha(HERE/f'results/selection_seed_{seed}.json')==frozen['all_selections_sha256'][str(seed)]==r['selection_sha256']
        order=joblib.load(folder/'case_order.joblib');weights={a:np.ones(40000) for a in protocol['arms']};assignment=[]
        for round_id,n in enumerate(protocol['round_sizes']):
            indices=order[:n]
            if round_id:
                new=order[protocol['round_sizes'][round_id-1]:n];f=joblib.load(folder/f'feedback_round_{round_id}.joblib')
                assert f['case_ids']==dev['parts']['train'].hadm_id.iloc[new].tolist()
                parent=joblib.load(folder/f['parent']['policy_file']);assert parent.sha256==f['parent']['policy_sha256']
                # Independent inference binds feedback to the previous accepted model.
                p=parent.predict_proba(dev['x']['train'][new]);assert np.allclose(p,f['preupdate_probabilities'],atol=1e-12,rtol=0)
                expected=[]
                for probability,target in zip(p,dev['y'][new]):
                    chosen={int(j) for j in np.argsort(-probability,kind='stable')[:20] if probability[j]>=f['parent']['threshold']}
                    gold=set(np.flatnonzero(target));denominator=len(chosen)+len(gold)
                    quality=2*len(chosen&gold)/denominator if denominator else 1.
                    expected.append(1+3*(1-quality))
                expected=np.asarray(expected);assert np.allclose(expected,f['feedback_weights'],atol=1e-12,rtol=0)
                assert np.array_equal(f['permuted_weights'],f['feedback_weights'][f['permutation']])
                weights['error_prioritized'][new]=f['feedback_weights'];weights['permuted_priority'][new]=f['permuted_weights']
                assignment.append({'round':round_id,'changed_assignments':int((expected!=f['permuted_weights']).sum()),'new_cases':len(new),
                    'error_random_weight_correlation':float(np.corrcoef(expected,f['permuted_weights'])[0,1]) if np.std(expected)>0 else None})
            distributions=[]
            for arm in protocol['arms']:
                journal=json.loads((HERE/f'results/journal_seed_{seed}_{arm}.json').read_text())[round_id]
                assert journal['training_membership_sha256']==hash_data(dev['parts']['train'].hadm_id.iloc[indices].tolist())
                w=weights[arm][indices];w=w/w.mean();assert hash_data(w.tolist())==journal['sample_weight_sha256']
                model=joblib.load(folder/journal['candidate']['policy_file']);assert model.iterations==[60]*128
                assert journal['logical_training_case_exposures']==n*60*128
                tool=joblib.load(folder/journal['candidate']['tool_file'])
                assert hash_data(tool.memory.orders)==hash_data([dev['truth']['train'][i] for i in indices])
                if arm!='uniform':distributions.append(np.sort(w))
            assert np.allclose(distributions[0],distributions[1],atol=1e-12,rtol=0)
        budget_audits.append({'seed':seed,'source_feedback_recomputed':'passed','exact_epochs_exposures':'passed','tool_seen_members_only':'passed','priority_distributions_equal':'passed','permutation_assignment':assignment})
        saved=joblib.load(folder/'all_test_predictions.joblib');assert saved['case_ids']==test['parts'].hadm_id.tolist()
        mats={}
        for name,pred in saved['predictions'].items():
            assert len(pred)==len(test['truth']);mat=np.array([counts(p,g) for p,g in zip(pred,test['truth'])]);mats[name]=mat
            if '_round_' in name:
                prefix,rid=name.rsplit('_round_',1);arm,kind=prefix.rsplit('_',1)
                metric=r['accepted_curves' if kind=='active' else 'raw_curves'][arm][int(rid)]['metrics']
            else:metric=r['methods'][name]
            assert np.allclose(scores(mat),[metric['drug_micro_f1'],metric['core_order_micro_f1']],rtol=0,atol=1e-12)
        summaries.append(r);rounds[str(seed)]={}
        for arm in protocol['arms']:
            curve=[];previous=None
            for i in range(5):
                mat=mats[f'{arm}_active_round_{i}'];quality=.5*(2*mat[:,0]/np.maximum(1,mat[:,1]+mat[:,2])+2*mat[:,3]/np.maximum(1,mat[:,4]+mat[:,5]))
                delta=quality-previous if previous is not None else np.zeros(len(quality));previous=quality
                curve.append({'round':i,'drug_f1':float(scores(mat)[0]),'order_f1':float(scores(mat)[1]),'cases_improved':int((delta>1e-12).sum()),'cases_regressed':int((delta< -1e-12).sum())})
            rounds[str(seed)][arm]=curve
        grouped={}
        for name,mat in mats.items():grouped[name]=np.zeros((npats,6));np.add.at(grouped[name],patient_ix,mat)
        paired[str(seed)]={}
        for left,right in [('error_prioritized','uniform'),('error_prioritized','permuted_priority'),('error_prioritized','full_data_uniform'),('error_prioritized','legacy_word_char_reference'),('error_prioritized','error_priority_freeze_initial_tool'),('uniform','initial_state')]:
            rng=np.random.default_rng(42);samples=[]
            for _ in range(2000):
                selected=rng.integers(0,npats,npats);samples.append(scores(grouped[left][selected])-scores(grouped[right][selected]))
            paired[str(seed)][left+'__minus__'+right]={'drug_order_difference':(scores(mats[left])-scores(mats[right])).tolist(),'patient_ci95':np.quantile(samples,[.025,.975],axis=0).tolist()}
    methods={}
    for name in summaries[0]['methods']:
        values=np.array([[r['methods'][name][k] for k in ['drug_micro_f1','core_order_micro_f1','empty_fraction']] for r in summaries])
        methods[name]={'drug_f1_mean':float(values[:,0].mean()),'drug_f1_sd':float(values[:,0].std(ddof=1)),'order_f1_mean':float(values[:,1].mean()),'order_f1_sd':float(values[:,1].std(ddof=1)),'empty_fraction':float(values[:,2].mean())}
    report={'status':'complete','test_admissions':len(test['truth']),'test_patients':npats,'methods':methods,'accepted_curves':rounds,'budget_feedback_audits':budget_audits,'paired':paired,
      'test_used_for_selection':False,'test_previously_observed':True,'independent_prediction_recounts':'passed',
      'claim_boundary':protocol['claim_boundary'],'interval_note':'Exploratory paired patient-cluster intervals2000 draws, no multiplicity adjustment. Three seeds jointly change exposure order and optimizer.'}
    save(HERE/'results/summary.json',report);print(json.dumps({'status':'complete','methods':methods}),flush=True)

if __name__=='__main__':main()
