"""Render one retained RxRSIAgent manuscript from saved evidence."""
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
    path=ROOT/name; SOURCES[name]=sha(path)
    return json.loads(path.read_text())

def table(caption,label,cols,header,rows):
    return ('\\begin{table*}[t]\\centering\\small\n\\setlength{\\tabcolsep}{4pt}\n'
            +'\\caption{'+caption+'}\n\\label{'+label+'}\n\\begin{tabular}{@{}'+cols+'@{}}\\toprule\n'
            +header+r'\\\midrule'+'\n'+'\n'.join(rows)+'\n\\bottomrule\\end{tabular}\n\\end{table*}')

def public_tables():
    data=read('upgrade_v17/results/summary.json')
    assert data['status']=='complete_main_comparison'
    assert all(d['independent_recount']=='passed' for d in data['datasets'].values())
    profile=read('rxrsiagent/evaluated_profile.json')
    assert profile['source_method_key']=='evolving_grounded' and profile['validation']['n_correct']==206
    assert sha(ROOT/profile['skill_path'])==profile['skill_sha256']
    def accuracy(key):
        return [f"{100*data['datasets'][ds]['methods'][key]['accuracy']:.2f}" for ds in ['rxsafebench','rxqa']]
    rows=[]
    for name,description in [(r'MedAgents \\citep{medagents}','Expert discussion'),(r'MDAgents \\citep{mdagents}','Adaptive collaboration'),(r'SafeRx-Agent \\citep{saferx}','Medication knowledge / verification')]:
        rows.append(name.replace('\\\\','\\')+' & '+description+r' & -- & -- \\')
    rows.append(r'GRASP \\citep{grasp}'.replace('\\\\','\\')+' & Author-core task adaptation & '+' & '.join(accuracy('author_grasp'))+r'\\')
    rows.append(r'\textbf{RxRSIAgent (ours)} & Evidence + selected skill memory & '+' & '.join(accuracy('evolving_grounded'))+r'\\')
    main=table('Main named-agent comparison: accuracy (\\%). Measured rows use the same DeepSeek backbone, one 512-token actor call, and identical questions. A dash means not executed under this protocol, not zero. The medical-agent comparison is incomplete; original-paper scores are not substituted.',
        'tab:main','llrr','Method & Main mechanism & RxSafeBench (988) & RxQA (300)',rows)
    rows=[]
    for key,label in [('cot','No evidence or learned skills (CoT)'),('author_grasp','Without evidence (GRASP skills)'),('fixed_grounded','Without learned skills (fixed grounding)'),('evolving_grounded',r'\textbf{RxRSIAgent}')]:
        rows.append(label+' & '+' & '.join(accuracy(key))+r'\\')
    abl=table('Component ablations of the selected agent. Accuracy (\\%); the same backbone, cases and inference cap apply. Component controls are not new paper methods.',
        'tab:ablation','lrr','Configuration & RxSafeBench & RxQA',rows)
    rows=[]
    for a,b in zip(data['rounds']['rxsafebench'],data['rounds']['rxqa']):
        rows.append(f"{a['round']} & {a['training_cases']} & {a['correct']}/988 & {b['correct']}/300"+r'\\')
    trajectory=table('Frozen learning checkpoints of the retained skill-learning algorithm; descriptive evaluation on the same questions. Round zero is fixed grounding. These are experience rounds, not competing historical versions.',
        'tab:trajectory','rrrr','Round & Training cases seen & RxSafeBench correct & RxQA correct',rows)
    return main,abl,trajectory

def order_table():
    d=read('upgrade_v25/results/summary.json');assert d['status']=='complete'
    audit=read('upgrade_v25/results/order_denominator_audit.json')
    read('upgrade_v25/results/order_denominator_summary.json')
    assert audit['status']=='passed' and audit['summary_sha256']==SOURCES['upgrade_v25/results/order_denominator_summary.json']
    rows=[]
    for key,label in [('error_priority_initial_tool','Fixed selected policy + initial order tool'),('error_prioritized','Same policy + learned order tool'),('uniform','Ordinary supervised update control')]:
        m=d['methods'][key]
        rows.append(f"{label} & {m['drug_f1_mean']:.5f} & {m['order_f1_mean']:.5f} & {100*m['predicted_order_completion']:.2f}"+r'\\')
    return table('Auxiliary order-tool experiment on 8,005 eICU test stays. Three-seed means; this is component evidence, not an end-to-end RxRSIAgent comparison. The first two rows hold medication selection fixed.',
        'tab:order','lrrr','Component configuration & Drug F1 & Joint-order F1 & Complete (\\%)',rows)

def coverage_table():
    d=read('rxrsiagent/results/retrieval_coverage.json');c=d['counts']
    assert d['status']=='complete' and not d['gold_used_for_retrieval'] and d['api_calls']==0
    assert d['retriever_sha256']==sha(ROOT/'rxrsiagent/core.py')
    rows=[f"Original option-name tool & {c['old_any_excerpt']} & {c['old_dosage_excerpt']}"+r'\\',
          f"Revised mention-aware tool & {c['new_any_excerpt']} & {c['new_dosage_excerpt']}"+r'\\']
    return table('Actual retrieval-only audit on all 300 public RxQA questions using the same frozen label corpus. Counts indicate excerpt availability, not verified relevance or clinical correctness. No answer scores are recomputed.',
        'tab:coverage','lrr','Retriever & Any excerpt /300 & Dosage excerpt /300',rows)

REFERENCES=r'''\begin{thebibliography}{99}
\bibitem[Ali et al.(2023)]{mrsurvey} Zafar Ali, Yi Huang, Irfan Ullah, Junlan Feng, Chao Deng, Nimbeshaho Thierry, Asad Khan, Asim Ullah Jan, Xiaoli Shen, Wu Rui, and Guilin Qi. 2023. Deep Learning for Medication Recommendation: A Systematic Survey. \emph{Data Intelligence}, 5(2):303--354. \url{https://doi.org/10.1162/dint_a_00197}.
\bibitem[Chen et al.(2026)]{rxeval} Shuhao Chen, Weisen Jiang, Changmiao Wang, Xiaoqing Wu, Xuanren Shi, Yu Zhang, and James T. Kwok. 2026. RxEval: A Prescription-Level Benchmark for Evaluating LLM Medication Recommendation. \emph{arXiv preprint arXiv:2605.14543}. \url{https://arxiv.org/abs/2605.14543}.
\bibitem[Jiang et al.(2025)]{medagentbench} Yixing Jiang, Kameron C. Black, Gloria Geng, Danny Park, James Zou, Andrew Y. Ng, and Jonathan H. Chen. 2025. MedAgentBench: A Realistic Virtual EHR Environment to Benchmark Medical LLM Agents. \emph{arXiv preprint arXiv:2501.14654}. \url{https://arxiv.org/abs/2501.14654}.
\bibitem[Johnson et al.(2024)]{mimiciv} Alistair Johnson, Lucas Bulgarelli, Tom Pollard, Brian Gow, Benjamin Moody, Steven Horng, Leo Anthony Celi, and Roger Mark. 2024. MIMIC-IV (version 3.1). PhysioNet. \url{https://doi.org/10.13026/kpb9-mt58}.
\bibitem[Kim et al.(2024)]{mdagents} Yubin Kim, Chanwoo Park, Hyewon Jeong, Yik Siu Chan, Xuhai Xu, Daniel McDuff, Hyeonhoon Lee, Marzyeh Ghassemi, Cynthia Breazeal, and Hae Won Park. 2024. MDAgents: An Adaptive Collaboration of LLMs for Medical Decision-Making. \emph{arXiv preprint arXiv:2404.15155}. \url{https://arxiv.org/abs/2404.15155}.
\bibitem[Madaan et al.(2023)]{selfrefine} Aman Madaan, Niket Tandon, Prakhar Gupta, Skyler Hallinan, Luyu Gao, Sarah Wiegreffe, Uri Alon, Nouha Dziri, Shrimai Prabhumoye, Yiming Yang, Shashank Gupta, Bodhisattwa Prasad Majumder, Katherine Hermann, Sean Welleck, Amir Yazdanbakhsh, and Peter Clark. 2023. Self-Refine: Iterative Refinement with Self-Feedback. \emph{Advances in Neural Information Processing Systems}. \url{https://arxiv.org/abs/2303.17651}.
\bibitem[Moll et al.(2026)]{grasp} Johannes Moll, Jean-Philippe Corbeil, Jiazhen Pan, Martin Hadamitzky, Daniel Rueckert, Lisa Adams, and Keno Bressem. 2026. GRASP: Gated Regression-Aware Skill Proposer for Self-Improving LLM Agents. \emph{arXiv preprint arXiv:2605.29668}. \url{https://arxiv.org/abs/2605.29668}.
\bibitem[NICE(2015)]{nice} National Institute for Health and Care Excellence. 2015. Medicines optimisation: The safe and effective use of medicines to enable the best possible outcomes. \emph{NICE guideline NG5}. \url{https://www.nice.org.uk/guidance/ng5/chapter/Recommendations}.
\bibitem[Palepu et al.(2025)]{rxqa} Anil Palepu, Valentin Li\'evin, Wei-Hung Weng, Khaled Saab, David Stutz, Yong Cheng, Kavita Kulkarni, S. Sara Mahdavi, Jo\"elle Barral, Dale R. Webster, Katherine Chou, Avinatan Hassidim, Yossi Matias, James Manyika, Ryutaro Tanno, Vivek Natarajan, Adam Rodman, Tao Tu, Alan Karthikesalingam, and Mike Schaekermann. 2025. Towards Conversational AI for Disease Management. \emph{arXiv preprint arXiv:2503.06074}. \url{https://arxiv.org/abs/2503.06074}.
\bibitem[Pollard et al.(2018)]{eicu} Tom J. Pollard, Alistair E. W. Johnson, Jesse D. Raffa, Leo A. Celi, Roger G. Mark, and Omar Badawi. 2018. The eICU Collaborative Research Database, a freely available multi-center database for critical care research. \emph{Scientific Data}, 5:180178. \url{https://doi.org/10.1038/sdata.2018.178}.
\bibitem[Shang et al.(2019)]{gamenet} Junyuan Shang, Cao Xiao, Tengfei Ma, Hongyan Li, and Jimeng Sun. 2019. GAMENet: Graph Augmented MEmory Networks for Recommending Medication Combination. \emph{Proceedings of AAAI}. \url{https://arxiv.org/abs/1809.01852}.
\bibitem[Shinn et al.(2023)]{reflexion} Noah Shinn, Federico Cassano, Ashwin Gopinath, Karthik Narasimhan, and Shunyu Yao. 2023. Reflexion: Language Agents with Verbal Reinforcement Learning. \emph{Advances in Neural Information Processing Systems}. \url{https://openreview.net/forum?id=vAElhFcKW6}.
\bibitem[Tang et al.(2024)]{medagents} Xiangru Tang, Anni Zou, Zhuosheng Zhang, Ziming Li, Yilun Zhao, Xingyao Zhang, Arman Cohan, and Mark Gerstein. 2024. MedAgents: Large Language Models as Collaborators for Zero-shot Medical Reasoning. \emph{Findings of ACL}, pages 599--621. \url{https://aclanthology.org/2024.findings-acl.33/}.
\bibitem[Wang et al.(2026)]{saferx} Xinyu Wang, Hanwei Wu, Zhenghan Tai, Sicheng Lyu, Qincheng Lu, Ziyu Zhao, Jijun Chi, Jingrui Tian, Xiao-Wen Chang, and Ziyang Song. 2026. SafeRx-Agent: A Knowledge-Grounded Multi-Agent Framework for Safe and Explainable Medication Recommendation. \emph{arXiv preprint arXiv:2605.29146}. \url{https://arxiv.org/abs/2605.29146}.
\bibitem[WHO(2019)]{who} World Health Organization. 2019. Medication safety in polypharmacy: Technical report. WHO-UHC-SDS-2019.11. \url{https://www.who.int/publications/i/item/WHO-UHC-SDS-2019.11}.
\bibitem[Wu et al.(2025)]{armr} Feiyue Wu, Tianxing Wu, and Shenqi Jing. 2025. ARMR: Adaptively Responsive Network for Medication Recommendation. \emph{Proceedings of IJCAI}, pages 7831--7839. \url{https://doi.org/10.24963/ijcai.2025/871}.
\bibitem[Yang et al.(2021)]{safedrug} Chaoqi Yang, Cao Xiao, Fenglong Ma, Lucas Glass, and Jimeng Sun. 2021. SafeDrug: Dual Molecular Graph Encoders for Recommending Effective and Safe Drug Combinations. \emph{Proceedings of IJCAI}. \url{https://arxiv.org/abs/2105.02711}.
\bibitem[Yang et al.(2025)]{rxbench} Yan Yang, Mouxiao Bian, Peiling Li, Bingjian Wen, Ruiyao Chen, Kangkun Mao, Xiaojun Ye, Tianbin Li, Pengcheng Chen, Bing Han, Jie Xu, Kaifeng Qiu, and Junyan Wu. 2025. Human-Level and Beyond: Benchmarking Large Language Models Against Clinical Pharmacists in Prescription Review. \emph{arXiv preprint arXiv:2512.02024}. \url{https://arxiv.org/abs/2512.02024}.
\bibitem[Zhao et al.(2025a)]{rxsafe} Jiahao Zhao, Luxin Xu, Minghuan Tan, Lichao Zhang, Ahmadreza Argha, Hamid Alinejad-Rokny, and Min Yang. 2025a. RxSafeBench: Identifying Medication Safety Issues of Large Language Models in Simulated Consultation. \emph{Proceedings of IEEE BIBM}, pages 4491--4496. \url{https://doi.org/10.1109/BIBM66473.2025.11356353}.
\bibitem[Zhao et al.(2025b)]{rxllm} Xingmeng Zhao, Kaitlin Blotske, Moriah Cargile, Adeleine Tilley, Brian Murray, Yanjun Gao, Kelli Henry, Susan E. Smith, Erin F. Barreto, Seth Bauer, Sunghwan Sohn, Tianming Liu, Tell Bennett, Mitch Cohen, and Andrea Sikora. 2025b. Rx-LLM: A Benchmarking Suite to Evaluate Safe Large Language Model Performance for Medication-Related Tasks. \emph{medRxiv preprint}. \url{https://doi.org/10.64898/2025.12.01.25341004}.
\bibitem[Zhao et al.(2025c)]{lamrec} Zihao Zhao, Chenxiao Fan, Junlong Liu, Zheng Wang, Xiangnan He, Chongming Gao, Juan Li, and Fuli Feng. 2025c. Fine-grained Alignment of Large Language Models for General Medication Recommendation without Overprescription. \emph{arXiv preprint arXiv:2503.03687}. \url{https://arxiv.org/abs/2503.03687}.
\end{thebibliography}'''

def run():
    main,abl,trajectory=public_tables()
    replacements={'AGENT_TABLE':main,'ABLATION_TABLE':abl,'TRAJECTORY_TABLE':trajectory,
                  'ORDER_TABLE':order_table(),'COVERAGE_TABLE':coverage_table(),'REFERENCES':REFERENCES}
    cases=read('rxrsiagent/results/case_studies.json')
    assert [(c['public_question_id'],c['fixed_prediction'],c['agent_prediction'],c['gold']) for c in cases['cases']]==[('104','C','B','B'),('10','C','A','C')]
    for name in ['paper/introduction_sources.json','rxrsiagent/clinical_skills.json','upgrade_v17/results/frozen_skills.json','rxrsiagent/results/contract_checks.json']:
        read(name)
    text=MANUSCRIPT
    for key,value in replacements.items():text=text.replace('@@'+key+'@@',value)
    assert '@@' not in text
    original=TARGET.read_text();prefix=original[:original.index(r'\documentclass')]
    start=prefix.index(r'\begin{filecontents*}[overwrite]{acl.sty}')+len(r'\begin{filecontents*}[overwrite]{acl.sty}')+1
    end=prefix.index(r'\end{filecontents*}',start)
    provenance=read('paper/latex/v0.3/acl_template_provenance.json')
    assert hashlib.sha256((prefix[start:end].rstrip()+'\n').encode()).hexdigest()==provenance['acl_sty_sha256']
    TARGET.write_text((prefix+text.lstrip('\n')).rstrip()+'\n')
    manifest={'snapshot':'2026-10-15 selected RxRSIAgent configuration and review-tool increment',
        'background_experiments_resumed':False,'new_work':'Read-only public case/retrieval audits and synthetic software checks',
        'paper_path':str(TARGET.relative_to(ROOT)),'paper_sha256':sha(TARGET),'acl_style_sha256':provenance['acl_sty_sha256'],
        'generator_sha256':sha(Path(__file__)),'narrative_sha256':sha(ROOT/'paper/acl_manuscript_text.py'),
        'source_sha256':SOURCES,'main_table':'Named agents; identical public questions for measured rows; medical-agent comparisons incomplete',
        'method':'RxRSIAgent','selected_profile':'rxrsiagent/evaluated_profile.json',
        'historical_prototypes_in_manuscript':False,'new_review_layer_in_main_scores':False}
    (ROOT/'paper/latex/v0.3/manuscript_evidence.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'written':str(TARGET),'sources':len(SOURCES),'method':'RxRSIAgent'}))
if __name__=='__main__':run()
