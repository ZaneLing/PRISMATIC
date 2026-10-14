# v0.20 — Actual order-entry time audit

## Why this audit is necessary

Previous order targets were selected by intended prescription starttime. Provider `ordertime` records when the provider order was made; pharmacy `entertime` records pharmacy entry. They are distinct clocks, so a future medication start is not necessarily a future prescribing decision. [Provider-order documentation](https://mimic.mit.edu/docs/iv/modules/hosp/poe.html), [pharmacy documentation](https://mimic.mit.edu/docs/iv/modules/hosp/pharmacy.html).

## Executed population-level results

Joined all 1,788,195 existing target rows across 142,768 admissions with at least one target. Timestamp counts use exact patient **and** admission identity matches.

| Timestamp finding | Order rows | Fraction of all target rows |
|---|---:|---:|
| Exact-identity provider time available | 1,743,666 | 97.51% |
| Provider order before admission | 42,005 | 2.35% |
| Provider order within next 6 hours | 1,425,392 | 79.71% |
| Provider order at/after hour 6 | 276,269 | 15.45% |
| Pharmacy entry within next 6 hours | 1,777,546 | 99.40% |

There are 438 provider-link admission conflicts and zero patient-identity conflicts. These links do not supply trusted timestamps. All pharmacy links match patient/admission identities; both link-key tables are unique. Rows without a trustworthy provider time remain unknown. Patient-level data and the joined table stay restricted/local.

The pharmacy and provider clocks differ materially: 99.40% enter pharmacy within the original horizon, but only 79.71% have a matching provider order within it. This audit does not establish the cause of every discrepancy, and does not silently choose the more favorable clock. The old scores remain valid for their declared retrospective start-window task, not proof of prospective new-order prediction.

## Required next protocol

Build a new cohort from the complete prescription/entry tables, with a fixed decision point, source-specific availability rules and a stated treatment of inconsistent clocks. Do not simply filter the old start-window target file: doing so would miss newly authored orders whose intended starts fall outside that old window. Exclude untimed triage/reconciliation fields in the strict-availability primary analysis; gate labs on both charttime and storetime. Preserve the old experiment as a separate protocol and use new patient-disjoint confirmation cases. No prediction metric is claimed for this audit.
