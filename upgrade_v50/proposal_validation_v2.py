"""Corrected proposal feedback, evaluated by replay; not the frozen six-round policy.

Numeric observations in an example are not automatically new dose instructions.
Training trace IDs must still be abstracted before a procedure enters memory.
The gate is syntactic/research-oriented, not clinical validation.
"""
import re
from common import condition
from experiment import validate_card
CONDITIONS={'always','labs_present','labs_missing','prior_orders_present','prior_orders_missing'}
DOSE=re.compile(r'\b\d+(?:\.\d+)?\s*(?:mg|mcg|ml|units|liters)\b',re.I)
def validate(card,cases):
    parts=[s.strip() for s in re.split(r'\s+and\s+|\s*&\s*',str(card.get('condition','')))]
    if not 1<=len(parts)<=2 or not all(p in CONDITIONS for p in parts):return 'unknown_observable_condition'
    reason=validate_card({**card,'condition':parts[0]})
    if reason:return reason
    if card.get('fact_scope') not in ['selected','all_observed']:return 'unsupported_fact_scope'
    if not any(condition(c,' & '.join(parts)) for c in cases):return 'condition_never_applies_in_training'
    if DOSE.search(card['instruction']):return 'unsupported_dose_instruction'
    # Explicit feedback about what to repair, not a false claim of a dose action.
    if re.search(r'\b(?:in|trace)\s+T\d+\b',card['counterexample'],re.I):return 'case_specific_counterexample_requires_abstraction'
    wording=card['instruction'].lower()
    names={o['drug_name'].lower() for c in cases for o in c['catalogue'].values()}
    if any(name and re.search(r'\b(?:prescribe|add|administer|start|choose|prefer|remove)\b[^.;]{0,40}\b'+re.escape(name)+r'\b',wording) for name in names):
        return 'named_drug_action_without_source_validation'
    return None
