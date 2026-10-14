"""Evaluate the external hospital holdout only after all choices freeze."""
import json,time
import numpy as np,joblib
from data_contract import HERE,PRIVATE,FIELDS,sha,digest,save
from learning import ranked_rows,choose,score,retrieval_probs,dump

def main():
    protocol=json.loads((HERE/'protocol.json').read_text());selections={}
    for seed in protocol['seeds']:
        p=HERE/f'results/selection_seed_{seed}.json';s=json.loads(p.read_text());assert s['status']=='selection_frozen' and not s['test_loaded']
        assert s['protocol_sha256']==sha(HERE/'protocol.json');selections[seed]=s
    hashes={str(seed):sha(HERE/f'results/selection_seed_{seed}.json') for seed in selections};lock=HERE/'results/frozen_before_test.json'
    frozen={'selections_sha256':hashes,'test_used_for_selection':False,'protocol_sha256':sha(HERE/'protocol.json')}
    if lock.exists():assert json.loads(lock.read_text())==frozen
    else:save(lock,frozen)
    meta=json.loads((HERE/'results/feature_manifest.json').read_text());assert sha(PRIVATE/'sealed_evaluation.joblib')==meta['sealed_evaluation_sha256']
    b=joblib.load(PRIVATE/'sealed_evaluation.joblib');ids=[c['case_id'] for c in b['cases']];classes=b['classes']
    rp=PRIVATE/'retrieval_test.joblib'
    if rp.exists():
        retrieved=joblib.load(rp);assert retrieved['case_ids']==ids
    else:
        dev=joblib.load(PRIVATE/'development.joblib');p=retrieval_probs(dev['train']['x'],dev['y'],b['x']);del dev
        retrieved={'case_ids':ids,'probabilities':p};dump(retrieved,rp)
    for seed,s in selections.items():
        report=HERE/f'results/test_seed_{seed}.json'
        if report.exists() and json.loads(report.read_text())['status']=='complete':continue
        folder=PRIVATE/f'seed_{seed}';cache=folder/'evaluation_cache';cache.mkdir(exist_ok=True)
        predictions={};curves={};raw_curves={}
        def predict(state):
            signature=digest([state['policy_sha256'],state['tool_sha256'],state['threshold'],digest(ids),meta['sealed_evaluation_sha256']])
            path=cache/(signature+'.joblib')
            if path.exists():
                saved=joblib.load(path);assert saved['case_ids']==ids;return saved['predictions']
            model=joblib.load(folder/state['policy_file']);assert model.sha256==state['policy_sha256']
            assert sha(folder/state['tool_file'])==state['tool_sha256'];tool=joblib.load(folder/state['tool_file']);start=time.time()
            rows,p=ranked_rows(model.predict_proba(b['x']),tool,b['word'],classes);pred=choose(rows,p,state['threshold'])
            dump({'case_ids':ids,'predictions':pred,'state':state,'seconds':time.time()-start},path);return pred
        for arm,states in s['raw_states'].items():
            journal=json.loads((HERE/f'results/journal_seed_{seed}_{arm}.json').read_text());curves[arm]=[];raw_curves[arm]=[]
            for j,state in zip(journal,states):
                assert j['candidate']==state
                for kind,chosen in [('raw',state),('active',j['active'])]:
                    pred=predict(chosen);predictions[f'{arm}_{kind}_round_{j["round"]}']=pred
                    (raw_curves if kind=='raw' else curves)[arm].append({'round':j['round'],'active_state_round':chosen['round'],'metrics':score(pred,b['truth'])})
            predictions[arm]=predictions[f'{arm}_active_round_4']
        predictions['initial_state']=predictions['uniform_raw_round_0'];predictions['full_data_uniform']=predictions['uniform_raw_round_4']
        chosen=s['selected']['error_prioritized'];initial=dict(chosen,tool_file='tool_round_0.joblib',tool_sha256=sha(folder/'tool_round_0.joblib'))
        predictions['error_priority_initial_tool']=predict(initial)
        init_policy=s['raw_states']['uniform'][0];final_tool=dict(init_policy,tool_file=s['static_tool_file'],tool_sha256=s['static_tool_sha256'])
        predictions['initial_policy_final_tool']=predict(final_tool)
        static=joblib.load(folder/'static_controls.joblib');tool=joblib.load(folder/s['static_tool_file']);assert sha(folder/s['static_tool_file'])==s['static_tool_sha256']
        probs={k:m.predict_proba(b[k]) for k,m in static['static_models'].items()}
        for name,choice in s['static'].items():
            if name=='reuse_prior_orders':
                pred=[];allowed=set(classes)
                for c in b['cases']:
                    seen=set();row=[]
                    for o in c['context']['prior_orders']:
                        n=o['drug_code']
                        if n not in allowed or n in seen:continue
                        seen.add(n);row.append({f:o[f] for f in FIELDS})
                        if len(row)==20:break
                    pred.append(row)
            else:
                if name=='prevalence_global':p=np.tile(static['prevalence'],(len(ids),1))
                elif name=='retrieval_conditional':p=retrieved['probabilities']
                elif name=='word_char_ensemble':p=choice['word_weight']*probs['word']+(1-choice['word_weight'])*probs['char']
                else:p=probs['word']
                rows,q=ranked_rows(p,tool,b['word'],classes,choice.get('conditional',True));pred=choose(rows,q,choice['threshold'])
            predictions[name]=pred
        method_names=['initial_state','prevalence_global','reuse_prior_orders','retrieval_conditional','word_global','word_conditional','word_char_ensemble',
          'full_data_uniform','uniform','error_prioritized','permuted_priority','error_priority_initial_tool','initial_policy_final_tool']
        dump({'case_ids':ids,'predictions':predictions},folder/'all_test_predictions.joblib')
        save(report,{'status':'complete','seed':seed,'methods':{k:score(predictions[k],b['truth']) for k in method_names},
          'accepted_curves':curves,'raw_curves':raw_curves,'selection_sha256':hashes[str(seed)],'evaluation_source_sha256':sha(HERE/'evaluate.py'),
          'test_used_for_selection':False,'scope':protocol['claim_boundary']})
        print(json.dumps({'seed':seed,'test_complete':True,'methods':{k:score(predictions[k],b['truth'])['drug_micro_f1'] for k in method_names}}),flush=True)

if __name__=='__main__':main()
