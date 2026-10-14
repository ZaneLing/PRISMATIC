"""Freeze ordinary proposal calibration, then evaluate every repaired state through a gate."""
import argparse,hashlib,json,sys,time
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;sys.path[:0]=[str(HERE),str(ROOT/'upgrade_v31')]
from views import view
from evaluation_gate import check
from evaluation_metrics import outputs,direct,evidence,probability_metrics,compile_metrics,contrast,invariance
from inference import Scorer,digest,sha,save_once
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v32';MODEL=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/models/qwen3-4b-instruct-2507-4bit'
def sources():
    names=['protocol.json','evaluation_addendum.json','inference.py','evaluate.py','evaluation_metrics.py','evaluation_gate.py','decision_loss.py'];out={str((HERE/n).relative_to(ROOT)):sha(HERE/n) for n in names}
    out.update({f'upgrade_v31/views.py':sha(ROOT/'upgrade_v31/views.py'),f'upgrade_v7/rx_agent.py':sha(ROOT/'upgrade_v7/rx_agent.py')});return out
def state_inventory():
    protocol=json.loads((HERE/'protocol.json').read_text());old=PRIVATE.parent/'prismatic-v31/seed42/permuted_uniform-round1/adapter';assert sha(old/'adapters.safetensors')==protocol['source_adapter_sha256']
    states={'frozen_base':{'adapter':None,'version':sha(MODEL/'model.safetensors')},'original_failed_adapter':{'adapter':old,'version':sha(old/'adapters.safetensors')}}
    for arm in protocol['arms']:
        p=PRIVATE/arm/'adapter';receipt=json.loads((PRIVATE/arm/'training_complete.json').read_text());assert sha(p/'adapters.safetensors')==receipt['adapter_sha256'];states[arm]={'adapter':p,'version':receipt['adapter_sha256']}
    return states
def select_threshold(probabilities,cases_by_view):
    curve=[];best=None
    for integer in range(1,100):
        threshold=integer/100.;metrics={kind:compile_metrics(probabilities[kind],cases,threshold)[0] for kind,cases in cases_by_view.items()};objective=float(np.mean([m['promotion_score'] for m in metrics.values()]));curve.append({'threshold':threshold,'objective':objective})
        if best is None or objective>best['objective']+1e-12 or abs(objective-best['objective'])<=1e-12 and threshold>best['threshold']:best={'threshold':threshold,'objective':objective}
    return {**best,'grid_objectives':curve}
def summarize(probabilities,cases_by_view,selected):
    endpoints={};rows={};predictions={};controls=['original_retrieval_top8','all20_candidate_tools'];arms=json.loads((HERE/'protocol.json').read_text())['arms']
    for endpoint in ['fixed_half','proposal_calibrated']:
        endpoints[endpoint]={};rows[endpoint]={};predictions[endpoint]={}
        for kind,cases in cases_by_view.items():
            scores={};evidences={};orders={}
            for name,views in probabilities.items():
                threshold=.5 if endpoint=='fixed_half' else selected[name]['threshold'];orders[name]=outputs(views[kind],cases,threshold);scores[name],evidences[name]=evidence(orders[name],cases);scores[name].update(threshold=threshold,**probability_metrics(views[kind],cases))
            for name,n in zip(controls,[8,20]):orders[name]=direct(cases,n);scores[name],evidences[name]=evidence(orders[name],cases)
            definitions={'zero_uniform_minus_teacher_uniform':[(1,'zero_uniform'),(-1,'teacher_uniform')],'zero_balanced_minus_teacher_balanced':[(1,'zero_balanced'),(-1,'teacher_balanced')],'zero_balanced_minus_zero_uniform':[(1,'zero_balanced'),(-1,'zero_uniform')],'teacher_balanced_minus_teacher_uniform':[(1,'teacher_balanced'),(-1,'teacher_uniform')],'prefix_by_balance_interaction':[(1,'zero_balanced'),(-1,'teacher_balanced'),(-1,'zero_uniform'),(1,'teacher_uniform')]}
            for arm in arms:
                for baseline in ['frozen_base','original_failed_adapter']+controls:definitions[arm+'_minus_'+baseline]=[(1,arm),(-1,baseline)]
            contrasts={name:contrast([(w,evidences[method]) for w,method in terms]) for name,terms in definitions.items()};endpoints[endpoint][kind]={'methods':scores,'contrasts':contrasts};rows[endpoint][kind]=evidences;predictions[endpoint][kind]=orders
    calibration={kind:{name:contrast([(1,rows['proposal_calibrated'][kind][name]),(-1,rows['fixed_half'][kind][name])]) for name in probabilities} for kind in cases_by_view};stable={}
    for endpoint,views in predictions.items():
        stable[endpoint]={kind:{name:invariance(views['ranked'][name],methods[name]) for name in methods} for kind,methods in views.items() if kind!='ranked'}
    return {'endpoints':endpoints,'calibration_only_contrasts':calibration,'view_invariance':stable}
def main(split):
    gate=check(split)
    if gate['status']!='open':raise RuntimeError('Repair evaluation remains closed: '+','.join(gate['pending']))
    audit=json.loads((HERE/'results/data_audit.json').read_text());states=state_inventory();config=json.loads((PRIVATE/'decision_config.json').read_text());assert sha(PRIVATE/'decision_config.json')==audit['decision_config_sha256'] and sha(PRIVATE/'proposal.json')==audit['prepared_proposal_sha256']
    lock={'source_sha256':sources(),'training_audit_sha256':sha(HERE/'results/training_audit.json'),'proposal_sha256':sha(PRIVATE/'proposal.json'),'source_cases_sha256':audit['source_cases_sha256'],'decision_config_sha256':sha(PRIVATE/'decision_config.json'),'state_versions':{k:s['version'] for k,s in states.items()},'batch_size':4};save_once(PRIVATE/'evaluation_lock.json',lock)
    output=HERE/f'results/{split}_summary.json'
    if output.exists():
        z=json.loads(output.read_text());assert z['status']=='executed_pending_independent_audit' and z['evaluation_lock_sha256']==sha(PRIVATE/'evaluation_lock.json')
        if split=='proposal':save_once(PRIVATE/'frozen_thresholds.json',{'selection':z['selected_thresholds'],'proposal_summary_sha256':sha(output),'evaluation_lock_sha256':sha(PRIVATE/'evaluation_lock.json'),'guard_inference_preceded_selection':False})
        print(json.dumps({'status':'already_complete','split':split}),flush=True);return
    if split=='proposal':original=json.loads((PRIVATE/'proposal.json').read_text());conditions=['ranked','permuted'];selected={}
    else:
        source=PRIVATE.parent/'prismatic-v31/cases.json';assert sha(source)==lock['source_cases_sha256'];original=json.loads(source.read_text())['guard'];conditions=['ranked','permuted','reversed'];frozen=json.loads((PRIVATE/'frozen_thresholds.json').read_text());selected=frozen['selection'];assert frozen['evaluation_lock_sha256']==sha(PRIVATE/'evaluation_lock.json')
    cases={kind:[view(c,kind) for c in original] for kind in conditions};probabilities={};binding_hashes={};start=time.perf_counter()
    for name,state in states.items():
        scorer=Scorer(MODEL,state['adapter'],state['version'],PRIVATE/'inference'/name,config,digest(lock));probabilities[name]={};binding_hashes[name]={}
        try:
            for kind,group in cases.items():
                binding=f'{split}-{kind}';probabilities[name][kind]=scorer.score(group,binding);binding_hashes[name][kind]=sha(PRIVATE/'inference'/name/'bindings'/f'{binding}.json')
        finally:scorer.close()
        if split=='proposal':selected[name]=select_threshold(probabilities[name],cases)
    accounting={}
    for name in states:
        bindings=[r for kind in conditions for r in json.loads((PRIVATE/'inference'/name/'bindings'/f'{split}-{kind}.json').read_text())];unique={r['signature'] for r in bindings};raw=[json.loads((PRIVATE/'inference'/name/'raw'/f'{s}.json').read_text()) for s in unique]
        accounting[name]={'logical_case_views':len(bindings),'unique_prompts_in_split':len(unique),'forward_seconds_for_unique_prompts':sum(r['seconds_per_unique_prompt'] for r in raw),'scope':'Stored unique-forward time excluding model loading/tokenization; not marginal new cost if a prompt is reused in another split.'}
    report={'status':'executed_pending_independent_audit','split':split,'evaluation_lock_sha256':sha(PRIVATE/'evaluation_lock.json'),'evaluation_gate':gate,'cases':len(original),'patients':len({c['subject_hash'] for c in original}),'views':conditions,'state_versions':lock['state_versions'],'binding_sha256':binding_hashes,'selected_thresholds':selected,**summarize(probabilities,cases,selected),'inference_accounting':accounting,'wall_seconds_this_invocation':time.perf_counter()-start,'api_calls':0,'old_test_inference':False,'scope':'One-seed supervised repair; proposal data select ordinary thresholds, guard is reused report-only development data. Binary probabilities compile supplied order templates; no free dose generation, clinical validation or unique RSI claim.'};save_once(output,report)
    if split=='proposal':save_once(PRIVATE/'frozen_thresholds.json',{'selection':selected,'proposal_summary_sha256':sha(output),'evaluation_lock_sha256':sha(PRIVATE/'evaluation_lock.json'),'guard_inference_preceded_selection':False})
    print(json.dumps({'status':report['status'],'split':split,'cases':len(original)}),flush=True)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('split',choices=['proposal','guard']);args=parser.parse_args();main(args.split)
