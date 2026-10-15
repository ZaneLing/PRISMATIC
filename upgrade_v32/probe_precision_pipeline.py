"""Synthetic metric pipeline with absent candidates, incomplete tuples and tied scores."""
import hashlib
import json
from pathlib import Path

import numpy as np

from audit_evaluation import compare
from audit_precision import independently_summarize
from precision_metrics import summarize

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def main():
    spec = json.loads((HERE / 'rank_diagnostic_protocol.json').read_text())
    protocol = json.loads((HERE / 'precision_protocol.json').read_text())
    cases = []
    for index in range(5):
        orders = [{'drug_name': f'synthetic-{i}', 'route': 'synthetic',
                   'dose_value': None if i == 3 else str(i), 'dose_unit': 'synthetic',
                   'frequency_per_24h': None} for i in range(20)]
        outside = {**orders[0], 'drug_name': 'synthetic-outside-catalogue'}
        gold = [] if index == 0 else orders[:index+2] + [outside]
        cases.append({'catalogue': {f'O{i+1}': o for i,o in enumerate(orders)}, 'gold': gold,
                      'subject_hash': str(index//2), 'original_rank_by_position': list(range(1,21)),
                      'target_mask': [int(o in gold) for o in orders]})
    changed = [{**c, 'catalogue': dict(reversed(list(c['catalogue'].items()))),
                'original_rank_by_position': list(reversed(c['original_rank_by_position'])),
                'target_mask': list(reversed(c['target_mask']))} for c in cases]
    groups = {'ranked': cases, 'permuted': changed}
    probabilities = {}
    for index,name in enumerate(protocol['states']):
        rng = np.random.default_rng(32000+index)
        p = rng.uniform(.05,.95,(5,20));p[0,:] = .5
        rounded = np.round(p,1)
        native = rounded.copy();native[1,:] = .2
        reads = {'native':native,'fp32_binary':p,'fp32_rerounded':rounded}
        probabilities[name] = {'ranked':reads,'permuted':{key:value[:,::-1] for key,value in reads.items()}}
    actual = summarize(probabilities,groups,spec)
    expected = independently_summarize(probabilities,groups,spec)
    compare(actual,expected)
    for panel in actual['panels'].values():
        for view in panel.values():
            for read in view.values():
                assert all(m['mean_predicted_drugs']==8 for m in read['methods'].values())
    names = ['precision_protocol.json','precision_metrics.py','run_precision.py','audit_precision.py',
             'precision_readout.py','audit_precision_probe.py','probe_precision_pipeline.py',
             'rank_diagnostic.py','audit_rank_diagnostic.py','rank_diagnostic_protocol.json',
             'evaluation_metrics.py','audit_evaluation.py','inference.py','evaluate.py','decision_loss.py']
    sha = lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    receipt = {'status':'passed','synthetic_only':True,'states':6,'readouts':3,'views':2,'tie_rules':2,
               'synthetic_cases':5,'synthetic_patients':3,'clinical_case_reads':0,
               'checks':['independent_order_and_drug_recount','unreachable_references_retained','incomplete_order_tuples',
                         'zero_target_cases_retained','patient_clustered_intervals','all_readout_contrasts',
                         'identity_ties','within_case_auroc','rank_alignment','fixed_eight_output'],
               'source_sha256':{str((HERE/n).relative_to(ROOT)):sha(HERE/n) for n in names}}
    (HERE/'results/precision_pipeline_probe.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'status':'passed','synthetic_only':True,'states':6,'readouts':3,'views':2,'tie_rules':2}))


if __name__=='__main__':main()
