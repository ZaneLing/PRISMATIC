"""Second-backbone budget repair chosen only on development, preserving defaults."""
import json,sys,urllib.request
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'upgrade_v11'))
from evidence_tool import EvidenceAgent,LOCAL
from public_client import LOCAL as DATA_LOCAL
from agent import empty_state,metrics,transition

def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')

def main():
    (HERE/'results').mkdir(exist_ok=True);model='google/gemini-3.8-flash'
    with urllib.request.urlopen('https://openrouter.ai/api/v1/models',timeout=30) as r:models=json.load(r)['data']
    meta=next(m for m in models if m['id']==model)
    assert meta['reasoning']['mandatory'] and 'low' in meta['reasoning']['supported_efforts']
    config={'model':model,'reasoning_metadata':meta['reasoning'],'configurations':[{'cap':512,'effort':'low'},{'cap':1024,'effort':'low'}],
        'selection_cases':'First 30 proposal cases, same for both settings','selection_rule':'Minimize invalid count, then maximize accuracy, then prefer lower cap.',
        'remaining_development':'Run all 190 proposal cases for CoT and safety evidence under the selected setting.',
        'test_used':False,'prompt_unchanged':True,'baseline':'v11 original 512 cap/default reasoning is retained, not overwritten.',
        'source':'https://openrouter.ai/docs/guides/best-practices/reasoning-tokens'}
    save(HERE/'protocol.json',config)
    parts=json.loads((DATA_LOCAL/'data.json').read_text())['parts'];agent=EvidenceAgent(parts['train'],model);agent.request_options={'reasoning_effort':'low'}
    candidates=[];folder=LOCAL/'budget-v16';folder.mkdir(exist_ok=True)
    for setting in config['configurations']:
        agent.output_token_limit=setting['cap'];rows=agent.batch(parts['proposal'][:30],empty_state());m=metrics(rows,parts['proposal'][:30])
        save(folder/f"pilot-{setting['cap']}.json",rows);candidates.append({'setting':setting,'metrics':m,
            'finish_reasons':{k:sum(r.get('finish_reason')==k for r in rows) for k in sorted({str(r.get('finish_reason')) for r in rows})},
            'reasoning_tokens':sum(r.get('reasoning_tokens') or 0 for r in rows)})
        save(HERE/'results/budget_candidates.json',candidates);print(json.dumps(candidates[-1]),flush=True)
    chosen=min(candidates,key=lambda c:(c['metrics']['invalid'],-c['metrics']['accuracy'],c['setting']['cap']))['setting']
    save(HERE/'results/frozen_budget.json',{'chosen':chosen,'test_used':False})
    agent.output_token_limit=chosen['cap'];base=agent.batch(parts['proposal'],empty_state());save(folder/'cot-proposal.json',base)
    state=empty_state();state['evidence_profile']='safety';review=agent.batch(parts['proposal'],state);save(folder/'safety-proposal.json',review)
    result={'status':'complete','split':'proposal','n':190,'selected_setting':chosen,'test_evaluated':False,
        'methods':{'cot':metrics(base,parts['proposal']),'safety_evidence':metrics(review,parts['proposal'])},
        'evidence_vs_cot':transition(base,review,parts['proposal']),
        'default_cap_v11':json.loads((HERE.parent/'upgrade_v11/results/backbone_development_pilot.json').read_text())}
    save(HERE/'results/development_results.json',result);print(json.dumps(result),flush=True)

if __name__=='__main__':main()
