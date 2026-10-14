"""Language-generated bounded rule programs from aggregate, not case, evidence."""
import copy,json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'upgrade_v8'))
from public_client import request,json_object,digest
from upgrade_v29.programs import canonical

def propose(payload,seed,round_number,arm,protocol):
    shown=copy.deepcopy(payload)
    if arm=='shuffled':
        rows=shown['single_predicate_evidence'];old=copy.deepcopy(rows);order=np.random.default_rng(seed+1000*round_number).permutation(len(rows))
        for i,j in enumerate(order):
            for key in ['induction_jaccard_gain','affected_visits','affected_patients']:rows[i][key]=old[j][key]
    system='Maintain executable statistical medication-class rules. Use the aggregate error evidence and allowed feature/drug dictionaries to synthesize up to four useful ADD or DELETE edits. ADD may combine one or two observed feature predicates to generalize or narrow a correction; at least one predicate must require presence. Account for overlap and existing rules. Do not merely invent clinical facts. No individual cases, doses or unrestricted code are available. Return JSON only: {"edits":[{"operation":"ADD","rule":{"drug_index":0,"conditions":[{"feature_index":0,"present":true}],"action":"include"}},{"operation":"DELETE","id":"existing_rule_id"}]}. Use actual allowed indices, include or exclude actions, and existing IDs for deletion. Each suggested edit consumes budget even if invalid or unhelpful. Empty edits are allowed.'
    shown['round']=round_number;config=protocol['agent']
    assert all(z['affected_patients']>=20 and z['affected_visits']>=30 for z in shown['single_predicate_evidence'])
    assert all(z['error_patients']>=20 and z['error_visits']>=30 for z in shown['focus_drugs'])
    response=request([{'role':'system','content':system},{'role':'user','content':json.dumps(shown)}],config['model'],config['max_tokens'],
      role='v30_aggregate_program_synthesis',temperature=config['temperature'],cache_salt=['v30-programs',seed,round_number,arm,digest(shown)])
    if response.get('error'):raise RuntimeError('Program proposer transport incomplete; no invented decision.')
    obj=json_object(response['raw']);raw=obj.get('edits');valid=isinstance(raw,list) and len(raw)<=4
    parsed=[];rejections=[];allowed_f={r['feature_index'] for r in shown['allowed_features']};allowed_d={r['drug_index'] for r in shown['focus_drugs']};memory={r['id']:r for r in shown['retained_rules']}
    if valid:
        for index,item in enumerate(raw):
            try:
                if not isinstance(item,dict):raise ValueError('edit_schema')
                if item.get('operation')=='DELETE' and set(item)=={'operation','id'} and item['id'] in memory:op={'operation':'DELETE','rule':memory[item['id']]}
                elif item.get('operation')=='ADD' and set(item)=={'operation','rule'}:op={'operation':'ADD','rule':canonical(item['rule'],allowed_f,allowed_d)}
                else:raise ValueError('edit_schema')
                if any(z==op for z in parsed):raise ValueError('duplicate_edit')
                parsed.append(op)
            except (ValueError,TypeError,KeyError) as error:rejections.append({'index':index,'reason':str(error)})
    return parsed,{'status':'valid_edit_list' if valid else 'invalid_edit_list','model_calls':1,'aggregate_payload':shown,
      'aggregate_prompt_sha256':digest(shown),'model_response':response,'parsed_programs':parsed,'grammar_rejections':rejections,'raw_edit_count':len(raw) if isinstance(raw,list) else None}
