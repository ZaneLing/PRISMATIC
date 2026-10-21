"""Offline RxRSIAgent execution with traceable experimental memory and preflight.

Default memory is empty. No learned state is promoted by benchmark score alone.
No function in this module reads a patient's reference target.
"""
from common53 import *
from programs import applies,operate
from clinical_checks import screen_case
def run_case(case,initial_orders,state=()):
    orders=list(initial_orders);trace=[]
    for card in state:
        if not applies(case,card):continue
        after=operate(orders,card)
        if {key(o) for o in after}!={key(o) for o in orders}:
            trace.append(dict(skill_sha256=digest(card),action=card['op'],before=len(orders),after=len(after),clinical_validity='awaiting_independent_review'))
        orders=after
    return dict(orders=orders,skill_trace=trace,preflight=screen_case(case,orders),clinical_appropriateness='not_assessed',research_only=True)
def run_decoded(case,decoded,enable_fallback=False):
    """Distinguish intentional abstention from failure; fallback is opt-in.

    On syntax failure or a nonempty invalid-ID list with no valid IDs, fall back
    to the SAME frozen supervised draft already available to the actor. This is
    a transparent engineering fallback, not learned prescribing or RSI. Valid
    empty decisions and known-ID subsets are preserved. No experimental memory.
    """
    failed=bool(decoded.get('syntax_failure')) or (not decoded['orders'] and decoded.get('invalid_ids',0)>0)
    fallback=failed and enable_fallback
    initial=[case['catalogue'][i] for i in case['frozen_draft']] if fallback else decoded['orders']
    result=run_case(case,initial)
    result.update(fallback_used=fallback,order_source='frozen_supervised_draft' if fallback else 'unresolved_generation' if failed else 'decoded_llm',generation_contract_failed=failed,requires_output_repair=failed and not fallback)
    return result
