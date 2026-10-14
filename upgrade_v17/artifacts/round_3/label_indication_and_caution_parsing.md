---
description: Select the indicated option; reject options whose explicit do-not-use/absolute-warning
  text is triggered by documented patient facts.
name: label_indication_and_caution_parsing
provenance:
  action: MODIFY
  epoch: 0
  fixes: 7
  parent_version: 1
  probe_score: 5
  regressions: 2
  triggering_sample_ids:
  - d572e969a54fb023
  - f30c6651e4647cd2
  - 21f3b3fa658f58a8
  - 994f067b99e29d69
  - d6a58ed53ae9f971
  - 98ad942f2201907f
  - a786f6a850496d15
  - d19929a7944e60c3
  - 2dbf4c414f9b4ef7
  - 05d578428599fb44
  update_cycle: 2
tags:
- contraindication
- safety
- label
- warning
- caution
- do not use
version: 2
---

## Purpose
Choose the single medication whose supplied label lists the stated diagnosis/problem as an indication AND whose explicit caution, warning, or do-not-use text is not triggered by a fact the patient has actually stated. An option with a matching indication but a label text whose literal trigger condition is met by a documented patient fact is the WRONG choice, even if no better option exists.

## When to Use This Skill
Use whenever the task asks you to select a medication that "best treats the stated problem while respecting the patient facts and medication safety" and label excerpts are provided. Primary trigger (observable from the instruction before acting): the task supplies patient facts (symptoms, history, current medications) AND at least one option excerpt contains a warning/caution or "do not use" clause. If no option excerpt contains a caution clause, this skill does not fire.

## Procedure
1. For every option, extract TWO things from its excerpt:
   a. INDICATION: does the excerpt list the stated diagnosis/problem by name (or an unmistakable synonym, e.g. brand vs generic of the same drug, or a directly matching organ/system indication)?
   b. CAUTION TRIGGER: does the excerpt contain a warning phrased as an absolute or near-absolute stop ("do not use if...", "contraindicated in...", "should not be administered to patients with...", "avoid use in...")? If yes, state the LITERAL trigger condition (e.g. "trouble or pain swallowing food", "vomiting with blood", "mononucleosis", "malabsorption syndrome", "dialysis-dependent", "lupus", "glaucoma", "peptic ulcer disease", "propylene glycol", "tizanidine", "severe renal impairment").
2. Match each CAUTION TRIGGER against the documented patient facts. A symptom the patient reported in the inquiry stage is a documented fact, not a hypothetical. If the literal trigger is met, mark that option CAUTION-TRIGGERED.
3. Prefer, in order:
   - (a) an option with a matching INDICATION and NO triggered CAUTION — select this.
   - (b) if no option has both, an option whose triggered caution is a monitoring/interaction note ("monitor", "may increase", "use with caution in") rather than an absolute do-not-use clause. Among absolute-stop options, the one whose stop clause is NOT literally met by the facts is preferable to the one whose stop clause IS met.
4. When a favorite option (matching indication) carries a triggered absolute caution, do NOT rationalize keeping it by pointing to a different mechanism (e.g. "the other option has a lupus caution so this one is safer"). Compare the two candidates on the SAME axis: which option's own stop clause is actually met by the patient's documented facts? Drop the one whose clause is met.
5. Never treat "no usable label excerpt" as a safe indication — an option with a missing/irrelevant excerpt cannot be selected over one with an excerpt that names the indication and has no triggered stop clause.

## Example Trajectory
WRONG:
Task: Select the PPI for erosive esophagitis; patient reports trouble/pain swallowing food and blood when coughing, and has a history of lupus. Options include omeprazole ("do not use if trouble or pain swallowing food or vomiting with blood") and rabeprazole ("PPI use has been associated with lupus exacerbation").
Think: Both have triggered-looking cautions; I'll pick the one whose caution matches a "softer" fact (lupus) rather than the swallowing/blood symptoms. Answer: A (rabeprazole).
Obs: Incorrect — the patient's documented swallowing difficulty and blood on coughing literally meet omeprazole's own stop clause, so omeprazole is the option whose caution is actually triggered; the correct pick is the one whose clause is NOT met by the reported symptoms.

CORRECT:
Task: same as above.
Think: Rabeprazole's lupus caution is a monitoring/association note, not a "do not use if lupus." Omeprazole's text is an absolute "do not use if trouble or pain swallowing food or vomiting with blood." The patient literally reports difficulty swallowing solids and blood when coughing, so omeprazole's trigger is met. Select the option whose stop clause is NOT met by the facts.
Obs: Correct.
