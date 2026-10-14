"""Language-agent edits from aggregate rule evidence, never patient records."""
import json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'upgrade_v8'))
from public_client import request,json_object,digest

def propose(candidates,memory,seed,round_number,arm,protocol):
    if not candidates:return [],{'status':'no_candidates','model_calls':0}
    rows=[{'id':c['id'],'operation':c['operation'],'feature':c['rule']['feature'],'drug':c['rule']['drug'],'action':c['rule']['action'],
       'induction_jaccard_gain':c['induction_jaccard_gain'],'affected_visits':c['affected_visits'],'affected_patients':c['affected_patients']} for c in sorted(candidates,key=lambda x:x['id'])]
    assert all(r['affected_patients']>=20 and r['affected_visits']>=30 for r in rows)
    if arm=='shuffled_evidence_rule_agent':
        rng=np.random.default_rng(seed+1000*round_number);order=rng.permutation(len(rows));original=[dict(r) for r in rows]
        for i,j in enumerate(order):
            for field in ['induction_jaccard_gain','affected_visits','affected_patients']:rows[i][field]=original[j][field]
    system='Maintain an executable statistical prescription-class rule memory. Select up to four candidate edit IDs using the supplied aggregate support and measured training error changes. Consider redundant or conflicting edits and existing rules. Return exactly a JSON object with an edits list of candidate IDs. Do not invent new IDs, patient examples, clinical facts, doses, or executable code. Selecting no edit is allowed.'
    payload={'round':round_number,'retained_rules':[{'id':r['id'],'feature':r['feature'],'drug':r['drug'],'action':r['action']} for r in memory],
       'candidate_edits':rows,'decision_schema':{'edits':['existing_candidate_id']}}
    config=protocol['agent'];response=request([{'role':'system','content':system},{'role':'user','content':json.dumps(payload)}],config['model'],config['max_tokens'],
        role='v27_aggregate_rule_proposer',temperature=config['temperature'],cache_salt=['v27-rules',seed,round_number,arm,digest(payload)])
    if response.get('error'):raise RuntimeError('Incomplete aggregate-rule proposer transport; no fabricated decision.')
    obj=json_object(response['raw']);edits=obj.get('edits');allowed={c['id'] for c in candidates}
    valid=isinstance(edits,list) and len(edits)<=4 and all(isinstance(x,str) for x in edits) and len(set(edits))==len(edits) and all(x in allowed for x in edits)
    receipt={'status':'valid' if valid else 'invalid_edit_response','model_calls':1,'aggregate_prompt_sha256':digest(payload),'selected_ids':edits if valid else [],
        'model_response':response,'aggregate_payload':payload}
    return edits if valid else [],receipt
