"""Compute fixed full-training retrieval only for development splits."""
import json,joblib
from data_contract import HERE,PRIVATE,sha,save
from learning import retrieval_probs,dump

def main():
    meta=json.loads((HERE/'results/feature_manifest.json').read_text());assert sha(PRIVATE/'development.joblib')==meta['development_sha256']
    b=joblib.load(PRIVATE/'development.joblib');out={'development_sha256':meta['development_sha256']}
    for s in ['proposal','guard']:
        out[s]=retrieval_probs(b['train']['x'],b['y'],b[s]['x']);print('Retrieved '+s,flush=True)
    dump(out,PRIVATE/'retrieval_development.joblib');save(HERE/'results/retrieval_manifest.json',{'development_sha256':meta['development_sha256'],
      'retrieval_sha256':sha(PRIVATE/'retrieval_development.joblib'),'neighbors':30,'test_queries_run':False})

if __name__=='__main__':main()
