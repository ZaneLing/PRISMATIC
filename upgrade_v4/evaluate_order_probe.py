"""Score structural outcomes only; save reviewed case bundles locally."""
import json,hashlib
from collections import Counter
from pathlib import Path
from jsonschema import Draft202012Validator
from order_protocol import normalize,review,schema

HERE=Path(__file__).resolve().parent
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v4'

def parse(raw):
    raw=raw.strip()
    if raw.startswith('```'):raw=raw.split('\n',1)[1].rsplit('```',1)[0].strip()
    return json.loads(raw)

def run():
    rows=[json.loads(x) for x in (PRIVATE/'order_probe_predictions.jsonl').read_text().splitlines()]
    validator=Draft202012Validator(schema());report={};reviews=[]
    for arm in ['direct','retrieval_harness']:
        n_raw=0;n_normalized=0;n_orders=0;n_missing=0;statuses=Counter();kinds=Counter();dose_known=0;fluid=0
        for row in rows:
            try:
                payload=parse(row[arm]['raw'])
                n_raw+=not list(validator.iter_errors(payload))
                bundle=normalize(payload)
                if list(validator.iter_errors(bundle)):raise ValueError('invalid normalized schema')
                n_normalized+=1;n_orders+=len(bundle['orders'])
                dose_known+=sum(o['dose_value'] is not None for o in bundle['orders'])
                r=review(bundle,{'E1','E2','E3','E1_chiefcomplaint','E2_acuity','E3_home_meds'})
                statuses[r['status']]+=1;kinds.update(f['kind'] for f in r['findings'])
                reviews.append({'case_id':row['case_id'],'arm':arm,'bundle':bundle,'review':r})
            except (ValueError,TypeError,KeyError):statuses['invalid_output']+=1
        report[arm]={'cases':len(rows),'raw_complete_schema_valid':int(n_raw),'normalized_schema_valid':n_normalized,
          'proposed_orders':n_orders,'orders_with_model_supplied_numeric_dose':dose_known,
          'statuses':dict(statuses),'finding_counts':dict(kinds),'clinical_correctness':'unrated',
          'generation_tokens_total':sum(r[arm]['tokens']+(r['direct']['tokens'] if arm=='retrieval_harness' else 0) for r in rows)}
    (PRIVATE/'reviewed_order_bundles_normalized.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in reviews))
    output={'run_id':'E01-complete-order-normalization-10-r2','metrics':report,'schema_sha256':hashlib.sha256((HERE/'order_schema.json').read_bytes()).hexdigest(),
      'limits':['Ten developmental cases; no clinical scoring or effectiveness claim.',
        'Normalization fills absent fields with null and uncertainty, never clinical values; raw completeness reported separately.',
        'r2: ATC strings with incorrect granularity/format become null with the raw string retained in uncertainty; no code is inferred.',
        'Numeric doses are model-supplied hypotheses, not checked recommendations.',
        'The draft is shared: retrieval_harness uses two calls including direct; this probe is not an equal-call causal comparison.',
        'No DDI/renal safety conclusion because validated knowledge is missing.']}
    (HERE/'results/order_probe_normalized_results.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output,indent=2))

if __name__=='__main__':run()
