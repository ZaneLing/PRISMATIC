"""Exercise the complete evaluation/recount flow on isolated synthetic receipts."""
import contextlib,copy,hashlib,importlib,io,json,subprocess,sys,tempfile
from pathlib import Path
import numpy as np
from transformers import AutoTokenizer
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;sys.path[:0]=[str(HERE),str(ROOT)]
import evaluate as runner
import audit_evaluation as auditor
from inference import encode,signature,digest,save_once,sha
def write(p,z):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(z)+'\n')
def main():
    closed=subprocess.run([sys.executable,str(HERE/'evaluate.py'),'proposal'],capture_output=True,text=True);assert closed.returncode!=0 and 'Repair evaluation remains closed:' in closed.stderr and 'ModuleNotFoundError' not in closed.stderr
    actual_model=runner.MODEL;tok=AutoTokenizer.from_pretrained(str(actual_model));config=json.loads((runner.PRIVATE/'decision_config.json').read_text());spec=json.loads((HERE/'protocol.json').read_text());source_names=list(runner.sources())+['upgrade_v32/audit_evaluation.py','upgrade_v32/audit_training.py']
    with tempfile.TemporaryDirectory(prefix='rxrsi-synthetic-repair-eval-') as tmp:
        root=Path(tmp);here=root/'upgrade_v32';private=root/'private/prismatic-v32';private.mkdir(parents=True)
        for name in source_names:
            out=root/name;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes((ROOT/name).read_bytes())
        catalogue={f'O{i+1}':{'drug_name':f'drug{i+1}','route':'oral','dose_value':str(i+1),'dose_unit':'mg','frequency_per_24h':'1'} for i in range(20)};cases=[]
        for i in range(4):
            gold=[catalogue['O1']] if i==0 else [catalogue['O2']] if i==1 else [{'drug_name':'unreachable','route':'oral','dose_value':'1','dose_unit':'mg','frequency_per_24h':'1'}] if i==2 else []
            cases.append({'case_id':f'synthetic{i+1}','subject_hash':'patient_one' if i<2 else 'patient_two','catalogue':copy.deepcopy(catalogue),'gold':copy.deepcopy(gold),'messages':[{'role':'system','content':'Synthetic research case; return an inclusion mask.'},{'role':'user','content':f'Synthetic context {min(i,2)}\nCandidate order tools:\nplaceholder'}]})
        guards=[{**copy.deepcopy(c),'case_id':'guard'+c['case_id'],'subject_hash':'guard'+c['subject_hash']} for c in cases]
        write(private/'proposal.json',cases);write(private.parent/'prismatic-v31/cases.json',{'validation':cases,'guard':guards});write(private/'decision_config.json',config)
        write(here/'results/data_audit.json',{'decision_config_sha256':sha(private/'decision_config.json'),'prepared_proposal_sha256':sha(private/'proposal.json'),'source_cases_sha256':sha(private.parent/'prismatic-v31/cases.json')});write(here/'results/training_audit.json',{'status':'passed','synthetic_fixture':True})
        names=['frozen_base','original_failed_adapter']+spec['arms'];states={name:{'adapter':None,'version':hashlib.sha256(name.encode()).hexdigest()} for name in names};reverse={v['version']:name for name,v in states.items()}
        class SyntheticScorer:
            def __init__(self,model_path,adapter,version,folder,cfg,source_signature):self.version=version;self.root=Path(folder);self.config=cfg;self.source_signature=source_signature
            def close(self):pass
            def score(self,group,binding):
                name=reverse[self.version];rows=[]
                for c in group:
                    context=c['messages'][1]['content'].split('\n')[0];index=int(context.rsplit(' ',1)[1]);values=[]
                    for rank in c['original_rank_by_position']:
                        if name=='frozen_base':value=.4 if rank==1 else .3 if rank==2 else .1
                        elif name=='original_failed_adapter':value=.2 if rank==1 else .15 if rank==2 else .05
                        elif name=='zero_uniform':value=(.8 if rank==index+1 else .1) if index<2 else .1
                        elif name=='teacher_uniform':value=.6 if rank==1 else .2
                        elif name=='zero_balanced':value=(.9 if rank==index+1 else .15) if index<2 else .15
                        else:value=.7 if rank in [1,2] else .3
                        values.append(value)
                    s=signature(c,self.version,self.source_signature,self.config);tokens,positions=encode(tok,c,self.config);raw={'signature':s,'state_version':self.version,'inference_source_signature':self.source_signature,'prompt_sha256':digest(c['messages']),'conditional_probabilities':values,'input_tokens':len(tokens),'decision_positions':positions,'actual_batch_size':1,'seconds_per_unique_prompt':.01};p=self.root/'raw'/f'{s}.json';save_once(p,raw);rows.append({'case_id':c['case_id'],'subject_hash':c['subject_hash'],'signature':s,'raw_sha256':sha(p),'conditional_probabilities':values})
                save_once(self.root/'bindings'/f'{binding}.json',rows);return np.asarray([r['conditional_probabilities'] for r in rows])
        synthetic_gate=lambda split:{'status':'open','pending':[],'proof':{'synthetic_fixture':True}}
        runner.ROOT=root;runner.HERE=here;runner.PRIVATE=private;runner.state_inventory=lambda:copy.deepcopy(states);runner.check=synthetic_gate;runner.Scorer=SyntheticScorer
        auditor.ROOT=root;auditor.HERE=here;auditor.PRIVATE=private;auditor.MODEL=actual_model;importlib.import_module('evaluation_gate').check=synthetic_gate
        with contextlib.redirect_stdout(io.StringIO()):runner.main('proposal');auditor.main('proposal');runner.main('guard');auditor.main('guard')
        result=json.loads((here/'results/proposal_summary.json').read_text());assert result['selected_thresholds']['zero_uniform']['threshold']==.8
        base_fixed=result['endpoints']['fixed_half']['ranked']['methods']['frozen_base']['drug_micro_f1'];base_cal=result['endpoints']['proposal_calibrated']['ranked']['methods']['frozen_base']['drug_micro_f1'];assert base_cal>base_fixed
        before={split:sha(here/f'results/{split}_summary.json') for split in ['proposal','guard']}
        with contextlib.redirect_stdout(io.StringIO()):runner.main('proposal');runner.main('guard')
        assert all(sha(here/f'results/{split}_summary.json')==h for split,h in before.items());audits=[json.loads((here/f'results/{split}_audit.json').read_text()) for split in ['proposal','guard']];assert all(a['status']=='passed' for a in audits);assert sum(a['case_probability_bindings_recounted'] for a in audits)==120
        assert audits[0]['unique_prompt_receipts_recounted']<audits[0]['case_probability_bindings_recounted']
        reporter=importlib.import_module('report');reporter.HERE=here;reporter.PRIVATE=private
        with contextlib.redirect_stdout(io.StringIO()):reporter.main()
        for lang in ['en','zh']:
            text=(here/f'RESULTS.{lang}.md').read_text()
            assert 'proposal_calibrated' in text and 'fixed_half' in text and 'prefix_by_balance_interaction' in text
            assert all('| '+name+' |' in text for name in names+['original_retrieval_top8','all20_candidate_tools'])
    proof={'status':'passed','synthetic_only':True,'clinical_model_inference':0,'real_guard_or_test_predictions_read':False,'real_proposal_entry_refuses_incomplete_training':True,'synthetic_case_probability_bindings_recounted':120,'source_sha256':{name:sha(ROOT/name) for name in source_names},'probe_sha256':sha(Path(__file__)),'checks':['six_neural_states_and_two_direct_controls','all99_thresholds_and_highest_tie_rule','fixed_vs_calibrated_decisions','unreachable_GT_and_empty_GT_preserved','duplicate_patient_cluster_and_duplicate_prompt_binding','factorial_and_calibration_only_contrasts','ranked_permuted_reversed_identity_transport','independent_source_and_score_recount','completed_result_resume_byte_identical']};(HERE/'results/evaluation_probe.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof),flush=True)
if __name__=='__main__':main()
