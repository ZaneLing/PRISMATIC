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
    base={r['case_id']:r for r in json.loads((PRIVATE/'qwen-test-rxrsi_base.json').read_text())['rows']};baseline=[base[i] for i in ids]
    b=Backend();rows=run(b,altered,'rxrsi',{'cards':[]},'catalogue-permutation')
    save(PRIVATE/'permuted-catalogue-test.json',{'rows':rows})
    drug_agreement=sum({o['drug_name'] for o in x['orders']}=={o['drug_name'] for o in y['orders']} for x,y in zip(baseline,rows))
    save(HERE/'results/catalogue_permutation.json',{'complete':True,'cases':len(cases),'original':metrics(baseline,cases),
      'permuted':metrics(rows,altered),'same_drug_set_cases':drug_agreement,'paired':paired(cases,baseline,rows),
      'selection_from_results':False,'api_cost_usd':0,'protocol_sha256':sha(HERE/'permutation_protocol.json')})
if __name__=='__main__':
    import sys
    declare() if '--declare' in sys.argv else main()
