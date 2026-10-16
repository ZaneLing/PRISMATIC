"""Traceable decision constraints, not a clinical-entailment classifier."""

CONTRACT = '''
Before deciding, preserve the requested decision and its time point. An intervention during active disease is not interchangeable with prophylaxis before exposure. A combination's indication is not the union of its components' indications. Do not promote a missing label section into evidence for safety, or a correlated fact (such as transfusions) into an unobserved condition (such as dialysis). Do not exclude an ingredient because one unrelated formulation was retrieved.
Add a compact decision_contract: {"target_quote":"exact question span", "time_quote":"exact timing span or empty"}. Add decisive_claims for at most four exclusions or preferences: [{"option":"letter", "claim":"brief", "patient_quote":"exact ORIGINAL PATIENT span supporting the precondition, or empty if unknown", "evidence_id":"E-number or empty", "source_quote":"exact source span or empty", "scope":"combination or component or general", "missing_conditions":["unobserved required qualifiers"]}]. Use the ORIGINAL question without options for patient evidence. Quotes prove provenance only; state unsupported clinical inferences as uncertain. A missing source does not automatically disqualify an otherwise appropriate treatment. Do not confuse the dataset reference with a clinical authority.
'''


def contract_checks(assessment, case, evidence):
    sources = {x['evidence_id']: x for x in evidence['excerpts']}
    contract = assessment.get('decision_contract', {})
    contract = contract if isinstance(contract, dict) else {}
    out = {'scope': 'Provenance and declared product scope only; semantic entailment and clinical correctness are NOT verified.', 'quotes': {}}
    for name in ('target_quote', 'time_quote'):
        quote = contract.get(name)
        out['quotes'][name] = 'input_bound' if isinstance(quote, str) and quote and quote in case['dialogue'] else 'unknown_or_unbound'
    out['claims'] = []
    claims = assessment.get('decisive_claims', [])
    for claim in claims[:4] if isinstance(claims, list) else []:
        if not isinstance(claim, dict):
            continue
        patient, quote = claim.get('patient_quote'), claim.get('source_quote')
        source = sources.get(claim.get('evidence_id'), {})
        out['claims'].append({'option': claim.get('option'),
            'patient_bound': isinstance(patient, str) and len(patient) >= 5 and patient in case['dialogue'],
            'source_bound': isinstance(quote, str) and len(quote) >= 8 and quote in source.get('quote', ''),
            'combination_scope_mismatch': claim.get('scope') == 'combination' and source.get('product_scope') != 'combination',
            'unresolved_conditions': claim.get('missing_conditions', [])})
    return out
