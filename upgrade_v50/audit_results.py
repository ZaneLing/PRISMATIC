"""Aggregate local predictions without publishing patient-level records."""
import json,collections,math
import numpy as np
from common import *
def counts(c,r):
    g={o['drug_name'] for o in c['gold']};p={o['drug_name'] for o in r['orders']};cat={o['drug_name'] for o in c['catalogue'].values()}
    prior={o['drug_name'] for o in c['context']['recorded_prior_orders']}
    g4={key(o) for o in c['gold'] if all(o.get(f) is not None for f in CORE)};p4={key(o) for o in r['orders'] if all(o.get(f) is not None for f in CORE)}
    drug_reachable_core={k for k in g4 if k[0] in p}
    cat4={key(o) for o in c['catalogue'].values() if all(o.get(f) is not None for f in CORE)}
    return {'tp':len(p&g),'pred':len(p),'gold':len(g),'fn':len(g-p),'fp':len(p-g),
      'catalogue_missing':len(g-cat),'selection_missing':len((g&cat)-p),'prior_gold':len(g&prior),'prior_hits':len(g&p&prior),
      'new_gold':len(g-prior),'new_hits':len((g-prior)&p),'core_hits':len(g4&p4),'core_pred':len(p4),'core_gold':len(g4),
      'core_reachable_given_drug':len(drug_reachable_core),'catalogue_core4_covered':len(g4&cat4),
      'no_labs':int(not c['context']['available_labs']),
      'all_predicted_tuples':len({key(o,FIELDS) for o in r['orders']}),
      'complete5_predicted_tuples':len({key(o,FIELDS) for o in r['orders'] if all(o.get(f) is not None for f in FIELDS)})}
def paired(cases,a,b,reps=2000):
    groups=collections.defaultdict(list)
    for i,c in enumerate(cases):groups[c['subject_hash']].append(i)
    groups=list(groups.values());d=[]
    ca=[counts(c,r) for c,r in zip(cases,a)];cb=[counts(c,r) for c,r in zip(cases,b)]
    arrays=[]
    for records in [ca,cb]:arrays.append(np.array([[sum(records[i][k] for i in group) for k in ['tp','pred','gold','core_hits','core_pred','core_gold']] for group in groups]))
    rng=np.random.default_rng(4916)
    for _ in range(reps):
        ix=rng.integers(len(groups),size=len(groups));sa=arrays[0][ix].sum(0);sb=arrays[1][ix].sum(0)
        d.append([2*sb[0]/max(1,sb[1]+sb[2])-2*sa[0]/max(1,sa[1]+sa[2]),2*sb[3]/max(1,sb[4]+sb[5])-2*sa[3]/max(1,sa[4]+sa[5])])
    return {'patients':len(groups),'resamples':reps,'drug_delta_ci95':np.quantile(np.array(d)[:,0],[.025,.975]).tolist(),
      'core4_delta_ci95':np.quantile(np.array(d)[:,1],[.025,.975]).tolist(),
      'changed_cases':sum({key(o,FIELDS) for o in x['orders']}!={key(o,FIELDS) for o in y['orders']} for x,y in zip(a,b)),
      'case_f1_improved':sum(score([y['orders']],[c['gold']])['drug_micro_f1']>score([x['orders']],[c['gold']])['drug_micro_f1'] for c,x,y in zip(cases,a,b)),
      'case_f1_regressed':sum(score([y['orders']],[c['gold']])['drug_micro_f1']<score([x['orders']],[c['gold']])['drug_micro_f1'] for c,x,y in zip(cases,a,b))}
def main():
    data=load_cases();cases=data['test'];methods={};private_cases=[]
    frozen=json.loads((PRIVATE/'test_freeze.json').read_text())
    for name in ['actor','evidence','common']:assert frozen[name+'_sha256']==sha(HERE/(name+'.py'))
    preparation=json.loads((HERE/'results/preparation.json').read_text());assert preparation['data_sha256']==sha(PRIVATE/'cases.json')
    seed=json.loads((PRIVATE/'flame-initial-seed.json').read_text())
    assert seed['case_ids']==[c['case_id'] for c in cases]
    seed_rows=[{'case_id':c['case_id'],'orders':[o for o in c['catalogue'].values() if o['drug_name'] in set(names)],'invalid':False}
      for c,names in zip(cases,seed['names'])]
    save(PRIVATE/'candidate-top8-test.json',{'rows':seed_rows})
    filenames={'rxrsi_base':'qwen-test-rxrsi_base.json','rxrsi_selected':'qwen-test-rxrsi_selected.json','direct':'qwen-test-direct.json','saferx':'qwen-test-saferx.json','skemex':'qwen-test-skemex.json','flame_list':'flame-list-test.json'}
    filenames['candidate_top8']='candidate-top8-test.json'
    raw={}
    for name,f in filenames.items():
        p=PRIVATE/f
        if not p.exists():continue
        rows=json.loads(p.read_text())['rows'];assert len(rows)==1082
        raw[name]=rows;total=collections.Counter()
        for c,r in zip(cases,rows):total.update(counts(c,r))
        methods[name]={'metrics':metrics(rows,cases),'counts':dict(total),'prediction_sha256':sha(p),
          'parsed_plan_fraction':sum(bool(parse(r.get('plan',''))) for r in rows)/len(rows),
          'parsed_assessment_fraction':sum(bool(parse(r.get('assessment',''))) for r in rows)/len(rows),
          'verified_fact_cases':sum(bool(r.get('checks',{}).get('verified_input_quotes')) for r in rows),
          'invalid_identifier_cases':sum(bool(r.get('invalid_ids')) for r in rows),
          'invalid_identifiers':sum(r.get('invalid_ids',0) for r in rows)}
        pairs=[({o['drug_name'] for o in c['gold']},{o['drug_name'] for o in r['orders']}) for c,r in zip(cases,rows)]
        methods[name]['descriptive_endpoints']={'drug_exact_set_accuracy':sum(g==p for g,p in pairs)/len(pairs),
          'mean_drug_jaccard':sum(len(g&p)/len(g|p) if g|p else 1.0 for g,p in pairs)/len(pairs),
          'missed_drugs_per_admission':total['fn']/len(cases),'extra_drugs_per_admission':total['fp']/len(cases),
          'prior_target_recall':total['prior_hits']/max(1,total['prior_gold']),
          'new_target_recall':total['new_hits']/max(1,total['new_gold']),
          'catalogue_core4_recall_ceiling':total['catalogue_core4_covered']/max(1,total['core_gold']),
          'joint_fields_recall_given_correct_drug':total['core_hits']/max(1,total['core_reachable_given_drug']),
          'core4_prediction_field_coverage':total['core_pred']/max(1,total['all_predicted_tuples']),
          'core5_prediction_field_coverage':total['complete5_predicted_tuples']/max(1,total['all_predicted_tuples']),
          'reference_relative_not_clinical_harm':True}
    contrasts={}
    if 'rxrsi_selected' in raw:
        for name in raw:
            if name!='rxrsi_selected':contrasts[name+'_to_rxrsi']=paired(cases,raw[name],raw['rxrsi_selected'])
    transfer_files=[PRIVATE/'llama-test-rxrsi_base.json',PRIVATE/'llama-test-rxrsi_selected.json']
    transfer=paired(cases,*[json.loads(p.read_text())['rows'] for p in transfer_files]) if all(p.exists() for p in transfer_files) else None
    # Training case studies only; raw materials stay credentialed and local.
    streams=[('corrected_interface',data['train'],'train')]
    patterns=collections.Counter()
    for phase,stream,prefix in streams:
      for r in range(1,7):
        before=PRIVATE/f'{prefix}-before-{r}.json';after=PRIVATE/f'{prefix}-after-{r}.json'
        if not before.exists():continue
        a=json.loads(before.read_text())['rows'];bb=json.loads(after.read_text())['rows'] if after.exists() else None
        for i,(c,x) in enumerate(zip(stream[(r-1)*24:r*24],a)):
            assert c['case_id']==x['case_id']
            ct=counts(c,x);later=counts(c,bb[i]) if bb else None
            patterns['training_cases']+=1
            patterns['cases_with_catalogue_misses']+=bool(ct['catalogue_missing'])
            patterns['cases_with_selection_misses']+=bool(ct['selection_missing'])
            patterns['cases_with_joint_field_loss']+=ct['core_reachable_given_drug']>ct['core_hits']
            patterns['cases_with_reference_relative_extras']+=bool(ct['fp'])
            if ct['fn'] or ct['fp']:
                old=score([x['orders']],[c['gold']]);new=score([bb[i]['orders']],[c['gold']]) if bb else None
                private_cases.append({'phase':phase,'round':r,'case_id':c['case_id'],'available_context':c['context'],
                  'reference':c['gold'],'before':x['orders'],'after':bb[i]['orders'] if bb else None,
                  'before_trace':{k:x.get(k) for k in ['plan','assessment','checks','evidence']},
                  'after_trace':{k:bb[i].get(k) for k in ['plan','assessment','checks','evidence']} if bb else None,
                  'drug_f1_before':old['drug_micro_f1'],'drug_f1_after':new['drug_micro_f1'] if new else None,
                  'error_counts_before':ct,'error_counts_after':later})
    save(PRIVATE/'failure_case_studies.json',private_cases)
    prior_root=PRIVATE.parent/'prismatic-v49';engineering={}
    if 'rxrsi_base' in raw:
        old=json.loads((prior_root/'qwen-test-rxrsi_base.json').read_text())['rows']
        engineering={'old_metrics':metrics(old,cases),'new_metrics':methods['rxrsi_base']['metrics'],
          'paired':paired(cases,old,raw['rxrsi_base']),'classification':'researcher output-interface repair, not accepted RSI update'}
    save(HERE/'results/audit.json',{'methods':methods,'paired_patient_bootstrap':contrasts,'private_training_case_studies':len(private_cases),
      'engineering_schema_repair':engineering,
      'training_error_pattern_counts':dict(patterns),'transfer_paired_patient_bootstrap':transfer,
      'api_cost_usd':0,'external_patient_requests':0,'full_test_cases':1082,'clinical_safety_validation':False})
    print({k:round(100*v['metrics']['drug_micro_f1'],2) for k,v in methods.items()})
if __name__=='__main__':main()
