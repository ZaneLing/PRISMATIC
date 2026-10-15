"""Read-only public-data audit: frozen selection, cases, and retrieval coverage.

No inference, no API, no update/selection from test labels. Contrasting cases
are selected post hoc by a declared deterministic rule and are illustrative.
"""
import hashlib
import json
import sys
from pathlib import Path
from .core import LabelIndex, HERE

ROOT = HERE.parent
LOCAL = Path.home() / 'Desktop/PRISMATIC/upgrade_v2/.local'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    base = LOCAL / 'rxrsi-v8'
    folder = base / 'grounded-grasp-v17-seed-42'
    data = read(base / 'data.json')
    scores = read(folder / 'val_scores.json')
    best = max(scores, key=lambda r: r['score'])
    assert best['n_correct'] == 206 and best['n_total'] == 387
    frozen_path = ROOT / 'upgrade_v17/results/frozen_skills.json'
    frozen = read(frozen_path)
    assert frozen['test_used_for_selection'] is False
    skill = ROOT / 'upgrade_v17/artifacts/round_4/label_indication_and_caution_parsing.md'
    assert sha(skill) == frozen['skills_sha256']['label_indication_and_caution_parsing.md']
    profile = {'name': 'RxRSIAgent', 'selection': 'Saved best end-of-epoch validation checkpoint, before this comparison; no test ranking.',
        'validation': best, 'backbone': 'deepseek/deepseek-v4.1-flash', 'actor_calls': 1, 'actor_output_tokens': 512,
        'skill_sha256': sha(skill), 'skill_path': str(skill.relative_to(ROOT)),
        'optimizer': 'Unmodified GRASP author core, credited',
        'evidence': 'Frozen balanced openFDA excerpt retrieval',
        'source_method_key': 'evolving_grounded', 'source_report': 'upgrade_v17/results/summary.json',
        'selection_source_sha256': sha(folder / 'val_scores.json'),
        'frozen_source_sha256': sha(frozen_path),
        'new_review_layer_in_scores': False, 'retired_weight_updates_in_profile': False,
        'scope': 'Executed option-selection configuration; full-order review layer requires separate end-to-end evaluation.'}
    (HERE / 'evaluated_profile.json').write_text(json.dumps(profile, indent=2)+'\n')
    pairs = {}
    prediction_recounts = {}
    main_summary = read(ROOT/'upgrade_v17/results/summary.json')
    for ds, cases in [('rxsafebench', data['parts']['test']), ('rxqa', data['transfer'])]:
        fixed = read(folder / ('fixed_grounded-' + ds + '.json'))
        agent = read(folder / ('evolving_grounded-' + ds + '.json'))
        assert [c['id'] for c in cases] == [r['case_id'] for r in fixed] == [r['case_id'] for r in agent]
        for c, f, a in zip(cases, fixed, agent):
            assert bool(f['correct']) == (f['prediction'] == c['gold'])
            assert bool(a['correct']) == (a['prediction'] == c['gold'])
        prediction_recounts[ds] = {}
        for key, predictions in [('fixed_grounded', fixed), ('evolving_grounded', agent)]:
            recounted = sum(p['prediction'] == c['gold'] for c, p in zip(cases, predictions))
            assert recounted == main_summary['datasets'][ds]['methods'][key]['correct']
            assert len(cases) == main_summary['datasets'][ds]['methods'][key]['n']
            prediction_recounts[ds][key] = {'correct': recounted, 'n': len(cases),
                'predictions_sha256': sha(folder/(key+'-'+ds+'.json'))}
        pairs[ds] = (cases, fixed, agent)
    cases, fixed, agent = pairs['rxqa']
    examples = []
    for kind in ('fix', 'regression'):
        candidates = [(c, f, a) for c, f, a in zip(cases, fixed, agent)
            if ((not f['correct'] and a['correct']) if kind == 'fix' else (f['correct'] and not a['correct']))]
        c, f, a = sorted(candidates, key=lambda row: str(row[0]['id']))[0]
        examples.append({'type': kind, 'public_dataset': 'RxQA-OpenFDA', 'public_question_id': c['id'],
            'gold': c['gold'], 'fixed_prediction': f['prediction'], 'agent_prediction': a['prediction'],
            'case_sha256': hashlib.sha256(json.dumps(c,sort_keys=True).encode()).hexdigest(),
            'interpretation_limit': 'Observed answers only; no causal reasoning trace or clinical recommendation inferred.'})
    case_report = {'selection_rule': 'First lexicographic public ID in each fix/regression group; selected after evaluation.',
        'public_data_only': True, 'cases': examples, 'prediction_recounts': prediction_recounts,
        'fixed_prediction_sha256': sha(folder/'fixed_grounded-rxqa.json'),
        'agent_prediction_sha256': sha(folder/'evolving_grounded-rxqa.json')}
    (HERE/'results/case_studies.json').write_text(json.dumps(case_report,indent=2)+'\n')
    sys.path.insert(0,str(ROOT/'upgrade_v11'))
    from evidence_tool import LabelEvidence
    old = LabelEvidence()
    new = LabelIndex(LOCAL/'rxrsi-v11/labels.json')
    raw_labels = read(LOCAL/'rxrsi-v11/labels.json')
    raw_by_id = {r['label']['id']: r['label'] for r in raw_labels.values()
                 if r.get('status') == 'matched' and r.get('label', {}).get('id')}
    verified_spans = 0
    counts = {'n':len(cases), 'old_any_excerpt':0, 'new_any_excerpt':0,
              'old_dosage_excerpt':0, 'new_dosage_excerpt':0, 'new_mentioned_label':0}
    by_case = {}
    for c in cases:
        before = old.query({'dialogue':c['dialogue'], 'options':c['options']}, 'balanced')
        after = new.query(c['dialogue'], c['options'])
        counts['old_any_excerpt'] += bool(before['excerpts'])
        counts['new_any_excerpt'] += bool(after['excerpts'])
        counts['old_dosage_excerpt'] += any(e['section']=='dosage_and_administration' for e in before['excerpts'])
        counts['new_dosage_excerpt'] += any(e['section']=='dosage_and_administration' for e in after['excerpts'])
        counts['new_mentioned_label'] += bool(after['label_ids'])
        if str(c['id']) in {str(e['public_question_id']) for e in examples}:
            by_case[str(c['id'])] = {'old_excerpts':len(before['excerpts']), 'new_excerpts':len(after['excerpts']),
                                    'new_label_ids':after['label_ids']}
        for e in after['excerpts']:
            assert e['source_sha256']==new.source_sha256
            source_values = raw_by_id[e['label_id']][e['section']]
            if isinstance(source_values, str):
                source_values = [source_values]
            source_paragraph = source_values[e['paragraph_index']]
            assert source_paragraph[e['offset']:e['offset']+len(e['quote'])] == e['quote']
            verified_spans += 1
    report = {'status':'complete','scope':'Retrospective retrieval-only coverage audit; no LLM predictions changed.',
        'counts':counts,'case_coverage':by_case,'source_label_sha256':new.source_sha256,
        'retriever_sha256':sha(HERE/'core.py'),'public_case_source_sha256':sha(base/'data.json'),
        'gold_used_for_retrieval':False,'api_calls':0,
        'source_spans_independently_recounted': verified_spans,
        'limits':'Mention matching and excerpt availability are not relevance, formulation applicability, clinical safety or accuracy.'}
    (HERE/'results/retrieval_coverage.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'profile_validation':best,'case_ids':[e['public_question_id'] for e in examples],**report}))


if __name__ == '__main__':
    main()
