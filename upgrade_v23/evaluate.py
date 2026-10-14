"""Evaluate only after every seed/arm selection has been frozen."""
import json,sys,time
import joblib
from components import HERE,PRIVATE,save,dump,sha,hash_data,compile_ranked,choose,score

def main():
    seeds=[42,137,2026];selections={}
    for seed in seeds:
        p=HERE/f'results/selection_seed_{seed}.json';d=json.loads(p.read_text())
        assert d['status']=='selection_frozen' and not d['test_loaded'];selections[seed]=d
    frozen={str(seed):sha(HERE/f'results/selection_seed_{seed}.json') for seed in seeds}
    before={'all_selections_sha256':frozen,'test_used_for_selection':False,'source_test_previously_observed':True}
    lock=HERE/'results/frozen_before_test.json'
    if lock.exists():assert json.loads(lock.read_text())==before
    else:save(lock,before)
    b=joblib.load(PRIVATE/'sealed_evaluation.joblib');case_ids=b['parts'].hadm_id.tolist()
    for seed,d in selections.items():
        report_path=HERE/f'results/test_seed_{seed}.json'
        if report_path.exists() and json.loads(report_path.read_text())['status']=='complete':continue
        folder=PRIVATE/f'seed_{seed}';cache=folder/'evaluated_states';cache.mkdir(exist_ok=True)
        predictions={};state_audits=[]
        def predict(state):
            signature=hash_data([state['policy_sha256'],state['tool_sha256'],state['threshold'],hash_data(case_ids)])
            path=cache/(signature+'.joblib')
            if path.exists():
                saved=joblib.load(path);assert saved['case_ids']==case_ids;return saved['orders']
            model=joblib.load(folder/state['policy_file']);assert model.sha256==state['policy_sha256']
            assert sha(folder/state['tool_file'])==state['tool_sha256'];tool=joblib.load(folder/state['tool_file'])
            start=time.time();rows,probs=compile_ranked(model,tool,b['x'],b['word'],b['classes']);pred=choose(rows,probs,state['threshold'])
            dump({'case_ids':case_ids,'orders':pred,'state':state,'inference_seconds':time.time()-start},path)
            return pred
        curves={};raw_curves={}
        for arm,states in d['raw_states'].items():
            journal=json.loads((HERE/f'results/journal_seed_{seed}_{arm}.json').read_text());curves[arm]=[];raw_curves[arm]=[]
            for j,state in zip(journal,states):
                assert state==j['candidate'];r=j['round']
                for kind,s in [('raw',state),('active',j['active'])]:
                    name=f'{arm}_{kind}_round_{r}';pred=predict(s);predictions[name]=pred;m=score(pred,b['truth'])
                    (raw_curves if kind=='raw' else curves)[arm].append({'round':r,'training_cases':j['training_cases'],'state_round':s['round'],'metrics':m})
            predictions[arm]=predictions[f'{arm}_active_round_4']
        predictions['initial_state']=predictions['uniform_raw_round_0']
        predictions['full_data_uniform']=predictions['uniform_raw_round_4']
        selected=d['selected']['error_prioritized'];ablation=dict(selected,tool_file='tool_round_0.joblib',tool_sha256=sha(folder/'tool_round_0.joblib'))
        predictions['error_priority_freeze_initial_tool']=predict(ablation)
        legacy=joblib.load(PRIVATE.parent/f'prismatic-v21/strong_seed_{seed}.joblib')
        old=joblib.load(PRIVATE.parent/'prismatic-v21/data.joblib')
        assert old['parts']['test'].hadm_id.tolist()==case_ids and old['truth']['test']==b['truth']
        predictions['legacy_word_char_reference']=legacy['predictions']['word_char_ensemble'];del old,legacy
        method_names=['initial_state','full_data_uniform','uniform','error_prioritized','permuted_priority','error_priority_freeze_initial_tool','legacy_word_char_reference']
        dump({'case_ids':case_ids,'predictions':predictions},folder/'all_test_predictions.joblib')
        save(report_path,{'status':'complete','seed':seed,'methods':{k:score(predictions[k],b['truth']) for k in method_names},
          'accepted_curves':curves,'raw_curves':raw_curves,'selection_sha256':frozen[str(seed)],
          'legacy_budget_note':'v21 word/character reference used early stopping and a regularization/ensemble search; only the three current feedback arms have identical exact epochs/exposures.',
          'interpretation':'Exploratory on the previously observed v21 test; no checkpoint is selected by these scores.'})
        print(json.dumps({'seed':seed,'methods':{k:score(predictions[k],b['truth'])['drug_micro_f1'] for k in method_names}}),flush=True)

if __name__=='__main__':main()
