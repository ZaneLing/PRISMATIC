"""Aggregate training-only evidence coverage and information-flow limits."""
import collections,json
from common import *
from evidence import bank,normalize
def main():
    data=load_cases();total=collections.Counter();by_context={};labels=bank()
    for rnd in range(1,7):
        rows=json.loads((PRIVATE/f'train-before-{rnd}.json').read_text())['rows']
        for c,r in zip(data['train'][(rnd-1)*24:rnd*24],rows):
            assert c['case_id']==r['case_id']
            gt={o['drug_name'] for o in c['gold']};pred={o['drug_name'] for o in r['orders']};cat={o['drug_name'] for o in c['catalogue'].values()}
            spans=r['evidence'].get('spans',[]);cited={c['catalogue'][s['order_id']]['drug_name'] for s in spans if s.get('order_id') in c['catalogue']}
            observed=c['input'].split(' ; ');checked=r['checks'].get('verified_input_quotes',[])
            counter={'cases':1,'reference_drugs':len(gt),'predicted_drugs':len(pred),'catalogue_drugs':len(cat),
             'catalogue_with_cached_product_label':r['evidence']['matched_candidate_drugs'],
             'reference_drugs_in_catalogue':len(gt&cat),
             'reference_candidate_drugs_with_cached_label':sum(bool(labels.get(normalize(n))) for n in gt&cat),'catalogue_drugs_with_excerpt':len(cited),
             'reference_drugs_with_excerpt':len(gt&cited),'predicted_drugs_with_excerpt':len(pred&cited),
             'observed_facts':len(observed),'checked_unique_facts':len(set(checked)),
             'cases_without_labs':int(not c['context']['available_labs']),
             'cases_without_prior_orders':int(not c['context']['recorded_prior_orders']),
             'cases_with_neither':int(not c['context']['available_labs'] and not c['context']['recorded_prior_orders'])}
            total.update(counter)
            group=('labs' if c['context']['available_labs'] else 'no_labs')+'_'+('prior' if c['context']['recorded_prior_orders'] else 'no_prior')
            by_context.setdefault(group,collections.Counter()).update(counter)
    save(HERE/'results/training_trace_audit.json',{'complete':True,'counts':dict(total),'by_observed_context':{k:dict(v) for k,v in by_context.items()},
      'scope':'144 new training admissions, incumbent traces before each update; no test-driven revision',
      'limits':['Source availability and excerpt coverage are not clinical relevance or causal benefit.','Exact-name cached labels, only two global sentences per case.','Fact counts measure the adapter representation, not all information in the underlying EHR.']})
    print(json.dumps(dict(total)))
if __name__=='__main__':main()
