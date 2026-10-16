"""Scoped repair replay and gated development confirmation; no test selection."""
import argparse
import json
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from scoped import reasons, ROOT
from common45 import RUN as BASE_RUN, OLD_RUN, digest, save, sha, ledger_total
from evidence45 import homeopathic
from agent45 import Agent45
from evidence46 import Evidence46
import importlib.util

HERE = ROOT / 'upgrade_v47'
RUN = BASE_RUN.parent / 'rxrsi-v47'
spec = importlib.util.spec_from_file_location('base_runner45', ROOT / 'upgrade_v45/run.py')
base = importlib.util.module_from_spec(spec); spec.loader.exec_module(base)


class RepairActor(Agent45):
    def __init__(self):
        super().__init__({'cards': [], 'product_scope': True, 'whole_sentence': True})
        self.labels = Evidence46()


def freeze():
    index = HERE / 'source_registry.json'
    if not index.exists():
        ids, hashes = set(), {}
        for path in (BASE_RUN / 'full_labels').glob('*.json'):
            record = json.loads(path.read_text())
            for label in record.get('labels', []):
                if homeopathic(label):
                    ids.add(label['id']); hashes[label['id']] = digest(label)
        save(index, {'explicitly_homeopathic_label_ids': sorted(ids), 'full_label_sha256': hashes,
                     'scope': 'Explicit source metadata only; no outcome, drug-name frequency or target-letter statistics. Unknown classification does not activate the router.'})
    implementation = {name: sha(HERE / name) for name in ['run.py', 'scoped.py', 'source_registry.json']}
    protocol = HERE / 'protocol.json'
    if not protocol.exists():
        save(protocol, {'created_utc': datetime.now(timezone.utc).isoformat(), 'implementation': implementation,
            'parent45_sha256': sha(ROOT / 'upgrade_v45/protocol.json'), 'parent46_sha256': sha(ROOT / 'upgrade_v46/protocol.json'),
            'router': 'Original plan joint-regimen structure OR original product exact label ID classified homeopathic by full public metadata. All other evidence and prompts remain original.',
            'development': 'All400 training cases for descriptive scope analysis; same310 proposal and317 guard. Earlier global-repair proposal outcomes have been seen. This is reused development, not independent confirmation of model design.',
            'gate': 'Proposal per-task no loss and pooled strict gain, no more invalid outputs; then guard per-task no loss. No main/independent test run.',
            'autonomous_RSI': False, 'case_id_answer_lookup_at_inference': False,
            'source_budget': 'Same18,000 evidence characters. Public metadata router adds source/CPU work; cached request replay does not erase logical inference cost.'})
    assert json.loads(protocol.read_text())['implementation'] == implementation


def run(split, data):
    cases = data[split]; old = base.baseline(data, split)
    actor = RepairActor(); folder = RUN / 'runs' / split
    folder.mkdir(parents=True, exist_ok=True)
    def one(case):
        path = folder / (digest(case['id']) + '.json')
        if path.exists():
            return json.loads(path.read_text())
        prior = old[case['id']]
        why = reasons(case, prior['plan'], prior['evidence'])
        if why:
            cache = BASE_RUN.parent / 'rxrsi-v46/runs/whole_sentence' / split / (digest(case['id']) + '.json')
            if cache.exists():
                row = json.loads(cache.read_text())
            else:
                row = actor.solve({k: case[k] for k in ['id', 'dialogue', 'options', 'multiple'] if k in case})
            assert row['calls'][0]['request_sha256'] == prior['calls'][0]['request_sha256']
        else:
            row = dict(prior)
        row = dict(row, scope_route=why, source_trace_sha256=digest(row), state_sha256=digest({'scope_router': sha(HERE / 'source_registry.json')}))
        save(path, row)
        return row
    rows_by_id = {}
    with ThreadPoolExecutor(max_workers=12) as pool:
        for future in as_completed([pool.submit(one, c) for c in cases]):
            row = future.result(); rows_by_id[row['case_id']] = row
    rows = [rows_by_id[c['id']] for c in cases]
    result = base.metrics(rows, cases, old)
    result['routed'] = sum(bool(r['scope_route']) for r in rows)
    result['unchanged_outside_scope'] = all(r['prediction'] == old[r['case_id']]['prediction'] for r in rows if not r['scope_route'])
    save(HERE / 'results' / (split + '.json'), result)
    print(json.dumps({'split': split, **result}), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--mode', choices=['freeze', 'development'], required=True)
    args = parser.parse_args(); freeze()
    if args.mode == 'freeze':
        print('Scoped-source router frozen'); return
    data = json.loads((OLD_RUN / 'data.json').read_text())
    train = run('train', data)
    proposal = {s: run(s, data) for s in ['proposal_rx', 'proposal_med']}
    good = all(m['correct'] >= m['baseline_correct'] and m['invalid'] <= m['baseline_invalid'] for m in proposal.values()) and sum(m['correct'] - m['baseline_correct'] for m in proposal.values()) > 0
    guard = {s: run(s, data) for s in ['guard_rx', 'guard_med']} if good else {}
    accepted = good and all(m['correct'] >= m['baseline_correct'] and m['invalid'] <= m['baseline_invalid'] for m in guard.values())
    save(HERE / 'results/selection.json', {'train': train, 'proposal': proposal, 'guard': guard,
        'accepted': accepted, 'proposal_passed': good, 'current_actor_replaced': False,
        'new_independent_task_result': False, 'scope': 'Researcher-authored routed tool repair; repeated development only; no autonomous RSI.'})


if __name__ == '__main__':
    main()
