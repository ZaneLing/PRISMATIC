"""Optional routing for explicitly documented pre-decision problem categories.

This is an input contract, not an ICD mapper or a diagnosis inference model.
Current MIMIC adapter cases do not supply available_problems. Discharge labels,
prior drug names, unrecorded timestamps and future problems never create scopes.
"""
import math
CATEGORIES=frozenset({'cardiovascular','respiratory','renal','infectious','endocrine_metabolic',
 'gastrointestinal_hepatic','hematologic','neurologic','oncologic','psychiatric','musculoskeletal','immune_inflammatory'})
PROBLEM_SCOPES=frozenset('diagnosis_'+x for x in CATEGORIES)

def diagnostic_scopes(c):
 context=c.get('context',{});decision=context.get('hours_since_admission');found=set()
 if isinstance(decision,bool) or not isinstance(decision,(int,float)) or not math.isfinite(decision):return found
 for problem in context.get('available_problems',[]):
  if not isinstance(problem,dict):continue
  hour=problem.get('recorded_hours_since_admission');category=problem.get('category')
  if problem.get('status') not in {'documented','confirmed'} or category not in CATEGORIES:continue
  if isinstance(hour,bool) or not isinstance(hour,(int,float)) or not math.isfinite(hour) or hour>decision:continue
  found.add('diagnosis_'+category)
 return found

def patient_facts(c):
 facts=c['input'].split(' ; ')
 for scope in sorted(diagnostic_scopes(c)):
  fact='documented_predecision_problem_category '+scope.removeprefix('diagnosis_')
  if fact not in facts:facts.append(fact)
 return facts
