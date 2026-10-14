"""Independently verify reported aggregates and record reproducibility hashes."""
import hashlib,json,platform,sys
from pathlib import Path
import numpy as np
from core import digest,parse_codes

HERE=Path(__file__).resolve().parent
ROOT=Path.home()/'Desktop/MedTreeBench/dataset/restricted'
PRIVATE=ROOT/'prismatic-v5'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def lines(p):return [json.loads(x) for x in p.read_text().splitlines()]
def metrics(rows,labels):
    hits=sum(len(set(r['codes'])&set(l['codes'])) for r,l in zip(rows,labels))
    pred=sum(len(r['codes']) for r in rows);truth=sum(len(l['codes']) for l in labels)
    return {'observed_micro_f1':2*hits/(pred+truth),'empty_output_fraction':sum(not r['codes'] for r in rows)/len(rows)}

def run():
    report=json.loads((HERE/'results/llm_repair_results.json').read_text())
    config=json.loads((HERE/'protocol.json').read_text())
    fingerprint=digest({'config':config,'source':(HERE/'run_llm_repair.py').read_text(),'core':(HERE/'core.py').read_text()})
    assert fingerprint==report['fingerprint']
    verification={};label_sets={}
    for split in ['val','test']:
        rows=lines(PRIVATE/f'{split}_llm_repair.jsonl')
        label_file=PRIVATE/'val_labels.jsonl' if split=='val' else ROOT/'prismatic-v4/llm_labels.jsonl'
        labels=lines(label_file);label_sets[split]={r['subject_id'] for r in labels}
        final=lines(PRIVATE/f'{split}_gated_final.jsonl')
        assert len(rows)==len(labels)==len(final)==50
        assert [r['case_id'] for r in rows]==[r['case_id'] for r in labels]==[r['case_id'] for r in final]
        assert len({r['case_id'] for r in rows})==50
        checks={};max_output={};fallbacks={}
        for arm in rows[0]['arms']:
            records=[r['arms'][arm] for r in rows]
            m=metrics(records,labels)
            for k,v in m.items():assert abs(v-report[split]['metrics'][arm][k])<1e-10
            checks[arm]=m
            max_output[arm]=max(r['tokens']-(x['arms']['retrieval_proposal']['tokens'] if arm=='repaired_review' else 0) for r,x in zip(records,rows))
            fallbacks[arm]=sum('fallback' in r.get('parse_status','') for r in records)
        for k,v in metrics(final,labels).items():assert abs(v-report[split]['metrics']['gated_harness'][k])<1e-10
        assert all(not r['clinical_review']['clinical_clearance'] and not r['clinical_review']['executable_orders'] for r in final)
        verification[split]={'cases':len(rows),'metric_recalculation':'passed','alignment':'passed',
           'max_generated_tokens_per_new_call':max_output,'fallback_counts':fallbacks,
           'all_clinical_clearance_false':True,'labels_sha256':sha(label_file),
           'trace_sha256':sha(PRIVATE/f'{split}_llm_repair.jsonl')}
    assert not label_sets['val'] & label_sets['test']
    from run_rankers import take,top,score
    import pandas as pd
    frame=take(pd.read_parquet(ROOT/'prismatic-v4/cohort.parquet'),'test',4000)
    truth=[set(x) for x in frame.atc4_codes]
    ranking=json.loads((HERE/'results/ranker_memory_results.json').read_text())
    saved=np.load(PRIVATE/'ranker_predictions.npz')
    for key,prediction in saved.items():
        assert score(truth,prediction,ranking['classes'])==ranking['metrics'][key]
    fusion=json.loads((HERE/'results/memory_fusion_results.json').read_text())
    assert score(truth,top(np.load(PRIVATE/'fused_test_scores.npy')),ranking['classes'])==fusion['test']
    # Manuscript integrity: embedded template content unchanged since v4.
    import subprocess
    current=(HERE.parent/'paper/latex/v0.3/prismatic_v03_en.tex').read_text().split('% PRISMATIC MANUSCRIPT START')[0]
    previous=subprocess.check_output(['git','show','57a2fbef:paper/latex/v0.3/prismatic_v03_en.tex'],cwd=HERE.parent).decode().split('% PRISMATIC MANUSCRIPT START')[0]
    assert current==previous
    manifest={'run_id':'E01-v5-verification-r1','python':platform.python_version(),
       'model_revision':json.loads((HERE.parent/'upgrade_v4/protocol.json').read_text())['llm_revision'],
       'checks':verification,'ranker_4000_aggregate_recalculation':'passed',
       'validation_test_patient_disjoint':True,'embedded_template_unchanged':True,
       'code_sha256':{p.name:sha(p) for p in HERE.glob('*.py')},
       'result_sha256':{p.name:sha(p) for p in (HERE/'results').glob('*.json') if p.name!='verification.json'}}
    (HERE/'results/verification.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'verification':'passed','cases_per_split':50,'max_tokens':{s:v['max_generated_tokens_per_new_call'] for s,v in verification.items()}}))

if __name__=='__main__':run()
