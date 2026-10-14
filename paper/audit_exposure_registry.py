"""Independently rebuild identity-only legacy sampling and exclusion membership."""
import datetime,hashlib,json
from pathlib import Path
import pandas as pd
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def digest(z):return hashlib.sha256(json.dumps(z,sort_keys=True).encode()).hexdigest()
def bucket(x,salt):return int.from_bytes(hashlib.blake2b((salt+':'+str(x)).encode(),digest_size=8).digest(),'big')
def part(x):
    i=bucket(x,'patient-split-2026')%10
    return 'test' if i==0 else ('val' if i==1 else 'train')
def choose(frame,split,cap,sort_first=False):
    subset=frame[frame.split==split]
    if sort_first:subset=subset.sort_values('hadm_id')
    assert subset.hadm_id.is_unique
    if len(subset)>cap:
        ranks=[bucket(v,'sample-2026') for v in subset.hadm_id];assert len(set(ranks))==len(ranks)
        subset=subset.iloc[sorted(range(len(ranks)),key=ranks.__getitem__)[:cap]]
    return subset
def main():
    path=PRIVATE/'prismatic-exposure/membership.json';frozen=json.loads(path.read_text());public=json.loads((HERE/'exposure_registry.json').read_text())
    assert sha(path)==public['membership_sha256'] and frozen['protocol_sha256']==sha(HERE/'prior_case_exclusion_protocol.json')
    assert frozen['builder_sha256']==sha(HERE/'build_exposure_registry.py')
    for name,h in frozen['sources'].items():assert sha((PRIVATE if name.startswith('private/') else ROOT)/name.split('/',1)[1])==h
    expected={};rows={}
    def read(name,columns):return pd.read_parquet(PRIVATE/name,columns=columns)
    def collect(name,roles):
        expected[name]={};rows[name]={}
        for role,x in roles.items():
            people={digest(str(s)) for s in x.subject_id} if isinstance(x,pd.DataFrame) else {c['subject_hash'] for c in x}
            expected[name][role]=people;rows[name][role]=len(x)
    for interval in ('6h','24h'):
        f=read(f'prismatic-v2/cohort_{interval}.parquet',['subject_id','hadm_id']);f['split']=f.subject_id.map(part)
        z=json.loads((ROOT/f'upgrade_v2/results/baseline_results_{interval}.json').read_text());collect('v2_'+interval,{s:choose(f,s,n) for s,n in z['sampled_admissions'].items()})
    f=read('prismatic-v2/supportive_cohort_6h.parquet',['subject_id','hadm_id']);f['split']=f.subject_id.map(part)
    z=json.loads((ROOT/'upgrade_v2/results/evolution_curve.json').read_text());collect('v2_legacy_support',{'train':choose(f,'train',z['training_cases_available']),'test':choose(f,'test',z['test_cases'])})
    f=read('prismatic-v3/cohort_atc4_6h.parquet',['subject_id','hadm_id','split']);assert f.subject_id.map(part).equals(f.split)
    z=json.loads((ROOT/'upgrade_v3/results/atc4_method_pilot.json').read_text());collect('v3',{s:choose(f,s,n,True) for s,n in z['sampled_admissions'].items()})
    f=read('prismatic-v4/cohort.parquet',['subject_id','hadm_id','split']);assert f.subject_id.map(part).equals(f.split)
    old={s:choose(f,s,n,True) for s,n in [('train',40000),('val',4000),('test',4000)]};collect('v4_v5_v6',old)
    val=f[(f.split=='val')&~f.subject_id.isin(old['val'].subject_id)].copy();val['bucket']=val.subject_id.map(lambda s:int(digest('v7-guard-'+str(s))[:8],16)%2)
    test=f[(f.split=='test')&~f.subject_id.isin(old['test'].subject_id)]
    collect('v7',{'train':old['train'],'proposal':choose(val[val.bucket==0],'val',2000,True),'guard':choose(val[val.bucket==1],'val',2000,True),'test':choose(test,'test',4000,True)})
    review=pd.read_csv(PRIVATE/'prismatic-v3/review_manifest.csv',dtype={'subject_id':str,'hadm_id':str});collect('prepared_review',{'reserved':review})
    for v in (9,15):
        data=json.loads((PRIVATE/f'prismatic-v{v}/cases.json').read_text());roles={k:x for k,x in data.items() if k!='blocks'};roles.update({f'feedback_block{i+1}':x for i,x in enumerate(data['blocks'])});collect(f'v{v}',roles)
    f=read('prismatic-v21/members.parquet',['subject_id','hadm_id','part']);collect('v21_v22_v23',{s:f[f.part==s] for s in ('train','proposal','guard','test')})
    f=read('prismatic-v27/members.parquet',['subject_id','hadm_id','part']);collect('current_v27_v29_v30',{s:f[f.part==s] for s in ('train','proposal','guard')})
    assert set(expected)==set(frozen['families'])==set(public['families'])
    unions={};role_count=0
    for name,roles in expected.items():
        assert set(roles)==set(frozen['families'][name]['roles']);unions[name]=set().union(*roles.values())
        for role,people in roles.items():
            p=frozen['families'][name]['roles'][role];q=public['families'][name]['roles'][role]
            assert sorted(people)==p['subject_hashes'] and len(people)==p['patients']==q['patients']
            assert rows[name][role]==p['admissions']==q['admissions'] and digest(sorted(people))==p['subject_membership_sha256']==q['subject_membership_sha256'];role_count+=1
    prior=set().union(*unions.values());test=f[f.part=='test'];reserved={digest(str(s)) for s in test.subject_id};kept=reserved-prior;excluded=reserved&prior
    for key,value in [('prior_union',prior),('reserved_test',reserved),('retained',kept),('excluded',excluded)]:assert sorted(value)==frozen[key]
    assignments={digest(['v27-visit',str(r.hadm_id)]):(digest(str(r.subject_id)),digest(str(r.subject_id)) in kept) for r in test.itertuples()}
    assert assignments=={r['case_id']:(r['subject_hash'],r['retained']) for r in frozen['test_assignments']}
    assert not kept&prior and len(assignments)==2422 and len(reserved)==890
    for name,union in unions.items():
        assert public['families'][name]['test_patient_overlap']==len(reserved&union)
        for other,pool in unions.items():assert public['pairwise_family_patient_overlap'][name][other]==len(union&pool)
    assert public['prior_union_patients']==len(prior) and public['retained_test_patients']==len(kept) and public['retained_test_visits']==sum(v[1] for v in assignments.values())
    assert not (ROOT/'upgrade_v27/results/test_summary.json').exists() and not (ROOT/'upgrade_v30/results/common_test_summary.json').exists()
    for folder in [PRIVATE/'prismatic-v27/evaluation',PRIVATE/'prismatic-v30/common-test']:assert not folder.exists() or not list(folder.iterdir())
    # Verify the alias claim against the actual prepared parameter studies.
    base=set().union(*expected['v15'].values())
    p31=json.loads((PRIVATE/'prismatic-v31/cases.json').read_text());all31=[c for b in p31['blocks'] for c in b]+p31['validation']+p31['guard'];assert {c['subject_hash'] for c in all31}<=base
    result={'status':'passed','auditor_sha256':sha(Path(__file__)),'registry_sha256':sha(HERE/'exposure_registry.json'),'private_membership_sha256':sha(path),'protocol_sha256':sha(HERE/'prior_case_exclusion_protocol.json'),'audit_time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'families_checked':len(expected),'roles_checked':role_count,'prior_union_patients':len(prior),'retained_test_patients':len(kept),'retained_test_visits':sum(v[1] for v in assignments.values()),'excluded_test_patients':len(excluded),'retained_prior_patient_overlap':0,'complete_patient_visit_retention':True,'test_execution_absent_at_independent_audit':True,'v31_parameter_membership_in_recorded_v15':True,'scope':'Independent deterministic-sampler reconstruction and stored patient identities, all role sets/counts/digests, overlaps and exact original-test subsetting. Covers named PRISMATIC histories; not undocumented use or foundation pretraining.'}
    (HERE/'exposure_registry_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['status','families_checked','roles_checked','retained_test_patients','retained_test_visits','retained_prior_patient_overlap']}))
if __name__=='__main__':main()
