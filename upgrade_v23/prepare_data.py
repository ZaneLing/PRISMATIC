"""Freeze development/test bundles before feedback experiments begin."""
import json,sys
from pathlib import Path
import joblib,numpy as np
from scipy.sparse import hstack
from sklearn.preprocessing import normalize
from components import HERE,PRIVATE,save,sha,hash_data

def main():
    PRIVATE.mkdir(exist_ok=True);(HERE/'results').mkdir(exist_ok=True)
    source=PRIVATE.parent/'prismatic-v21';protocol=json.loads((HERE/'protocol.json').read_text())
    lock=PRIVATE/'protocol_lock.json'
    if lock.exists():assert json.loads(lock.read_text())['sha256']==hash_data(protocol)
    else:save(lock,{'sha256':hash_data(protocol)})
    audit=json.loads((HERE.parent/'upgrade_v21/results/independent_cohort_audit.json').read_text())
    assert sha(source/'cases.json')==audit['private_cases_sha256']
    raw=json.loads((source/'cases.json').read_text());b=joblib.load(source/'data.joblib')
    fitted=joblib.load(source/'run_seed_42.joblib');vectorizer=fitted['vectorizer'];del fitted
    pilot=joblib.load(PRIVATE.parent/'prismatic-v22/pilot.joblib');typed=pilot['numeric_features'];del pilot
    assert hash_data(typed.scale)==json.loads((HERE.parent/'upgrade_v22/results/development_results.json').read_text())['numeric_state_sha256']
    classes=b['classes'];word={s:vectorizer.transform(b['text'][s]) for s in raw}
    x={s:normalize(hstack([word[s],typed.transform(raw[s])],format='csr'),copy=False) for s in raw}
    dev={k:{s:v[s] for s in ['train','proposal','guard']} for k,v in [('x',x),('word',word),('truth',b['truth']),('parts',b['parts'])]}
    dev['classes']=classes;names=[{o['drug_name'] for o in row} for row in dev['truth']['train']]
    dev['y']=np.asarray([[n in row for n in classes] for row in names],dtype=np.float64)
    joblib.dump(dev,PRIVATE/'development.joblib')
    joblib.dump({'x':x['test'],'word':word['test'],'truth':b['truth']['test'],'parts':b['parts']['test'],'classes':classes},PRIVATE/'sealed_evaluation.joblib')
    save(HERE/'results/data_manifest.json',{'protocol_sha256':hash_data(protocol),'cohort_cases_sha256':audit['private_cases_sha256'],
      'splits':{s:len(raw[s]) for s in raw},'membership_sha256':{s:hash_data([c['case_id'] for c in raw[s]]) for s in raw},
      'classes_sha256':hash_data(classes),'numeric_state_sha256':hash_data(typed.scale),'features':x['train'].shape[1],
      'representation_source_sha256':sha(HERE.parent/'upgrade_v22/state_features.py'),'test_previously_observed_in_v21':True,'no_new_test_score':True})
    print(json.dumps({'prepared':True,'features':x['train'].shape[1],'cases':len(raw['train'])}),flush=True)

if __name__=='__main__':main()
