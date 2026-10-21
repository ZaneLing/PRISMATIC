"""Trace the template bottleneck and candidate rejection on development only."""
import json
from collections import Counter
from common53 import *
import learn
from programs import predict,applies,operate
def main():
    cs,base=learn.load_development();original=learn.templates
    library={key(r['template']) for r in json.loads((PRIVATE/'training_joint_library.json').read_text())}
    backed=lambda seen:[dict(zip(FIELDS,k)) for k in sorted({key(o) for c in seen for o in c['gold'] if all(o.get(f) for f in FIELDS)}&library)]
    result={}
    for name,fn in [('feedback_only',original),('training_backed',backed)]:
        learn.templates=fn;proposals=learn.candidates(cs['reflection'],base['reflection'],[]);stages=Counter();fail=Counter();trace=Counter()
        for item in proposals:
            op=item['card']['op'];stages[op+':reflection_pass']+=1
            pd=learn.diff(learn.err(predict(cs['proposal'],base['proposal'],[item['card']]),cs['proposal']),learn.err(base['proposal'],cs['proposal']))
            if learn.pareto(pd):stages[op+':proposal_pass']+=1
            else:
                for j,label in enumerate(['missed','extra','joint']):
                    if pd[j]>0:fail[op+':'+label+'_increased']+=1
                if not any(pd):fail[op+':no_error_change']+=1
            if op=='replace':
                for case,orders in zip(cs['proposal'],base['proposal']):
                    card=item['card']
                    if not applies(case,card):trace['condition_not_met']+=1
                    elif not any(o['drug_code']==card['drug_code'] for o in orders):trace['condition_met_target_drug_absent']+=1
                    elif set(map(key,operate(orders,card)))==set(map(key,orders)):trace['condition_met_tuple_already_equal']+=1
                    else:
                        trace['changed']+=1
                        d=learn.diff(counts(operate(orders,card),case['gold'])[:3],counts(orders,case['gold'])[:3])
                        trace['changed_without_error_change' if not any(d) else 'changed_component_regression' if max(d)>0 else 'changed_pareto_improvement']+=1
        result[name]=dict(usable_templates=len(fn(cs['reflection'])),stages=dict(stages),proposal_rejection_components=dict(fail),field_repair_execution_trace=dict(trace))
    learn.templates=original
    result['analysis']='All192 reflection patients and empty starting memory; not a newly tuned trajectory. Failures may count in multiple components.'
    save(HERE/'results/development_bottleneck.json',result);print(json.dumps(result,indent=2))
if __name__=='__main__':main()
