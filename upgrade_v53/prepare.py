"""Fresh audit only. Derived from v52 prepare.py; identical frozen training tools."""
import sys,json
from collections import defaultdict,Counter
from common53 import *
sys.path.insert(0,str(ROOT/'upgrade_v25'))
import duckdb,joblib,numpy as np,pandas as pd
from scipy.sparse import hstack
from sklearn.preprocessing import normalize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from data_contract import norm,order
from learning import text

CATEGORIES=['cardiovascular','pulmonary','neurologic','renal','gastrointestinal','endocrine','infectious diseases','hematology','burns/trauma','toxicology','oncology','transplant','obstetrics/gynecology','genitourinary','musculoskeletal']
def main():
 PRIVATE.mkdir(exist_ok=True)
 lock=PRIVATE/'protocol_lock.json'
 if lock.exists():assert json.loads(lock.read_text())['sha256']==sha(HERE/'protocol.json')
 else:save(lock,{'sha256':sha(HERE/'protocol.json')})
 db=duckdb.connect(str(PRIVATE.parent/'prismatic-v24/audit.duckdb'),read_only=True)
 db.execute('SET threads=1');db.execute("SET memory_limit='3GB'")
 dxpath=str(PRIVATE.parent/'eicu-crd-v2.0/diagnosis.csv.gz')
 db.execute("CREATE TEMP TABLE dx AS SELECT DISTINCT patientunitstayid,diagnosisstring,lower(split_part(diagnosisstring,'|',1)) AS category FROM read_csv_auto(?,all_varchar=true) WHERE try_cast(diagnosisoffset AS DOUBLE) BETWEEN 0 AND 360",[dxpath])
 db.execute('CREATE TEMP TABLE clinical_dx AS SELECT * FROM dx WHERE category IN (SELECT unnest(?))',[CATEGORIES])
 db.execute('CREATE TEMP TABLE old_members AS SELECT * FROM read_parquet(?)',[str(SOURCE/'members.parquet')])
 db.execute('''CREATE TEMP TABLE eligible53 AS SELECT c.*,d.ncategory FROM cohort c JOIN
 (SELECT patientunitstayid,count(DISTINCT category) AS ncategory FROM clinical_dx GROUP BY patientunitstayid) d USING(patientunitstayid)
 WHERE c.uniquepid NOT IN (SELECT uniquepid FROM old_members)
 AND c.uniquepid NOT IN (SELECT uniquepid FROM read_parquet('/Users/bytedance/Desktop/MedTreeBench/dataset/restricted/prismatic-v52/members.parquet'))
 AND NOT EXISTS (SELECT 1 FROM targets t WHERE t.patientunitstayid=c.patientunitstayid AND NOT coalesce(try_cast(t.drughiclseqno AS BIGINT)>0 AND try_cast(t.drughiclseqno AS DOUBLE)=try_cast(t.drughiclseqno AS BIGINT),false))''')
 pool=db.execute("SELECT * FROM eligible53 QUALIFY row_number() OVER(PARTITION BY uniquepid ORDER BY sha256('v53-stay:'||patientunitstayid))=1").df()
 selected=[]
 for source,dest,size,offset in [('guard','audit',256,0)]:
  for multi in [False,True]:
   subset=pool[(pool['split']==source)&((pool['ncategory']>=2)==multi)].copy()
   subset['sample_order']=subset['patientunitstayid'].map(lambda x:digest(['v53-member',x]))
   sub=subset.sort_values('sample_order').iloc[offset:offset+size//2].copy();assert len(sub)==size//2
   sub['source_split']=source;sub['split']=dest;selected.append(sub)
 members=pd.concat(selected,ignore_index=True);assert members.uniquepid.nunique()==len(members)
 db.register('members53',members);members.to_parquet(PRIVATE/'members.parquet',index=False)
 details=db.execute("SELECT m.*,p.gender,CASE WHEN replace(p.age,' ','')='>89' THEN90 ELSE floor(try_cast(p.age AS DOUBLE)/10)*10 END AS age_decade FROM members53 m JOIN patient p USING(patientunitstayid)".replace('THEN90','THEN 90')).df()
 rawprior=db.execute('''SELECT m.*,try_cast(drughiclseqno AS BIGINT) AS hicl,try_cast(drugorderoffset AS DOUBLE) AS ordered_at FROM medication m JOIN members53 s USING(patientunitstayid)
 WHERE try_cast(drugorderoffset AS DOUBLE)>=-1080 AND try_cast(drugorderoffset AS DOUBLE)<360
 QUALIFY row_number() OVER(PARTITION BY patientunitstayid ORDER BY try_cast(drugorderoffset AS DOUBLE) DESC,try_cast(medicationid AS BIGINT) DESC)<=24''').df()
 rawlabs=db.execute('''SELECT l.*,lower(trim(labname)) AS lab_key,lower(trim(coalesce(nullif(trim(labmeasurenamesystem),''),nullif(trim(labmeasurenameinterface),''),''))) AS unit_key,
 try_cast(labresultoffset AS DOUBLE) AS drawn_at,try_cast(labresultrevisedoffset AS DOUBLE) AS revised_at,try_cast(labresult AS DOUBLE) AS value FROM lab l JOIN members53 s USING(patientunitstayid)
 WHERE try_cast(labresultoffset AS DOUBLE) BETWEEN -1080 AND 360 AND try_cast(labresultrevisedoffset AS DOUBLE)<=360 AND isfinite(try_cast(labresult AS DOUBLE)) AND nullif(trim(labname),'') IS NOT NULL
 QUALIFY row_number() OVER(PARTITION BY patientunitstayid,lab_key,unit_key ORDER BY drawn_at DESC,revised_at DESC,try_cast(labid AS BIGINT) DESC)=1''').df()
 rawgold=db.execute('SELECT t.*,try_cast(drughiclseqno AS BIGINT) AS hicl FROM targets t JOIN members53 s USING(patientunitstayid)').df()
 prior=defaultdict(list);labs=defaultdict(list);gold=defaultdict(list);dx=defaultdict(list);categories=defaultdict(set)
 for r in rawprior.sort_values('ordered_at',ascending=False).to_dict('records'):
  h=r['hicl'];prior[r['patientunitstayid']].append(dict(drug_code='hicl:'+str(int(h)) if pd.notna(h) and h>0 else None,drug_name=norm(r['drugname']),route=norm(r['routeadmin']),dosage=norm(r['dosage']),frequency=norm(r['frequency']),order_offset=r['ordered_at']))
 for r in rawlabs.sort_values(['drawn_at','revised_at'],ascending=False).to_dict('records'):
  labs[r['patientunitstayid']].append(dict(name=r['lab_key'],unit=r['unit_key'],value=r['value'],draw_offset=r['drawn_at'],revised_offset=r['revised_at']))
 for r in rawgold.to_dict('records'):gold[r['patientunitstayid']].append(order(r))
 for h,d,cat in db.execute('SELECT patientunitstayid,diagnosisstring,category FROM clinical_dx ORDER BY patientunitstayid,diagnosisstring').fetchall():dx[h].append(d);categories[h].add(cat)
 cases={s:[] for s in ['audit']}
 for r in details.sort_values('sample_order').to_dict('records'):
  h=r['patientunitstayid'];c={'case_id':digest(['eicu-v53',h]),'patient_hash':digest(['eicu-patient',r['uniquepid']]),'hospital_hash':digest(['eicu-hospital',r['hospitalid']]),'context':dict(gender=norm(r['gender']),age_decade=int(r['age_decade']),prior_orders=prior[h],available_labs=labs[h][:32],diagnoses=dx[h],categories=sorted(categories[h])),'gold':uniq(gold[h])}
  cases[r['split']].append(c)
 old=joblib.load(SOURCE/'cases.joblib');train=old['train'];oldpatients={c['patient_hash'] for cs in old.values() for c in cs}
 assert not oldpatients.intersection(c['patient_hash'] for cs in cases.values() for c in cs)
 assert not set(members.uniquepid)&set(pd.read_parquet(DEV/'members.parquet').uniquepid)
 oldtrain=db.execute("SELECT patientunitstayid FROM old_members WHERE split='train'").fetchall();oldhash={digest(['eicu-v25',h]):h for h, in oldtrain}
 for c in train:
  h=oldhash[c['case_id']];c['context']['diagnoses']=dx[h];c['context']['categories']=sorted(categories[h])
 save(PRIVATE/'cases.json',cases)
 save(HERE/'results/cohort.json',{'status':'membership_frozen_before_actor','protocol_sha256':sha(HERE/'protocol.json'),'members_sha256':sha(PRIVATE/'members.parquet'),'prior_patient_overlap':0,'one_stay_per_patient':True,'categories':CATEGORIES,'splits':{s:dict(patients=len(cs),multi=sum(len(c['context']['categories'])>=2 for c in cs),zero_target=sum(not c['gold'] for c in cs),hospitals=len({c['hospital_hash'] for c in cs})) for s,cs in cases.items()}})
 print('New patient membership and source inputs frozen.',flush=True)
 rep=joblib.load(SOURCE/'representations.joblib');policy=joblib.load(SOURCE/'seed_42/uniform_policy_round_4.joblib');tool=joblib.load(SOURCE/'seed_42/tool_round_4.joblib')
 trainword=rep['word'].transform([text(c) for c in train]);dxvec=TfidfVectorizer(max_features=8000,ngram_range=(1,2),min_df=2,dtype=np.float32)
 traindx=dxvec.fit_transform([' '.join(c['context']['diagnoses']) for c in train]);tx=normalize(hstack([trainword,traindx*2],format='csr'))
 nn=NearestNeighbors(n_neighbors=8,metric='cosine',algorithm='brute',n_jobs=1).fit(tx)
 names=defaultdict(Counter)
 for c in train:
  for o in c['context']['prior_orders']:
   if o['drug_code'] and o['drug_name']:names[o['drug_code']][o['drug_name']]+=1
 for split,cs in cases.items():
  word=rep['word'].transform([text(c) for c in cs]);x=normalize(hstack([word,rep['numeric'].transform(cs)],format='csr'));p=policy.predict_proba(x)
  qdx=dxvec.transform([' '.join(c['context']['diagnoses']) for c in cs]);_,ni=nn.kneighbors(normalize(hstack([word,qdx*2],format='csr')))
  ix=np.argsort(-p,axis=1,kind='stable')[:,:24];compiled=tool.compile([[rep['classes'][j] for j in row] for row in ix],word,True)
  for i,c in enumerate(cs):
   assert all(train[j]['patient_hash']!=c['patient_hash'] for j in ni[i])
   neighbors=[train[j] for j in ni[i] if set(c['context']['categories'])&set(train[j]['context']['categories'])]
   dc=Counter(code for n in neighbors for code in {o['drug_code'] for o in n['gold']});oc=Counter(key(o) for n in neighbors for o in uniq(n['gold']) if all(o.get(f) for f in FIELDS))
   cat={};lookup={}
   def add(o):
    k=key(o);oid='O'+digest(k)[:8];cat[oid]={f:o.get(f) for f in FIELDS};lookup[k]=oid;return oid
   for o in compiled[i]:add(o)
   # Fixed access for every arm: top8 retrieved drug identities and strongest full joint templates.
   for code,_ in sorted(dc.items(),key=lambda z:(-z[1],z[0]))[:8]:
    variants=[(k,n) for k,n in oc.items() if k[0]==code]
    for k,n in sorted(variants,key=lambda z:(-z[1],str(z[0])))[:2]:add(dict(zip(FIELDS,k)))
   probs={rep['classes'][j]:float(p[i,j]) for j in range(len(rep['classes']))}
   c['catalogue']=cat;c['drug_names']={o['drug_code']:names[o['drug_code']].most_common(1)[0][0] if names[o['drug_code']] else o['drug_code'] for o in cat.values()}
   c['frozen_draft']=[lookup[key(o)] for o,j in zip(compiled[i][:20],ix[i][:20]) if p[i,j]>=.1]
   c['evidence']={'neighbors':len(neighbors),'drug_support':dict(dc),'order_support':{oid:oc[key(o)] for oid,o in cat.items()},'probabilities':probs,'neighbor_patients':[n['patient_hash'] for n in neighbors]}
  save(PRIVATE/(split+'.json'),cs);print('Prepared fixed tools: '+split,flush=True)
 save(HERE/'results/tool_manifest.json',{'protocol_sha256':sha(HERE/'protocol.json'),'frozen_policy_sha256':sha(SOURCE/'seed_42/uniform_policy_round_4.joblib'),'frozen_order_tool_sha256':sha(SOURCE/'seed_42/tool_round_4.joblib'),'training_stays':len(train),'new_weight_updates':0,'files':{s:sha(PRIVATE/(s+'.json')) for s in cases},'training_diagnosis_retrieval':'TFIDF fitted on old training only,8 neighbors with overlapping recorded category','test_metric_inspected':False})

if __name__=='__main__':main()
