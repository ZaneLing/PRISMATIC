"""Data-linked manuscript additions for the prescribing-gap and spend audits."""


def render(read):
    audit=read('upgrade_v50/results/audit.json')['methods']['rxrsi_selected']
    counts=audit['counts'];de=audit['descriptive_endpoints'];m=audit['metrics']
    spend=read('paper/total_spend_audit.json');low,high=spend['located_successful_reported_usd_range']
    gap_text=r'\paragraph{Where current order agreement is lost.} '
    gap_text+=f"RxRSIAgent predicts {m['mean_predicted_drugs']:.2f} drugs per admission against {counts['gold']/m['cases']:.2f} recorded target drugs. Reference-relative omissions and extras average {de['missed_drugs_per_admission']:.2f} and {de['extra_drugs_per_admission']:.2f}; mean drug Jaccard is {100*de['mean_drug_jaccard']:.2f}\\%, with {100*de['drug_exact_set_accuracy']:.2f}\\% exact drug-set agreement. Recall is {100*de['prior_target_recall']:.2f}\\% for targets already present in prior orders versus {100*de['new_target_recall']:.2f}\\% for other targets. Among complete Core4 targets whose drug is selected, {100*de['joint_fields_recall_given_correct_drug']:.2f}\\% match all four fields. "
    gap_text+=r'''
These descriptive endpoints concern the current local actor, not clinical appropriateness. Recorded prescriptions expose clinician actions, not their complete reasoning or a uniquely appropriate regimen. Agreement should therefore be supplemented by treatment-goal coverage, acceptable alternatives and clinician edit burden. Establishing a workflow mechanism requires changing a stage while holding cases and resources fixed, observing intermediate changes, and confirming corrections without regressions on independent cases. Patient-condition overgeneralization and harmful memory are already studied by MedPIC, GRASP and SkeMex \citep{medpic,grasp,skemex}; we do not claim those broad phenomena as new discoveries. No neural-circuit mechanism is established here.
'''
    cost_text = r'''\paragraph{Cumulative response expenditure.}
''' + f"The located successful-response costs across the upgrade studies total approximately USD{(low+high)/2:.2f}: USD{spend['main_ledger']['reported_usd']:.5f} in {spend['main_ledger']['successful_response_events']:,} shared-ledger events, plus USD{spend['legacy']['deduplicated_recorded_usd']:.5f}--{spend['legacy']['all_records_usd']:.5f} in legacy records. " + r'''The narrow range reflects ambiguous identical pilot/full-run records, not bounds on unrecorded charges. Cached rereads are not added; separately logged repeated requests are retained. Six legacy records lack prices, and failed requests, local compute, earlier unrecorded work and account adjustments remain unreconciled. This is provider-reported receipt cost, not an invoice. Previously reported study increments are already included. The audit itself performs no model calls.
'''
    return gap_text, cost_text
