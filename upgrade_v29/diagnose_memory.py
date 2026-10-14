"""Replay registered, proposal-only memory effects on frozen audited artifacts."""
import hashlib,json,sys
from pathlib import Path
import joblib,numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;sys.path.insert(0,str(ROOT/'upgrade_v27'))
from audit_controls import reconstruct
from evaluation_metrics import score
from audit import execute,change,probabilities
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v29';SOURCE=PRIVATE.parent/'prismatic-v27'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    result={'status':'partial','split':'proposal','test_inference':False,'new_model_calls':0,'runs':{},'protocol_sha256':sha(HERE/'diagnostic_addendum.json')}
    source=joblib.load(SOURCE/'visits.joblib')
    for panel in ['full','molecular']:
        b=joblib.load(SOURCE/(panel+'-models.joblib'));meds=b['medications'];x,gold,_,people,_=reconstruct(source['data']['proposal'],source['vocab'],meds)
        if panel=='molecular':gold=[g&set(meds) for g in gold]
        y=np.array([[m in g for m in meds] for g in gold]);counts=np.array([len(g) for g in gold])
        def evaluate(pred):
            metrics,patient,keys=score(pred,gold,people,meds);tp=(pred&y).sum(1);den=pred.sum(1)+counts
            visits=np.divide(2*tp,den,out=np.ones(len(tp)),where=den>0)
            return metrics,patient,visits
        for seed in [42,137,2026]:
            ap=HERE/f'results/{panel}-audit-seed{seed}.json'
            if not ap.exists():continue
            audit=json.loads(ap.read_text());assert audit['status']=='passed'
            state_file=HERE/f'results/{panel}-seed{seed}.json';assert audit['source_report_sha256']==sha(state_file)
            state=json.loads(state_file.read_text());folder=PRIVATE/f'{panel}-seed{seed}';prior=[];rows=[];last_effect=None;counts_out={'accepted_positive_transfer':0,'accepted_negative_transfer':0,'accepted_zero_transfer':0,'rejected_edits':0}
            for row in state['rounds']:
                part=folder/f'round{row["round"]}';fits=json.loads((part/'fits.json').read_text());prob=probabilities(joblib.load(part/fits['base_file']),x);thresholds=np.load(part/'thresholds.npy')
                final=json.loads((part/'memories.json').read_text())['own_error_program_agent'];evidence=json.loads((part/'own_error_program_agent-evidence.json').read_text())
                none,_,_=evaluate(execute([],x,prob,thresholds));carry,_,_=evaluate(execute(prior,x,prob,thresholds));complete,_,_=evaluate(execute(final,x,prob,thresholds))
                assert abs(complete['patient_f1']-row['arms']['own_error_program_agent']['proposal']['patient_f1'])<1e-12
                replay=list(prior);edits=[]
                for original in evidence['edits']:
                    candidate_state=change(replay,original['operation']);before=execute(replay,x,prob,thresholds);after=execute(candidate_state,x,prob,thresholds)
                    a,_,av=evaluate(before);b0,_,bv=evaluate(after);difference=b0['patient_f1']-a['patient_f1']
                    if original['accepted']:
                        label='positive' if difference>1e-12 else 'negative' if difference< -1e-12 else 'zero';counts_out['accepted_'+label+'_transfer']+=1
                    else:counts_out['rejected_edits']+=1
                    edits.append({'operation':original['operation'],'accepted_on_actual_witness':original['accepted'],
                      'witness_f1_delta':original['witness_after']['patient_f1']-original['witness_before']['patient_f1'],
                      'proposal_f1_delta':difference,'proposal_jaccard_delta':b0['patient_jaccard']-a['patient_jaccard'],
                      'affected_proposal_patients':len(set(people[np.any(before!=after,axis=1)])),
                      'proposal_visit_fixes':int(np.sum(bv>av+1e-12)),'proposal_visit_regressions':int(np.sum(bv<av-1e-12))})
                    if original['accepted']:replay=candidate_state
                assert replay==final
                carry_effect=carry['patient_f1']-none['patient_f1'];new_effect=complete['patient_f1']-none['patient_f1']
                rows.append({'round':row['round'],'calibrated_policy_f1':none['patient_f1'],'prior_memory_on_current_policy_f1':carry['patient_f1'],'current_memory_f1':complete['patient_f1'],
                  'carryover_memory_effect':carry_effect,'current_edits_effect':complete['patient_f1']-carry['patient_f1'],
                  'change_in_prior_memory_effect_since_previous_policy':None if last_effect is None else carry_effect-last_effect,'edits':edits})
                prior=final;last_effect=new_effect
            result['runs'][f'{panel}-seed{seed}']={'audit_sha256':sha(ap),'rounds':rows,**counts_out}
    if len(result['runs'])==6:result['status']='complete'
    result['scope']='Controlled replay on already used proposal cases; no new fitting, rule generation, decisions or test scores. Separates old-memory effect under the current policy from actual new-edit effect. These effects do not establish the outcome of a separately learned alternative trajectory.'
    (HERE/'results/memory_diagnostic.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'audited_runs':list(result['runs'])}),flush=True)
if __name__=='__main__':main()
