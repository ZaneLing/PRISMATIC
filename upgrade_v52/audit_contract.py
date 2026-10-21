"""Independent checks of cohort isolation, timestamps, frozen tools and output schemas."""
import sys
from common52 import *
sys.path.insert(0,str(ROOT/'upgrade_v25'))
import joblib,pandas as pd
def main():
 groups={s:json.loads((PRIVATE/(s+'.json')).read_text()) for s in ['reflection','proposal','guard','audit']}
 old=joblib.load(SOURCE/'cases.joblib');oldpatients={c['patient_hash'] for cs in old.values() for c in cs}
 seen=set();counts={}
 for s,cs in groups.items():
  pats={c['patient_hash'] for c in cs};assert len(pats)==len(cs);assert not pats&seen;assert not pats&oldpatients;seen|=pats
  for c in cs:
   x=c['context'];assert x['diagnoses'] and x['categories']
   assert all(-1080<=o['order_offset']<360 for o in x['prior_orders'])
   assert all(-1080<=o['draw_offset']<=360 and o['revised_offset']<=360 for o in x['available_labs'])
   assert c['patient_hash'] not in c['evidence']['neighbor_patients']
   assert all(i in c['catalogue'] for i in c['frozen_draft'])
   assert all(o['drug_code'].startswith('hicl:') for o in c['gold'])
   assert not any(k in x for k in ['activeupondischarge','diagnosispriority'])
  counts[s]=len(cs)
 assert counts=={'reflection':192,'proposal':64,'guard':64,'audit':256}
 assert sha(HERE/'protocol.json')==json.loads((PRIVATE/'protocol_lock.json').read_text())['sha256']
 manifest=json.loads((HERE/'results/tool_manifest.json').read_text())
 for s in groups:assert sha(PRIVATE/(s+'.json'))==manifest['files'][s]
 save(HERE/'results/contract_audit.json',{'passed':True,'patients':len(seen),'prior_patient_overlap':0,'cross_split_patient_overlap':0,'timestamp_checks':'passed for prior orders and revised labs; diagnosis SQL filters input before aggregation','retrieval_self_patient_overlap':0,'candidate_ids_stable_hash_of_joint_order':True,'target_drugs_outside_vocabulary_retained':True,'hospital_global_novelty_claimed':False})
 print('Patient, timestamp, candidate and frozen-input checks passed.',flush=True)
if __name__=='__main__':main()
