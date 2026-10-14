"""Freeze patient exclusions from recorded experiment membership, without outcomes."""
import datetime,hashlib,json,sys
from pathlib import Path
import numpy as np,pandas as pd
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted';OUT=PRIVATE/'prismatic-exposure'
sys.path[:0]=[str(ROOT/'upgrade_v2'),str(ROOT/'upgrade_v3')]
from train_baselines import sampled_indices,stable_bucket
from run_atc4_methods import take
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()
def digest(z):return hashlib.sha256(json.dumps(z,sort_keys=True).encode()).hexdigest()
def save(p,z):
    t=p.with_suffix('.tmp');t.write_text(json.dumps(z,indent=2)+'\n');t.replace(p)
def main():
    OUT.mkdir(exist_ok=True);freeze=OUT/'membership.json'
    if freeze.exists():
        frozen=json.loads(freeze.read_text());assert frozen['protocol_sha256']==sha(HERE/'prior_case_exclusion_protocol.json') and frozen['builder_sha256']==sha(Path(__file__))
        for name,h in frozen['sources'].items():assert sha((PRIVATE if name.startswith('private/') else ROOT)/name.split('/',1)[1])==h
        print(json.dumps({'status':'existing_frozen_membership_verified','test_predictions_read':False}));return
    def no_test():
        assert not (ROOT/'upgrade_v27/results/test_summary.json').exists()
        assert not (ROOT/'upgrade_v30/results/common_test_summary.json').exists()
        for folder in [PRIVATE/'prismatic-v27/evaluation',PRIVATE/'prismatic-v30/common-test']:
            assert not folder.exists() or not list(folder.iterdir()),'Test execution already began; no retrospective clean-subset registration.'
    no_test();sources={};families={};checks=[]
    def track(path,base):sources[('private/' if base==PRIVATE else 'repo/')+str(path.relative_to(base))]=sha(path);return path
    def report(name):return json.loads(track(ROOT/name,ROOT).read_text())
    def frame(name,columns):return pd.read_parquet(track(PRIVATE/name,PRIVATE),columns=columns)
    def add(name,roles,proof):
        families[name]={'roles':{},'proof':proof}
        for role,rows in roles.items():
            if isinstance(rows,pd.DataFrame):people=sorted({digest(str(x)) for x in rows.subject_id});n=len(rows)
            else:people=sorted({c['subject_hash'] for c in rows});n=len(rows)
            families[name]['roles'][role]={'subject_hashes':people,'admissions':n,'patients':len(people),'subject_membership_sha256':digest(people)}
    for period in ['6h','24h']:
        f=frame(f'prismatic-v2/cohort_{period}.parquet',['subject_id','hadm_id']);f['split']=f.subject_id.map(lambda x:'test' if stable_bucket(x,'patient-split-2026')%10==0 else ('val' if stable_bucket(x,'patient-split-2026')%10==1 else 'train'))
        z=report(f'upgrade_v2/results/baseline_results_{period}.json');parts={s:f.iloc[sampled_indices(f,s,n)] for s,n in z['sampled_admissions'].items()}
        assert {s:len(p) for s,p in parts.items()}==z['sampled_admissions'] and {s:p.subject_id.nunique() for s,p in parts.items()}==z['sampled_patients']
        add('v2_'+period,parts,'Original deterministic sampler reconstructed; public per-role admission/patient counts match. No original membership hash was recorded.')
    f=frame('prismatic-v2/supportive_cohort_6h.parquet',['subject_id','hadm_id']);f['split']=f.subject_id.map(lambda x:'test' if stable_bucket(x,'patient-split-2026')%10==0 else ('val' if stable_bucket(x,'patient-split-2026')%10==1 else 'train'))
    z=report('upgrade_v2/results/evolution_curve.json');add('v2_legacy_support',{s:f.iloc[sampled_indices(f,s,n)] for s,n in [('train',z['training_cases_available']),('test',z['test_cases'])]},'Original deterministic sampler; historical membership only, no legacy endpoint recomputed.')
    f=frame('prismatic-v3/cohort_atc4_6h.parquet',['subject_id','hadm_id','split']);z=report('upgrade_v3/results/atc4_method_pilot.json');parts={s:take(f,s,n) for s,n in z['sampled_admissions'].items()}
    assert {s:p.subject_id.nunique() for s,p in parts.items()}==z['sampled_patients'];add('v3',parts,'Original deterministic sampler; recorded role counts match.')
    f=frame('prismatic-v4/cohort.parquet',['subject_id','hadm_id','split']);z=report('upgrade_v4/results/protocol_method_results.json');parts={s:take(f,s,n) for s,n in z['sample_sizes'].items()}
    assert sha(PRIVATE/'prismatic-v4/cohort.parquet')==z['cohort_sha256']
    assert {s:p.subject_id.nunique() for s,p in parts.items()}==z['sample_patients']
    assert {s:hashlib.sha256('\n'.join(sorted(p.hadm_id.astype(str))).encode()).hexdigest() for s,p in parts.items()}==z['split_member_sha256']
    add('v4_v5_v6',parts,'Source cohort hash and original admission membership hashes match; v5/v6 use the same deterministic selection.')
    val=f[(f.split=='val')&~f.subject_id.isin(parts['val'].subject_id)].copy();val['bucket']=val.subject_id.map(lambda s:int(digest('v7-guard-'+str(s))[:8],16)%2)
    test=f[(f.split=='test')&~f.subject_id.isin(parts['test'].subject_id)]
    p7={'train':parts['train'],'proposal':take(val[val.bucket==0],'val',2000),'guard':take(val[val.bucket==1],'val',2000),'test':take(test,'test',4000)};z=report('upgrade_v7/results/data_manifest.json')
    assert {s:digest(sorted(p.hadm_id.astype(str))) for s,p in p7.items()}==z['membership_sha256'];assert {s:p.subject_id.nunique() for s,p in p7.items()}==z['patients'];add('v7',p7,'All original role membership hashes and patient counts match.')
    review=pd.read_csv(track(PRIVATE/'prismatic-v3/review_manifest.csv',PRIVATE),dtype={'subject_id':str,'hadm_id':str});add('prepared_review',{'reserved':review},'Read saved manifest; conservatively exclude despite no completed clinician ratings.')
    for version in (9,15):
        z=json.loads(track(PRIVATE/f'prismatic-v{version}/cases.json',PRIVATE).read_text());roles={s:c for s,c in z.items() if s!='blocks'}
        roles.update({f'feedback_block{i+1}':v for i,v in enumerate(z['blocks'])});add(f'v{version}',roles,'Exact saved local parameter-case patient membership; all listed roles excluded.')
    f=frame('prismatic-v21/members.parquet',['subject_id','hadm_id','part']);z=report('upgrade_v21/results/data_manifest.json')
    p21={s:f[f.part==s] for s in z['samples']}
    assert {s:digest([digest(['v21',str(h)]) for h in p.hadm_id]) for s,p in p21.items()}==z['membership_sha256'];add('v21_v22_v23',p21,'Stored source IDs reconstruct all original case membership hashes.')
    f=frame('prismatic-v27/members.parquet',['subject_id','hadm_id','part']);z=report('upgrade_v27/results/cohort_manifest.json');assert sha(PRIVATE/'prismatic-v27/members.parquet')==z['membership_sha256']
    p27={s:f[f.part==s] for s in z['splits']}
    assert {s:p.subject_id.nunique() for s,p in p27.items()}=={s:v['patients'] for s,v in z['splits'].items()}
    add('current_v27_v29_v30',{s:p for s,p in p27.items() if s!='test'},'Current fitting/development membership included; reserved unexecuted test handled separately.')
    for relative in ['upgrade_v2/train_baselines.py','upgrade_v2/evolution_curve.py','upgrade_v3/run_atc4_methods.py','upgrade_v3/prepare_clinical_review.py','upgrade_v4/run_protocol_methods.py','upgrade_v5/run_rankers.py','upgrade_v6/run_evolution.py','upgrade_v7/prepare_data.py','upgrade_v9/prepare_local.py','upgrade_v15/prepare_binary.py','upgrade_v21/build_temporal_cohort.py','upgrade_v27/build_cohort.py','upgrade_v26/prepare.py','upgrade_v31/prepare.py']:
        p=ROOT/relative
        if p.exists():track(p,ROOT)
    unions={name:set().union(*(set(v['subject_hashes']) for v in z['roles'].values())) for name,z in families.items()};prior=set().union(*unions.values());test_people={digest(str(s)) for s in p27['test'].subject_id};kept=test_people-prior;excluded=test_people&prior
    assert len(test_people)==890 and not kept&prior
    assignments=[{'case_id':digest(['v27-visit',str(row.hadm_id)]),'subject_hash':digest(str(row.subject_id)),'retained':digest(str(row.subject_id)) in kept} for row in p27['test'].itertuples()]
    assert len(assignments)==2422 and len({r['case_id'] for r in assignments})==2422
    no_test();frozen={'protocol_sha256':sha(HERE/'prior_case_exclusion_protocol.json'),'builder_sha256':sha(Path(__file__)),'sources':sources,'families':families,'prior_union':sorted(prior),'reserved_test':sorted(test_people),'retained':sorted(kept),'excluded':sorted(excluded),'test_assignments':assignments,'freeze_time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'test_prediction_directories_empty_at_freeze':True}
    save(freeze,frozen)
    public={'status':'membership_frozen_pending_independent_audit','protocol_sha256':frozen['protocol_sha256'],'builder_sha256':frozen['builder_sha256'],'freeze_time_utc':frozen['freeze_time_utc'],'membership_sha256':sha(freeze),'sources':sources,'families':{n:{'roles':{r:{k:v for k,v in row.items() if k!='subject_hashes'} for r,row in x['roles'].items()},'proof':x['proof'],'test_patient_overlap':len(test_people&unions[n])} for n,x in families.items()},'pairwise_family_patient_overlap':{a:{b:len(unions[a]&unions[b]) for b in unions} for a in unions},'prior_union_patients':len(prior),'reserved_test_patients':890,'retained_test_patients':len(kept),'excluded_test_patients':len(excluded),'retained_test_visits':sum(r['retained'] for r in assignments),'excluded_test_visits':sum(not r['retained'] for r in assignments),'retained_prior_patient_overlap':0,'test_predictions_read':False,'test_prediction_directories_empty_at_freeze':True,'source_population_census':{'all_eligible_repeat_patients':z['flow']['eligible_repeated_patients'],'all_allocated_patients':sum(p.subject_id.nunique() for p in p27.values())},'coverage':'Named PRISMATIC MIMIC-IV family membership only; no guarantee about undocumented use or model pretraining. Reconstructed early samples lack original membership digests; exact source and reconstruction hashes are retained.'}
    save(HERE/'exposure_registry.json',public);print(json.dumps({k:public[k] for k in ['status','prior_union_patients','retained_test_patients','retained_test_visits','excluded_test_patients','test_predictions_read']}))
if __name__=='__main__':main()
