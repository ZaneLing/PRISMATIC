"""Post-freeze source attribution: predictive tool use is not newly learned pharmacology."""
import json,collections
from common import *
def main():
 data=load_cases();cs=data['audit'];folder=PRIVATE/'cloud'
 a=json.loads((folder/'audit-round-0.json').read_text())['rows'];b=json.loads((folder/'audit-final.json').read_text())['rows'];out={}
 for label,rows in [('initial',a),('retained',b)]:
  ct=collections.Counter()
  for c,r in zip(cs,rows):
   draft=set(c['retrieval_meta']['classifier_rank'][:8]);p={o['drug_name'] for o in r['orders']};g={o['drug_name'] for o in c['gold']};cat={o['drug_name'] for o in r['catalogue'].values()}
   ct.update(predicted=len(p),true_positives=len(p&g),predicted_inside_draft=len(p&draft),true_positives_inside_draft=len(p&g&draft),true_positives_outside_draft=len((p&g)-draft),draft_instances=len(draft),gt_instances=len(g),gt_outside_actual_catalogue=len(g-cat))
  out[label]=dict(ct);out[label].update(precision=ct['true_positives']/max(1,ct['predicted']),recall=ct['true_positives']/max(1,ct['gt_instances']),missed_gt_per_admission=(ct['gt_instances']-ct['true_positives'])/len(cs),extra_vs_gt_per_admission=(ct['predicted']-ct['true_positives'])/len(cs));out[label]['fraction_predictions_inside_draft']=ct['predicted_inside_draft']/max(1,ct['predicted']);out[label]['fraction_correct_drugs_inside_draft']=ct['true_positives_inside_draft']/max(1,ct['true_positives']);out[label]['draft_retention']=ct['predicted_inside_draft']/max(1,ct['draft_instances'])
 recovered=outside=lost=0
 for c,x,z in zip(cs,a,b):
  g={o['drug_name'] for o in c['gold']};p={o['drug_name'] for o in x['orders']};q={o['drug_name'] for o in z['orders']};cat={o['drug_name'] for o in x['catalogue'].values()}
  recovered+=len((q-p)&g);outside+=len(((q-p)&g)-cat);lost+=len((p-q)&g)
 save(HERE/'results/mechanism_audit.json',{'complete':True,'audit_cases':len(cs),'methods':out,'newly_recovered_gt_instances':recovered,'recovered_from_outside_original_catalogue':outside,'lost_gt_instances':lost,
 'interpretation':'Quantifies uptake of a fixed supervised source. It does not prove new disease-specific knowledge, clinical appropriateness, or elimination of drug-name priors. No audit outcome selects a state.'})
if __name__=='__main__':main()
