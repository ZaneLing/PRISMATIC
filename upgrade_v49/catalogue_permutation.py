"""Fixed test-subset position diagnostic, not a model-selection experiment."""
import json,random,time
from common import *
from local_backend import Backend
from actor import run
from audit_results import paired

def declare():
    p=HERE/'permutation_protocol.json'
    if p.exists():return
    assert not (HERE/'results/comparison.json').exists()
    parent=json.loads((HERE/'component_protocol.json').read_text())
    save(p,{'declared_unix':time.time(),'cases':128,'member_sha256':parent['member_sha256'],
      'state':'initial state, no cards','intervention':'permute the same catalogue orders and reassign A IDs deterministically by case hash',
      'patient_information_unchanged':True,'candidate_content_unchanged':True,'seed':4916,'selection_from_results':False,
      'limits':'Position sensitivity only; cannot eliminate pretrained medication priors or patient information in the supervised candidate set'})

def main():
    protocol=json.loads((HERE/'permutation_protocol.json').read_text());ids=json.loads((PRIVATE/'component-test-members.json').read_text())
    assert digest(ids)==protocol['member_sha256'];pool={c['case_id']:c for c in load_cases()['test']};cases=[pool[i] for i in ids]
    altered=[]
    for c in cases:
        values=list(c['catalogue'].values());random.Random(int(digest([4916,c['case_id']])[:16],16)).shuffle(values)
        cc={**c,'catalogue':{f'A{i+1}':o for i,o in enumerate(values)}}
        assert sorted(json.dumps(x,sort_keys=True) for x in cc['catalogue'].values())==sorted(json.dumps(x,sort_keys=True) for x in c['catalogue'].values())
        altered.append(cc)
    baseline=json.loads((PRIVATE/'component-initial.json').read_text())['rows'];assert [r['case_id'] for r in baseline]==ids
    b=Backend();namespace=PRIVATE/'permutation-controlled-generation'/str(time.time_ns());original_batch=b.batch
    def controlled(messages,cap=128,tag='infer'):
        b.cache=namespace/tag.replace('/','_');b.cache.mkdir(parents=True,exist_ok=True)
        return original_batch(messages,cap,tag)
    b.batch=controlled
    rows=run(b,altered,'rxrsi',{'cards':[]},'catalogue-permutation')
    save(PRIVATE/'permuted-catalogue-test.json',{'rows':rows})
    drug_agreement=sum({o['drug_name'] for o in x['orders']}=={o['drug_name'] for o in y['orders']} for x,y in zip(baseline,rows))
    save(HERE/'results/catalogue_permutation.json',{'complete':True,'cases':len(cases),'original':metrics(baseline,cases),
      'permuted':metrics(rows,altered),'same_drug_set_cases':drug_agreement,'paired':paired(cases,baseline,rows),
      'baseline':'fresh component initial-state replay, same case/chunk order',
      'selection_from_results':False,'api_cost_usd':0,'protocol_sha256':sha(HERE/'permutation_protocol.json')})
if __name__=='__main__':
    import sys
    declare() if '--declare' in sys.argv else main()
