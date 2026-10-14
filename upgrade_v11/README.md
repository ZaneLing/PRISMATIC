# v0.11 — grounded prescription evidence tools

Motivation from completed/development experiments: broad language reflections can regress correct decisions; narrowly memorized trigger rules barely cover new cases. The next increment adds retrieved drug-label evidence and compares a fixed evidence tool with feedback-selected tool configurations under equal evidence access.

`prepare_labels.py` queries only public candidate drug names from RxSafeBench. It sends no patient text or reference answers. It caches the response hash, label identifiers, effective date, exact query, matched names and failures. Missing labels remain missing. The source is [openFDA drug labeling](https://open.fda.gov/apis/drug/label/), which distributes company-submitted label records; its content is not uniformly FDA-verified. Labels are research evidence, not a clinical decision authority.

First stage: audit source/option coverage and compare fixed evidence retrieval against CoT on development cases. Only if the tool can support useful grounded decisions will the full configuration-evolution experiment proceed. Candidate configurations will be selected without test feedback; original negative versions remain available.
