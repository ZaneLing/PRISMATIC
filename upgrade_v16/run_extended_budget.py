"""Declared follow-up after residual truncation at 1,024 tokens; dev only."""
import json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'upgrade_v11'))
from evidence_tool import EvidenceAgent,LOCAL
from public_client import LOCAL as DATA_LOCAL
from agent import empty_state,metrics,transition

def main():
    previous=json.loads((HERE/'results/development_results.json').read_text())
    protocol={'motivation':'16/190 CoT and 13/190 evidence replies remain invalid at cap 1024, low reasoning.',
        'followup_setting':{'cap':2048,'effort':'low'},'cases':'Same entire 190-case proposal split, not test',
        'prior_results_preserved':True,'prompt_unchanged':True,'selection':'Compare invalid count, then accuracy on development only; no test-based choice.'}
    (HERE/'results/extended_budget_protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    parts=json.loads((DATA_LOCAL/'data.json').read_text())['parts'];agent=EvidenceAgent(parts['train'],'google/gemini-3.8-flash')
    agent.request_options={'reasoning_effort':'low'};agent.output_token_limit=2048;outputs={};summary={}
    for name,profile in [('cot',None),('safety_evidence','safety')]:
        state=empty_state();state['evidence_profile']=profile
        rows=agent.batch(parts['proposal'],state);outputs[name]=rows
        (LOCAL/'budget-v16'/f'{name}-2048-proposal.json').write_text(json.dumps(rows)+'\n')
        summary[name]=metrics(rows,parts['proposal']);summary[name]['finish_length']=sum(r.get('finish_reason')=='length' for r in rows)
        print(json.dumps({'method':name,**summary[name]}),flush=True)
    result={'status':'complete','split':'proposal','n':190,'setting':protocol['followup_setting'],'test_evaluated':False,'methods':summary,
        'evidence_vs_cot':transition(outputs['cot'],outputs['safety_evidence'],parts['proposal'])}
    (HERE/'results/extended_development_results.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
