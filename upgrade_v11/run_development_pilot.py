"""Development-only tool utility check before any new test evaluation."""
import json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'upgrade_v8'))
from public_client import LOCAL as DATA_LOCAL,digest
from agent import empty_state,metrics,transition
from evidence_tool import EvidenceAgent,PROFILES,LOCAL

def run():
    data=json.loads((DATA_LOCAL/'data.json').read_text());p=data['parts'];agent=EvidenceAgent(p['train'],'deepseek/deepseek-v4.1-flash')
    cases=p['proposal'];base=agent.batch(cases,empty_state());report={'split':'proposal','n':len(cases),'test_evaluated':False,'methods':{'cot':metrics(base,cases)}}
    for name in PROFILES:
        state=empty_state();state['evidence_profile']=name;rows=agent.batch(cases,state)
        report['methods'][name]={**metrics(rows,cases),'versus_cot':transition(base,rows,cases)}
        (LOCAL/(name+'-proposal.json')).write_text(json.dumps(rows)+'\n');(HERE/'results/development_pilot.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({'profile':name,'score':report['methods'][name]}),flush=True)

if __name__=='__main__':run()
