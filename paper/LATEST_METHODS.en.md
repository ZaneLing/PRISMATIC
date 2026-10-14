# Recent methods: source and protocol audit

Updated **15 October 2026**. This is an increment to the [current results](CURRENT_RESULTS.en.md), not a new ranking of incompatible scores. `(R)` means reported by the cited authors. Our executions remain in their own tables.

## 1. Published results worth comparing

| Method / publication | Dataset and prediction target | Author-reported result (R) | Comparison role |
|---|---|---|---|
| [ARMR, IJCAI 2025](https://www.ijcai.org/proceedings/2025/0871.pdf), Tables 2–3 | MIMIC-III: 6,350 patients / 15,032 visits; MIMIC-IV: 9,036 / 20,616; 131 ATC-L3 classes; current diagnoses/procedures and visit history | F1 0.6959 / 0.6712, respectively; patient-averaged scoring | Important recent structured prescription baseline. Piecewise history encoding and existing/new-drug attention; temporal/component ablations. [Author code](https://github.com/seucoin/armr2). |
| [HADRec, October 2026 preprint](https://arxiv.org/html/2610.00984v1), Tables 4, 8 | MIMIC-III / IV; hierarchy and molecular features; published hierarchy label requires the code audit below | MIMIC-III F1 0.7010; IV 0.6408; III→IV transfer 0.5901 | Cite as reported results. Drug identity and hierarchy must be resolved before a matched reproduction. Transfer is not an across-the-board accuracy gain. |
| [LT3, CL4Health 2025](https://aclanthology.org/2025.cl4health-1.17/), Table 2 | n2c2-2018 / MIMIC-III; given medication attributes → synthetic instruction text | BLEU 78.52; ROUGE-L 77.55 | Text realization comparator, not patient-to-medication selection. Its 96–98% downstream NER F1 is not medication-set F1. The official training set is split 9:1 for training/validation; the official test is retained. |

## 2. Executed code audit

- **ARMR identity.** The IJCAI 2025 author repository is pinned to `750480158e94ed5be37011e05fe1212d9ba60705`. Its forward implementation includes piecewise temporal/Mamba blocks and existing/new-drug representations. It can execute with ordinary PyTorch; a CUDA-only Mamba dependency is not required by this implementation. No author patient records were checked out.
- **DREAM citation mismatch.** At `a9851583a4b90904e7aa697f6bd6cddb89b03d33`, the [README](https://github.com/novzyg/DREAM) identifies ARMR as the 2021 adversarial method, while `models/armr.py` contains piecewise/Mamba components resembling the 2025 method. This is an unresolved metadata/implementation inconsistency; neither identity nor its leaderboard score is accepted solely from the table name. Prefer the 2025 authors' code for our run.
- **HADRec hierarchy mismatch.** At `93d8e171bb028a54a7a81a384e80d1b8f58ed0d3`, `construction.py:107` and `data_process.py:117` truncate codes to four characters. `data_process.py:176–177` assign that same prefix to levels 3 and 4. Other tokenizer code expects five-character children. [Source](https://github.com/wjk78623-cell/HADRec/blob/93d8e171bb028a54a7a81a384e80d1b8f58ed0d3/data_process.py). Standard ATC-L3 is four characters and L4 five, e.g. A10B versus A10BA. [WHO collaborating centre](https://atcddd.fhi.no/atc/structure_and_principles/). This audit concerns released code; it does not reconstruct which unpublished artifacts generated every paper score.

## 3. Work now executed toward a common method table

The [v0.27 protocol](../upgrade_v27/protocol.json) registers a separate retrospective visit-set panel from licensed local MIMIC-IV 3.1, with patient-disjoint splits, true five-character ATC-L4, and training-only vocabularies. It will support ARMR, GAMENet, SafeDrug, RETAIN and conventional controls alongside the RxRSI prescription tool under the same information contract. It uses completed visit diagnoses/procedures; it is not the six-hour recorded-availability experiment.

The public molecular bridge has actually resolved **746/746 CIDs**, validated their SMILES with RDKit, and covers **399 ATC-L4 classes**. Raw response hashes and missingness are saved in the [resource audit](../upgrade_v27/results/molecular_resource_audit.json). Cohort-specific coverage, graph construction and substructure compatibility are still required before claiming a complete SafeDrug run. This replaces the earlier blanket “only ATC-L3 molecules available” blocker with a verified resource and explicit remaining checks.

Next gates: independent cohort reconstruction → molecular/graph coverage and author-core execution → register training/selection budgets → run common methods → frozen predictions and patient-cluster uncertainty. Do not insert unavailable scores as zero, substitute diagnosis words for longitudinal structured inputs, or label this exploratory panel an untouched confirmation set.
