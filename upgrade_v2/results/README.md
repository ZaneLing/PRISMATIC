# Aggregate results only

These JSON files contain cohort counts and aggregate metrics. Patient-level
cohorts, model artifacts trained on patient data, prompts, and predictions are
stored under `~/Desktop/MedTreeBench/dataset/restricted/prismatic-v2/` by default.

`supportive_cohort_audit.json` and `evolution_curve.json` are aggregate
summaries of local restricted-data experiments. `evolution_curve.png` is the
same aggregate learning curve. `openrouter_rxsafe_pilot*.json` and
`openrouter_rxqa_pilot*.json` contain only answers to pinned public benchmark
items, without prompts. `public_paired_comparison.json` gives paired
question-bootstrap intervals. Do not add any patient-level MIMIC exports here.
