"""Reproduce the v4 deletion failure without exporting patient-level traces."""
import json
from pathlib import Path
from collections import Counter

PRIVATE = Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v4'
OUT = Path(__file__).parent/'results'

def run():
    predictions = [json.loads(s) for s in (PRIVATE/'llm_method_predictions.jsonl').read_text().splitlines()]
    labels = {r['case_id']: r for r in map(json.loads, (PRIVATE/'llm_labels.jsonl').read_text().splitlines())}
    count = Counter(cases=len(predictions))
    for row in predictions:
        proposal = row['arms']['case_retrieval']; final = row['arms']['bounded_harness']
        truth = set(labels[row['case_id']]['codes'])
        removed = set(proposal['codes']) - set(final['codes'])
        count['retrieval_observed_hits'] += len(set(proposal['codes']) & truth)
        count['harness_observed_hits'] += len(set(final['codes']) & truth)
        count['retrieval_candidates_removed'] += len(removed)
        if not final['codes']:
            count['final_empty'] += 1
            count['final_empty_valid'] += int(final['valid'])
            count['nonempty_retrieval_before_empty'] += int(bool(proposal['codes']))
            count['empty_with_nonempty_observed_target'] += int(bool(truth))
            count['correct_codes_deleted_on_empty_cases'] += len(removed & truth)
    OUT.mkdir(exist_ok=True)
    report = {'counts': dict(count), 'diagnosis': 'Valid empty arrays caused by blanket removal instruction; not JSON parse failure.',
              'scope': '50 developmental cases; historical mapped labels are not clinical truth.'}
    (OUT/'empty_audit.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report))

if __name__ == '__main__': run()
