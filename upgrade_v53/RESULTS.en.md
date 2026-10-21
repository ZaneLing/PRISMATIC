# RxRSIAgent: order-specific memory on256 new patients

**The full hypothesis remains unsupported.** This is a completed experiment, not a promised result. Three case orders retain5,4,4 rules, all deletions and none with empirical exception clauses. The first prespecified stream changes Qwen drug F1 from 6.61% to 6.65%; Llama changes from 4.58% to 4.64%. A gain in F1 or fewer extra tuples does not establish simultaneous improvement in all three errors.

## Design and scope

- Audit256 new patients, disjoint from all prior v25/v52 members. Both backbones run on all256. Reuse192 reflection/64 proposal/64 guard patients for development; those sets were already exposed.
- Six cumulative32-case rounds under seeds53/153/253. Qwen-derived programs transfer unchanged to Llama. This is not independent learning under two backbones or an estimate across arbitrary models.
- Frozen prompt, catalogue, actor weights, output cap and complete-JSON decoder. All local actors use one256-token call; postprocessing controls reuse exactly the same responses. Equal LLM generation does not mean identical information, extra tool work or supervision.
- New/changed **recorded** orders at hours6–12, not the full treatment plan. Native4 is HICL/route/dosage-string/frequency-string; exact mismatches do not establish clinical errors.
- The learner induces drug-specific programs over diagnostic paths and prior-record status. Statistical conditions require clinical review; removal means omitting a predicted future event, not stopping a patient's medication.
- Templates initially require3 reflection patients. A pre-outcome amendment uses3,815 old-training templates with at least3 distinct-patient support,125 encountered in reflection. Fourteen new field-repair candidates pass reflection but do not reduce aggregate proposal errors; retained programs are unchanged. No support/gate threshold was relaxed.

## Completed comparison

| Backbone / method | Drug F1 % | Native4 F1 % | Missed / patient ↓ | Extra / patient ↓ | Joint discrepancy / patient ↓ |
|---|---:|---:|---:|---:|---:|
| qwen / Frozen LLM agent | 6.61 | 1.49 | 1.516 | 6.980 | 7.223 |
| qwen / Fixed contract fallback (not RSI) | 6.60 | 1.49 | 1.516 | 6.992 | 7.234 |
| qwen / RxRSIAgent / order53 | 6.65 | 1.44 | 1.523 | 6.707 | 6.969 |
| qwen / RxRSIAgent / order153 | 6.63 | 1.43 | 1.523 | 6.727 | 6.980 |
| qwen / RxRSIAgent / order253 | 6.63 | 1.43 | 1.523 | 6.727 | 6.980 |
| qwen / Frozen supervised draft | 14.14 | 2.98 | 1.598 | 1.059 | 2.289 |
| qwen / Raw feedback correction replay | 5.94 | 1.31 | 1.555 | 6.734 | 7.086 |
| qwen / Learned actions without conditions | 6.23 | 1.21 | 1.562 | 6.082 | 6.371 |
| qwen / Shuffled reflection feedback | 6.60 | 1.33 | 1.527 | 6.652 | 6.969 |
| llama / Frozen LLM agent | 4.58 | 0.73 | 1.605 | 7.188 | 7.387 |
| llama / Fixed contract fallback (not RSI) | 6.72 | 1.30 | 1.488 | 7.625 | 7.684 |
| llama / RxRSIAgent / order53 | 4.64 | 0.75 | 1.605 | 7.066 | 7.270 |
| llama / RxRSIAgent / order153 | 4.63 | 0.74 | 1.605 | 7.090 | 7.293 |
| llama / RxRSIAgent / order253 | 4.63 | 0.75 | 1.605 | 7.082 | 7.285 |
| llama / Frozen supervised draft | 14.14 | 2.98 | 1.598 | 1.059 | 2.289 |
| llama / Raw feedback correction replay | 4.27 | 0.54 | 1.625 | 6.965 | 7.254 |
| llama / Learned actions without conditions | 4.21 | 0.69 | 1.637 | 6.535 | 6.789 |
| llama / Shuffled reflection feedback | 4.56 | 0.64 | 1.609 | 7.059 | 7.289 |

## Frozen round trajectory / 冻结的逐轮轨迹

| Round | Feedback cases | Rules | Exceptions | Qwen drug F1 % | Missed | Extra | Joint |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 | 6.61 | 1.516 | 6.980 | 7.223 |
| 1 | 32 | 1 | 0 | 6.59 | 1.520 | 6.898 | 7.141 |
| 2 | 64 | 2 | 0 | 6.64 | 1.520 | 6.832 | 7.070 |
| 3 | 96 | 3 | 0 | 6.59 | 1.523 | 6.781 | 7.012 |
| 4 | 128 | 4 | 0 | 6.63 | 1.523 | 6.734 | 6.988 |
| 5 | 160 | 4 | 0 | 6.63 | 1.523 | 6.734 | 6.988 |
| 6 | 192 | 5 | 0 | 6.65 | 1.523 | 6.707 | 6.969 |

![All frozen streams](results/retention.png)

## Paired uncertainty / 配对不确定性

| Model / order | Δ missed [95% CI] | Δ extra [95% CI] | Δ joint [95% CI] | Patients with any worsened component |
|---|---|---|---|---:|
| qwen / 53 | +0.0078 [+0.0000, +0.0195] | -0.2734 [-0.3594, -0.1953] | -0.2539 [-0.3359, -0.1758] | 2 |
| qwen / 153 | +0.0078 [+0.0000, +0.0195] | -0.2539 [-0.3320, -0.1836] | -0.2422 [-0.3164, -0.1719] | 2 |
| qwen / 253 | +0.0078 [+0.0000, +0.0195] | -0.2539 [-0.3320, -0.1836] | -0.2422 [-0.3164, -0.1719] | 2 |
| llama / 53 | +0.0000 [+0.0000, +0.0000] | -0.1211 [-0.1875, -0.0625] | -0.1172 [-0.1836, -0.0586] | 0 |
| llama / 153 | +0.0000 [+0.0000, +0.0000] | -0.0977 [-0.1484, -0.0508] | -0.0938 [-0.1445, -0.0469] | 0 |
| llama / 253 | +0.0000 [+0.0000, +0.0000] | -0.1055 [-0.1602, -0.0547] | -0.1016 [-0.1562, -0.0508] | 0 |

## Recorded disease-system strata / 记录的疾病系统分层

| Model / stratum | Baseline → final drug F1 % | Baseline → final missed | Baseline → final extra | Baseline → final joint |
|---|---:|---:|---:|---:|
| qwen / one_system | 8.08 → 8.03 | 1.859 → 1.867 | 5.961 → 5.828 | 6.984 → 6.875 |
| qwen / multiple_systems | 5.32 → 5.40 | 1.172 → 1.180 | 8.000 → 7.586 | 7.461 → 7.062 |
| llama / one_system | 5.34 → 5.36 | 1.938 → 1.938 | 7.477 → 7.438 | 8.180 → 8.141 |
| llama / multiple_systems | 3.68 → 3.77 | 1.273 → 1.273 | 6.898 → 6.695 | 6.594 → 6.398 |

## Output contract / 输出协议

| Backbone | Syntax failure | Responses with unknown IDs | Empty output | Empty with nonempty target |
|---|---:|---:|---:|---:|
| qwen | 2/256 | 4/256 | 2/256 | 0/256 |
| llama | 104/256 | 43/256 | 125/256 | 65/256 |

All round states were frozen before audit outcomes. These are repeated measurements of the same256 patients, not independent256-patient experiments per round. The displayed95% intervals are marginal; `results/audit.json` also reports one-sided Bonferroni bounds over36 error/design/order/model tests. No favorable stream or checkpoint was selected. The static contract fallback raises Llama drug F1 from4.58% to6.72%, but increases extra and joint discrepancies; it also slightly worsens Qwen. It remains opt-in, with no experimental memory, and is not counted as RSI or promoted by its F1 gain.

## What changed, and what did not

- External memory grew; no LLM weights, pharmacological knowledge or executable interpreter code evolved autonomously.
- The two template-bank designs retain identical programs. The shuffled-reflection control keeps true proposal/guard labels, so any gain there can be supplied by development selection.
- Actor catalogue coverage is 244/465 drug targets (52.47%) and 43/411 complete reference tuples (10.46%). Added template access is not proof of useful template selection.
- Qwen shared-drug field mismatches: 61/75 before, 59/72 after. A changed denominator must be read with omissions; removing identities is not a dose repair.
- Two fixed local backbones, three orders, sparse labels and reused gates do not establish stable model-independent prescribing improvement. Multiple-system membership is not validated chronic multimorbidity.

## Appropriateness and deliverables

Three source-backed partial label tools now preserve unknown facts and distinguish initiation from continuation. Only1/1,836 final Qwen order rows receives partial checks, with all3 findings unknown. This very low coverage does not satisfy a full appropriateness audit. They run as preflight findings in `runtime.py`; they do not modify the frozen benchmark orders or certify clinical safety. See [sources and research](RESEARCH.en.md).

A local two-reviewer, method-blinded package contains32 random stratified patients and 7 unique rules. Sources are masked, presentation randomized, identical plans deduplicated; original recorded orders are also reviewed. **Completed annotations:0.** The [rubric](REVIEW_PROTOCOL.en.md) reports assessable denominators and missing-context rates. Case-level illustrations and all patient-derived rules remain restricted in `prismatic-v53/CASE_STUDIES.md` and `review/`.

New API spend: **USD0**. New local calls: 512; input/output tokens 937,139/70,649. Local compute is unpriced. The standing USD10 budget has USD0.085203 spent on the earlier aggregate-only proposer and USD9.914797 remaining; historical located response costs of approximately USD89.53 precede that cap.

## Next evidence needed

The observed failure has narrowed: template access improves, but condition-to-action transfer and productive repairs do not follow. Next work must obtain defensible treatment intent and active disease evidence; learn additions/field repairs that actually execute on independent cases; compare them against raw feedback memory; and complete blinded appropriateness/skill review. Do not tune further on these now-exposed256 patients or call rule accumulation clinical RSI.
