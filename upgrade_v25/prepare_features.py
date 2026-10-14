"""Fit all representations and labels on initial training contexts; seal evaluation."""
import json
from collections import Counter
import numpy as np,joblib
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize
from data_contract import HERE,PRIVATE,sha,digest,save
from learning import NumericState,text,dump

def main():
    audit=json.loads((HERE/'results/cohort_audit.json').read_text());assert audit['status']=='passed'
    assert sha(PRIVATE/'cases.joblib')==audit['cases_sha256']
    cases=joblib.load(PRIVATE/'cases.joblib');initial=cases['train'][:8000]
    count=Counter(n for c in initial for n in {o['drug_code'] for o in c['gold']})
    classes=[k for k,_ in sorted(count.items(),key=lambda x:(-x[1],x[0]))[:512]];assert len(classes)==512
    word=TfidfVectorizer(max_features=6000,ngram_range=(1,2),min_df=2,dtype=np.float32)
    char=TfidfVectorizer(max_features=5000,analyzer='char',ngram_range=(3,5),min_df=2,dtype=np.float32)
    word.fit([text(c) for c in initial]);char.fit([text(c) for c in initial]);numeric=NumericState(initial)
    bundle={s:{'cases':cs,'truth':[c['gold'] for c in cs]} for s,cs in cases.items()}
    for s,cs in cases.items():
        docs=[text(c) for c in cs];b=bundle[s];b['word']=word.transform(docs);b['char']=char.transform(docs)
        b['x']=normalize(hstack([b['word'],numeric.transform(cs)],format='csr'),copy=False)
    ys=[{o['drug_code'] for o in c['gold']} for c in cases['train']]
    development={s:bundle[s] for s in ['train','proposal','guard']};development['classes']=classes
    development['y']=np.asarray([[n in row for n in classes] for row in ys],dtype=np.float64)
    dump(development,PRIVATE/'development.joblib');dump(dict(bundle['test'],classes=classes),PRIVATE/'sealed_evaluation.joblib')
    dump({'word':word,'char':char,'numeric':numeric,'classes':classes},PRIVATE/'representations.joblib')
    save(HERE/'results/feature_manifest.json',{'status':'prepared','classes':len(classes),'class_space_sha256':digest(classes),
      'word_features':len(word.vocabulary_),'char_features':len(char.vocabulary_),'typed_features':len(numeric.vectorizer.vocabulary_),
      'typed_scales':len(numeric.scales),'initial_training_membership_sha256':digest([c['case_id'] for c in initial]),
      'representation_sha256':sha(PRIVATE/'representations.joblib'),'development_sha256':sha(PRIVATE/'development.joblib'),
      'sealed_evaluation_sha256':sha(PRIVATE/'sealed_evaluation.joblib'),'test_used_for_fitting':False,'no_model_scores':True,'feature_source_sha256':{n:sha(HERE/n) for n in ['learning.py','prepare_features.py','data_contract.py']}})
    print('Initial-only representations frozen; development and test bundles separated.',flush=True)

if __name__=='__main__':main()
