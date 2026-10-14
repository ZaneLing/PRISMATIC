# -*- coding: utf-8 -*-
"""Recount existing compute receipts without inference, fitting or new API requests."""
import hashlib
import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HERE = ROOT / 'paper'
PRIVATE = Path.home() / 'Desktop/MedTreeBench/dataset/restricted'
SEEDS = [42, 137, 2026]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    sources = {}
    private_receipts = {}

    def public(path):
        sources[str(path.relative_to(ROOT))] = sha(path)
        return json.loads(path.read_text())

    def events(version, panel, seed):
        name = f'{panel}-rsi-seed{seed}' if version == 27 else f'{panel}-seed{seed}'
        path = PRIVATE / f'prismatic-v{version}' / name / 'fit_events.jsonl'
        private_receipts[str(path.relative_to(PRIVATE))] = sha(path)
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        expected = {f'round{r}-C{c}' for r in range(1, 6) for c in [.1, 1., 10.]}
        expected |= {f'round{r}-fold{f}' for r in range(1, 6) for f in range(3)}
        assert {z['fit'] for z in rows} == expected
        assert all(z['seconds'] >= 0 and math.isfinite(z['seconds']) and z['visits'] > 0 for z in rows)
        return rows

    def calls(z):
        out = {}
        for row in z['rounds']:
            for arm, r in row['arms'].items():
                value = out.setdefault(arm, {'logical_calls': 0, 'known_logical_response_usd': 0., 'unpriced_logical_calls': 0})
                value['logical_calls'] += r['proposer_calls']
                if r['proposer_cost_usd'] is None:
                    value['unpriced_logical_calls'] += r['proposer_calls']
                else:
                    assert math.isfinite(r['proposer_cost_usd']) and r['proposer_cost_usd'] >= 0
                    value['known_logical_response_usd'] += r['proposer_cost_usd']
        return out

    report = {'status': 'receipt_recount_complete', 'author_runs': [], 'shared_policy_runs': [],
              'conventional_controls': [], 'reused_policy_runs': [], 'pending': [],
              'source_sha256': sources, 'private_receipt_sha256': private_receipts,
              'new_model_fits': 0, 'new_api_calls': 0, 'test_predictions_read': False,
              'scope': 'Recount of recorded costs and prior audited development results. Timing is not independent profiling, GPU time, FLOPs or a complete expenditure ledger; concurrent jobs share hardware. Logical response prices are not fresh physical spend.'}
    visits = public(ROOT / 'upgrade_v27/results/cohort_manifest.json')['splits']['train']['visits']
    for panel in ['full', 'molecular']:
        for method in (['ARMR', 'GAMENet'] if panel == 'full' else ['ARMR', 'GAMENet', 'SafeDrug']):
            for seed in SEEDS:
                path = ROOT / f'upgrade_v27/results/{panel}-{method}-seed{seed}.json'
                audit_path = ROOT / f'upgrade_v27/results/{panel}-{method}-selection-audit-seed{seed}.json'
                name = f'{panel}/{method}/{seed}'
                if not path.exists() or not audit_path.exists():
                    report['pending'].append(name); continue
                z = public(path); audit = public(audit_path)
                assert z['status'] == 'selection_frozen' and audit['status'] == 'passed'
                assert audit['source_report_sha256'] == sha(path)
                assert all(sha(ROOT / 'upgrade_v27' / n) == h for n, h in audit['source_sha256'].items())
                assert z['lock']['training_protocol_sha256'] == sha(ROOT / 'upgrade_v27/training_addendum.json')
                rows = z['epochs']; assert len(rows) == 50
                assert [r['epoch'] for r in rows] == list(range(1, 51))
                assert [r['cumulative_visit_exposures'] for r in rows] == [visits * i for i in range(1, 51)]
                log = PRIVATE / f'prismatic-v27/{panel}-{method}-seed{seed}.log'
                logged = {}
                for line in log.read_text().splitlines():
                    try: item = json.loads(line)
                    except json.JSONDecodeError: continue
                    if 'cumulative_optimizer_steps' in item:
                        logged[item['epoch']] = item
                assert all(all(logged[r['epoch']][k] == v for k, v in r.items()) for r in rows)
                private_receipts[str(log.relative_to(PRIVATE))] = sha(log)
                steps = [r['cumulative_optimizer_steps'] for r in rows]
                assert steps[0] > 0 and all(b > a for a, b in zip(steps, steps[1:]))
                times = [r['training_seconds'] for r in rows]
                assert all(t >= 0 and math.isfinite(t) for t in times)
                report['author_runs'].append({'panel': panel, 'method': method, 'seed': seed,
                    'epochs': 50, 'optimizer_steps': steps[-1], 'visit_exposures': rows[-1]['cumulative_visit_exposures'],
                    'parameters': z['parameters'], 'device': z['lock']['device'],
                    'summed_training_seconds': math.fsum(times), 'selected_epoch': z['selection']['epoch'],
                    'proposal_epoch_threshold_candidates': 50 * 6,
                    'guard_patient_f1': audit['splits']['guard']['selected_metrics']['patient_f1'],
                    'guard_patient_jaccard': audit['splits']['guard']['selected_metrics']['patient_jaccard']})
        control = public(ROOT / f'upgrade_v27/results/{panel}-controls.json')
        assert control['status'] == 'selection_frozen'
        for name, z in control['methods'].items():
            report['conventional_controls'].append({'panel': panel, 'method': name,
                'recorded_seconds': z['seconds'], 'timing_measured': name not in ['prevalence', 'last_visit'],
                'configuration_candidates': len(z['configuration'].get('trials', [{}])),
                'proposal_configuration_threshold_candidates': 6 * len(z['configuration'].get('trials', [{}])),
                'shared_feature_seconds': control['feature_seconds'],
                'timing_scope': 'The recorded cosine/LR block includes proposal search and guard prediction. Prevalence/last-visit zero is an unmeasured sentinel, not zero runtime. Feature construction is shared.'})
        for version in [27, 29]:
            for seed in SEEDS:
                prefix = f'{panel}-rsi' if version == 27 else panel
                path = ROOT / f'upgrade_v{version}/results/{prefix}-seed{seed}.json'
                audit_path = ROOT / f'upgrade_v{version}/results/{panel}-{"rsi-learning-audit" if version == 27 else "audit"}-seed{seed}.json'
                if not path.exists() or not audit_path.exists():
                    report['pending'].append(f'v{version}/{panel}/{seed}'); continue
                z = public(path); audit = public(audit_path)
                assert z['status'] == 'selection_frozen' and audit['status'] == 'passed'
                assert audit['source_report_sha256'] == sha(path)
                if version == 27:
                    assert all(sha(ROOT / 'upgrade_v27' / n) == h for n, h in audit['auditor_sources'].items())
                else:
                    assert audit['auditor_sha256'] == sha(ROOT / 'upgrade_v29/audit.py')
                fit_rows = events(version, panel, seed)
                if version == 27: assert fit_rows == z['fit_events']
                last = z['rounds'][-1]
                report['shared_policy_runs'].append({'version': version, 'panel': panel, 'seed': seed,
                    'rounds': len(z['rounds']), 'fit_events': len(fit_rows),
                    'unique_fit_labels': len({r['fit'] for r in fit_rows}),
                    'repeated_fit_events': len(fit_rows) - len({r['fit'] for r in fit_rows}),
                    'fit_input_rows_summed': sum(r['visits'] for r in fit_rows),
                    'summed_fit_seconds': math.fsum(r['seconds'] for r in fit_rows),
                    'methods_sharing_fits': list(last['arms']),
                    'final_policy_fit_patients': last['training_patients'] if version == 27 else last['policy_fit_patients'],
                    'final_policy_fit_visits': last['training_visits'] if version == 27 else last['fit_visits'],
                    'logical_proposals_by_arm': calls(z)})
        for seed in SEEDS:
            path = ROOT / f'upgrade_v30/results/{panel}-seed{seed}.json'
            audit_path = ROOT / f'upgrade_v30/results/{panel}-audit-seed{seed}.json'
            if not path.exists() or not audit_path.exists():
                report['pending'].append(f'v30/{panel}/{seed}'); continue
            z = public(path); audit = public(audit_path)
            assert z['status'] == 'selection_frozen' and audit['status'] == 'passed'
            assert audit['source_report_sha256'] == sha(path) and audit['auditor_sha256'] == sha(ROOT / 'upgrade_v30/audit.py')
            source_audit = ROOT / f'upgrade_v29/results/{panel}-audit-seed{seed}.json'
            assert audit['v29_audit_sha256'] == sha(source_audit)
            for r in z['rounds']:
                source = PRIVATE / f'prismatic-v29/{panel}-seed{seed}/round{r["round"]}/complete.json'
                assert r['source_round_sha256'] == sha(source)
                private_receipts[str(source.relative_to(PRIVATE))] = sha(source)
            report['reused_policy_runs'].append({'version': 30, 'panel': panel, 'seed': seed,
                'source_fit_run': f'v29/{panel}/{seed}', 'new_policy_fits': 0,
                'methods_sharing_fits': list(z['rounds'][-1]['arms']), 'logical_proposals_by_arm': calls(z)})
    groups = {}
    for row in report['author_runs']:
        groups.setdefault(row['panel'] + '/' + row['method'], []).append(row)
    report['author_method_summary'] = {name: {'seeds': [r['seed'] for r in rows],
        **{key: {'mean': statistics.mean(r[key] for r in rows),
                 'seed_sd': statistics.stdev(r[key] for r in rows) if len(rows) > 1 else None}
           for key in ['guard_patient_f1', 'guard_patient_jaccard', 'summed_training_seconds']}}
        for name, rows in groups.items()}
    report['script_sha256'] = sha(Path(__file__))
    (HERE / 'compute_accounting.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'status': report['status'], 'completed_audited_author_runs': len(report['author_runs']),
                      'shared_policy_runs': len(report['shared_policy_runs']), 'reused_policy_runs': len(report['reused_policy_runs'])}))


if __name__ == '__main__':
    main()
