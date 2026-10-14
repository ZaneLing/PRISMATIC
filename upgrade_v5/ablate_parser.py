"""Replay identical cached generations through old/new parsers; no new LLM calls."""
import ast,json
from pathlib import Path
from core import parse_codes
from verify_results import ROOT,PRIVATE,HERE,lines,metrics

def run():
    tree=ast.parse((HERE.parent/'upgrade_v4/run_local_harness.py').read_text())
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='extract')
    scope={'json':json};exec(compile(ast.Module(body=[node],type_ignores=[]),'<v4-parser>','exec'),scope)
    strict=scope['extract']
    inputs=lines(ROOT/'prismatic-v4/llm_inputs.jsonl');labels=lines(ROOT/'prismatic-v4/llm_labels.jsonl')
    old=lines(ROOT/'prismatic-v4/llm_method_predictions.jsonl');new=lines(PRIVATE/'test_llm_repair.jsonl')
    allowed={x['atc4'] for x in inputs[0]['candidates']}
    arms={}
    def evaluate(rows):
        result=metrics(rows,labels)
        hits=sum(len(set(r['codes'])&set(l['codes'])) for r,l in zip(rows,labels))
        n=sum(len(r['codes']) for r in rows);truth=sum(len(l['codes']) for l in labels)
        return {**result,'observed_precision':hits/n if n else 0,'observed_recall':hits/truth,
                'mean_predicted_classes':n/len(rows)}
    for name,rows in [('v4_retrieval',[r['arms']['case_retrieval'] for r in old]),
                      ('v4_bounded',[r['arms']['bounded_harness'] for r in old]),
                      ('v5_repaired_generation',[r['arms']['repaired_review'] for r in new])]:
        arms[name+'_strict']=evaluate([{'codes':strict(r['raw'],allowed)[0]} for r in rows])
        arms[name+'_salvage']=evaluate([parse_codes(r['raw'],allowed) for r in rows])
    report={'run_id':'E01-v5-parser-replay-r1','cases':50,'new_model_calls':0,'metrics':arms,
            'scope':'Same cached raw generations, different parsing only; not an independently selected policy.'}
    (HERE/'results/parser_ablation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))

if __name__=='__main__':run()
