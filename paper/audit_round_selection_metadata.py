"""Audit historical best-round metadata without changing frozen experiment files.

The training loop retained a mutable best dictionary in its rolling export.
Immutable per-round receipts and per-arm best_round values remain correct.
This audit releases corrected historical selections; metrics and final selected
models are never rewritten and source-lock hashes remain valid.
"""
import copy,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent;PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    out={'status':'passed_for_completed_rounds','studies':{},'finding':'Rolling public exports reuse a mutable nested best dictionary; earlier round.best entries can reflect later choices. Immutable round/complete.json receipts and each arm.best_round preserve the historical state. Corrected historical choices are listed here. Proposal metrics, rule states and final selections are unchanged.'}
    for version,glob in [('v27','*-rsi-seed*.json'),('v29','*-seed*.json')]:
        rows=[]
        for path in sorted((ROOT/('upgrade_'+version)/'results').glob(glob)):
            raw=path.read_bytes();z=json.loads(raw)
            if 'lock' not in z:continue
            folder=PRIVATE/('prismatic-'+version)/path.stem;best={};history=[];stale=0
            for row in z['rounds']:
                original=json.loads((folder/f'round{row["round"]}/complete.json').read_text())
                a=copy.deepcopy(row);b=copy.deepcopy(original);a.pop('best');b.pop('best');assert a==b
                for arm,r in row['arms'].items():
                    if arm not in best or r['proposal']['patient_jaccard']>best[arm]['objective']:best[arm]={'round':row['round'],'objective':r['proposal']['patient_jaccard']}
                    assert original['best'][arm]['round']==best[arm]['round'] and r['best_round']==best[arm]['round']
                corrected={k:v['round'] for k,v in best.items()};stale+=row['best']!=original['best']
                history.append({'round':row['round'],'correct_best_so_far':corrected,'immutable_receipt_sha256':sha(folder/f'round{row["round"]}/complete.json')})
            if z['status']=='selection_frozen':assert all(z['selections'][k]['round']==v['round'] for k,v in best.items())
            rows.append({'run':path.stem,'source_report_sha256':hashlib.sha256(raw).hexdigest(),'completed_rounds':len(history),'stale_nested_best_entries':stale,'corrected_history':history,'final_selection_verified':z['status']=='selection_frozen'})
        out['studies'][version]=rows
    (ROOT/'paper/round_selection_metadata_audit.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'runs':sum(map(len,out['studies'].values())),'stale_entries':sum(r['stale_nested_best_entries'] for s in out['studies'].values() for r in s),'actual_metric_or_final_selection_changes':0}),flush=True)
if __name__=='__main__':main()
