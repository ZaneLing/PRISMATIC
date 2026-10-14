---
description: Select the option whose label explicitly lists the stated diagnosis as
  an indication and whose cautions are not triggered by documented patient facts.
name: label_indication_and_caution_parsing
provenance:
  action: ADD
  epoch: 0
  fixes: 3
  probe_score: 3
  regressions: 0
  triggering_sample_ids:
  - e0164f22b7e7dbc0
  - c67eba231012cd18
  - fa21564227b1e8e9
  - 9a26c6e7c83b8697
  - 08d195a2671118d7
  - 52e2bc59eca07a3a
  - 428357a20d8cdb92
  - 8df6455d01ff63b5
  - af446476f000fca0
  - c0ed6b2c5b81d02b
  update_cycle: 1
tags:
- contraindication
- interaction
- medication option
- select
- best treats
- patient facts
- medication safety
version: 1
---

## When to Use This Skill
Use this skill for every single-choice medication selection task where the instruction asks you to pick the one medication that best treats the stated problem while respecting patient facts and safety. The primary trigger is the presence of a stated diagnosis or problem in the dialogue (e.g. "my initial diagnosis is X") plus a set of candidate medication options, each accompanied by a drug-label excerpt. If the task text contains words like "select", "best treats", "contraindication", "interaction", or "medication option", this skill applies.

## Core Decision Rule
For each candidate option, evaluate in this order:
1. **Indication match**: Does the supplied label excerpt explicitly list the stated diagnosis or problem as an indication? An option with no matching indication is eliminated first, regardless of safety.
2. **Documented contraindication**: Does the label excerpt list a contraindication that matches a patient fact explicitly stated in the dialogue (allergy, organ disease, pregnancy, specific condition)? If yes, eliminate.
3. **Documented caution/warning triggered by patient facts**: Does the label excerpt contain a warning that is directly triggered by a documented patient fact (e.g. "avoid in renal impairment" + documented kidney disease)? If yes, this option is unsafe; eliminate unless no safer option exists.
4. **Interaction check**: Does the label excerpt document an interaction with a medication the patient is currently taking? If yes, eliminate.
5. Among surviving options, prefer the one whose label excerpt most explicitly and specifically names the stated diagnosis as its indication.

## Critical Rules
- A missing label excerpt does NOT establish safety. If an option has no usable excerpt, it cannot be the best-supported choice over an option with a clear matching indication and no triggered cautions.
- Do not infer undocumented contraindications. Only eliminate for safety when the label excerpt itself documents the contraindication or warning and a patient fact in the dialogue directly matches it.
- When two options both list the stated diagnosis, prefer the one whose excerpt names it more specifically (e.g. names the exact condition rather than a broader category).
- When the stated diagnosis is a symptom or syndrome, match against the label's listed indications for that symptom, not a related but distinct condition.
- Do not select an option solely because it is a known treatment for the condition from external knowledge; the selection must be supported by the supplied label excerpt.

## Example Trajectory

### Wrong
Task: "Select the single medication option that best treats the stated problem while respecting the patient facts and medication safety." Patient has suspected pulmonary embolism; options include warfarin and Pepcid.
- Think: "Pulmonary embolism needs anticoagulation. Warfarin is an anticoagulant. The patient has trouble adhering to a strict schedule, but that's not a documented contraindication. I'll pick warfarin."
- Act: `{"evidence": "Stated problem is suspected pulmonary embolism requiring anticoagulation; warfarin is an anticoagulant...", "final": "A"}`
- Obs: Incorrect — the correct answer accounts for the fact that the patient's documented adherence difficulty is a patient fact that makes warfarin a poor fit, and the label excerpt for the chosen option must be checked against it.

### Correct
Task: "Select the single medication option that best treats the stated problem while respecting the patient facts and medication safety." Patient has suspected pulmonary embolism and documented difficulty adhering to a strict daily medication schedule; options include warfarin, Jantoven, and Pepcid.
- Think: "Pulmonary embolism requires anticoagulation. Warfarin and Jantoven are both anticoagulants, but both require a strict daily schedule which this patient cannot follow — that is a documented patient fact. Pepcid's label warns not to use with chest pain or shortness of breath without seeing a doctor, and it is not an anticoagulant. I must check whether any option's label excerpt supports use despite the adherence limitation."
- Act: `{"evidence": "Suspected pulmonary embolism requires anticoagulation; warfarin/Jantoven are anticoagulants but the patient has documented adherence difficulty with a strict warfarin schedule. Pepcid is not indicated for pulmonary embolism and its label warns not to use with chest pain/shortness of breath without seeing a doctor. No option is clearly best supported for this patient's adherence limitation.", "final": "A"}`
- Obs: The evidence explicitly weighs the documented patient fact (adherence difficulty) against each option's label before selecting.

## Failure Tags Addressed
- wrong_contraindication_selection
- wrong_interaction_selection
