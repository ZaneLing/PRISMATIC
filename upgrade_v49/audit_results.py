"""Aggregate local predictions without publishing patient-level records."""
import json,collections,math
import numpy as np
from common import *
def counts(c,r):
    g={o['drug_name'] for o in c['gold']};p={o['drug_name'] for o in r['orders']};cat={o['drug_name'] for o in c['catalogue'].values()}
    prior={o['drug_name'] for o in c['context']['recorded_prior_orders']}
    g4={key(o) for o in c['gold'] if all(o.get(f) is not None for f in CORE)};p4={key(o) for o in r['orders'] if all(o.get(f) is not None for f in CORE)}
    drug_reachable_core={k for k in g4 if k[0] in p}
    return {'tp':len(p&g),'pred':len(p),'gold':len(g),'fn':len(g-p),'fp':len(p-g),
      'catalogue_missing':len(g-cat),'selection_missing':len((g&cat)-p),'prior_gold':len(g&prior),'prior_hits':len(g&p&prior),
      'new_gold':len(g-prior),'new_hits':len((g-prior)&p),'core_hits':len(g4&p4),'core_pred':len(p4),'core_gold':len(g4),
      'core_reachable_given_drug':len(drug_reachable_core),'no_labs':int(not c['context']['available_labs'])}
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
      'changed_cases':sum(x['orders']!=y['orders'] for x,y in zip(a,b)),
      'case_f1_improved':sum(score([y['orders']],[c['gold']])['drug_micro_f1']>score([x['orders']],[c['gold']])['drug_micro_f1'] for c,x,y in zip(cases,a,b)),
      'case_f1_regressed':sum(score([y['orders']],[c['gold']])['drug_micro_f1']<score([x['orders']],[c['gold']])['drug_micro_f1'] for c,x,y in zip(cases,a,b))}
def main():
    data=load_cases();cases=data['test'];methods={};private_cases=[]
    filenames={'rxrsi_base':'qwen-test-rxrsi_base.json','rxrsi_selected':'qwen-test-rxrsi_selected.json','direct':'qwen-test-direct.json','saferx':'qwen-test-saferx.json','skemex':'qwen-test-skemex.json','flame_list':'flame-list-test.json'}
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
          'verified_fact_cases':sum(bool(r.get('checks',{}).get('verified_input_quotes')) for r in rows)}
    contrasts={}
    if 'rxrsi_selected' in raw:
        for name in raw:
            if name!='rxrsi_selected':contrasts[name+'_to_rxrsi']=paired(cases,raw[name],raw['rxrsi_selected'])
    # Training case studies only; raw materials stay credentialed and local.
    for r in range(1,4):
        before=PRIVATE/f'train-before-{r}.json';after=PRIVATE/f'train-after-{r}.json'
        if not before.exists():continue
        a=json.loads(before.read_text())['rows'];bb=json.loads(after.read_text())['rows'] if after.exists() else None
        for i,(c,x) in enumerate(zip(data['train'][(r-1)*24:r*24],a)):
            ct=counts(c,x)
            if ct['fn'] or ct['fp']:
                private_cases.append({'round':r,'case_id':c['case_id'],'available_context':c['context'],
                  'reference':c['gold'],'before':x['orders'],'after':bb[i]['orders'] if bb else None,
                  'error_counts_before':ct,'error_counts_after':counts(c,bb[i]) if bb else None})
    save(PRIVATE/'failure_case_studies.json',private_cases)
    save(HERE/'results/audit.json',{'methods':methods,'paired_patient_bootstrap':contrasts,'private_training_case_studies':len(private_cases),
      'api_cost_usd':0,'external_patient_requests':0,'full_test_cases':1082,'clinical_safety_validation':False})
    print({k:round(100*v['metrics']['drug_micro_f1'],2) for k,v in methods.items()})
if __name__=='__main__':main()
