"""Observable multi-label context scopes, executable exceptions, and bounded tools.

These are measurement/context strata, NOT inferred diagnosis classes. No future
ICD labels or target names are consulted. A diagnosis adapter can be supplied
only with a recorded_at value <= decision time; this cohort supplies none.
"""
import copy,re
from common import digest
from disease_memory import diagnostic_scopes,patient_facts,PROBLEM_SCOPES
GROUPS={
 'renal_labs':{'creatinine','urea nitrogen'},
 'glucose_electrolyte_labs':{'glucose','sodium','potassium','chloride','bicarbonate','calcium, total','magnesium','phosphate'},
 'hematology_labs':{'white blood cells','hemoglobin','platelet count','hematocrit','inr(pt)','pt','ptt'},
 'liver_labs':{'bilirubin, total','alanine aminotransferase (alt)','asparate aminotransferase (ast)','alkaline phosphatase'},
 'blood_gas_labs':{'ph','po2','pco2','lactate','base excess'}}
SCOPES={'all','labs_present','labs_missing','prior_present','prior_missing','no_observations','no_neighbors','multiple_facts'}|set(GROUPS)
OPERATORS={'candidate_wide48','candidate_retrieval48','evidence_route','evidence_diverse','fact_all','temporal_reconcile','ranked_draft'}
REPAIRABLE={'candidate_omission':{'candidate_wide48','candidate_retrieval48'}, 'selection_omission':{'ranked_draft','evidence_route','evidence_diverse','temporal_reconcile','fact_all'}, 'extra_drugs':{'ranked_draft','evidence_route','evidence_diverse','temporal_reconcile'}, 'joint_field_mismatch':set()}
PROCEDURES={
 'ranked_draft':'Consult the frozen training-derived ranked draft as a predictive tool, then verify against observed patient context. Its ranking does not establish an indication; you may add or remove catalogue orders.',
 'candidate_wide48':'Review the expanded candidate set; inclusion is not proof of indication. Select only likely new or changed orders.',
 'candidate_retrieval48':'Review candidates recalled from similar training contexts, including outside the old vocabulary. Case similarity is not an indication and is not a reason to copy all retrieved drugs.',
 'evidence_route':'Use source-route compatibility to assess evidence attribution; unknown or partial compatibility does not establish a contraindication.',
 'evidence_diverse':'Consider drug-specific retrieved evidence separately. A label quotation for one drug cannot support another drug.',
 'fact_all':'Check all available observed facts before deciding; the absence of a value is not a normal result.',
 'temporal_reconcile':'Distinguish prior therapy from a NEW or CHANGED order in the target window. Compare the candidate joint fields with prior orders. A prior order alone is neither evidence of a new order nor a prohibition on renewal or change.'}
def scopes(c):
 ctx=c['context'];labs=ctx['available_labs'];prior=ctx['recorded_prior_orders'];out={'all','labs_present' if labs else 'labs_missing','prior_present' if prior else 'prior_missing'}
 names={x['name'].lower() for x in labs}
 out|={g for g,ns in GROUPS.items() if names&ns}
 out|=diagnostic_scopes(c)
 if not labs and not prior:out.add('no_observations')
 if len(patient_facts(c))>3:out.add('multiple_facts')
 if not c.get('retrieval_meta',{}).get('neighbor_drug_votes'):out.add('no_neighbors')
 return out
def applies(c,card):
 s=scopes(c);return card['when'] in s and not any(x in s for x in card.get('unless',[]))
def active_cards(c,state):return [x for x in state.get('cards',[]) if applies(c,x)]
def config(c,state):
 conf={'candidate':'base24','route_filter':False,'diverse':False,'fact_scope':'selected','ranked_draft':False}
 for x in active_cards(c,state):
  op=x['operator']
  if op.startswith('candidate_'):conf['candidate']=op.replace('candidate_','')
  elif op=='evidence_route':conf['route_filter']=True
  elif op=='evidence_diverse':conf['diverse']=True
  elif op=='fact_all':conf['fact_scope']='all_observed'
  elif op=='ranked_draft':conf['ranked_draft']=True
 return conf
def instructions(c,state):
 return '\n'.join('SCOPE: '+x['when']+'; EXECUTABLE EXCEPTIONS: '+','.join(x['unless'])+'; PROCEDURE: '+PROCEDURES[x['operator']]+' '+x['instruction'] for x in active_cards(c,state))
def prepare_case(c,state):
 c={**c,'input':' ; '.join(patient_facts(c))};conf=config(c,state);out={**c,'catalogue':c['catalogues'][conf['candidate']]}
 if conf['ranked_draft']:
  ranks=c['retrieval_meta']['classifier_rank'][:8];by_name={o['drug_name']:cid for cid,o in out['catalogue'].items()}
  out['ranked_draft']={'ids':[by_name[n] for n in ranks if n in by_name], 'source':'frozen 40000-admission supervised candidate scorer; not an indication check'}
 return out
def validate(card,cases):
 if not isinstance(card,dict):return 'not_object'
 for k in ['root_cause','cluster','operator','when','instruction','counterexample']:
  if not isinstance(card.get(k),str) or not card[k].strip():return 'missing_'+k
 if card['operator'] not in OPERATORS:return 'unknown_operator'
 if card['cluster'] not in REPAIRABLE or card['operator'] not in REPAIRABLE[card['cluster']]:return 'operator_cannot_repair_declared_root'
 if re.search(r'only (?:include|select).*differ',card['instruction'],re.I):return 'incorrect_temporal_rule_excludes_recorded_renewals'
 allowed=SCOPES|{s for c in cases for s in scopes(c)}
 if card['when'] not in allowed:return 'unknown_scope'
 if not isinstance(card.get('unless'),list) or any(x not in allowed for x in card['unless']):return 'invalid_executable_exceptions'
 if len(card['instruction'].split())>90:return 'instruction_too_long'
 if re.search(r'\b(?:gt|gold|ground.truth|reference|target drug|correct answer)\b',card['instruction'],re.I):return 'unobservable_instruction'
 if re.search(r'\b\d+(?:\.\d+)?\s*(?:mg|mcg|ml|units|liters)\b',card['instruction'],re.I):return 'unsupported_dose_instruction'
 if re.search(r'\b(?:in|trace)\s+T\d+\b',card['counterexample'],re.I):return 'case_specific_counterexample_requires_abstraction'
 if not any(applies(c,card) for c in cases):return 'condition_never_applies'
 names={o['drug_name'] for c in cases for cat in c['catalogues'].values() for o in cat.values()}
 if any(n and re.search(r'\b(?:prescribe|add|administer|start|choose|prefer|remove)\b[^.;]{0,40}\b'+re.escape(n)+r'\b',card['instruction'],re.I) for n in names):return 'unsupported_named_drug_action'
 return None

def effect_probe(cases,before,state,candidate):
 """Require observable execution changes before using validation labels."""
 from evidence_tool import retrieve
 changes=[];applicable=0
 for c,row in zip(cases,before):
  if not applies(c,candidate['cards'][-1]):continue
  applicable+=1;a=prepare_case(c,state);b=prepare_case(c,candidate);ca=config(c,state);cb=config(c,candidate);effects=[]
  if digest(a['catalogue'])!=digest(b['catalogue']):effects.append('candidate_set')
  if b.get('ranked_draft') and a.get('ranked_draft')!=b.get('ranked_draft'):effects.append('frozen_predictive_draft_tool')
  if ca['fact_scope']!=cb['fact_scope'] and len(patient_facts(c))>len(set(row['checks'].get('verified_input_quotes',[]))):effects.append('checked_facts')
  if (ca['route_filter'],ca['diverse'])!=(cb['route_filter'],cb['diverse']):
   if retrieve(a,row['plan'],ca)['spans']!=retrieve(b,row['plan'],cb)['spans']:effects.append('retrieved_evidence')
  if candidate['cards'][-1]['operator']=='temporal_reconcile' and c['context']['recorded_prior_orders']:effects.append('explicit_temporal_review_prompt')
  if effects:changes.append({'case_id':c['case_id'],'effects':effects})
 return {'applicable_cases':applicable,'effective_cases':len(changes),'changes':changes,'requires_output_effect_after_inference':True}

def normalize_card(obj):
 """Unwrap exactly one provider-returned proposal without changing its contents."""
 if isinstance(obj,dict) and 'operator' not in obj and isinstance(obj.get('proposals'),list) and len(obj['proposals'])==1 and isinstance(obj['proposals'][0],dict):
  return obj['proposals'][0]
 return obj
