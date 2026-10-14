"""Fixed local model, four matched-case arms, private prompts and predictions.

This bounded prototype has retrieval/state/verification/revision, but no validated
clinical DDI/renal knowledge. Never label its structural checks clinical safety.
"""
from __future__ import annotations
import hashlib,json,time,platform
from pathlib import Path
import numpy as np
from mlx_lm import load,generate
from mlx_lm.sample_utils import make_sampler

HERE=Path(__file__).resolve().parent
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v4'
MODEL=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/models/qwen3-4b-instruct-2507-4bit'
ARMS=['direct','ordinary_repeat','case_retrieval','bounded_harness']

def extract(raw,allowed):
    raw=raw.strip()
    if raw.startswith('```'):
        raw=raw.split('\n',1)[1].rsplit('```',1)[0].strip()
    try:
        obj=json.loads(raw); codes=obj['codes']
        valid=isinstance(codes,list) and len(codes)<=5 and all(isinstance(c,str) and c in allowed for c in codes) and len(set(codes))==len(codes)
        return codes if valid else [],bool(valid)
    except (ValueError,KeyError,TypeError):return [],False

def stats(rows,labels):
    truth=[set(x['codes']) for x in labels]
    hits=sum(len(set(r['codes'])&g) for r,g in zip(rows,truth))
    n_pred=sum(len(r['codes']) for r in rows); n_true=sum(map(len,truth))
    return {'cases':len(rows),'valid_json_fraction':sum(r['valid'] for r in rows)/len(rows),
      'observed_micro_f1':2*hits/(n_pred+n_true) if n_pred+n_true else 0,
      'observed_precision':hits/n_pred if n_pred else 0,'observed_recall':hits/n_true if n_true else 0,
      'mean_predicted_classes':n_pred/len(rows),'empty_output_fraction':sum(not r['codes'] for r in rows)/len(rows),
      'generated_tokens':sum(r['tokens'] for r in rows),'input_tokens':sum(r['input_tokens'] for r in rows),
      'arm_seconds':round(sum(r['seconds'] for r in rows),2)}

def paired(a,b,labels):
    ids=sorted(set(r['subject_id'] for r in labels)); groups=[]
    for sid in ids:
        ix=[i for i,r in enumerate(labels) if r['subject_id']==sid]
        groups.append([sum(len(set(rows[i]['codes'])&set(labels[i]['codes'])) for i in ix) for rows in [a,b]]+
                      [sum(len(rows[i]['codes']) for i in ix) for rows in [a,b]]+[sum(len(labels[i]['codes']) for i in ix)])
    arr=np.array(groups);rng=np.random.default_rng(20261014);ds=[]
    for _ in range(2000):
        x=arr[rng.integers(0,len(arr),len(arr))].sum(0)
        ds.append(2*x[1]/max(1,x[3]+x[4])-2*x[0]/max(1,x[2]+x[4]))
    return {'delta':stats(b,labels)['observed_micro_f1']-stats(a,labels)['observed_micro_f1'],
            'patient_bootstrap_95pct':np.quantile(ds,[.025,.975]).tolist(),'patients':len(ids),'draws':2000}

def run():
    config=json.loads((HERE/'protocol.json').read_text())
    cases=[json.loads(s) for s in (PRIVATE/'llm_inputs.jsonl').read_text().splitlines()]
    labels=[json.loads(s) for s in (PRIVATE/'llm_labels.jsonl').read_text().splitlines()]
    protocol_hash=hashlib.sha256((HERE/'protocol.json').read_bytes()).hexdigest()
    input_hash=hashlib.sha256((PRIVATE/'llm_inputs.jsonl').read_bytes()).hexdigest()
    label_hash=hashlib.sha256((PRIVATE/'llm_labels.jsonl').read_bytes()).hexdigest()
    completed_report=HERE/'results/local_harness_results.json'
    if completed_report.exists():
        previous=json.loads(completed_report.read_text())
        if previous['input_file_sha256']!=input_hash or previous['label_file_sha256']!=label_hash:
            raise ValueError('Input/label content changed; start a separately identified run')
    model,tokenizer=load(str(MODEL));sampler=make_sampler(temp=0.0)
    system=('Offline historical-order prediction research, not patient care. Use only the supplied admission snapshot. '
       'Availability of triage/home-medication entry is uncertain. Select up to five ATC4 classes from the allowed list; '
       'classes are not interchangeable ingredients. Return only a JSON object {"codes":["CODE"]}. '
       'Do not output explanations, dose advice, or invent codes. Empty output is allowed.')
    output=PRIVATE/'llm_method_predictions.jsonl'
    done={}
    if output.exists():
        for line in output.read_text().splitlines():
            row=json.loads(line)
            if row['protocol_sha256']!=protocol_hash:raise ValueError('Existing run protocol mismatch')
            case=next(c for c in cases if c['case_id']==row['case_id'])
            digest=hashlib.sha256(json.dumps(case,sort_keys=True).encode()).hexdigest()
            if row.get('case_input_sha256',digest)!=digest:raise ValueError('Case input changed')
            if 'case_input_sha256' not in row and not completed_report.exists():
                raise ValueError('Legacy partial log has no input hash; validate it before resuming')
            done[row['case_id']]=row
    def infer(messages):
        prompt=tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
        t=time.monotonic()
        raw=generate(model,tokenizer,prompt=prompt,max_tokens=192,sampler=sampler,verbose=False)
        return {'raw':raw,'tokens':len(tokenizer.encode(raw)),'input_tokens':len(tokenizer.encode(prompt)),
                'seconds':time.monotonic()-t}
    for case in cases:
        if case['case_id'] in done:continue
        allowed={r['atc4'] for r in case['candidates']}
        evidence={'E1_chiefcomplaint':case['chiefcomplaint'],'E2_acuity':case['acuity'],
                  'E3_home_meds':case['home_meds'],'availability':case['availability']}
        user=json.dumps({'patient_evidence':evidence,'candidate_class_examples':case['candidates']})
        base=[{'role':'system','content':system},{'role':'user','content':user}]
        direct=infer(base)
        repeated=infer(base+[{'role':'assistant','content':direct['raw']},
            {'role':'user','content':'Review your previous selection once and return the final codes JSON.'}])
        retrieval_context=json.dumps(case['retrieved_cases'])
        rag=base+[{'role':'user','content':'Training-case retrieval (historical behavior, not clinical evidence for this patient): '+retrieval_context}]
        retrieval=infer(rag)
        codes,valid=extract(retrieval['raw'],allowed)
        checks={'format_valid':valid,'candidate_count':len(codes),'clinical_knowledge':'DDI/renal/allergy validation unavailable',
                'missing_patient_evidence':['allergies','body weight','verified current renal function'],
                'instruction':'Independently reconsider each selection from this patient. Do not copy retrieved drugs without patient support. '
                   'Do not infer fluid purpose or dose from drug names. Remove unsupported selections, allow abstention. Return final codes JSON.'}
        final=infer(rag+[{'role':'assistant','content':retrieval['raw']},{'role':'user','content':json.dumps(checks)}])
        rows={}
        for name,r,prior in [('direct',direct,None),('ordinary_repeat',repeated,direct),
                              ('case_retrieval',retrieval,None),('bounded_harness',final,retrieval)]:
            pred,ok=extract(r['raw'],allowed)
            rows[name]={**r,'codes':pred,'valid':ok,'calls':1 if prior is None else 2}
            for field in ['tokens','input_tokens','seconds']:
                rows[name][field]=r[field]+(prior[field] if prior else 0)
        record={'case_id':case['case_id'],'protocol_sha256':protocol_hash,'arms':rows,
                'case_input_sha256':hashlib.sha256(json.dumps(case,sort_keys=True).encode()).hexdigest(),
                'state_transitions':['snapshot','retrieve','propose','structural_check','bounded_revision','final_parse'],
                'checks':checks}
        with output.open('a') as f:f.write(json.dumps(record)+'\n')
        done[case['case_id']]=record
        print(json.dumps({'completed_cases':len(done),'total':len(cases)}),flush=True)
    ordered=[done[c['case_id']] for c in cases]
    arms={arm:[r['arms'][arm] for r in ordered] for arm in ARMS}
    report={'run_id':'E01-v4-local-harness-50-r1','protocol_sha256':protocol_hash,
        'model':config['llm_base'],'revision':config['llm_revision'],'hardware':platform.machine(),
        'input_file_sha256':hashlib.sha256((PRIVATE/'llm_inputs.jsonl').read_bytes()).hexdigest(),
        'label_file_sha256':hashlib.sha256((PRIVATE/'llm_labels.jsonl').read_bytes()).hexdigest(),
        'case_count':len(cases),'metrics':{arm:stats(rows,labels) for arm,rows in arms.items()},
        'paired_harness_minus_repeat':paired(arms['ordinary_repeat'],arms['bounded_harness'],labels),
        'paired_harness_minus_retrieval':paired(arms['case_retrieval'],arms['bounded_harness'],labels),
        'limits':['Shared direct first response for repeat and shared retrieval first response for harness; per-arm costs include both calls.',
          'Same per-call output cap and call count for repeat/harness; retrieval adds input tokens, so not exact token-cost matching.',
          'Bounded engineering prototype, not clinically complete harness: no validated ingredient-level DDI/renal knowledge.',
          'Developmental 50-case pilot; historical observed overlap only; no clinical ratings.']}
    (HERE/'results/local_harness_results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':run()
