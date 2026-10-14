# v0.21 — Recorded-availability-controlled order study

## Completed cohort and independent audit

The decision is actual admission plus6h; predict new/changed orders in the following6h. Both provider and pharmacy entry times must lie within that window, with exact identity/linkage and verification by its end. Ambiguous potential targets are excluded. Inputs use recorded prior orders and blood labs available before the decision, plus demographics.

40,000 training /2,000 proposal /2,000 guard /1,082 test admissions, with1,024 test patients. Splits are patient-disjoint and the new test excludes old v6/v7/v9 test patients. An independent reconstruction audit checks198,850 target,589,393 prior-order and506,710 lab rows: all12 clock/identity/finiteness checks pass.

## Method experiment running

The frozen three-seed suite includes supervised word/character policies, retrieval, global/conditional order tools, growing policy/memory/tool states, object freezes, prevalence and prior-order reuse. It shares inputs, initial8k-frozen128-name vocabulary,20-order cap and scorer. All choices are selected on development; within-seed test scoring starts after that seed's full state trajectory is frozen. The complete table will be written only after all registered runs and independent recounts finish.

## Scope

This is a selected coherent-time, nonempty-target retrospective cohort, not all admissions. Recorded clocks do not provide complete field-version history. Raw-name scores are separate from earlier starttime tables and published ATC/RxNorm scores. The changing artifacts here are supervised selection parameters, episode memory and order-tool parameters; there is no LLM/API call or executable-code mutation. Restricted data remains local.

See `protocol.json`, `evaluation_protocol.json`, and `results/independent_cohort_audit.json`.
