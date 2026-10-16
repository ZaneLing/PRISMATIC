"""Generate the declared FLAME-component initializer using the existing sklearn env."""
import json
import joblib,numpy as np
from common import *
def main():
    source=joblib.load(SOURCE/'run_seed_42.joblib');bundle=joblib.load(SOURCE/'data.joblib')
    rankings=source['probs'][40000]['test'];classes=bundle['classes'];data=load_cases()
    save(PRIVATE/'flame-initial-seed.json',{'case_ids':[c['case_id'] for c in data['test']],
      'names':[[classes[j] for j in np.argsort(-p)[:8]] for p in rankings],
      'source_sha256':sha(SOURCE/'run_seed_42.joblib'),'k':8,'test_labels_used':False})
if __name__=='__main__':main()
