"""Render the paused evidence snapshot into the existing English ACL editor file.

Only saved aggregate artifacts are read. No experiment, API request, or private
patient inference is launched. The editorial narrative lives in Python so the
existing .tex remains the sole standalone manuscript document.
"""
import hashlib
import json
from pathlib import Path
from acl_manuscript_text import MANUSCRIPT

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / 'paper/latex/v0.3/prismatic_v03_en.tex'
SOURCES = {}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    path = ROOT / name
    SOURCES[name] = sha(path)
    return json.loads(path.read_text())


def score(value):
    return f"{value['mean']:.5f}" + (f" $\\pm$ {value['seed_sd']:.5f}" if value['seed_sd'] is not None else '')


def table(caption, label, columns, header, rows, wide=False, note=''):
    env = 'table*' if wide else 'table'
    return (f'\\begin{{{env}}}[t]\\centering\\small\n'+(r'\setlength{\tabcolsep}{4pt}'+'\n' if wide else '')
            + '\\caption{' + caption + '}\n\\label{' + label + '}\n'
            + '\\begin{tabular}{@{}' + columns + '@{}}\\toprule\n' + header + r'\\\midrule' + '\n'
            + '\n'.join(rows) + '\n\\bottomrule\\end{tabular}\n' + note + '\n'
            + f'\\end{{{env}}}')


def common_table():
    data = read('upgrade_v27/results/development_methods.json')
    assert data['test_predictions_read'] is False
    assert all(sha(ROOT / name) == digest for name, digest in data['source_sha256'].items())
    extra = read('upgrade_v27/results/molecular-ARMR-selection-audit-seed42.json')
    report = read('upgrade_v27/results/molecular-ARMR-seed42.json')
    assert extra['status'] == 'passed' and extra['source_report_sha256'] == SOURCES['upgrade_v27/results/molecular-ARMR-seed42.json']
    assert report['status'] == 'selection_frozen' and len(report['epochs']) == 50
    labels = [('prevalence','Training prevalence'),('last_visit','Previous-visit reuse'),('cosine_knn','Case retrieval'),
              ('structured_logistic','Structured logistic regression'),('ARMR','ARMR author core'),('GAMENet','GAMENet author core'),
              ('SafeDrug','SafeDrug author core'),('uniform_policy','Shared policy / no rule updates'),('greedy_error_rules','Greedy error rules'),
              ('random_candidate_rules','Random candidate rules'),('own_error_rule_agent',r'\textbf{RxRSIAgent: own-error memory}'),
              ('shuffled_evidence_rule_agent','Shuffled-evidence memory'),('matched_proposals_without_witness_gate','Same proposals / no witness gate')]
    rows=[]; jaccard_rows=[]
    for key,label in labels:
        counts=[]; f1=[]; jaccard=[]
        for panel in ['full','molecular']:
            m=data['panels'][panel]['methods'].get(key)
            if m:
                counts.append(str(m['runs']));f1.append(score(m['patient_f1']));jaccard.append(score(m['patient_jaccard']))
            elif key=='ARMR' and panel=='molecular':
                m=extra['splits']['guard']['selected_metrics'];counts.append(r'1$^{\dagger}$');f1.append(f"{m['patient_f1']:.5f}");jaccard.append(f"{m['patient_jaccard']:.5f}")
            else:counts.append('--');f1.append('--');jaccard.append('--')
        rows.append(' & '.join([label,'/'.join(counts)]+f1)+r'\\')
        jaccard_rows.append(' & '.join([label,'/'.join(counts)]+jaccard)+r'\\')
    main=table('Common MIMIC-IV development comparison on the same 1,231 visits/467 patients. Full and molecular panels have different target spaces. Values are patient-average F1; $\\pm$ denotes completed-seed SD. Author cores use declared local adaptations. $\\dagger$: molecular ARMR has one completed seed; two remain unfinished. These are not final-test results.',
                 'tab:main','lrrr',r'Method & Runs full/mol. & Full 271-class F1 & Molecular 219-class F1',rows,True)
    supplemental=table('Patient-average Jaccard for the same development methods, cases, and completed seeds as Table~\\ref{tab:main}. $\\dagger$ marks the single completed molecular ARMR seed.',
                 'tab:jaccard','lrrr',r'Method & Runs full/mol. & Full Jaccard & Molecular Jaccard',jaccard_rows,True)
    return main,supplemental


def eicu_tables():
    data=read('upgrade_v25/results/summary.json');assert data['status']=='complete' and data['test_used_for_selection'] is False
    assert all(a['all_prediction_recounts']=='passed' for a in data['audits'])
    read('upgrade_v25/results/frozen_before_test.json');read('upgrade_v25/results/interval_numeric_audit.json')
    denominator=read('upgrade_v25/results/order_denominator_summary.json');audit=read('upgrade_v25/results/order_denominator_audit.json')
    assert audit['status']=='passed' and audit['summary_sha256']==SOURCES['upgrade_v25/results/order_denominator_summary.json']
    labels=[('initial_state','Initial 8k state'),('prevalence_global','Prevalence + global orders'),('reuse_prior_orders','Reuse prior orders'),
            ('retrieval_conditional','Case retrieval + conditional tool'),('word_global','Word policy + global orders'),('word_conditional','Word policy + conditional tool'),
            ('word_char_ensemble','Word/character ensemble'),('full_data_uniform','Full-data uniform learning'),('uniform','Uniform round updates'),
            ('error_prioritized',r'\textbf{Own-error round updates}'),('permuted_priority','Shuffled priorities'),
            ('error_priority_initial_tool','Own-error policy + initial tool'),('initial_policy_final_tool','Initial policy + final tool')]
    rows=[]
    for key,label in labels:
        m=data['methods'][key]
        rows.append(f"{label} & {m['drug_f1_mean']:.5f} $\\pm$ {m['drug_f1_sd']:.5f} & {m['order_f1_mean']:.5f} $\\pm$ {m['order_f1_sd']:.5f} & {100*m['predicted_order_completion']:.2f} \\\\")
    main=table('External eICU hospital test: 8,005 stays, 6,227 patients, sixteen hospitals. Three-seed means and SD; the primary joint score uses complete tuples, with output coverage reported. Ordinary full-data learning has the highest F1 point estimates.',
               'tab:eicu','lrrr',r'Method / configuration & Drug F1 & Joint-order F1 & Complete outputs (\%)',rows,True)
    rows=[]
    for r in range(5):
        cells=[str(r),f'{8000*(r+1):,}']
        for arm in ['uniform','error_prioritized','permuted_priority']:
            vals=[sum(s[arm][r][metric] for s in data['accepted_curves'].values())/3 for metric in ['drug_f1','order_f1']]
            cells.append('/'.join(f'{v:.5f}' for v in vals))
        rows.append(' & '.join(cells)+r'\\')
    growth=table('Frozen active-state trajectories on the same eICU test. Cells are drug/joint-order F1 averaged across three seeds. The horizontal axis counts encountered cases; rejected updates can retain earlier parameters and tools.',
                 'tab:growth','rrrrr','Round & Cases & Uniform & Own-error & Shuffled',rows,True)
    return main,growth


def parameter_tables():
    data=read('upgrade_v31/results/seed42.json');audit=read('upgrade_v31/results/audit-seed42.json')
    assert audit['source_public_snapshot_sha256']==SOURCES['upgrade_v31/results/seed42.json']
    count=sum(len(rows) for rows in data['arms'].values())
    assert count==9, 'Refresh the editorial snapshot before changing completed-run claims.'
    labels={'permuted_uniform':'Permuted / uniform','ranked_uniform':'Ranked / uniform','permuted_own_error':'Permuted / own-error','permuted_shuffled_error':'Permuted / shuffled'}
    rows=[]
    for name,states in data['arms'].items():
        for state in states:
            cells=[labels[name],str(state['round'])]
            for kind in ['ranked','permuted']:
                m=state['proposal'][kind];cells.append(f"{m['drug_micro_f1']:.5f}/{m['core_order_micro_f1']:.5f}")
            cells.append('/'.join(f"{100*state['proposal'][k]['empty_fraction']:.0f}" for k in ['ranked','permuted']))
            rows.append(' & '.join(cells)+r'\\')
    result=table('All nine completed parameter updates at the paused snapshot (seed 42). Scores are proposal drug/core-order F1. Empty rates are ranked/permuted percentages. This is a partial 36-update study, not a completed three-seed evaluation.',
                 'tab:parameters','lrrrr','Training / feedback & Round & Ranked & Permuted & Empty (\\%)',rows,True)
    return str(count),result


def precision_tables():
    data=read('upgrade_v32/results/proposal_precision.json');audit=read('upgrade_v32/results/proposal_precision_audit.json')
    assert audit['status']=='passed' and audit['summary_sha256']==SOURCES['upgrade_v32/results/proposal_precision.json']
    assert audit['auditor_sha256']==sha(ROOT/'upgrade_v32/audit_precision.py')
    read('upgrade_v32/results/precision_execution_lock.json');read('upgrade_v32/results/proposal_summary.json');read('upgrade_v32/results/proposal_audit.json')
    labels={'frozen_base':'Frozen base','original_failed_adapter':'Original failed adapter','teacher_uniform':'Teacher / uniform',
            'zero_uniform':'Zero / uniform','teacher_balanced':'Teacher / balanced','zero_balanced':'Zero / balanced','original_retrieval_top8':'Retrieval top-eight'}
    panels=data['panels']['drug_sha256'];rows=[]
    for key,label in labels.items():
        cells=[label]
        for kind in ['ranked','permuted']:
            for readout in ['native','fp32_binary']:
                m=panels[kind][readout]['methods'][key];cells.append(f"{m['drug_micro_f1']:.4f}/{m['core_order_micro_f1']:.4f}")
        rows.append(' & '.join(cells)+r'\\')
    main=table('Fixed-eight numerical diagnosis on 100 proposal admissions/97 patients. Drug/core-order F1 is shown under the primary drug-identity-hash tie rule. All readouts share frozen hidden states. This one-seed post-proposal analysis makes no new selection.',
               'tab:precision','lrrrr',r'& \multicolumn{2}{c}{Ranked candidates} & \multicolumn{2}{c}{Permuted candidates}\\\cmidrule(lr){2-3}\cmidrule(lr){4-5} State & Native & FP32 & Native & FP32',rows,True)
    rows=[]
    for key in data['state_versions']:
        for readout,label in [('native','Native'),('fp32_binary','FP32'),('fp32_rerounded',r'FP32 $\to$ BF16')]:
            cells=[labels[key],label]
            for kind in ['ranked','permuted']:
                m=panels[kind][readout]['methods'][key]
                cells += [f"{m['within_case_auroc_mean']:.4f}",str(m['boundary_tie_cases'])]
            a=data['score_rank_alignment'][readout]['permuted'][key]
            cells += [f"{a['drug_identity_aligned']['mean_spearman']:.4f}",f"{a['same_display_slots_unaligned']['mean_spearman']:.4f}"]
            rows.append(' & '.join(cells)+r'\\')
    detail=table('Numerical and identity-alignment diagnostics. AUROC averages 67 eligible admissions; all 100 remain in F1. Tie counts refer to the eighth/ninth score boundary. Correlations compare ranked/permuted outputs aligned by drug identity or unchanged display slot.',
                 'tab:precision-detail','llrrrrrr',r'State & Readout & R AUC & R ties & P AUC & P ties & Identity $\rho$ & Slot $\rho$',rows,True)
    return main,detail


def fhir_table():
    data=read('upgrade_v28/results/summary.json');rows=[]
    for name,condition in data['conditions'].items():
        cells=[name]
        for split in ['val','id_test','test']:
            if split not in condition['splits']:cells.append('--');continue
            r=condition['splits'][split];assert r['independent_reference_field_and_arithmetic_audit']=='passed'
            cells.append(f"{r['state_correct']}/{r['n']}")
        rows.append(' & '.join(cells)+r'\\')
    return table('Executed repair factorial. C: answer contract; S: source-bound observation statistics; K: frozen learned skills. A dash denotes an unfinished cell, not a failure score. Reused exploratory splits.',
                 'tab:fhir-repair','lrrr','Condition & Validation & ID & Held-out type',rows)


REFERENCES=r'''\begin{thebibliography}{99}
\bibitem[Johnson et al.(2024)]{mimiciv} Alistair Johnson, Lucas Bulgarelli, Tom Pollard, Brian Gow, Benjamin Moody, Steven Horng, Leo Anthony Celi, and Roger Mark. 2024. MIMIC-IV (version 3.1). PhysioNet. \url{https://doi.org/10.13026/kpb9-mt58}.
\bibitem[Jiang et al.(2025)]{medagentbench} Yixing Jiang, Kameron C. Black, Gloria Geng, Danny Park, James Zou, Andrew Y. Ng, and Jonathan H. Chen. 2025. MedAgentBench: A Realistic Virtual EHR Environment to Benchmark Medical LLM Agents. \emph{arXiv preprint arXiv:2501.14654}. \url{https://arxiv.org/abs/2501.14654}.
\bibitem[Madaan et al.(2023)]{selfrefine} Aman Madaan, Niket Tandon, Prakhar Gupta, Skyler Hallinan, Luyu Gao, Sarah Wiegreffe, Uri Alon, Nouha Dziri, Shrimai Prabhumoye, Yiming Yang, Shashank Gupta, Bodhisattwa Prasad Majumder, Katherine Hermann, Sean Welleck, Amir Yazdanbakhsh, and Peter Clark. 2023. Self-Refine: Iterative Refinement with Self-Feedback. \emph{Advances in Neural Information Processing Systems}. \url{https://arxiv.org/abs/2303.17651}.
\bibitem[Moll et al.(2026)]{grasp} Johannes Moll, Jean-Philippe Corbeil, Jiazhen Pan, Martin Hadamitzky, Daniel Rueckert, Lisa Adams, and Keno Bressem. 2026. GRASP: Gated Regression-Aware Skill Proposer for Self-Improving LLM Agents. \emph{arXiv preprint arXiv:2605.29668}. \url{https://arxiv.org/abs/2605.29668}.
\bibitem[Palepu et al.(2025)]{rxqa} Anil Palepu, Valentin Li\'evin, Wei-Hung Weng, Khaled Saab, David Stutz, Yong Cheng, Kavita Kulkarni, S. Sara Mahdavi, Jo\"elle Barral, Dale R. Webster, Katherine Chou, Avinatan Hassidim, Yossi Matias, James Manyika, Ryutaro Tanno, Vivek Natarajan, Adam Rodman, Tao Tu, Alan Karthikesalingam, and Mike Schaekermann. 2025. Towards Conversational AI for Disease Management. \emph{arXiv preprint arXiv:2503.06074}. \url{https://arxiv.org/abs/2503.06074}.
\bibitem[Pollard et al.(2018)]{eicu} Tom J. Pollard, Alistair E. W. Johnson, Jesse D. Raffa, Leo A. Celi, Roger G. Mark, and Omar Badawi. 2018. The eICU Collaborative Research Database, a freely available multi-center database for critical care research. \emph{Scientific Data}, 5:180178. \url{https://doi.org/10.1038/sdata.2018.178}.
\bibitem[Shang et al.(2019)]{gamenet} Junyuan Shang, Cao Xiao, Tengfei Ma, Hongyan Li, and Jimeng Sun. 2019. GAMENet: Graph Augmented MEmory Networks for Recommending Medication Combination. \emph{Proceedings of AAAI}. \url{https://arxiv.org/abs/1809.01852}.
\bibitem[Shinn et al.(2023)]{reflexion} Noah Shinn, Federico Cassano, Ashwin Gopinath, Karthik Narasimhan, and Shunyu Yao. 2023. Reflexion: Language Agents with Verbal Reinforcement Learning. \emph{Advances in Neural Information Processing Systems}. \url{https://openreview.net/forum?id=vAElhFcKW6}.
\bibitem[Wang et al.(2026)]{saferx} Xinyu Wang, Hanwei Wu, Zhenghan Tai, Sicheng Lyu, Qincheng Lu, Ziyu Zhao, Jijun Chi, Jingrui Tian, Xiao-Wen Chang, and Ziyang Song. 2026. SafeRx-Agent: A Knowledge-Grounded Multi-Agent Framework for Safe and Explainable Medication Recommendation. \emph{arXiv preprint arXiv:2605.29146}. \url{https://arxiv.org/abs/2605.29146}.
\bibitem[Wu et al.(2025)]{armr} Feiyue Wu, Tianxing Wu, and Shenqi Jing. 2025. ARMR: Adaptively Responsive Network for Medication Recommendation. \emph{Proceedings of IJCAI}, pages 7831--7839. \url{https://doi.org/10.24963/ijcai.2025/871}.
\bibitem[Yang et al.(2021)]{safedrug} Chaoqi Yang, Cao Xiao, Fenglong Ma, Lucas Glass, and Jimeng Sun. 2021. SafeDrug: Dual Molecular Graph Encoders for Recommending Effective and Safe Drug Combinations. \emph{Proceedings of IJCAI}. \url{https://arxiv.org/abs/2105.02711}.
\bibitem[Zhao et al.(2025)]{rxsafe} Jiahao Zhao, Luxin Xu, Minghuan Tan, Lichao Zhang, Ahmadreza Argha, Hamid Alinejad-Rokny, and Min Yang. 2025. RxSafeBench: Identifying Medication Safety Issues of Large Language Models in Simulated Consultation. \emph{Proceedings of IEEE BIBM}, pages 4491--4496. \url{https://doi.org/10.1109/BIBM66473.2025.11356353}.
\end{thebibliography}'''


def run():
    common,jaccard=common_table();external,growth=eicu_tables();count,parameters=parameter_tables();precision,detail=precision_tables()
    replacements={'COMMON_TABLE':common,'JACCARD_TABLE':jaccard,'EICU_TABLE':external,'GROWTH_TABLE':growth,'PARAMETER_COUNT':count,
                  'PARAMETER_TABLE':parameters,'PRECISION_TABLE':precision,'PRECISION_DETAIL_TABLE':detail,
                  'FHIR_TABLE':fhir_table(),'REFERENCES':REFERENCES}
    for name in ['upgrade_v27/rsi_addendum.json','upgrade_v27/results/cohort_audit.json','upgrade_v25/protocol.json',
                 'upgrade_v31/protocol.json','upgrade_v32/protocol.json','upgrade_v29/results/summary.json',
                 'upgrade_v17/results/summary.json','upgrade_v18/results/summary.json','upgrade_v19/results/summary.json']:
        read(name)
    text=MANUSCRIPT
    for key,value in replacements.items():text=text.replace('@@'+key+'@@',value)
    assert '@@' not in text
    original=TARGET.read_text()
    prefix=original[:original.index(r'\documentclass')]
    start=prefix.index(r'\begin{filecontents*}[overwrite]{acl.sty}')+len(r'\begin{filecontents*}[overwrite]{acl.sty}')+1
    end=prefix.index(r'\end{filecontents*}',start)
    provenance=read('paper/latex/v0.3/acl_template_provenance.json')
    # The standalone wrapper adds one separator newline after the original file.
    assert hashlib.sha256((prefix[start:end].rstrip()+'\n').encode()).hexdigest()==provenance['acl_sty_sha256']
    output=prefix+text.lstrip('\n')
    TARGET.write_text(output)
    manifest={'snapshot':'2026-10-15 paused experimental evidence','experiments_resumed':False,
              'paper_path':str(TARGET.relative_to(ROOT)),'paper_sha256':sha(TARGET),'acl_style_sha256':provenance['acl_sty_sha256'],
              'generator_sha256':sha(Path(__file__)),'narrative_sha256':sha(ROOT/'paper/acl_manuscript_text.py'),
              'source_sha256':SOURCES,'completed_author_runs':13,'registered_author_runs':15,
              'completed_parameter_updates':int(count),'registered_parameter_updates':36,
              'common_main_table':'MIMIC guard development; no final-test scores',
              'external_main_table':'eICU held-out-hospital test; three seeds',
              'precision':'100 proposal admissions, one training seed; independent readout audit passed'}
    (ROOT/'paper/latex/v0.3/manuscript_evidence.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'written':str(TARGET),'evidence_sources':len(SOURCES),'experiments_resumed':False}))


if __name__=='__main__':run()
