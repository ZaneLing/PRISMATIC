# -*- coding: utf-8 -*-
"""Recount completed cross-method guard outputs and pair patients across methods."""
import hashlib
import json
import statistics
from pathlib import Path

import joblib
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIVATE = Path.home() / 'Desktop/MedTreeBench/dataset/restricted/prismatic-v27'
SEEDS = [42, 137, 2026]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    sources = {}; private_sources = {}

    def public(path):
        sources[str(path.relative_to(ROOT))] = sha(path)
        return json.loads(path.read_text())

    def saved(path):
        private_sources[str(path.relative_to(PRIVATE))] = sha(path)
        return np.load(path, allow_pickle=False)

    source = joblib.load(PRIVATE / 'visits.joblib')
    private_sources['visits.joblib'] = sha(PRIVATE / 'visits.joblib')
    cohort = public(HERE / 'results/cohort_manifest.json')
    cohort_audit = public(HERE / 'results/cohort_audit.json')
    resources = public(HERE / 'results/model_resource_manifest.json')
    assert cohort_audit['status'] == 'passed'
    assert cohort['bundle_sha256'] == cohort_audit['bundle_sha256'] == private_sources['visits.joblib']
    results = {'status': 'partial_audited_development', 'panels': {}, 'source_sha256': sources,
               'private_prediction_sha256': private_sources, 'new_model_inference': 0,
               'test_predictions_read': False, 'bootstrap_draws': 4000, 'bootstrap_seed': 27033,
               'scope': 'Post-training cross-method recount on the reused guard; no method/threshold selection. Paired patient intervals average available matched seeds first, without multiplicity correction or seed-population uncertainty. Prior checkpoint/source audits are retained; this analysis does not reexecute neural forwards.'}
    for panel in ['full', 'molecular']:
        bundle_path = PRIVATE / (panel + '-models.joblib')
        bundle = joblib.load(bundle_path); private_sources[bundle_path.name] = sha(bundle_path)
        assert resources['panels'][panel]['bundle_sha256'] == private_sources[bundle_path.name]
        med = bundle['medications']; med_set = set(med); gold = []; people = []; identities = []
        for person in source['data']['guard']:
            for visit in person['visits']:
                gold.append(set(visit['medications']) if panel == 'full' else set(visit['medications']) & med_set)
                people.append(person['subject_hash']); identities.append((visit['case_id'], person['subject_hash']))
        expected = [(v['case_id'], p['subject_hash']) for p in bundle['data']['guard'] for v in p['visits']]
        assert expected == identities and len(gold) == 1231
        keys, inverse = np.unique(people, return_inverse=True)
        assert len(keys) == 467
        methods = {}; methods_private = {}; patient_counts = np.bincount(inverse)

        def recount(name, seed, path, threshold, reference):
            probability = saved(path); assert probability.shape == (len(gold), len(med)) and np.isfinite(probability).all()
            predictions = probability >= threshold; values = []
            for row, target in zip(predictions, gold):
                pred = {med[i] for i in np.flatnonzero(row)}; hit = len(pred & target)
                values.append([2 * hit / (len(pred) + len(target)) if pred or target else 1.,
                               hit / len(pred | target) if pred or target else 1.])
            per_visit = np.asarray(values); patient = np.zeros((len(keys), 2))
            np.add.at(patient, inverse, per_visit); patient /= patient_counts[:, None]
            for i, key in enumerate(['patient_f1', 'patient_jaccard']):
                assert abs(float(patient[:, i].mean()) - reference[key]) < 1e-10
            methods_private.setdefault(name, {})[str(seed)] = patient
            methods.setdefault(name, []).append({'seed': seed, 'patient_f1': float(patient[:, 0].mean()),
                'patient_jaccard': float(patient[:, 1].mean()), 'prediction_sha256': sha(path)})
            return patient

        controls = public(HERE / f'results/{panel}-controls.json')
        control_audit = public(HERE / 'results/control_audit.json')
        assert controls['status'] == 'selection_frozen' and control_audit['status'] == 'passed'
        for name, value in controls['methods'].items():
            recount(name, 'fixed', PRIVATE / f'{panel}-controls/{name}-guard.npy', value['selection']['threshold'], control_audit['panels'][panel]['methods'][name])
        for method in (['ARMR', 'GAMENet'] if panel == 'full' else ['ARMR', 'GAMENet', 'SafeDrug']):
            for seed in SEEDS:
                audit_path = HERE / f'results/{panel}-{method}-selection-audit-seed{seed}.json'
                if not audit_path.exists(): continue
                audit = public(audit_path); path = HERE / f'results/{panel}-{method}-seed{seed}.json'; state = public(path)
                assert audit['status'] == 'passed' and audit['source_report_sha256'] == sha(path)
                assert all(sha(HERE / f) == h for f, h in audit['source_sha256'].items())
                assert state['status'] == 'selection_frozen' and len(state['epochs']) == 50
                recount(method, seed, PRIVATE / f'{panel}-{method}-seed{seed}/guard_probabilities.npy', state['selection']['threshold'], audit['splits']['guard']['selected_metrics'])
        for seed in SEEDS:
            audit_path = HERE / f'results/{panel}-rsi-learning-audit-seed{seed}.json'
            cross_path = HERE / f'results/{panel}-rsi-crossfit-audit-seed{seed}.json'
            if not audit_path.exists() or not cross_path.exists(): continue
            audit = public(audit_path); cross = public(cross_path); path = HERE / f'results/{panel}-rsi-seed{seed}.json'; state = public(path)
            assert audit['status'] == 'passed' and cross['status'] == 'complete' and audit['source_report_sha256'] == sha(path)
            assert all(sha(HERE / f) == h for f, h in audit['auditor_sources'].items())
            scores = saved(PRIVATE / f'{panel}-rsi-seed{seed}/audited-guard-patient-scores.npz')
            assert np.array_equal(scores['people'], keys)
            for name, reference in audit['guard'].items():
                patient = recount(name, seed, PRIVATE / f'{panel}-rsi-seed{seed}/{name}-guard.npy', .5, reference)
                np.testing.assert_allclose(patient, scores[name], atol=1e-12, rtol=0)
        aggregate = {}
        for name, rows in methods.items():
            aggregate[name] = {'seeds': [r['seed'] for r in rows], 'runs': len(rows),
                **{metric: {'mean': statistics.mean(r[metric] for r in rows),
                    'seed_sd': statistics.stdev(r[metric] for r in rows) if len(rows) > 1 else None}
                   for metric in ['patient_f1', 'patient_jaccard']}}
        own = methods_private['own_error_rule_agent']; contrasts = {}
        rng = np.random.default_rng(27033); draws = rng.integers(0, len(keys), (4000, len(keys)))
        for name, runs in methods_private.items():
            if name == 'own_error_rule_agent': continue
            common = sorted(own, key=int) if 'fixed' in runs else sorted(set(own) & set(runs), key=int)
            if not common: continue
            delta = np.mean([own[s] - runs['fixed' if 'fixed' in runs else s] for s in common], axis=0)
            boot = delta[draws].mean(axis=1)
            contrasts[name] = {'matched_seeds': [int(s) for s in common], 'fixed_control_reused': 'fixed' in runs,
                **{metric: {'difference': float(delta[:, i].mean()),
                    'patient_ci95': np.quantile(boot[:, i], [.025, .975]).tolist(),
                    'patients_with_positive_mean_difference': int((delta[:, i] > 1e-12).sum()),
                    'patients_with_negative_mean_difference': int((delta[:, i] < -1e-12).sum()),
                    'patients_with_zero_mean_difference': int((abs(delta[:, i]) <= 1e-12).sum())}
                   for i, metric in enumerate(['patient_f1', 'patient_jaccard'])}}
        results['panels'][panel] = {'visits': len(gold), 'patients': len(keys), 'methods': aggregate,
            'method_runs': methods, 'own_rule_agent_minus_control': contrasts}
    results['script_sha256'] = sha(Path(__file__))
    (HERE / 'results/development_methods.json').write_text(json.dumps(results, indent=2) + '\n')
    for lang in ['en', 'zh']:
        en = lang == 'en'
        lines = [('# Cross-method development comparison' if en else '# 同一数据上的跨方法开发集比较'), '',
                 ('All rows use 1,231 guard visits from 467 MIMIC-IV patients. Full ATC-L4 (271 classes) and the molecular subspace (219 classes) are separate. Current-visit diagnosis/procedure inputs define a retrospective task. Models and thresholds are selected on proposal data. Only completed, independently audited methods are recounted here; the final test gate stays closed.' if en else
                  '所有行均使用 MIMIC-IV 同一 1,231 次 guard 就诊／467 位患者。完整 ATC-L4（271 类）与分子子空间（219 类）分别报告。输入含本次完整就诊的诊断／操作，属于回顾性任务。模型和阈值由 proposal 选择。这里只重算已经完成并独立核验的方法；最终测试仍等待全部方法完成。'), '',
                 ('No model call, fit, test prediction or new selection is performed by this analysis. It reconstructs GT and patient ordering from the frozen source, counts the saved predictions separately, verifies published metrics and the prior audited rule-score arrays, then pairs identical patients and matched seeds.' if en else
                  '本次分析没有模型调用、拟合、测试预测或新的版本选择。它从冻结源数据重建 GT 与患者顺序，独立计数已保存预测，核对已发布指标及既有规则方法审计数组，再按相同患者和匹配种子做配对比较。'), '']
        for panel, data in results['panels'].items():
            lines += ['## ' + panel, '', '| Method | Completed runs | Patient F1 ± seed SD | Patient Jaccard ± seed SD |', '|---|---:|---:|---:|']
            for name, r in data['methods'].items():
                vals = []
                for metric in ['patient_f1', 'patient_jaccard']:
                    q = r[metric]; vals.append(f"{q['mean']:.5f}" + (f" ± {q['seed_sd']:.5f}" if q['seed_sd'] is not None else ''))
                lines.append(f"| {name} | {r['runs']} | " + ' | '.join(vals) + ' |')
            lines += ['', ('### Own-error rule agent minus each comparator' if en else '### 自身错误规则 agent 相对各对照的差值'), '',
                      '| Comparator | Matched seeds | F1 difference (pp) | Patient 95% interval (pp) |', '|---|---|---:|---:|']
            for name, r in data['own_rule_agent_minus_control'].items():
                q = r['patient_f1']; lo, hi = q['patient_ci95']
                lines.append(f"| {name} | {', '.join(map(str,r['matched_seeds']))} | {100*q['difference']:+.3f} | [{100*lo:+.3f}, {100*hi:+.3f}] |")
            lines += ['']
        lines += [('## Interpretation' if en else '## 解释边界'), '',
                  ('The paired comparison uses only shared completed seeds for neural models. A fixed conventional control is reused for each matched seed. Intervals use 4,000 paired patient-cluster resamples after averaging the observed seeds; they describe patient uncertainty conditional on those seeds and do not include a new-seed population or multiple-comparison correction. This post-training development analysis cannot promote a method or establish untouched-test superiority. A benefit over older neural architectures must also be compared with strong ordinary learning and greedy-memory controls.' if en else
                   '神经方法之间只比较共同完成的种子；固定传统对照在各匹配种子中复用。区间先平均已有种子，再做 4,000 次患者聚类配对重采样，反映给定这些种子的患者不确定性，不包含新种子总体波动或多重比较校正。这项训练后的开发集分析不用于升级方法，不能证明未触碰测试集上的领先。即使超过较早神经方法，也必须同时对照强普通学习和贪心记忆方法。'), '',
                  '[All source hashes, per-run metrics and paired effects](results/development_methods.json) · [Actual compute accounting](../paper/COMPUTE_ACCOUNTING.' + lang + '.md) · [Final-test execution status](RESULTS.' + lang + '.md)', '']
        (HERE / f'DEVELOPMENT_METHODS.{lang}.md').write_text('\n'.join(lines))
    print(json.dumps({'status': results['status'], 'recounted_method_runs': {k: sum(v['runs'] for v in p['methods'].values()) for k, p in results['panels'].items()}, 'test_predictions_read': False}))


if __name__ == '__main__':
    main()
