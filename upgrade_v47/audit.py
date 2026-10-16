"""Verify scope routing, cached/new receipts and paired development counts."""
import json
from scoped import ROOT, reasons
from common45 import RUN as SOURCE_RUN, OLD_RUN, digest, save, sha
from actor44 import parse_answer
import importlib.util
spec = importlib.util.spec_from_file_location('scoped_runner47', ROOT / 'upgrade_v47/run.py')
runner = importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)


def main():
    runner.freeze()
    data = json.loads((OLD_RUN / 'data.json').read_text())
    sources = {}
    for path in (SOURCE_RUN / 'full_labels').glob('*.json'):
        sources.update({x['id']: x for x in json.loads(path.read_text()).get('labels', [])})
    public, span_count, outcomes = [], 0, {}
    for split in ['train', 'proposal_rx', 'proposal_med', 'guard_rx', 'guard_med']:
        summary = runner.HERE / 'results' / (split + '.json')
        if not summary.exists():
            continue
        cases = data[split]; old = runner.base.baseline(data, split)
        rows = [json.loads((runner.RUN / 'runs' / split / (digest(c['id']) + '.json')).read_text()) for c in cases]
        score = runner.base.metrics(rows, cases, old)
        score['routed'] = sum(bool(r['scope_route']) for r in rows)
        score['unchanged_outside_scope'] = all(r['prediction'] == old[r['case_id']]['prediction'] for r in rows if not r['scope_route'])
        assert score == json.loads(summary.read_text()); outcomes[split] = score
        for row, case in zip(rows, cases):
            previous = old[case['id']]
            assert row['scope_route'] == reasons(case, previous['plan'], previous['evidence'])
            if not row['scope_route']:
                assert row['calls'] == previous['calls'] and row['evidence'] == previous['evidence']
            else:
                assert row['calls'][0]['request_sha256'] == previous['calls'][0]['request_sha256']
                for span in row['evidence']['excerpts']:
                    paragraphs = sources[span['label_id']][span['section']]
                    paragraphs = [paragraphs] if isinstance(paragraphs, str) else paragraphs
                    text = paragraphs[span['paragraph']]
                    assert text[span['offset']:span['offset'] + len(span['quote'])] == span['quote']
                    span_count += 1
            answer, _ = parse_answer(row['calls'][-1]['raw'], len(case['options']), case.get('multiple', False))
            assert answer == row['prediction']
            public.append({'case_id': case['id'], 'split': split, 'gold': runner.base.target(case), 'prediction': row['prediction'],
                           'baseline_prediction': previous['prediction'], 'scope_route': row['scope_route']})
    path = runner.HERE / 'results/public_predictions.jsonl'
    path.write_text(''.join(json.dumps(x) + '\n' for x in public))
    save(runner.HERE / 'results/audit.json', {'status': 'passed', 'rows': len(public), 'routed_source_spans_checked': span_count,
        'outcomes': outcomes, 'public_predictions_sha256': sha(path), 'unchanged_receipts_and_evidence_outside_scope': True,
        'scope_checks_not_clinical_entailment': True})
    print(json.dumps({'status': 'passed', 'rows': len(public), 'routed_source_spans': span_count}))


if __name__ == '__main__':
    main()
