"""Second-backbone development probe; no test evaluation or artifact fitting."""
import json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'upgrade_v8'))
from public_client import LOCAL as DATA_LOCAL
from agent import empty_state,metrics,transition
from evidence_tool import EvidenceAgent,LOCAL

def run():
    data=json.loads((DATA_LOCAL/'data.json').read_text());p=data['parts'];model='google/gemini-3.8-flash';agent=EvidenceAgent(p['train'],model)
    cases=p['proposal'];base=agent.batch(cases,empty_state());out={'model':model,'split':'proposal','n':len(cases),'test_evaluated':False,'methods':{'cot':metrics(base,cases)}}
    (LOCAL/'gemini-cot-proposal.json').write_text(json.dumps(base)+'\n');(HERE/'results/backbone_development_pilot.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'method':'cot','metrics':out['methods']['cot']}),flush=True)
    state=empty_state();state['evidence_profile']='safety';rows=agent.batch(cases,state)
    out['methods']['safety_evidence']={**metrics(rows,cases),'versus_cot':transition(base,rows,cases)}
    (LOCAL/'gemini-safety-proposal.json').write_text(json.dumps(rows)+'\n');(HERE/'results/backbone_development_pilot.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'method':'safety_evidence','metrics':out['methods']['safety_evidence']}),flush=True)

if __name__=='__main__':run()
