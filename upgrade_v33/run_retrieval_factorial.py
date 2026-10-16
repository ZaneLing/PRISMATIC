"""Bounded public development audit; test evaluation requires a frozen gate.

Uses the exact author-core skill injection and prior task prompt. API failures
stop evaluation rather than becoming wrong answers. Raw receipts stay local.
"""
import argparse
import hashlib
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RESOURCE = Path.home() / 'Desktop/PRISMATIC/upgrade_v2/.local/resources/GRASP'
for p in (RESOURCE, ROOT, ROOT/'upgrade_v8', ROOT/'upgrade_v10', ROOT/'upgrade_v11'):
    sys.path.insert(0, str(p))
from public_client import LOCAL, request, digest, ledger_total
from grasp_task import MedicationTask
from grasp.skills.agent import SkillAwareAgent
from grasp.skills.repository import SkillRepository
from evidence_tool import LabelEvidence
from rxrsiagent.core import LabelIndex

RUN = LOCAL.parent/'rxrsi-v33'
LABELS = LOCAL.parent/'rxrsi-v11/labels.json'
SKILLS = ROOT/'upgrade_v17/artifacts/round_4'
CONFIGS = ('old_no_skill', 'old_skill', 'new_no_skill', 'new_skill')
DISCLAIMER = ('\nDrug-label tool excerpts (company-submitted labels via openFDA; '
    'incomplete excerpts, apply only to documented patient facts; missing text '
    'is not proof of safety):\n')


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n')
    temp.replace(path)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Backend:
    def inference(self, history, tools=None):
        assert tools is None
        self.receipt = request(history, 'deepseek/deepseek-v4.1-flash', 512,
                               role='retrieval_factorial_actor')
        if self.receipt.get('error'):
            raise RuntimeError('Transport failure; not a model score')
        return self.receipt['raw']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', choices=['proposal', 'guard', 'test'], required=True)
    args = parser.parse_args()
    data = json.loads((LOCAL/'data.json').read_text())
    RUN.mkdir(parents=True, exist_ok=True)
    empty = RUN/'empty'
    empty.mkdir(exist_ok=True)
    protocol_path = HERE/'protocol.json'
    if not protocol_path.exists():
        assert args.stage == 'proposal'
        protocol = {
            'created_utc': datetime.now(timezone.utc).isoformat(),
            'design': 'old/new retrieval crossed with absent/frozen incumbent skill',
            'configs': list(CONFIGS), 'model': 'deepseek/deepseek-v4.1-flash',
            'output_tokens': 512, 'calls_per_case': 1, 'temperature': 0,
            'proposal_n': 190, 'guard_n': 197,
            'promotion': 'new_skill must strictly beat old_skill in correct count on proposal; then strictly beat old_skill on guard with no increase in invalid answers. Otherwise reject; no test run.',
            'no_skill_controls': 'diagnostic; cannot be renamed an evolved agent',
            'test_if_promoted': 'freeze new_skill, then all 988 RxSafe and 300 RxQA; no test-driven revision',
            'exposure': 'Development sets and test benchmarks were observed in historical work. Results are exploratory, not fresh confirmatory evaluation.',
            'label_sha256': sha(LABELS), 'data_sha256': sha(LOCAL/'data.json'),
            'skill_sha256': {p.name: sha(p) for p in SKILLS.glob('*.md')},
            'retriever_sha256': sha(ROOT/'rxrsiagent/core.py'),
            'runner_sha256': sha(Path(__file__)),
            'source_optimizer': 'Previously learned GRASP author-core skill; no new learning in this diagnostic experiment.',
            'maximum_incremental_usd': 8,
            'ledger_start_usd': ledger_total(),
            'restricted_data': False,
        }
        save(protocol_path, protocol)
    protocol = json.loads(protocol_path.read_text())
    assert protocol['data_sha256'] == sha(LOCAL/'data.json')
    assert protocol['label_sha256'] == sha(LABELS)
    assert protocol['retriever_sha256'] == sha(ROOT/'rxrsiagent/core.py')
    assert protocol['runner_sha256'] == sha(Path(__file__))
    assert protocol['skill_sha256'] == {p.name: sha(p) for p in SKILLS.glob('*.md')}
    os.environ['RXRSI_PUBLIC_COST_CAP_USD'] = str(protocol['ledger_start_usd']+8)
    if args.stage in ('guard', 'test'):
        prior = json.loads((HERE/'results'/('proposal.json' if args.stage == 'guard' else 'guard.json')).read_text())
        if not prior['gate_passed']:
            raise RuntimeError('Development promotion gate failed; no dependent evaluation permitted')
    if args.stage == 'test':
        save(HERE/'results/test_freeze.json', {'config': 'new_skill', 'protocol_sha256': sha(protocol_path),
            'guard_sha256': sha(HERE/'results/guard.json'), 'frozen_utc': datetime.now(timezone.utc).isoformat()})
    sets = [('rxsafebench', data['parts']['test']), ('rxqa', data['transfer'])] if args.stage == 'test' else [(args.stage, data['parts'][args.stage])]
    configs = CONFIGS if args.stage == 'proposal' else ('old_skill', 'new_skill') if args.stage == 'guard' else ('new_skill',)
    old, new = LabelEvidence(), LabelIndex(LABELS)
    task = MedicationTask()
    report = {'stage': args.stage, 'status': 'running', 'results': {}}
    for dataset, cases in sets:
        views = {c['id']: {'old': old.query(c, 'balanced'), 'new': new.query(c['dialogue'], c['options'])} for c in cases}
        report['results'][dataset] = {}
        all_rows = {}
        for config in configs:
            folder = RUN/args.stage/dataset/config
            folder.mkdir(parents=True, exist_ok=True)
            def one(c):
                path = folder/(digest(c['id'])+'.json')
                if path.exists():
                    return json.loads(path.read_text())
                evidence = views[c['id']][config.split('_')[0]]
                view = dict(c, dialogue=c['dialogue']+DISCLAIMER+json.dumps(evidence, ensure_ascii=False))
                backend = Backend()
                learned = SKILLS if config.endswith('_skill') and 'no_skill' not in config else empty
                actor = SkillAwareAgent(backend, SkillRepository(base_dir=empty, learned_dir=learned))
                # Empty base has no markdown; absent skills cannot be duplicated.
                out = task.rollout(view, actor)
                row = {**backend.receipt, 'case_id': c['id'], 'prediction': out.answer or None,
                       'correct': out.answer == c['gold'], 'excerpt_count': len(evidence['excerpts']),
                       'evidence_sha256': digest(evidence)}
                save(path, row)
                return row
            rows_by_id = {}
            with ThreadPoolExecutor(max_workers=8) as pool:
                jobs = [pool.submit(one, c) for c in cases]
                for future in as_completed(jobs):
                    row = future.result()
                    rows_by_id[row['case_id']] = row
                    if len(rows_by_id) % 25 == 0:
                        print(json.dumps({'dataset': dataset, 'config': config, 'completed': len(rows_by_id), 'n': len(cases)}), flush=True)
            rows = [rows_by_id[c['id']] for c in cases]
            assert len(rows_by_id) == len(cases)
            all_rows[config] = rows
            summary = {'n': len(rows), 'correct': sum(r['correct'] for r in rows),
                       'invalid': sum(r['prediction'] is None for r in rows),
                       'logical_cost_usd': sum(r.get('cost_usd') or 0 for r in rows),
                       'input_tokens': sum(r.get('input_tokens') or 0 for r in rows),
                       'output_tokens': sum(r.get('output_tokens') or 0 for r in rows),
                       'with_excerpts': sum(r['excerpt_count'] > 0 for r in rows),
                       'predictions_sha256': digest([{'case_id': r['case_id'], 'prediction': r['prediction'], 'request_sha256': r['request_sha256']} for r in rows])}
            summary['accuracy'] = summary['correct']/summary['n']
            report['results'][dataset][config] = summary
            save(HERE/'results'/(args.stage+'.json'), report)
            print(json.dumps({'dataset': dataset, 'config': config, **summary}), flush=True)
        if args.stage != 'test':
            previous, candidate = all_rows['old_skill'], all_rows['new_skill']
            report['paired'] = {'fixes': sum(not a['correct'] and b['correct'] for a,b in zip(previous,candidate)),
                               'regressions': sum(a['correct'] and not b['correct'] for a,b in zip(previous,candidate))}
            metrics = report['results'][dataset]
            report['gate_passed'] = (metrics['new_skill']['correct'] > metrics['old_skill']['correct'] and
                                    metrics['new_skill']['invalid'] <= metrics['old_skill']['invalid'])
    report['status'] = 'complete'
    report['ledger_increment_usd'] = ledger_total()-protocol['ledger_start_usd']
    save(HERE/'results'/(args.stage+'.json'), report)


if __name__ == '__main__':
    main()
