"""Freeze, run paired development controls, then report-only guard confirmation."""
import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from common45 import HERE, ROOT, RUN, OLD_RUN, digest, ledger_total, save, sha, MODEL
from agent45 import Agent45

ARMS = {'tools': {'cards': [], 'product_scope': True},
        'tools_contract': {'cards': [], 'product_scope': True, 'obligations': True}}
FILES = ['common45.py', 'evidence45.py', 'obligations.py', 'agent45.py', 'run.py']


def target(case):
    return sorted(case['gold']) if isinstance(case['gold'], list) else [case['gold']]


def baseline(data, split):
    old = RUN.parent / 'rxrsi-v44'
    if split == 'train':
        return {r['case_id']: r for r in json.loads((old / 'learning/feedback.json').read_text())}
    folder = old / 'runs' / digest({'cards': []}) / split
    return {r['case_id']: r for r in [json.loads(p.read_text()) for p in folder.glob('*.json')]}


def freeze():
    data = json.loads((OLD_RUN / 'data.json').read_text())
    special = ['e7a30d739ee5b9be', '20084f0b868433c8',
               'medqa_train_c4e678277e783a1e81dd07dc02dcf4c7d022ab3880fc2159f1f6652309b9f438',
               'medqa_train_1dfc1ce340194dc95c79eb28942261aff7eef35c0d03229c97c8f4b31f33fc1e',
               'medqa_train_3c30873078694d879ef41f26260d3525c9c5b0343d3c3713ad6db24e06cebd77']
    train = []
    for is_med in (False, True):
        train += sorted([c for c in data['train'] if c['id'].startswith('medqa_') == is_med], key=lambda c: digest(['v45-pilot', c['id']]))[:40]
    ids = {c['id'] for c in train}
    train += [c for c in data['train'] if c['id'] in special and c['id'] not in ids]
    protocol = {'created_utc': datetime.now(timezone.utc).isoformat(), 'model': MODEL,
                'ledger_start_usd': ledger_total(), 'max_incremental_usd': 8,
                'data_sha256': sha(OLD_RUN / 'data.json'), 'implementation': {f: sha(HERE / f) for f in FILES},
                'arms': ARMS, 'training_pilot_ids': [c['id'] for c in train], 'illustration_ids': special,
                'proposal': ['proposal_rx', 'proposal_med'], 'guard': ['guard_rx', 'guard_med'],
                'selection': 'On full proposal: no accuracy loss within either task, pooled strict gain, no invalid increase. Choose pooled correct; ties choose tools. Only that candidate enters guard, with same per-task no-loss and invalid check. If neither qualifies retain frozen incumbent. No test execution in this development study.',
                'budget': 'Same plan prompt and cache; three calls x1536 total maximum4608. Increased source lookup and input costs disclosed.',
                'changes': 'Researcher-authored repair derived from recurring TRAIN failures; not autonomous RSI. Full source metadata; homeopathic exclusion; combination evidence; option-role preservation; optional typed decision obligations.',
                'exposure': 'Same public training and historically reused development splits; no fresh final-test claim. No restricted MIMIC records sent to provider.'}
    path = HERE / 'protocol.json'
    if path.exists():
        old = json.loads(path.read_text())
        assert old['implementation'] == protocol['implementation']
        assert old['data_sha256'] == protocol['data_sha256']
        return old, data
    save(path, protocol)
    return protocol, data


def metrics(rows, cases, old):
    hits = [r['prediction'] == target(c) for r, c in zip(rows, cases)]
    before = [old[c['id']]['prediction'] == target(c) for c in cases]
    calls = [x for r in rows for x in r['calls']]
    return {'n': len(cases), 'correct': sum(hits), 'baseline_correct': sum(before),
            'fixes': sum(b and not a for a, b in zip(before, hits)),
            'regressions': sum(a and not b for a, b in zip(before, hits)),
            'invalid': sum(r['prediction'] is None for r in rows),
            'baseline_invalid': sum(old[c['id']]['prediction'] is None for c in cases),
            'calls': len(calls), 'input_tokens': sum(x['input_tokens'] for x in calls),
            'output_tokens': sum(x['output_tokens'] for x in calls),
            'logical_cost_usd': sum(x.get('cost_usd') or 0 for x in calls),
            'predictions_sha256': digest([r['prediction'] for r in rows])}


def run(arm, split, protocol, data):
    cases = data[split]
    if split == 'train':
        by_id = {c['id']: c for c in cases}
        cases = [by_id[i] for i in protocol['training_pilot_ids']]
    old = baseline(data, split)
    assert all(c['id'] in old for c in cases)
    folder = RUN / 'runs' / arm / split
    folder.mkdir(parents=True, exist_ok=True)
    agent = Agent45(ARMS[arm])
    def one(case):
        path = folder / (digest(case['id']) + '.json')
        if path.exists():
            return json.loads(path.read_text())
        result = agent.solve({k: case[k] for k in ('id', 'dialogue', 'options', 'multiple') if k in case})
        # Same initial planning call must be reused; no additional inference budget.
        assert result['calls'][0]['request_sha256'] == old[case['id']]['calls'][0]['request_sha256']
        save(path, result)
        return result
    results = {}
    with ThreadPoolExecutor(max_workers=12) as pool:
        for future in as_completed([pool.submit(one, c) for c in cases]):
            result = future.result(); results[result['case_id']] = result
            if len(results) % 25 == 0:
                print(json.dumps({'arm': arm, 'split': split, 'done': len(results), 'n': len(cases)}), flush=True)
    rows = [results[c['id']] for c in cases]
    result = metrics(rows, cases, old)
    save(HERE / 'results' / (arm + '-' + split + '.json'), result)
    print(json.dumps({'arm': arm, 'split': split, **result}), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['freeze', 'train', 'proposal', 'guard'], required=True)
    args = parser.parse_args(); protocol, data = freeze()
    if args.mode == 'freeze':
        print('Frozen', len(protocol['training_pilot_ids']), 'training diagnostics'); return
    if args.mode in ('train', 'proposal'):
        for arm in ARMS:
            for split in (['train'] if args.mode == 'train' else protocol['proposal']):
                run(arm, split, protocol, data)
    else:
        candidates = []
        for arm in ARMS:
            ms = [json.loads((HERE / 'results' / (arm + '-' + split + '.json')).read_text()) for split in protocol['proposal']]
            if all(m['correct'] >= m['baseline_correct'] and m['invalid'] <= m['baseline_invalid'] for m in ms) and sum(m['correct'] - m['baseline_correct'] for m in ms) > 0:
                candidates.append((sum(m['correct'] for m in ms), arm == 'tools', arm))
        selected = max(candidates)[2] if candidates else None
        guard = {split: run(selected, split, protocol, data) for split in protocol['guard']} if selected else {}
        accepted = bool(selected) and all(m['correct'] >= m['baseline_correct'] and m['invalid'] <= m['baseline_invalid'] for m in guard.values())
        save(HERE / 'results/selection.json', {'proposal_selected': selected, 'guard': guard,
             'accepted': accepted, 'current_method_replaced': False,
             'scope': 'Exploratory development gate; main/independent tests not run. No autonomous RSI claim.',
             'ledger_increment_usd': ledger_total() - protocol['ledger_start_usd']})


if __name__ == '__main__':
    main()
