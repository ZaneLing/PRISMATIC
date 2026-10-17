"""Post hoc fixed parser replay, without new inference or GT-driven rule choice."""
from collections import Counter
import time
from common import *
from format_recovery import recover
from audit_results import paired

def main():
    cases=load_cases()['test'];results={}
    protocol_path=HERE/'format_replay_protocol.json'
    if protocol_path.exists():
        assert json.loads(protocol_path.read_text())['code_sha256']==sha(HERE/'format_recovery.py')
    else:
        save(protocol_path,{
        'declared_unix':time.time(),'timing':'After original test scores and aggregate invalid-output structure inspection, before replay scoring',
        'rule':'Recover only a complete JSON array of strings with a sole order_ids key and missing closing delimiters/trailing comma; never extract identifiers from prose or complete a partial item',
        'code_sha256':sha(HERE/'format_recovery.py'),'new_inference':False,
        'autonomous_rsi':False,'main_checkpoint_replaced':False})
    for model in ['qwen','llama']:
        rows=json.loads((PRIVATE/f'{model}-test-rxrsi_base.json').read_text())['rows']
        out=[];counts=Counter()
        for c,r in zip(cases,rows):
            assert c['case_id']==r['case_id'];parsed,changed=recover(r['raw'],c)
            counts['invalid_original']+=r['invalid'];counts['recovered']+=changed
            counts['recovered_nonempty']+=changed and bool(parsed['orders'])
            counts['invalid_without_order_key']+=r['invalid'] and '"order_ids"' not in r['raw']
            out.append({**r,**parsed})
        save(PRIVATE/f'{model}-format-replay.json',{'rows':out})
        results[model]={'counts':dict(counts),'baseline':metrics(rows,cases),
            'replayed':metrics(out,cases),'paired':paired(cases,rows,out)}
    save(HERE/'results/format_replay.json',{'complete':True,'models':results,
        'protocol_sha256':sha(HERE/'format_replay_protocol.json'),
        'interpretation':'Post hoc engineering replay; not a prospective validation, learned state, clinical check, or main-table score.'})
    print({k:{'counts':v['counts'],'old_f1':v['baseline']['drug_micro_f1'],'new_f1':v['replayed']['drug_micro_f1']} for k,v in results.items()})

if __name__=='__main__':main()
