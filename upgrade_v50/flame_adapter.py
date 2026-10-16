"""Released FLAME GRPO list-policy transfer, not a full FLAME reproduction."""
import json,re
from common import *
from local_backend import Backend
def main():
    data=load_cases();cases=data['test'];b=Backend('flame')
    templates=json.loads((RESOURCES/'FLAME/utils/templates/list.json').read_text())
    seed=json.loads((PRIVATE/'flame-initial-seed.json').read_text())
    assert seed['case_ids']==[c['case_id'] for c in cases]
    initial=[set(x) for x in seed['names']]
    pred=[set(x) for x in initial];tokens=[{'input_tokens':0,'output_tokens':0} for _ in cases];traces=[[] for _ in cases]
    invalid=[0]*len(cases)
    for action,cap in [('remove',128),('add',128),('remove',96)]:
        prompts=[]
        for c,ps in zip(cases,pred):
            body=templates['prompt_no_history_'+action].format(input=c['input']+'\nForecast new/change orders in the next six hours. Available names:\n'+'\n'.join(o['drug_name'] for o in c['catalogue'].values()),pre_predicted='\n'.join(sorted(ps)))
            prompts.append(body)
        outputs=b.batch(prompts,cap,'flame/'+action)
        for i,(c,r) in enumerate(zip(cases,outputs)):
            normalize=lambda x:re.sub(r'[\s-]','',x.lower())
            names={normalize(o['drug_name']):o['drug_name'] for o in c['catalogue'].values()}
            selected=set();unknown=[]
            for line in r['raw'].splitlines():
                clean=normalize(line)
                if clean in names:selected.add(names[clean])
                elif clean:unknown.append(line)
            invalid[i]+=bool(unknown)
            pred[i]=pred[i]-selected if action=='remove' else pred[i]|selected
            for k in tokens[i]:tokens[i][k]+=r[k]
            traces[i].append({'action':action,'raw':r['raw'],'matched_names':sorted(selected),'unknown_lines':unknown})
    rows=[]
    for i,(c,ps) in enumerate(zip(cases,pred)):
        rows.append({'case_id':c['case_id'],'orders':[o for o in c['catalogue'].values() if o['drug_name'] in ps],
          'invalid':bool(invalid[i]),'logical_calls':3,**tokens[i],'traces':traces[i]})
    save(PRIVATE/'flame-list-test.json',{'rows':rows})
    initial_rows=[{'case_id':c['case_id'],'orders':[o for o in c['catalogue'].values() if o['drug_name'] in ps],'invalid':False} for c,ps in zip(cases,initial)]
    save(HERE/'results/flame.json',{'complete':True,'method':'FLAME released list-policy + local supervised initializer',
      'model_sha256':b.model_hash,'metrics':metrics(rows,cases),'initializer':metrics(initial_rows,cases),
      'limits':['not full FLAME classifier or embedding pipeline','different pretrained backbone and training data','4-bit converted checkpoint','MIMIC-III trained list-policy transferred to MIMIC-IV 6h task','strict raw-name matching','no diagnosis/procedure or patient embedding tokens','extra initializer information; not equal information to other actors']})
if __name__=='__main__':main()
