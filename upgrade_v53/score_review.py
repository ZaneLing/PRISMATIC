"""Validate returned blinded ratings and summarize agreement, without inventing ratings."""
import argparse,json,math
from collections import Counter
from common53 import *
from review import DIMENSIONS
ALLOWED={'appropriate','marginal','inappropriate','unknown','not_applicable'}
def main():
    p=argparse.ArgumentParser();p.add_argument('--reviewer-a',type=Path,default=PRIVATE/'review/reviewer_A.json');p.add_argument('--reviewer-b',type=Path,default=PRIVATE/'review/reviewer_B.json');a=p.parse_args()
    returned=[json.loads(path.read_text()) for path in [a.reviewer_a,a.reviewer_b]]
    counts=[];rows=[]
    for rater,obj in zip(['A','B'],returned):
        original=json.loads((PRIVATE/'review'/('reviewer_'+rater+'.json')).read_text());expected={p['plan_id']:p for c in original['cases'] for p in c['plans']}
        received={p['plan_id']:p for c in obj['cases'] for p in c['plans']}
        assert set(received)==set(expected),'Plan IDs changed'
        supplied=0;missing=0;ratings={}
        for pid,plan in received.items():
            assert plan['orders']==expected[pid]['orders'],'Order content changed'
            reviews=plan['order_reviews'];assert len(reviews)==len(plan['orders'])
            assert [x['order_index'] for x in reviews]==list(range(len(reviews)))
            for rr in reviews:
                assert set(rr['ratings'])==set(DIMENSIONS)
                for dim,value in rr['ratings'].items():
                    if value is None:missing+=1;continue
                    assert value in ALLOWED,'Invalid rating category'
                    supplied+=1;ratings[(pid,rr['order_index'],dim)]=value
        counts.append(dict(rater=rater,supplied_order_dimensions=supplied,pending_order_dimensions=missing));rows.append(ratings)
    if any(x['pending_order_dimensions'] for x in counts):
        save(HERE/'results/review_status.json',dict(status='pending',counts=counts,unblinded=False,clinical_effectiveness_claim=False))
        print('Blinded annotations incomplete; no method scores or appropriateness claims produced.');return
    # Unblind only after all order-dimension ratings are supplied for both raters.
    keymap=json.loads((PRIVATE/'review/BLINDING_KEY_DO_NOT_SHARE.json').read_text());aligned=[]
    for ratings in rows:
        joined={}
        for (pid,idx,dim),v in ratings.items():
            k=keymap[pid];joined[(k['case_id'],tuple(sorted(k['sources'])),idx,dim)]=v
        aligned.append(joined)
    assert set(aligned[0])==set(aligned[1])
    assessable=[k for k in aligned[0] if aligned[0][k] in ['appropriate','marginal','inappropriate'] and aligned[1][k] in ['appropriate','marginal','inappropriate']]
    agreement=sum(aligned[0][k]==aligned[1][k] for k in assessable)/max(1,len(assessable))
    save(HERE/'results/review_status.json',dict(status='order_dimensions_completed',counts=counts,paired_assessable_dimensions=len(assessable),raw_agreement=agreement,unknown_or_not_applicable_pairs=len(aligned[0])-len(assessable),clinical_effectiveness_claim=False,limitation='Treatment-goal, omission, severity and independent skill assessments still require explicit adjudication; no automatic promotion.'))
    print('Validated order-dimension ratings and saved aggregate agreement; no automatic clinical promotion.')
if __name__=='__main__':main()
