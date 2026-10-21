"""Research-only, source-grounded preflight checks; never authorize a prescription.

This fixed label tool is engineering, not learned RSI. Clinical facts are typed,
timestamped and three-valued. It does not infer treatment intent from a missing
prior order, infer eGFR from creatinine, or interpret missing data as normal.
"""
import math,re
SOURCES={
 'metformin':'https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=4e4c4ba9-65c6-4273-8f6b-2423ab521dad',
 'enoxaparin':'https://dailymed.nlm.nih.gov/dailymed/lookup.cfm?setid=d8afb29f-cbed-43bc-809f-09b30fca28f5',
 'eplerenone':'https://dailymed.nlm.nih.gov/dailymed/fda/fdaDrugXsl.cfm?setid=bcd7595f-700f-48ba-bf83-05a995ce0731&type=display'}
def measurement(facts,name,unit,cutoff):
    f=facts.get(name)
    if not isinstance(f,dict) or f.get('unit')!=unit:return None
    try:
        value=float(f['value']);time=float(f['available_at']);measured=float(f['measured_at'])
    except (KeyError,TypeError,ValueError):return None
    if not math.isfinite(value) or value<0 or not math.isfinite(time) or not math.isfinite(measured) or measured>time or time>cutoff or cutoff-measured>360:return None
    return value
def observed_fact(facts,name,cutoff):
    f=facts.get(name)
    if not isinstance(f,dict) or not f.get('provenance'):return None
    try:time=float(f['available_at'])
    except (KeyError,TypeError,ValueError):return None
    if not math.isfinite(time) or time>cutoff or cutoff-time>360:return None
    return f.get('value')
def check(ingredient,facts,cutoff=360):
    rows=[]
    intent=observed_fact(facts,'intent',cutoff)
    def add(rule,status,reason):rows.append(dict(rule=rule,status=status,reason=reason,source=SOURCES[ingredient]))
    if ingredient not in SOURCES:return dict(coverage='not_covered',checks=[],clinical_appropriateness='not_assessed')
    if ingredient=='metformin':
        egfr=measurement(facts,'egfr','mL/min/1.73m2',cutoff)
        if egfr is None:add('renal','unknown','Need a current, directly recorded, correctly unit-typed eGFR.')
        elif egfr<30:add('renal','contraindication','Label contraindication at eGFR below30.')
        elif egfr<45:
            add('renal','initiation_not_recommended' if intent=='initiate' else 'review_required','Initiation and continuation have different label instructions; intent must be established.')
        else:add('renal','no_trigger','This renal threshold is not triggered; other contraindications remain unassessed.')
        # Only accept explicit current assessments, not an unqualified diagnosis mention.
        acidosis=observed_fact(facts,'active_metabolic_acidosis',cutoff)
        add('acidosis','contraindication' if acidosis is True else 'no_trigger' if acidosis is False else 'unknown','Acute/chronic metabolic acidosis is contraindicated; recorded diagnosis alone does not establish active state.')
        contrast=observed_fact(facts,'iodinated_contrast',cutoff)
        add('contrast','review_required' if contrast is True else 'no_trigger' if contrast is False else 'unknown','Contrast handling requires route, timing, renal function and comorbidities; no automatic restart.')
    if ingredient=='enoxaparin':
        crcl=measurement(facts,'crcl','mL/min',cutoff)
        add('renal_dose','unknown' if crcl is None else 'dose_review_required' if crcl<30 else 'no_trigger','Severe renal impairment requires indication-specific dose adjustment; eGFR is not substituted for CrCl. Weight and indication remain necessary.')
    if ingredient=='eplerenone':
        crcl=measurement(facts,'crcl','mL/min',cutoff);potassium=measurement(facts,'potassium','mEq/L',cutoff)
        add('renal','unknown' if crcl is None else 'contraindication' if crcl<=30 else 'no_trigger','General contraindication at CrCl at or below30; hypertension-specific restrictions are additional.')
        if potassium is None:add('potassium','unknown','Need current serum potassium with supported units.')
        elif potassium>5.5:add('potassium','contraindication' if intent=='initiate' else 'review_required','Initiation above5.5 is contraindicated; continuation uses different dose-management instructions.')
        else:add('potassium','no_trigger','Initiation potassium threshold not triggered; this does not establish overall suitability.')
    return dict(coverage='partial_label_checks',checks=rows,clinical_appropriateness='not_assessed',requires_review=True)
def screen_case(c,orders):
    facts={};labmap={'egfr':('egfr','mL/min/1.73m2'),'creatinine clearance':('crcl','mL/min'),'potassium':('potassium','mEq/L')}
    units={'ml/min/1.73m2':'mL/min/1.73m2','ml/min/1.73 m2':'mL/min/1.73m2','ml/min':'mL/min','meq/l':'mEq/L'}
    for l in c['context']['available_labs']:
        pair=labmap.get(l['name'].strip().lower());unit=units.get(l['unit'].strip().lower())
        if pair and unit==pair[1]:facts[pair[0]]=dict(value=l['value'],unit=unit,measured_at=l['draw_offset'],available_at=max(l['draw_offset'],l['revised_offset']))
    result=[]
    for o in orders:
        name=c['drug_names'].get(o['drug_code'],'').lower()
        hits=[x for x in SOURCES if re.search(r'\b'+x+r'\b',name)]
        screening=check(hits[0],facts) if len(hits)==1 else dict(coverage='not_covered',checks=[],clinical_appropriateness='not_assessed')
        result.append(dict(drug_code=o['drug_code'],identity_status='training_name_screen_only',**screening))
    return result
