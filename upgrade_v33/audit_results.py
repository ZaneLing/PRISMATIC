"""Recount local public predictions and verify provenance without model calls."""
import json
import hashlib
import subprocess
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/'upgrade_v8'))
from public_client import LOCAL, digest


def main():
    protocol = json.loads((HERE/'protocol.json').read_text())
    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()
    assert protocol['runner_sha256'] == sha(HERE/'run_retrieval_factorial.py')
    assert protocol['retriever_sha256'] == sha(HERE.parent/'rxrsiagent/core.py')
    assert protocol['data_sha256'] == sha(LOCAL/'data.json')
    assert protocol['label_sha256'] == sha(LOCAL.parent/'rxrsi-v11/labels.json')
    assert protocol['skill_sha256'] == {p.name: sha(p) for p in (HERE.parent/'upgrade_v17/artifacts/round_4').glob('*.md')}
    resource = LOCAL.parent/'resources/GRASP'
    pin = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=resource, text=True).strip()
    assert pin == '9d7d125a3e9b46ed591692475eb07aff4ae67d34'
    assert not subprocess.check_output(['git', 'diff', 'HEAD', '--', 'grasp'], cwd=resource, text=True).strip()
    data = json.loads((LOCAL/'data.json').read_text())
    root = LOCAL.parent/'rxrsi-v33'
    audit = {'status': 'passed', 'stages': {}, 'new_model_calls': 0, 'prior_cached_responses': 0,
             'protocol_sha256': sha(HERE/'protocol.json'), 'audit_sha256': sha(Path(__file__)),
             'grasp_author_core_commit': pin, 'author_core_modified': False,
             'interval': 'Exploratory item-paired bootstrap, 4000 draws, seed 33; no multiplicity adjustment. Development-selected effects are optimistic.'}
    for stage in ('proposal', 'guard', 'test'):
        path = HERE/'results'/(stage+'.json')
        if not path.exists():
            continue
        report = json.loads(path.read_text())
        assert report['status'] == 'complete'
        audit['stages'][stage] = {}
        for dataset, methods in report['results'].items():
            cases = data['transfer'] if dataset == 'rxqa' else data['parts']['test' if stage == 'test' else stage]
            outcomes = {}
            records = {}
            for method, summary in methods.items():
                folder = root/stage/dataset/method
                rows = [json.loads((folder/(digest(c['id'])+'.json')).read_text()) for c in cases]
                assert len(rows) == summary['n']
                assert all(r['case_id'] == c['id'] and not r.get('error') for r,c in zip(rows,cases))
                outcome = np.array([r['prediction'] == c['gold'] for r,c in zip(rows,cases)], dtype=int)
                assert int(outcome.sum()) == summary['correct']
                assert digest([{'case_id': r['case_id'], 'prediction': r['prediction'], 'request_sha256': r['request_sha256']} for r in rows]) == summary['predictions_sha256']
                for r in rows:
                    cache = json.loads((LOCAL/'cache'/(r['request_sha256']+'.json')).read_text())
                    assert cache['raw'] == r['raw']
                    assert cache['input_tokens'] == r['input_tokens']
                    if cache['role'] == 'retrieval_factorial_actor':
                        audit['new_model_calls'] += 1
                    else:
                        audit['prior_cached_responses'] += 1
                outcomes[method] = outcome
                records[method] = rows
            if 'old_skill' in outcomes and 'new_skill' in outcomes:
                diff = outcomes['new_skill']-outcomes['old_skill']
                rng = np.random.default_rng(33)
                draws = np.array([diff[rng.integers(0,len(diff),len(diff))].mean() for _ in range(4000)])
                audit['stages'][stage][dataset] = {
                    'fixes': int((diff == 1).sum()), 'regressions': int((diff == -1).sum()),
                    'difference': float(diff.mean()), 'ci95': np.quantile(draws,[.025,.975]).tolist()}
                missing = np.array([r['excerpt_count'] == 0 for r in records['new_skill']])
                audit['stages'][stage][dataset]['new_retrieval_without_excerpts'] = {
                    'n': int(missing.sum()),
                    'old_skill_correct': int(outcomes['old_skill'][missing].sum()),
                    'new_skill_correct': int(outcomes['new_skill'][missing].sum())}
                assert audit['stages'][stage][dataset]['fixes'] == report['paired']['fixes']
                assert audit['stages'][stage][dataset]['regressions'] == report['paired']['regressions']
    (HERE/'results/audit.json').write_text(json.dumps(audit, indent=2)+'\n')
    print(json.dumps(audit))


if __name__ == '__main__':
    main()
