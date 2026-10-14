"""Transfer frozen seed-42 artifacts to the protocol's second public backbone."""
import json
from pathlib import Path
from public_client import LOCAL,digest
from agent import Agent,empty_state,metrics,transition
HERE=Path(__file__).resolve().parent

def run():
    config=json.loads((HERE/'protocol.json').read_text());data=json.loads((LOCAL/'data.json').read_text())
    versions=json.loads((LOCAL/'seed-42/rxrsi-versions.json').read_text());assert len(versions)==5
    state=versions[-1]['active'];assert digest(state)==versions[-1]['state_sha256']
    agent=Agent(data['parts']['train'],config['transfer_backbone']);out={'model':agent.model,'source_model':config['backbone'],'source_state_sha256':digest(state),'updates_on_transfer_labels':False,'datasets':{}}
    for name,cases in [('rxsafebench',data['parts']['test']),('rxqa',data['transfer'])]:
        base=agent.batch(cases,empty_state());evolved=agent.batch(cases,state)
        out['datasets'][name]={'cot':metrics(base,cases),'rxrsi':metrics(evolved,cases),'change':transition(base,evolved,cases)}
        (LOCAL/f'backbone-transfer-{name}.json').write_text(json.dumps({'cot':base,'rxrsi':evolved})+'\n')
        (HERE/'results/backbone_transfer.json').write_text(json.dumps(out,indent=2)+'\n')
        print(json.dumps({'dataset':name,**out['datasets'][name]}),flush=True)

if __name__=='__main__':run()
