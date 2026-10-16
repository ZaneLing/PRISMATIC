"""Recount all completed development rows, provenance, budgets, and frozen code."""
import json
from common45 import ROOT, RUN, OLD_RUN, digest, save, sha
from actor44 import parse_answer
from evidence45 import homeopathic
import importlib.util
_spec = importlib.util.spec_from_file_location('audited_runner45', ROOT / 'upgrade_v45/run.py')
_runner = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_runner)
baseline, metrics, target = _runner.baseline, _runner.metrics, _runner.target


def main():
    protocol = json.loads((ROOT / 'upgrade_v45/protocol.json').read_text())
    for name, expected in protocol['implementation'].items():
        assert sha(ROOT / 'upgrade_v45' / name) == expected
    second = json.loads((ROOT / 'upgrade_v46/protocol.json').read_text())
    for name, expected in second['implementation'].items():
        assert sha(ROOT / 'upgrade_v46' / name) == expected
    assert sha(OLD_RUN / 'data.json') == protocol['data_sha256']
    data = json.loads((OLD_RUN / 'data.json').read_text())
    sources = {}
    source_records = [json.loads(p.read_text()) for p in (RUN / 'full_labels').glob('*.json')]
    for record in source_records:
        sources.update({x['id']: x for x in record.get('labels', [])})
    count = spans = 0
    outcomes, public = {}, []
    for version, arms in [('45', ['tools', 'tools_contract']), ('46', ['whole_sentence'])]:
        for arm in arms:
            for split in ['train', 'proposal_rx', 'proposal_med', 'guard_rx', 'guard_med']:
                summary = ROOT / ('upgrade_v' + version) / 'results' / (arm + '-' + split + '.json')
                if not summary.exists():
                    continue
                cases = data[split]
                if split == 'train':
                    by = {c['id']: c for c in cases}; cases = [by[i] for i in protocol['training_pilot_ids']]
                folder = RUN.parent / ('rxrsi-v' + version) / 'runs' / arm / split
                rows = [json.loads((folder / (digest(c['id']) + '.json')).read_text()) for c in cases]
                old = baseline(data, split)
                result = metrics(rows, cases, old)
                assert result == json.loads(summary.read_text())
                outcomes[arm + '-' + split] = result
                for row, case in zip(rows, cases):
                    count += 1
                    assert len(row['calls']) == 3
                    assert row['calls'][0]['request_sha256'] == old[case['id']]['calls'][0]['request_sha256']
                    answer, _ = parse_answer(row['calls'][-1]['raw'], len(case['options']), case.get('multiple', False))
                    assert answer == row['prediction']
                    assert row['evidence']['chars_used'] == sum(len(e['quote']) for e in row['evidence']['excerpts']) <= 18000
                    for product in row['evidence']['products']:
                        assert not homeopathic(sources[product['label_id']])
                    for excerpt in row['evidence']['excerpts']:
                        text = sources[excerpt['label_id']][excerpt['section']]
                        text = [text] if isinstance(text, str) else text
                        text = text[excerpt['paragraph']]
                        assert text[excerpt['offset']:excerpt['offset'] + len(excerpt['quote'])] == excerpt['quote']
                        spans += 1
                    public.append({'case_id': case['id'], 'split': split, 'arm': arm, 'gold': target(case), 'prediction': row['prediction'],
                                   'baseline_prediction': old[case['id']]['prediction'], 'trace_sha256': sha(folder / (digest(case['id']) + '.json'))})
    outpath = ROOT / 'upgrade_v45/results/public_development_predictions.jsonl'
    outpath.write_text(''.join(json.dumps(x) + '\n' for x in public))
    save(ROOT / 'upgrade_v45/results/audit.json', {'status': 'passed', 'rows': count, 'source_spans': spans,
         'outcomes': outcomes, 'public_predictions_sha256': sha(outpath), 'max_source_characters': 18000,
         'same_initial_request_all_rows': True, 'no_final_test_inference': True,
         'source_requests': len(source_records), 'source_status': {s: sum(r['status'] == s for r in source_records) for s in sorted({r['status'] for r in source_records})}})
    print(json.dumps({'status': 'passed', 'rows': count, 'source_spans': spans}))


if __name__ == '__main__':
    main()
