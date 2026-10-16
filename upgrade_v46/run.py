"""Predeclared next repair; same training and development memberships as v45."""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'upgrade_v45'))
import common45
import importlib.util
spec = importlib.util.spec_from_file_location('runner45', ROOT / 'upgrade_v45/run.py')
runner = importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)
from evidence46 import Evidence46
from agent45 import Agent45

HERE = ROOT / 'upgrade_v46'
RUN = common45.RUN.parent / 'rxrsi-v46'


class Agent46(Agent45):
    def __init__(self, state=None):
        super().__init__(state)
        self.labels = Evidence46()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['freeze', 'train', 'proposal', 'guard'], required=True)
    args = parser.parse_args()
    original = json.loads((ROOT / 'upgrade_v45/protocol.json').read_text())
    code = {name: common45.sha(HERE / name) for name in ('evidence46.py', 'run.py')}
    path = HERE / 'protocol.json'
    if not path.exists():
        common45.save(path, {'created_utc': datetime.now(timezone.utc).isoformat(), 'implementation': code,
            'parent_protocol_sha256': common45.sha(ROOT / 'upgrade_v45/protocol.json'),
            'source': 'TRAINING combination case source window loses patient-population qualifier. No development/test response motivated this repair.',
            'change': 'Expand retrieved span to original sentence boundaries; keep exact source offsets; omit whole spans rather than truncate to budget. Everything else uses frozen tool-only v45.',
            'shared_total_cost_limit_usd': original['max_incremental_usd'],
            'selection': original['selection'], 'autonomous_RSI': False})
    frozen = json.loads(path.read_text())
    assert frozen['implementation'] == code
    assert frozen['parent_protocol_sha256'] == common45.sha(ROOT / 'upgrade_v45/protocol.json')
    for name, h in original['implementation'].items():
        assert common45.sha(ROOT / 'upgrade_v45' / name) == h
    if args.mode == 'freeze':
        print('Whole-sentence intervention frozen'); return
    runner.HERE, runner.RUN, runner.Agent45 = HERE, RUN, Agent46
    runner.ARMS = {'whole_sentence': {'cards': [], 'product_scope': True, 'whole_sentence': True}}
    data = json.loads((common45.OLD_RUN / 'data.json').read_text())
    if args.mode in ('train', 'proposal'):
        for split in (['train'] if args.mode == 'train' else original['proposal']):
            runner.run('whole_sentence', split, original, data)
    else:
        ms = [json.loads((HERE / 'results' / ('whole_sentence-' + s + '.json')).read_text()) for s in original['proposal']]
        selected = all(m['correct'] >= m['baseline_correct'] and m['invalid'] <= m['baseline_invalid'] for m in ms) and sum(m['correct'] - m['baseline_correct'] for m in ms) > 0
        guard = {s: runner.run('whole_sentence', s, original, data) for s in original['guard']} if selected else {}
        accepted = selected and all(m['correct'] >= m['baseline_correct'] and m['invalid'] <= m['baseline_invalid'] for m in guard.values())
        common45.save(HERE / 'results/selection.json', {'proposal_selected': selected, 'guard': guard, 'accepted': accepted,
            'current_method_replaced': False, 'scope': 'Researcher tool repair, reused development, no new main/independent result.'})


if __name__ == '__main__':
    main()
