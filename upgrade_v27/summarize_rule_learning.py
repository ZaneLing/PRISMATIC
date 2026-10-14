"""Aggregate only audited rule-development runs, preserving all comparators."""
import hashlib,json
from pathlib import Path
import numpy as np
from evaluation_metrics import paired
HERE=Path(__file__).resolve().parent;PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v27'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    result={'status':'partial','split':'guard','test_inference':False,'panels':{}}
    for panel in ['full','molecular']:
        audits=[];per_seed=[];seeds=[]
        for seed in [42,137,2026]:
            path=HERE/f'results/{panel}-rsi-learning-audit-seed{seed}.json';cross=HERE/f'results/{panel}-rsi-crossfit-audit-seed{seed}.json'
            if not path.exists() or not cross.exists():continue
            audit=json.loads(path.read_text());check=json.loads(cross.read_text())
            assert audit['status']=='passed' and audit['source_report_sha256']==sha(HERE/f'results/{panel}-rsi-seed{seed}.json')
            if check['status']!='complete':continue
            for f,h in audit['auditor_sources'].items():assert sha(HERE/f)==h
            z=np.load(PRIVATE/f'{panel}-rsi-seed{seed}/audited-guard-patient-scores.npz')
            if per_seed:np.testing.assert_array_equal(z['people'],per_seed[0]['people'])
            audits.append(audit);per_seed.append({k:z[k] for k in z.files});seeds.append(seed)
        if not audits:continue
        arms={};curves={}
        for arm in audits[0]['guard']:
            scores=[a['guard'][arm] for a in audits]
            arms[arm]={k:{'mean':float(np.mean([z[k] for z in scores])),'seed_sd':float(np.std([z[k] for z in scores],ddof=1)) if len(scores)>1 else None} for k in scores[0] if isinstance(scores[0][k],(float,int))}
            curves[arm]=[{'round':r+1,'training_patients':[a['rounds'][r]['training_patients'] for a in audits],
              'proposal_patient_f1':[a['rounds'][r]['arms'][arm]['proposal_metrics']['patient_f1'] for a in audits],
              'proposal_patient_jaccard':[a['rounds'][r]['arms'][arm]['proposal_metrics']['patient_jaccard'] for a in audits],
              'memory_size':[a['rounds'][r]['arms'][arm]['memory_size'] for a in audits]} for r in range(5)]
        own=np.array([z['own_error_rule_agent'] for z in per_seed])
        contrasts={name:paired(own,np.array([z[name] for z in per_seed])) for name in ['uniform_policy','greedy_error_rules','random_candidate_rules','shuffled_evidence_rule_agent','matched_proposals_without_witness_gate']}
        result['panels'][panel]={'seeds':seeds,'methods':arms,'own_agent_minus_control':contrasts,'proposal_curves':curves,
          'patients':len(per_seed[0]['people']),'visits':audits[0]['guard']['own_error_rule_agent']['visits']}
    if len(result['panels'])==2 and all(len(v['seeds'])==3 for v in result['panels'].values()):result['status']='complete'
    result['claim_boundary']='Report-only development patients; proposal curves include model/round selection. Patient intervals average observed seeds before 4000 resamples and are not hierarchical seed uncertainty. Cross-fit and candidate/output audits passed for included seeds; witness decisions have a separate receipt. More data improving the shared predictor does not establish a unique language-agent evolution gain.'
    (HERE/'results/rsi_development_summary.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'seeds':{k:v['seeds'] for k,v in result['panels'].items()}}),flush=True)
if __name__=='__main__':main()
