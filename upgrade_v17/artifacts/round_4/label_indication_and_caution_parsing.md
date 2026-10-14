---
description: Parse option labels for indication match AND triggered absolute cautions;
  when only one option matches the indication, still check its caution text for a
  literal triggered stop clause before selecting.
name: label_indication_and_caution_parsing
provenance:
  action: MODIFY
  epoch: 0
  fixes: 3
  parent_version: 2
  probe_score: 2
  regressions: 0
  triggering_sample_ids:
  - 2e5a9c8a7cc5beaf
  - 50e8f694821665a3
  - 94ea9efb5c41b013
  - e94bbf0c3fb11e83
  - babc0647a9d8b25e
  - 58b561d685a5a456
  - 1a1494874174efd2
  - 5c6475706206df20
  - 3852774624518ee0
  - 49edbae95bb22f29
  update_cycle: 3
tags:
- contraindication
- interaction
- select
- medication
- contraindicated
- do not use
- not recommended
- avoid in patients with
- medication safety
version: 3
---

## When to Use This Skill

Use this skill for every medication-selection task where you must pick the single best option. It applies whenever the task instruction contains words like "select", "which medication", "best treats", "contraindication", "interaction", "do not infer undocumented contraindications", or "respecting the patient facts and medication safety". The primary trigger is the presence of a list of candidate options whose label excerpts must be compared against documented patient facts.

## Core Rule

For each option, evaluate two things in order:

1. **Indication match**: Does the label excerpt explicitly name the stated problem (or a direct synonym)? An option with no matching indication is a fallback at best — it can only be selected if no option matches.
2. **Triggered absolute caution**: Does the label excerpt contain a literal do-not-use / stop / avoid clause whose condition is met by a documented patient fact (e.g. "do not use if you have kidney disease" + documented kidney disease; "contraindicated in severe renal impairment" + documented severe kidney disease; "avoid in patients with myasthenia gravis" + documented myasthenia gravis; "do not use if trouble or pain swallowing food" + reported trouble swallowing)?

Select the option that both matches the indication AND has no triggered absolute caution. If no option satisfies both, prefer the option whose indication matches and whose caution is a monitoring/dose-adjustment note rather than a literal stop clause.

## Decision Procedure

1. Extract the stated problem from the dialogue (final diagnosis or chief symptom cluster).
2. For each option, scan its label excerpt for the indication. Note whether the indication is named explicitly.
3. For each option, scan for absolute stop language: "do not use", "contraindicated", "avoid in patients with", "not recommended in", "should not be administered to".
4. Cross-check each stop clause against the documented patient facts. A stop clause fires only if the exact condition named in the label is present in the dialogue.
5. Eliminate any option whose stop clause fires. Among survivors, pick the one with the strongest indication match.
6. If the only indication-matching option has a fired stop clause, do NOT select it on the theory that "indication beats caution". Instead select the best option among those without a fired stop clause, even if its indication is weaker.

## Common Misjudgments

- Treating a monitoring/interaction note ("monitor INR", "may increase risk of", "use with caution") as an absolute contraindication. These are not stop clauses.
- Treating a missing label excerpt as evidence of safety. Missing excerpts never establish safety and never override a matching indication with a clean caution.
- Selecting an option because it is the only one naming the indication, while ignoring a literal stop clause that the patient's documented facts trigger.
- Treating a same-drug duplicate (brand vs generic) as two separate options when one has a usable excerpt and the other does not.

## Example Trajectory

### Wrong trajectory (selects the indication-matching option despite a fired stop clause)

Task: "Select the single medication option that best treats the stated problem while respecting the patient facts and medication safety. Do not infer undocumented contraindications." Patient has documented severe kidney disease; options are Fenofibrate, Gemfibrozil, Fluconazole.

Think: Fenofibrate is indicated for hyperlipoproteinemia type V and the patient has that condition. Let me check the others.
Act: {"evidence": "Fenofibrate is indicated for hyperlipoproteinemia type V, matching the stated problem. Gemfibrozil also treats elevated triglycerides. Fluconazole is not indicated.", "final": "A"}
Obs: Wrong — Fenofibrate's label contains a literal contraindication in severe renal impairment, and the patient has documented severe kidney disease. The stop clause fires.

### Correct trajectory (checks the stop clause before selecting)

Task: Same as above.

Think: Fenofibrate's indication matches, but I must scan its caution text for a literal stop clause. The label says "contraindicated in severe renal impairment." The patient has documented severe kidney disease. That stop clause fires, so Fenofibrate is eliminated despite the indication match. Gemfibrozil is indicated for elevated triglycerides and its excerpt shows no triggered absolute stop clause. Fluconazole has no matching indication.
Act: {"evidence": "Fenofibrate is indicated for hyperlipoproteinemia type V but is contraindicated in severe renal impairment, which the patient reports. Gemfibrozil is indicated for elevated triglycerides (type V) and its excerpt shows no triggered absolute contraindication from the documented facts. Fluconazole is not indicated for hyperlipoproteinemia.", "final": "B"}
Obs: Correct — Gemfibrozil selected because its indication matches and no stop clause fires.

## Output Requirement

Your evidence string must state, for each option: (a) whether the indication matches, and (b) whether any absolute stop clause in its label is triggered by a documented patient fact. Then state which option survives both checks and why.
