"""Same local LLM: repaired RAG review and validation-gated anchor review.

The 50 old test proposals are replayed without new generation; their original
cost is charged to the replay arm. Validation decisions precede test inference.
Raw predictions and patient text remain restricted. No API requests are made.
"""
import hashlib,json,time,sys
from pathlib import Path
import numpy as np
from mlx_lm import load,generate
from mlx_lm.sample_utils import make_sampler
from core import parse_codes,clinical_review,digest

HERE=Path(__file__).resolve().parent
ROOT=Path.home()/'Desktop/MedTreeBench/dataset/restricted'
PRIVATE=ROOT/'prismatic-v5'
MODEL=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/models/qwen3-4b-instruct-2507-4bit'
sys.path.insert(0,str(HERE.parent/'upgrade_v4'))
from run_local_harness import stats,paired

def run():
    config=json.loads((HERE/'protocol.json').read_text())
    fingerprint=digest({'config':config,'source':Path(__file__).read_text(),'core':(HERE/'core.py').read_text()})
    model,tok=load(str(MODEL)); sampler=make_sampler(temp=0.0)
    graph=np.load(Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/resources/atc4_graphs.npz')['ddi']
    graph_classes=json.loads((HERE.parent/'upgrade_v4/results/graph_resource_audit.json').read_text())['classes']
    ci={c:i for i,c in enumerate(graph_classes)}
    system=('Offline historical-order prediction research, not patient care. Use only the supplied admission snapshot. '
       'Availability of triage/home-medication entry is uncertain. Select up to five ATC4 classes from the allowed list; '
       'classes are not interchangeable ingredients. Return only a JSON object {"codes":["CODE"]}. '
       'Do not output explanations, dose advice, or invent codes. Empty output is allowed.')
    def infer(messages,cap):
        prompt=tok.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
        t=time.monotonic();raw=generate(model,tok,prompt=prompt,max_tokens=cap,sampler=sampler,verbose=False)
        return {'raw':raw,'tokens':len(tok.encode(raw)),'input_tokens':len(tok.encode(prompt)),'seconds':time.monotonic()-t}
    def wrap(result,allowed,fallback=(),prior=None):
        parsed=parse_codes(result['raw'],allowed,fallback)
        r={**result,**parsed,'valid':parsed['raw_valid'],'calls':1+int(prior is not None)}
        if prior:
            for k in ['tokens','input_tokens','seconds']:r[k]+=prior[k]
        r['clinical_review']=clinical_review(r['codes'])
        return r
    def anchor_row(codes):
        return {'codes':codes,'valid':True,'raw_valid':True,'parse_status':'structured_ranker',
                'tokens':0,'input_tokens':0,'seconds':0,'calls':0}
    all_rows={}; all_labels={}; report={}
    for split in ['val','test']:
        source=PRIVATE if split=='val' else ROOT/'prismatic-v4'
        prefix='val' if split=='val' else 'llm'
        cases=[json.loads(s) for s in (source/f'{prefix}_inputs.jsonl').read_text().splitlines()]
        labels=[json.loads(s) for s in (source/f'{prefix}_labels.jsonl').read_text().splitlines()]
        anchors=json.loads((PRIVATE/f'{split}_anchor.json').read_text())
        old={r['case_id']:r for r in map(json.loads,(ROOT/'prismatic-v4/llm_method_predictions.jsonl').read_text().splitlines())} if split=='test' else {}
        path=PRIVATE/f'{split}_llm_repair.jsonl'; done={}
        if path.exists():
            for line in path.read_text().splitlines():
                r=json.loads(line)
                if r['fingerprint']!=fingerprint: raise ValueError('Run configuration changed')
                done[r['case_id']]=r
        for case in cases:
            case_hash=digest({'case':case,'anchor':anchors[case['case_id']]})
            if case['case_id'] in done:
                assert done[case['case_id']]['case_sha256']==case_hash
                continue
            allowed={x['atc4'] for x in case['candidates']}
            evidence={'E1_chiefcomplaint':case['chiefcomplaint'],'E2_acuity':case['acuity'],
                      'E3_home_meds':case['home_meds'],'availability':case['availability']}
            messages=[{'role':'system','content':system}, {'role':'user','content':json.dumps({
                'patient_evidence':evidence,'candidate_class_examples':case['candidates']})},
                {'role':'user','content':'Training-case retrieval (historical behavior, not clinical evidence for this patient): '+json.dumps(case['retrieved_cases'])}]
            proposal=(old[case['case_id']]['arms']['case_retrieval'] if split=='test' else
                      wrap(infer(messages,192),allowed))
            prior=parse_codes(proposal['raw'],allowed)
            repair_instruction=('Review historical-order predictions once. Missing allergy, weight, renal function, '
               'or indication documentation is UNKNOWN, not evidence that no historical medication was ordered. '
               'Do not empty the list merely because clinical safety cannot be verified. '
               'Use the admission context and retrieved historical behavior to select up to five likely recorded classes. '
               'You may change a prediction when the supplied case supports a better historical prediction. '
               'Keep clinical clearance separate: these predictions never authorize administration. Return codes JSON only.')
            revision=wrap(infer(messages+[{'role':'assistant','content':proposal['raw']},
                       {'role':'user','content':repair_instruction}],384),allowed,prior['codes'],proposal)
            anchor_codes=[x['atc4'] for x in anchors[case['case_id']]]
            # Coarse graph findings are inspectable flags, never ingredient-level contraindications.
            flags=[{'pair':[a,b],'resource':'TWOSIDES ATC-class projection','status':'needs_ingredient_verification'}
                   for i,a in enumerate(anchor_codes) for b in anchor_codes[i+1:]
                   if a in ci and b in ci and graph[ci[a],ci[b]]]
            anchor_prompt={'historical_ranker_candidates':anchors[case['case_id']],
                           'class_level_flags_not_clinical_contraindications':flags,
                           'instruction':repair_instruction+' The ranker was trained on the training split. '
                              'Its candidate scores are statistical estimates, not calibrated clinical probabilities.'}
            reviewed_anchor=wrap(infer(messages+[{'role':'user','content':json.dumps(anchor_prompt)}],384),allowed,anchor_codes)
            r={'case_id':case['case_id'],'case_sha256':case_hash,'fingerprint':fingerprint,
               'arms':{'retrieval_proposal':proposal,'repaired_review':revision,
                       'anchor_only':anchor_row(anchor_codes),'anchor_llm_revision':reviewed_anchor},
               'graph_flags':flags,'state_transitions':['snapshot','retrieve','rank','flag','revise','parse_or_recover','clinical_unknown','validation_policy']}
            with path.open('a') as f:f.write(json.dumps(r)+'\n')
            done[case['case_id']]=r
            print(json.dumps({'split':split,'completed':len(done),'total':len(cases)}),flush=True)
        ordered=[done[c['case_id']] for c in cases]
        arms={a:[r['arms'][a] for r in ordered] for a in ordered[0]['arms']}
        if split=='val':
            anchor_f1=stats(arms['anchor_only'],labels)['observed_micro_f1']
            revision_f1=stats(arms['anchor_llm_revision'],labels)['observed_micro_f1']
            # Strict improvement is required; tie keeps simpler ranker.
            gate={'use_llm_prediction_revision':revision_f1>anchor_f1,
                  'validation_anchor_f1':anchor_f1,'validation_llm_revision_f1':revision_f1,
                  'fingerprint':fingerprint,'rule':'strict validation improvement; no test labels used'}
            (HERE/'results/llm_validation_gate.json').write_text(json.dumps(gate,indent=2)+'\n')
        else:
            gate=json.loads((HERE/'results/llm_validation_gate.json').read_text())
        # In shadow mode the LLM still runs and is charged; only predictions revert.
        arms['gated_harness']=[]
        for a,r in zip(arms['anchor_only'],arms['anchor_llm_revision']):
            final=dict(r)
            if not gate['use_llm_prediction_revision']:
                final.update(codes=a['codes'],parse_status='validation_gate_preserved_anchor')
                final['clinical_review']=clinical_review(a['codes'])
            arms['gated_harness'].append(final)
        all_rows[split]=arms;all_labels[split]=labels
        report[split]={'metrics':{a:stats(rows,labels) for a,rows in arms.items()},
           'raw_parse_status':{a:dict(__import__('collections').Counter(r.get('parse_status','v4_raw') for r in rows)) for a,rows in arms.items()},
           'graph_flag_count':sum(len(r['graph_flags']) for r in ordered)}
        (PRIVATE/f'{split}_gated_final.jsonl').write_text(''.join(json.dumps({'case_id':c['case_id'],**r})+'\n' for c,r in zip(cases,arms['gated_harness'])))
    test=all_rows['test']; labels=all_labels['test']
    old=[r['arms']['bounded_harness'] for r in sorted(old.values(),key=lambda r:next(i for i,l in enumerate(labels) if l['case_id']==r['case_id']))]
    report.update(run_id='E01-v5-local-repair-50-r1',fingerprint=fingerprint,gate=gate,
        paired_repaired_minus_v4=paired(old,test['repaired_review'],labels),
        paired_repaired_minus_retrieval=paired(test['retrieval_proposal'],test['repaired_review'],labels),
        paired_gated_minus_anchor=paired(test['anchor_only'],test['gated_harness'],labels),
        limits=['Developmental same-50-case repair, not independent confirmation.',
        'v4 output cap 192; v5 revision cap 384. Actual token counts reported; not exact cost matching.',
        'No complete-order or clinical improvement claim. Clinical clearance remains false.',
        'Training-memory growth is separately evaluated at 4,000 cases; this LLM arm uses the validation-selected statistical anchor.'])
    (HERE/'results/llm_repair_results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'gate':gate,'test_metrics':report['test']['metrics']}),flush=True)

if __name__=='__main__':run()
