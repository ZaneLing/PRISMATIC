"""Development-driven amendment: use recurrent old-training joint templates.

Frozen before audit outcomes, after independent audit inference started. This
addresses the two-template reflection bottleneck without relaxing any gate.
"""
import json
from collections import defaultdict
from common53 import *
import learn
def main():
    import joblib
    support=defaultdict(set)
    for c in joblib.load(SOURCE/'cases.joblib')['train']:
        for k in {key(o) for o in c['gold'] if all(o.get(f) for f in FIELDS)}:support[k].add(c['patient_hash'])
    library={k:len(v) for k,v in support.items() if len(v)>=3}
    save(PRIVATE/'training_joint_library.json',[dict(template=dict(zip(FIELDS,k)),distinct_training_patients=n) for k,n in sorted(library.items())])
    def backed_templates(cases):
        observed={key(o) for c in cases for o in c['gold'] if all(o.get(f) for f in FIELDS)}
        return [dict(zip(FIELDS,k)) for k in sorted(observed&set(library))]
    learn.templates=backed_templates
    learn.PRIVATE=PRIVATE/'library';learn.PRIVATE.mkdir(exist_ok=True)
    learn.HERE=HERE/'library'
    for seed in [53,153,253]:learn.learn(seed)
    learn.learn(53,True)
    save(PRIVATE/'library_lock.json',dict(audit_metrics_present=(HERE/'results/audit.json').exists(),audit_generation_started=any(PRIVATE.glob('*-audit.json')),amendment='Recurrent templates from40000 old training stays, distinct-patient support>=3, intersect seen reflection targets. Original recurrence>=3 reflection is retained as ablation. No gate relaxation.',library_sha256=sha(PRIVATE/'training_joint_library.json'),implementation_sha256=sha(Path(__file__)),states={p.name:sha(p) for p in learn.PRIVATE.glob('*-states.json')},template_count=len(library),new_weight_updates=0))
    print(json.dumps(dict(old_training_supported_templates=len(library),seen_reflection_usable=len(backed_templates(learn.load_development()[0]['reflection'])))),flush=True)
if __name__=='__main__':main()
