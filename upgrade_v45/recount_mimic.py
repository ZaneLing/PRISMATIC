"""Local-only recount of frozen MIMIC predictions. No fitting or provider calls."""
import gc
import json
import sys
from pathlib import Path
import joblib
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'upgrade_v7'))
from rx_agent import CORE, FIELDS

PRIVATE = Path('/Users/bytedance/Desktop/MedTreeBench/dataset/restricted/prismatic-v21')
METHODS = ['retrieval_conditional_tool', 'rxrsi_selected', 'word_char_ensemble']


def tally(predictions, golds):
    counts = np.zeros(9, dtype=np.int64)
    incomplete_gold = incomplete_pred = gold_rows = pred_rows = 0
    for predictions_one, gold_one in zip(predictions, golds):
        for j, fields in enumerate([('drug_name',), CORE, FIELDS]):
            pred = {tuple(x.get(k) for k in fields) for x in predictions_one if all(x.get(k) is not None for k in fields)}
            gold = {tuple(x.get(k) for k in fields) for x in gold_one if all(x.get(k) is not None for k in fields)}
            counts[j * 3:j * 3 + 3] += [len(pred & gold), len(pred), len(gold)]
        pred_rows += len(predictions_one); gold_rows += len(gold_one)
        incomplete_pred += sum(any(x.get(k) is None for k in FIELDS) for x in predictions_one)
        incomplete_gold += sum(any(x.get(k) is None for k in FIELDS) for x in gold_one)
    out = {'counts_hits_pred_gold': counts.tolist(), 'gold_rows': gold_rows, 'pred_rows': pred_rows,
           'complete_five_field_gold_fraction': (gold_rows - incomplete_gold) / max(1, gold_rows),
           'complete_five_field_pred_fraction': (pred_rows - incomplete_pred) / max(1, pred_rows)}
    for i, name in enumerate(['drug', 'core4', 'order5']):
        hit, pred, gold = map(int, counts[i * 3:i * 3 + 3])
        out[name + '_precision'] = hit / max(1, pred)
        out[name + '_recall'] = hit / max(1, gold)
        out[name + '_f1'] = 2 * hit / max(1, pred + gold)
    return out


def main():
    data = json.loads((PRIVATE / 'cases.json').read_text())
    golds = [c['gold'] for c in data['test']]
    published = json.loads((ROOT / 'upgrade_v21/results/summary.json').read_text())
    out = {'n': len(golds), 'patients': published['test_patients'], 'new_model_inference': False,
           'restricted_records_sent_to_api': False, 'old_predictions_only': True,
           'scope': 'MIMIC-IV admission+6h, next6h new/changed orders; same old128 normalized-name vocabulary. A historical reference, not clinical adjudication.',
           'new_endpoint': 'Five-field exact matching adds frequency_per_24h to original core4; only complete observed tuples score, with completeness denominators. Post hoc descriptive recount, not used to select methods.',
           'per_seed': [], 'methods': {}}
    for seed in (42, 137, 2026):
        row = {'seed': seed, 'methods': {}}
        for filename, names in [(f'run_seed_{seed}.joblib', METHODS[:2]), (f'strong_seed_{seed}.joblib', METHODS[2:])]:
            loaded = joblib.load(PRIVATE / filename)
            for method in names:
                score = tally(loaded['predictions'][method], golds)
                prior = next(x for x in published['per_seed'] if x['seed'] == seed)['methods'][method]
                assert abs(score['drug_f1'] - prior['drug_f1']) < 1e-12
                assert abs(score['core4_f1'] - prior['order_f1']) < 1e-12
                row['methods'][method] = score
            del loaded; gc.collect()
        out['per_seed'].append(row)
    for method in METHODS:
        out['methods'][method] = {k: {'mean': float(np.mean([r['methods'][method][k] for r in out['per_seed']])),
                                    'seed_sd': float(np.std([r['methods'][method][k] for r in out['per_seed']], ddof=1))}
                                  for k in out['per_seed'][0]['methods'][method] if k != 'counts_hits_pred_gold'}
    path = ROOT / 'upgrade_v45/results/mimic_recount.json'
    path.write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps({method: {k: round(v['mean'], 5) for k, v in metrics.items() if k in ['drug_precision', 'drug_recall', 'drug_f1', 'core4_f1', 'order5_f1', 'complete_five_field_gold_fraction']} for method, metrics in out['methods'].items()}))


if __name__ == '__main__':
    main()
