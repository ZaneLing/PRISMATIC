"""Finish all full-size evaluations after the six-round development trajectory is frozen."""
import argparse,json
from common import *
from experiment import execute
from local_backend import Backend
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--model',choices=['qwen','llama'],default='qwen');a=ap.parse_args()
    data=load_cases();freeze=json.loads((PRIVATE/'test_freeze.json').read_text());state=freeze['state']
    assert not freeze['selection_used_test_labels'];b=Backend(a.model)
    report={};path=HERE/'results'/('comparison.json' if a.model=='qwen' else 'transfer.json')
    arms=[('rxrsi_base','rxrsi',{'cards':[]}),('rxrsi_selected','rxrsi',state)]
    if a.model=='qwen':arms.extend([('direct','direct',{'cards':[]}),('saferx','saferx',{'cards':[]})])
    for name,method,st in arms:
        rows=execute(b,data['test'],method,st,a.model+'-test-'+name)
        report[name]=metrics(rows,data['test']);save(path,{'model':a.model,'model_sha256':b.model_hash,'methods':report,'complete':False,'selection':'test_freeze_scope.json'})
        print(json.dumps({'method':name,'metrics':report[name]}),flush=True)
    save(path,{'model':a.model,'model_sha256':b.model_hash,'methods':report,'complete':True,'selection':'test_freeze_scope.json'})
if __name__=='__main__':main()
