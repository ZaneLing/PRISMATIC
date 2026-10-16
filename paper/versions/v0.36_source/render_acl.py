"""Render the current English ACL source in place from audited results."""
import hashlib,json
from pathlib import Path
from acl_manuscript_text import MANUSCRIPT
from acl_references import REFERENCES
ROOT=Path(__file__).resolve().parent.parent
TARGET=ROOT/'paper/latex/v0.3/prismatic_v03_en.tex';SOURCES={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):
 p=ROOT/p;SOURCES[str(p.relative_to(ROOT))]=sha(p);return json.loads(p.read_text())
def table(caption,label,cols,head,rows):
 return '\\begin{table*}[t]\\centering\\small\n\\setlength{\\tabcolsep}{4pt}\n\\caption{'+caption+'}\n\\label{'+label+'}\n\\begin{tabular}{@{}'+cols+'@{}}\\toprule\n'+head+r'\\\midrule'+'\n'+'\n'.join(rows)+'\n\\bottomrule\\end{tabular}\n\\end{table*}'
def clinical():
 d=read('rxrsiagent/clinical_evaluation_protocol.json');assert not d['clinical_results_available'];rows=[]
 for x in d['endpoints']:
  name=r'\textbf{'+x['name']+'}' if x['priority']=='primary' else x['name'];rows.append(name+' & '+x['unit']+' & '+x['definition']+r'\\')
 return '\\begin{table*}[t]\\centering\\small\n'+r'\caption{Proposed clinical endpoints; all scores await blinded annotation. Bold rows are primary. This research rubric is not a validated clinical scale.}\label{tab:clinicalmetrics}\begin{tabularx}{\textwidth}{@{}p{3.4cm}p{1.4cm}X@{}}\toprule Endpoint & Unit & Definition\\\midrule'+'\n'+'\n'.join(rows)+'\n'+r'\bottomrule\end{tabularx}\end{table*}'
def run():
 d=read('upgrade_v35/results/audit.json');assert d['status']=='passed_complete';native=read('upgrade_v34/results/audit.json')['author_methods'];m=d['methods'];v=read('upgrade_v36/results/audit.json');assert v['status']=='complete';diag=read('upgrade_v35/results/calibration_diagnostics.json');curve=read('upgrade_v35/results/calibration_curve.json')['curve'];selection=read('upgrade_v35/results/calibration_selection.json');assert selection['guard_pass'];read('upgrade_v35/test_freeze.json');read('upgrade_v35/protocol.json');read('upgrade_v36/protocol.json')
 # A candidate is selected by development gates only, never by RxQA score.
 freeze=ROOT/'upgrade_v36/test_freeze.json';chosen=None
 if freeze.exists():
  chosen=read('upgrade_v36/test_freeze.json')['selected_arm'];assert v['results'][chosen+'-guard']['guard_pass']
 q=v['results'][chosen+'-rxqa'] if chosen else m['calibrated']['rxqa'];n=q['correct'];acc=100*n/300
 fmt=lambda r:f"{100*r['correct']/r['n']:.2f}"
 rows=[]
 for key,name in [('grasp',r'GRASP \citep{grasp}'),('medagents',r'MedAgents \citep{medagents}'),('mdagents',r'MDAgents \citep{mdagents}'),('calibrated',r'\textbf{RxRSIAgent}')]:
  x=m[key]['test'];y=q if key=='calibrated' else m[key]['rxqa'];yc=y.get('mean_calls',y['calls']/y['n']);rows.append(f"{name} & {fmt(x)} & {fmt(y)} & {x['mean_calls']:.2f}/{yc:.2f} & {x['invalid']}/{y['invalid']}"+r'\\')
 main=table('Named-agent comparison on identical public questions and the same served model. All rows allow at most4,608 generated output tokens/case. Calls, inputs and actual cost differ; this is not equal total compute. RxSafe is a derived option-selection task; RxQA is the public OpenFDA subset.','tab:main','lrrrr','Method & RxSafe988 (\\%) & RxQA300 (\\%) & Calls: S/Q & Invalid: S/Q',rows)
 rows=[]
 for key,name in [('medagents','MedAgents'),('mdagents','MDAgents')]:
  x=native[key]['test'];y=native[key]['rxqa'];rows.append(f"{name} & 24,000 & {fmt(x)} & {fmt(y)} & {x['mean_calls']:.2f}/{y['mean_calls']:.2f}"+r'\\')
 rows.append(r'GRASP (earlier one-call cap) & 512 & 50.81 & 63.00 & 1/1\\')
 nt=table('Previously completed runs with different output allowances, retained for budget sensitivity. These are not substitutes for the common-allowance comparison.','tab:native','lrrrr','Method & Output cap & RxSafe988 (\\%) & RxQA300 (\\%) & Calls: S/Q',rows)
 rows=[]
 for key,name in [('no_evidence','Three-call no-evidence control'),('old_evidence','Original option-name retrieval'),('verified_evidence','Verified static retrieval, no calibration'),('calibrated','Verified retrieval + selected calibration')]:
  rows.append(f"{name} & {fmt(m[key]['test'])} & {fmt(m[key]['rxqa'])}"+r'\\')
 abl=table('Initial component intervention: same three calls and1,536-token per-call cap. The static calibrated row is frozen before follow-up development.','tab:ablation','lrr','Configuration & RxSafe988 (\\%) & RxQA300 (\\%)',rows)
 rows=[]
 for key,label in [('identity_only','Medication identity only'),('identity_and_draft','Identity + LLM draft'),('context_only','Medication--context interactions'),('context_and_draft','Interactions + LLM draft')]:
  x=diag['arms'][key]['splits'];rows.append(f"{label} & {x['proposal']['correct']}/190 & {x['guard']['correct']}/197 & {x['test']['correct']}/988"+r'\\')
 diagnostics=table('Post-selection calibration diagnostics, fixed C=10 and gap0.2. No diagnostic replaces the pre-test selected agent based on its test score. Strong identity-only performance is evidence of a possible benchmark shortcut.','tab:calibrationdiag','lrrr','Features & Proposal & Guard & RxSafe test',rows)
 rows=[]
 for r in curve:rows.append(f"{r['cases']} & {r['features']:,} & {r['proposal']['correct']}/190 & {r['guard']['correct']}/197 & 0/0"+r'\\')
 trajectory=table('Fixed-hyperparameter training-prefix diagnostics. Hyperparameters use full training/development feedback, so this is not prospective online RSI. The last column shows retained text cards in two separately gated four-round runs.','tab:trajectory','rrrrr','Cases seen & Numeric features & Proposal & Guard & Text cards: run1/2',rows)
 data=table('Data boundaries. Main benchmarks have prior research exposure; new selection excludes their evaluation answers. The independent development cohort is not a final test.','tab:data','p{3.4cm}p{6.5cm}p{4.9cm}','Resource & Local use & Measured endpoint',[
 r'RxSafeBench adaptation & 625 train;190 proposal;197 guard;988 test & Choice accuracy\\',r'RxQA OpenFDA & All300 released questions & Choice accuracy\\',r'MedQA public training mirror & 120 proposal;120 guard;input-selected & Independent development accuracy\\',r'eICU (separate component) & 8,005 held-out hospital stays & Joint-order F1\\',r'Clinician study / MedAgentBench & Pending & Not reported as completed\\'])
 rows=[]
 for key,label in [('grasp','GRASP'),('medagents','MedAgents'),('mdagents','MDAgents'),('calibrated','RxRSIAgent')]:
  for split,ds in [('test','RxSafe988'),('rxqa','RxQA300')]:
   x=q if key=='calibrated' and split=='rxqa' else m[key][split];rows.append(f"{label} & {ds} & {x['input_tokens']:,} & {x['output_tokens']:,} & {x['logical_cost_usd']:.3f}"+r'\\')
 compute=table('Aggregate logical inference use under the common output allowance. Costs sum successful response receipts at recorded provider rates, including reused receipts; they differ from newly billed cost.','tab:compute','llrrr','Method & Task & Input tokens & Output tokens & Logical USD',rows)
 independent=[]
 for arm,label in [('full_section_context','Expanded source context'),('contrastive_review','Independent draft and contradiction review'),('training_memory','External training-example memory')]:
  x=v['results'].get(arm+'-proposal')
  if x:
   z=f"{label} scores {x['correct']}/120 on proposal"
   if arm+'-guard' in v['results']:z+=f" and {v['results'][arm+'-guard']['correct']}/120 on guard"
   z+=', passing both gates.' if chosen==arm else ', and is not promoted.';independent.append(z)
 indep=' '.join(independent)
 if chosen:
  desc='The selected long-option branch retrieves three input-similar MedQA training examples, excludes development/evaluation text overlap, and supplies the reference answers as fallible examples to calls two and three. Applicability conditions must match; examples are not label authority. This adds external training data and does not establish an equal-data advantage.' if chosen=='training_memory' else 'The selected long-option branch adds an independent preliminary draft, explicit option-clause contradiction review and final arbitration, with the same three-call cap.'
 else:desc=''
 transfer=f"On RxQA the selected agent answers {n}/300 ({acc:.2f}\\%), compared with200 for matched-output MedAgents and208 for the higher-allowance run. "
 if n<=208:transfer+='It does not exceed the strongest completed medical-agent comparator. '
 else:transfer+='It exceeds the observed higher-allowance MedAgents count, subject to exploratory repeated-benchmark and single-run limits. '
 abstract='The strongest higher-allowance medical-agent comparator answers208/300; cross-benchmark superiority is not established.' if n<=208 else 'The selected independent-development intervention exceeds the observed higher-allowance MedAgents count of208/300, with exploratory evaluation limits.'
 refs=REFERENCES.replace(r'\end{thebibliography}',r'\bibitem[Jin et al.(2020)]{medqa} Di Jin, Eileen Pan, Nassim Oufattole, Wei-Hung Weng, Hanyi Fang, and Peter Szolovits. 2020. What Disease does this Patient Have? A Large-scale Open Domain Question Answering Dataset from Medical Exams. \emph{arXiv:2009.13081}. \url{https://github.com/jind11/MedQA}.'+'\n'+r'\end{thebibliography}')
 repl={'DATA_TABLE':data,'AGENT_TABLE':main,'NATIVE_TABLE':nt,'ABLATION_TABLE':abl,'CALIBRATION_DIAGNOSTICS':diagnostics,'TRAJECTORY_TABLE':trajectory,'COMPUTE_TABLE':compute,'CLINICAL_METRICS_TABLE':clinical(),'REFERENCES':refs,'RXQA_CORRECT':str(n),'RXQA_ACC':f'{acc:.2f}','ABSTRACT_TRANSFER':abstract,'MAIN_TRANSFER':transfer,'CONTRAST_METHOD':desc,'INDEPENDENT_RESULTS':indep,'CONCLUSION_TRANSFER':('RxQA remains below the strongest completed medical-agent comparator.' if n<=208 else 'An independently gated intervention also increases the RxQA result.'),'AUDIT_DETAILS':f"The follow-up audit checks {v['source_spans_checked']:,} source spans; its successful-response ledger increment is USD{v['ledger_increment_usd']:.3f}. The initial experiment costs USD16.261 in new successful responses."}
 text=MANUSCRIPT
 for k,val in repl.items():text=text.replace('@@'+k+'@@',val)
 assert '@@' not in text
 original=TARGET.read_text();prefix=original[:original.index(r'\documentclass')];start=prefix.index(r'\begin{filecontents*}[overwrite]{acl.sty}')+len(r'\begin{filecontents*}[overwrite]{acl.sty}')+1;end=prefix.index(r'\end{filecontents*}',start);provenance=read('paper/latex/v0.3/acl_template_provenance.json');assert hashlib.sha256((prefix[start:end].rstrip()+'\n').encode()).hexdigest()==provenance['acl_sty_sha256'];TARGET.write_text('\n'.join(line.rstrip() for line in (prefix+text.lstrip()).splitlines()).rstrip()+'\n')
 manifest={'snapshot':'2026-10-16 verified evidence, equal output allowance, supervised experience calibration and independent follow-up','method':'RxRSIAgent','paper_path':str(TARGET.relative_to(ROOT)),'paper_sha256':sha(TARGET),'generator_sha256':sha(__file__),'narrative_sha256':sha(ROOT/'paper/acl_manuscript_text.py'),'references_sha256':sha(ROOT/'paper/acl_references.py'),'acl_style_sha256':provenance['acl_sty_sha256'],'sources':SOURCES,'selected_calibration_sha256':selection['model_sha256'],'selected_followup':chosen,'main_counts':{'rxsafe':556,'rxqa':n},'historical_versions_in_manuscript':False,'background_queues_resumed':False};(TARGET.parent/'manuscript_evidence.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({'written':str(TARGET),'main_counts':manifest['main_counts']}))
if __name__=='__main__':run()
