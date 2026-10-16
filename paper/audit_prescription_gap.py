"""Post hoc aggregate error audit of historical, frozen MIMIC predictions.

No fitting, checkpoint selection, inference, API use, or patient-level exports.
These test strata are descriptive and must not select a revised method.
"""
import gc
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
import joblib
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
PRIVATE = ROOT.parent.parent / 'MedTreeBench/dataset/restricted/prismatic-v21'
sys.path.insert(0, str(ROOT / 'upgrade_v7'))
from rx_agent import CORE


def tally(cases, predictions, vocabulary):
    total = Counter()
    burden = defaultdict(Counter)
    for c, orders in zip(cases, predictions):
        gold = {o['drug_name'] for o in c['gold']}
        pred = {o['drug_name'] for o in orders}
        prior = {o['drug_name'] for o in c['context']['recorded_prior_orders']}
        hits = gold & pred
        counter = Counter(cases=1, gold=len(gold), pred=len(pred), hits=len(hits),
                          false_positive=len(pred-gold), false_negative=len(gold-pred),
                          false_negative_oov=len((gold-pred)-vocabulary),
                          false_negative_in_vocabulary=len((gold-pred)&vocabulary),
                          gold_in_vocabulary=len(gold&vocabulary),
                          gold_in_prior=len(gold&prior), hit_in_prior=len(hits&prior),
                          gold_not_in_prior=len(gold-prior), hit_not_in_prior=len(hits-prior),
                          empty_output=int(not pred),
                          without_prior_orders=int(not prior),
                          without_labs=int(not c['context']['available_labs']))
        gt4 = {tuple(o.get(k) for k in CORE) for o in c['gold'] if all(o.get(k) is not None for k in CORE)}
        pr4 = {tuple(o.get(k) for k in CORE) for o in orders if all(o.get(k) is not None for k in CORE)}
        counter['complete_gold_core4'] = len(gt4)
        counter['gold_core4_with_correct_drug'] = sum(t[0] in pred for t in gt4)
        counter['correct_core4'] = len(gt4 & pr4)
        total.update(counter)
        burden['1' if len(gold)==1 else '2-4' if len(gold)<=4 else '5+'].update(counter)
    def score(c):
        return {**c, 'drug_precision': c['hits']/max(1,c['pred']),
                'drug_recall': c['hits']/max(1,c['gold']),
                'drug_f1': 2*c['hits']/max(1,c['pred']+c['gold']),
                'oov_fraction_of_false_negatives':c['false_negative_oov']/max(1,c['false_negative']),
                'prior_target_recall':c['hit_in_prior']/max(1,c['gold_in_prior']),
                'new_target_recall':c['hit_not_in_prior']/max(1,c['gold_not_in_prior']),
                'core4_recall_conditional_on_correct_drug':c['correct_core4']/max(1,c['gold_core4_with_correct_drug'])}
    return {'overall': score(total), 'gold_drug_burden': {k: score(v) for k,v in sorted(burden.items())}}


def main():
    raw = (PRIVATE/'cases.json').read_bytes()
    cases = json.loads(raw)['test']
    data = joblib.load(PRIVATE/'data.joblib')
    vocabulary = set(data['classes']); del data; gc.collect()
    rows = []
    for seed in (42,137,2026):
        for filename, method in [(f'run_seed_{seed}.joblib','rxrsi_selected'),(f'strong_seed_{seed}.joblib','word_char_ensemble')]:
            data = joblib.load(PRIVATE/filename)
            rows.append({'seed':seed, 'historical_method':method, **tally(cases,data['predictions'][method],vocabulary)})
            del data;gc.collect()
    aggregate = {}
    for method in ('rxrsi_selected','word_char_ensemble'):
        selected = [r for r in rows if r['historical_method']==method]
        aggregate[method] = {k:float(np.mean([r['overall'][k] for r in selected])) for k in selected[0]['overall']}
    existing = json.loads((ROOT/'upgrade_v45/results/mimic_recount.json').read_text())
    for method, row in aggregate.items():
        assert abs(row['drug_f1']-existing['methods'][method]['drug_f1']['mean'])<1e-12
    out = {'scope':'Historical frozen order pipelines; NOT the current LLM RxRSIAgent.',
           'design':'Post hoc descriptive test error decomposition; no selection or training. GT-based burden strata are unavailable at deployment.',
           'test_cases':len(cases), 'input_source_sha256':hashlib.sha256(raw).hexdigest(),
           'network_calls':0,'new_inference':False,'restricted_rows_exported':False,
           'per_seed':rows,'mean_counts_and_metrics':aggregate,
           'interpretation_limits':['In-vocabulary misses identify a selection gap, not its clinical cause.',
                                    'Raw drug-name matching can penalize equivalent names; no unvalidated equivalence credit is introduced.',
                                    'Historical orders reveal actions, not the clinician reasoning or uniquely appropriate treatment.',
                                    'Burden is target drug count, not diagnosis count or confirmed multimorbidity.']}
    (ROOT/'paper/prescription_gap_audit.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(aggregate,indent=2))


if __name__=='__main__':main()
