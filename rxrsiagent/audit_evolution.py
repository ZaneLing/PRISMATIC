"""Recount frozen skill lineage and proposal gates without running an actor."""
import difflib
import hashlib
import json
import re
import random
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCAL = Path.home() / 'Desktop/PRISMATIC/upgrade_v2/.local'
RUN = LOCAL / 'rxrsi-v8/grounded-grasp-v17-seed-42'
CORE = LOCAL / 'resources/GRASP'
PIN = '9d7d125a3e9b46ed591692475eb07aff4ae67d34'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=CORE, text=True).strip() == PIN
    assert not subprocess.check_output(['git', 'diff', '--', 'grasp'], cwd=CORE)
    updates = read(RUN / 'epoch_0/skill_updates.json')
    summary = read(ROOT / 'upgrade_v17/results/summary.json')
    hashes = read(ROOT / 'upgrade_v17/results/round_artifacts.json')
    data = read(LOCAL / 'rxrsi-v8/data.json')
    traces_path = RUN/'epoch_0/dev_runs.jsonl'
    traces = [json.loads(line) for line in traces_path.read_text().splitlines() if line]
    train = {c['id']: c for c in data['parts']['train']}
    assert len(traces) == len(train) == 625
    assert {r['sample_id'] for r in traces} == set(train)
    assert len({r['sample_id'] for r in traces}) == len(traces)

    def stratified(samples, n, rng):
        groups = {}
        for sample in samples:
            groups.setdefault(sample.get('type', 'other'), []).append(sample)
        if not groups:
            return []
        per = max(1, n//len(groups))
        chosen = [s for group in groups.values() for s in rng.sample(group, min(per, len(group)))]
        remaining = n-len(chosen)
        if remaining > 0:
            selected = {c['id'] for c in chosen}
            pool = [s for s in samples if s['id'] not in selected]
            chosen.extend(rng.sample(pool, min(remaining, len(pool))))
        return chosen
    interpretations = {
        0: 'No learned skill; fixed label evidence.',
        1: 'All four proposals rejected by the regression gate; no retained change.',
        2: 'Adds indication matching followed by patient-triggered label cautions.',
        3: 'Revises the distinction between triggered stop language and monitoring cautions.',
        4: 'Requires checking stop clauses even for the only indication-matching option; expands output evidence instructions.'}
    rounds = []
    previous_lines = []
    cumulative = 0
    for r in range(5):
        row = {'round': r, 'cases_seen': cumulative, 'skill_count': int(r >= 2),
               'artifact_revision': max(0, r-1), 'semantic_change': interpretations[r],
               'interpretation_status': 'Researcher description of artifact text, not verified clinical knowledge'}
        if r:
            u = updates[r-1]
            assert u['update_cycle'] == r-1
            cumulative += u['batch_size']
            current = [t for t in traces if t['update_cycle'] == r-1]
            prior = [t for t in traces if t['update_cycle'] < r-1]
            assert len(current) == u['batch_size']
            probe_pool = prior or current
            rng = random.Random(f'42:probe:0:{r-1}')
            probe = stratified([train[t['sample_id']] for t in probe_pool if not t['is_correct']], 20, rng)
            probe += stratified([train[t['sample_id']] for t in probe_pool if t['is_correct']], 20, rng)
            current_ids = {t['sample_id'] for t in current}
            assert len(probe) == 40
            row.update(cases_seen=cumulative, new_cases=u['batch_size'],
                       proposal_evaluations=len(u['grpo']),
                       initial_proposal_evaluations=sum(not x.get('contrastive_revision', False) for x in u['grpo']),
                       revision_evaluations=sum(bool(x.get('contrastive_revision')) for x in u['grpo']))
            row.update(reconstructed_probe_cases=len(probe),
                       probe_overlap_with_proposal_batch=sum(p['id'] in current_ids for p in probe))
            candidates = []
            for c in u['grpo']:
                score = ((c['fixes']-c['baseline_fixes']) -
                         (c['regressions']-c['baseline_regressions']) -
                         (c.get('invalid_action_regression_penalty', 2)-1)*c['invalid_action_regressions'])
                assert score == c['score']
                candidates.append(dict(action=c['proposal']['action'], name=c['proposal']['name'],
                    score=score, fixes=c['fixes'], regressions=c['regressions'],
                    baseline_fixes=c['baseline_fixes'], baseline_regressions=c['baseline_regressions'],
                    eligible=score > 0 and c['regressions'] <= c['baseline_regressions'],
                    contrastive_revision=bool(c.get('contrastive_revision'))))
            eligible = [c for c in candidates if c['eligible']]
            winner = max(eligible, key=lambda c: c['score']) if eligible else None
            assert bool(winner) == bool(u['applied'])
            if winner:
                assert (winner['action'], winner['name']) == (u['applied'][0]['action'], u['applied'][0]['name'])
            row.update(action=winner['action'] if winner else 'NONE', winner=winner, candidates=candidates)
        else:
            row.update(new_cases=0, action='INITIAL', proposal_evaluations=0,
                       initial_proposal_evaluations=0, revision_evaluations=0, winner=None, candidates=[])
        lines = []
        if r >= 2:
            path = ROOT / f'upgrade_v17/artifacts/round_{r}/label_indication_and_caution_parsing.md'
            assert sha(path) == hashes[f'round_{r}']
            text = path.read_text()
            # Exclude metadata so counts describe the actual instruction body.
            body = text.split('---', 2)[2].strip()
            lines = body.splitlines()
            row.update(artifact_path=str(path.relative_to(ROOT)), artifact_sha256=sha(path),
                       body_words=len(re.findall(r'\S+', body)))
        else:
            row.update(artifact_path=None, artifact_sha256=None, body_words=0)
        changes = list(difflib.ndiff(previous_lines, lines))
        row.update(body_lines_added=sum(x.startswith('+ ') for x in changes),
                   body_lines_removed=sum(x.startswith('- ') for x in changes))
        previous_lines = lines
        rounds.append(row)
    assert cumulative == 625
    prediction_hashes = {}
    for ds, cases in [('rxsafebench', data['parts']['test']), ('rxqa', data['transfer'])]:
        previous = None
        for r, row in enumerate(rounds):
            name = 'fixed_grounded' if r <= 1 else f'round_{r}'
            path = RUN / 'round_evaluation' / f'{name}-{ds}.json'
            predictions = read(path)
            assert [x['case_id'] for x in predictions] == [c['id'] for c in cases]
            correct = [p['prediction'] == c['gold'] for p, c in zip(predictions, cases)]
            assert all(bool(p['correct']) == c for p, c in zip(predictions, correct))
            fixes = sum(a and not b for a, b in zip(correct, previous)) if previous is not None else 0
            regressions = sum(b and not a for a, b in zip(correct, previous)) if previous is not None else 0
            saved = summary['rounds'][ds][r]
            assert (sum(correct), fixes, regressions) == (saved['correct'], saved['fixes'], saved['regressions'])
            row[ds] = dict(n=len(cases), correct=sum(correct), fixes=fixes, regressions=regressions,
                           accuracy=sum(correct)/len(cases), reused_same_state=r == 1)
            previous = correct
            prediction_hashes[f'{name}-{ds}'] = sha(path)
    report = {'status': 'complete', 'scope': 'Frozen public skill lineage and output audit; no new inference',
              'source_core_commit': PIN, 'core_modified': False, 'rounds': rounds,
              'initial_proposals_evaluated': sum(x['initial_proposal_evaluations'] for x in rounds),
              'contrastive_revisions_evaluated': sum(x['revision_evaluations'] for x in rounds),
              'accepted_updates': sum(x['winner'] is not None for x in rounds),
              'validation': read(RUN/'val_scores.json'),
              'validation_timing': 'Baseline and end of one epoch only; no per-round development curve was measured.',
              'probe_scope': 'Configured 40 training probes (target 20 failing/20 passing); first batch reuses its own training cases; later batches use prior training batches. No independent clinical regression set.',
              'unchanged_modules': ['LLM weights', 'retrieval code', 'label corpus', 'output contract'],
              'counts_are_not_capability_scores': True, 'api_calls': 0,
              'source_sha256': {'skill_updates': sha(RUN/'epoch_0/skill_updates.json'),
                  'training_traces': sha(traces_path),
                  'core_cycle': sha(CORE/'grasp/cycle.py'), 'summary': sha(ROOT/'upgrade_v17/results/summary.json'),
                  'audit_code': sha(Path(__file__)), 'predictions': prediction_hashes}}
    (ROOT/'rxrsiagent/results/evolution_audit.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: report[k] for k in ['status','initial_proposals_evaluated','contrastive_revisions_evaluated','accepted_updates','api_calls']}))
    for r in rounds:
        print(json.dumps({k:r[k] for k in ['round','cases_seen','action','skill_count','body_words','body_lines_added','body_lines_removed','rxsafebench','rxqa']}))


if __name__ == '__main__':
    main()
