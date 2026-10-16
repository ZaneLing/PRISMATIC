"""Independent source/receipt recount and rejection-gate audit."""
import json,sys
from datetime import datetime,timezone
from experiment import ROOT,HERE,RUN,LOCAL,digest,sha,save,ledger_total
from workflow import verify
sys.path.insert(0,str(ROOT/'upgrade_v35'));from audit import paired

def main():
 data=json.loads((RUN/'data.json').read_text());labels={}
 for x in json.loads((LOCAL.parent/'rxrsi-v11/labels.json').read_text()).values():
  if x.get('label'):labels[x['label']['id']]=x['label']
 files=list((LOCAL.parent/'rxrsi-v35/label_requests').glob('*.json'))
 for f in files:
  for x in json.loads(f.read_text()).get('labels',[]):labels[x['id']]=x
 out={'status':'complete','code_sha256':sha(__file__),'results':{},'source_spans_checked':0,'paired':{},'source_snapshot_hash':digest(sorted((k,digest(v)) for k,v in labels.items())),'test_selection_uses_only_development':True};allrows={}
 for arm in ('static_v35','full_section_context','contrastive_review','training_memory'):
  for split in ('proposal','guard','rxqa'):
   path=HERE/'results'/f'{arm}-{split}.json'
   if not path.exists():continue
   cs=json.loads((LOCAL/'data.json').read_text())['transfer'] if split=='rxqa' else data[split];rows=[]
   for c in cs:
    r=json.loads((RUN/arm/split/(digest(c['id'])+'.json')).read_text());assert r['case_id']==c['id'];assert len(r['calls'])==3;assert sum(x['output_tokens'] for x in r['calls'])<=4608
    for call in r['calls']:assert not call.get('error') and call.get('model_returned')
    for z in r['evidence']['excerpts']:
     ls=labels[z['label_id']][z['section']];ls=[ls] if isinstance(ls,str) else ls;assert ls[z['paragraph']][z['offset']:z['offset']+len(z['quote'])]==z['quote'];out['source_spans_checked']+=1
    txt=c['dialogue']+'\nOptions:\n'+'\n'.join(f'{chr(65+i)}. {o}' for i,o in enumerate(c['options']));assert verify(r['assessment'],r['evidence'],txt)==r['checks'];a=r['final'].get('final');a=a.strip().upper() if isinstance(a,str) else None
    if a not in [chr(65+i) for i in range(len(c['options']))]:a=None
    assert a==r['prediction'];rows.append(r)
   m={'n':len(cs),'correct':sum(r['prediction']==c['gold'] for r,c in zip(rows,cs)),'invalid':sum(r['prediction'] is None for r in rows),'predictions_sha256':digest([r['prediction'] for r in rows])};d=json.loads(path.read_text());assert all(d[k]==v for k,v in m.items());out['results'][arm+'-'+split]=d;allrows[(arm,split)]=rows
 for arm in ('full_section_context','contrastive_review','training_memory'):
  if (arm,'proposal') not in allrows:continue
  out['paired'][arm+'-proposal']=paired(allrows[('static_v35','proposal')],allrows[(arm,'proposal')],data['proposal'])
  if arm!='contrastive_review':assert all(x['calls'][0]['raw']==y['calls'][0]['raw'] for x,y in zip(allrows[('static_v35','proposal')],allrows[(arm,'proposal')]))
  x=out['results'][arm+'-proposal'];base=out['results']['static_v35-proposal'];passed=x['correct']>base['correct'] and x['invalid']<=base['invalid'];out['results'][arm+'-proposal']['proposal_pass']=passed
  if not passed:assert (arm,'guard') not in allrows and (arm,'rxqa') not in allrows
  if (arm,'guard') in allrows:
   g=out['results'][arm+'-guard'];b=out['results']['static_v35-guard'];out['results'][arm+'-guard']['guard_pass']=g['correct']>b['correct'] and g['invalid']<=b['invalid'];out['paired'][arm+'-guard']=paired(allrows[('static_v35','guard')],allrows[(arm,'guard')],data['guard'])
 out['ledger_increment_usd']=ledger_total()-json.loads((HERE/'protocol.json').read_text())['ledger_start_usd'];save(HERE/'results/audit.json',out);print(json.dumps({k:v for k,v in out.items() if k not in ['results']}))
if __name__=='__main__':main()
