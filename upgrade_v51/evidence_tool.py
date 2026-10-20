"""Route-aware and drug-diverse label tool; unchanged two-span allowance."""
import heapq
import evidence
from route_evidence import route_status

def retrieve(c,plan,config):
 if not config['route_filter'] and not config['diverse']:return evidence.retrieve(c,plan)
 words=set(evidence.normalize(c['input']+' '+plan).split());found={};matched=0
 for cid,o in c['catalogue'].items():
  labels=evidence.bank().get(evidence.normalize(o['drug_name']),{});matched+=bool(labels)
  for lid,label in labels.items():
   routes=label.get('openfda',{}).get('route',[])
   if config['route_filter'] and route_status(o.get('route'),routes)=='no_declared_overlap':continue
   for section in ['indications_and_usage','dosage_and_administration','contraindications']:
    for sentence in evidence.sentences(' '.join(label.get(section) or [])):
     item=(-len(words&evidence.sentence_words(sentence)),cid,lid,section,sentence,routes)
     if sentence not in found or item[:5]<found[sentence][:5]:found[sentence]=item
 chosen=[];seen=set()
 for item in sorted(found.values(),key=lambda x:x[:5]):
  if config['diverse'] and item[1] in seen:continue
  chosen.append(item);seen.add(item[1])
  if len(chosen)==2:break
 return {'matched_candidate_drugs':matched,'candidate_drugs':len(c['catalogue']),
  'spans':[dict(order_id=cid,source_id=lid,section=sec,source_route=routes,quote=sentence) for _,cid,lid,sec,sentence,routes in chosen],
  'limits':'Exact cached product identity only. Label retrieval is not verification of patient indication, contraindication, dose or clinical safety.'}
