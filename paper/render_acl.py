"""Render the current ACL source in place, using independently recounted results."""
import hashlib,json,re
from pathlib import Path
from acl_manuscript_text import MANUSCRIPT
from acl_references import REFERENCES
from failure_case_sections import render as render_failure_sections
from research_assessment_sections import render as render_research_assessment
from local_prescription_sections import render as render_local_prescription
ROOT=Path(__file__).resolve().parent.parent;TARGET=ROOT/'paper/latex/v0.3/prismatic_v03_en.tex';SOURCES={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):
 p=ROOT/p;SOURCES[str(p.relative_to(ROOT))]=sha(p);return json.loads(p.read_text())
def table(caption,label,cols,head,rows):
 return '\\begin{table*}[t]\\centering\\small\n\\setlength{\\tabcolsep}{4pt}\n\\caption{'+caption+'}\n\\label{'+label+'}\n\\begin{tabular}{@{}'+cols+'@{}}\\toprule\n'+head+r'\\\midrule'+'\n'+'\n'.join(rows)+'\n\\bottomrule\\end{tabular}\n\\end{table*}'
def clinical():
 d=read('rxrsiagent/clinical_evaluation_protocol.json');assert not d['clinical_results_available'];rows=[]
 for x in d['endpoints']:rows.append((r'\textbf{'+x['name']+'}' if x['priority']=='primary' else x['name'])+' & '+x['unit']+' & '+x['definition']+r'\\')
 return '\\begin{table*}[t]\\centering\\small\n'+r'\caption{Planned clinical endpoints; scores await blinded annotation. This research rubric is not a validated clinical scale.}\label{tab:clinicalmetrics}\begin{tabularx}{\textwidth}{@{}p{3.4cm}p{1.4cm}X@{}}\toprule Endpoint & Unit & Definition\\\midrule'+'\n'+'\n'.join(rows)+'\n'+r'\bottomrule\end{tabularx}\end{table*}'
def run():
 audit=read('upgrade_v44/results/audit.json');assert audit['status']=='complete';learning=read('upgrade_v44/results/learning.json');ind=read('upgrade_v44/results/independent.json');short=read('upgrade_v44/results/shortcuts.json');read('upgrade_v44/test_freeze.json');read('upgrade_v44/implementation.json');read('upgrade_v44/learning_protocol.json');read('upgrade_v37/protocol.json');read('upgrade_v37/independent_protocol.json')
 old=read('upgrade_v35/results/audit.json')['methods'];native=read('upgrade_v34/results/audit.json')['author_methods'];x=audit['methods']['test_rx']['final'];y=audit['methods']['test_qa']['final'];rx=x['correct'];qa=y['correct'];states=learning['rounds'];last=states[-1];ncard=len(last['state']['cards']);fmt=lambda r:f"{100*r['correct']/r['n']:.2f}"
 rows=[]
 for k,n in [('grasp',r'GRASP \citep{grasp}'),('medagents',r'MedAgents \citep{medagents}'),('mdagents',r'MDAgents \citep{mdagents}')]:
  a,b=old[k]['test'],old[k]['rxqa'];rows.append(f"{n} & {fmt(a)} & {fmt(b)} & {a['mean_calls']:.2f}/{b['mean_calls']:.2f} & {a['invalid']}/{b['invalid']}"+r'\\')
 rows.append(f"Supervised source-agent control & 56.28 & 66.33 & 3/3 & 0/0"+r'\\')
 rows.append(f"\\textbf{{RxRSIAgent}} & {fmt(x)} & {fmt(y)} & 3/3 & {x['invalid']}/{y['invalid']}"+r'\\')
 main=table('Same-question, same-backbone local task adaptations. All rows permit4,608 generated output tokens/case. Actual input cost, calls and training supervision differ. The supervised source-agent control uses the earlier fixed evidence workflow plus a labeled option calibrator; it is not an RSI result.','tab:main','lrrrr','Method & RxSafe988 (\\%) & RxQA300 (\\%) & Calls S/Q & Invalid S/Q',rows)
 rows=[]
 for k,n in [('medagents','MedAgents'),('mdagents','MDAgents')]:rows.append(f"{n} & 24,000 & {fmt(native[k]['test'])} & {fmt(native[k]['rxqa'])}"+r'\\')
 rows.append(r'GRASP (earlier allowance) & 512 & 50.81 & 63.00\\')
 nt=table('Completed different-allowance comparisons; these remain visible to avoid a superiority claim based only on constrained comparator budgets.','tab:native','lrrr','Method & Output cap & RxSafe988 (\\%) & RxQA300 (\\%)',rows)
 dt=table('Evaluation boundaries and endpoints. Repeated development is disclosed; independent evaluation starts only after all trajectories are frozen.','tab:data','p{3.1cm}p{6.8cm}p{4.7cm}','Resource & Use & Endpoint',[
 r'RxSafeBench local protocol & 200/625 train;190 proposal;197 guard;988 evaluation & Single-choice accuracy\\',r'RxQA public OpenFDA & All300 released questions; BNF unavailable & Single-choice accuracy\\',r'MedQA public train & 200 new training cases;120 proposal;120 guard & Single-choice accuracy\\',r'MedPIC-Bench & All467 test questions;35 strict same-option pairs & Exact-set and pair accuracy\\',r'MIMIC-IV local order task & 40,000 candidate-tool training;144 reflection;48/64 gates;1,082 evaluation & Drug-set and joint-order agreement\\',r'Clinical/real EHR execution & Pending, no completed clinical score & Appropriateness and state execution\\'])
 rows=[]
 for s,i in zip(states,ind['trajectory']):
  cards=s['state']['cards'];terms=sum(len(v) for c in cards for v in c.get('trigger_terms',{}).values());patches=sum(len(c.get('retrieval_patch',{})) for c in cards);g=s['gates'];rows.append(f"{s['round']} & {s['cases_seen']} & {len(cards)}/{patches}/{terms} & {g['proposal_rx']['correct']}/{g['proposal_med']['correct']} & {g['guard_rx']['correct']}/{g['guard_med']['correct']} & {i['metrics']['correct']}/467"+r'\\')
 traj=table('Frozen sequential trajectory. C/R/V are retained procedural cards, retrieval parameters and context-vocabulary entries. Proposal denominators are190/120; guard197/120. Reused training cohorts and identical-state prediction reuse are disclosed. No test-selected checkpoint.','tab:trajectory','rrrrrr','Round & Cases & C/R/V & Proposal S/M & Guard S/M & Independent',rows)
 rows=[]
 labels={37:'Full trace and broad context',38:'Typed roles and supported roots',39:'Narrow single-change proposals',40:'Learnable context vocabulary',41:'Compact root-cluster context',42:'External proposer with actual traces',43:'Explicit no-edit decision preserved',44:'Cumulative roots and near-miss replay'}
 for v in [37,38,39,40,41,42,43,44]:
  l=read(f'upgrade_v{v}/results/learning.json');ts=[t for s in l['rounds'] for t in s.get('trials',[])];counts={k:sum(t.get('rejection')==k for t in ts) for k in ['schema','training_intervention','proposal','guard','no_supported_edit']};rows.append(f"{labels[v]} & {len(ts)} & {counts['schema']}/{counts['no_supported_edit']} & {counts['training_intervention']} & {counts['proposal']}/{counts['guard']} & {sum(t['accepted'] for t in ts)}"+r'\\')
 upd=table('Updater development experiments on the same400-case cohort, not independent repetitions or additional unique cases. Each has four rounds. Schema includes role/scope validation or no valid proposal. Earlier designs are mechanism controls, not separately named paper methods.','tab:updates','p{4.7cm}rrrrr','Updater control & Attempts & Schema/declined & Probe & Proposal/guard & Retained',rows)
 sd=short['result']['final'];rows=[]
 for key,label in [('original','Original patient context'),('permuted','Permuted options'),('no_patient','Patient vignette removed')]:
  if key=='original':correct=sd['original_correct'];pair=sd[key]['paired']['both_correct'];inv='--'
  else:correct=sd[key]['metrics']['correct'];pair=sd[key]['detail']['paired']['both_correct'];inv=str(sd[key].get('same_prediction_after_remap','--'))
  rows.append(f"{label} & {correct}/70 & {pair}/35 & {inv}"+r'\\')
 shortcut=table('Predeclared diagnostics on all35 recovered same-option counterfactual pairs. The final column counts identical predictions after answer remapping. These tests do not establish absence of every shortcut.','tab:shortcuts','lrrr','Condition & Exact answers & Both members correct & Remap agreement',rows)
 z=ind['trajectory'][-1];families=z['detail']['families'];gf=families['guideline_following'];cf=families['counterfactual'];ip=z['detail']['paired'];delta=audit['comparisons']['initial_to_final_test_qa'];compare=audit['comparisons']['native_medagents_to_final_test_qa'];rxdelta=audit['comparisons']['initial_to_final_test_rx']
 abstract=f"The frozen agent answers{rx}/988 RxSafeBench and{qa}/300 public RxQA questions. " + ('It does not exceed the strongest completed controls on both tasks.' if rx<=556 or qa<=208 else 'Its observed counts exceed the completed named-agent controls, with repeated-benchmark limitations.')+f" The final state retains{ncard} procedural cards."
 maintext=f"RxRSIAgent answers{rx}/988 ({fmt(x)}\\%) on RxSafe and{qa}/300 ({fmt(y)}\\%) on RxQA. Against higher-allowance MedAgents'208/300, its RxQA difference is{100*compare['difference']:+.2f} percentage points (paired95\\% interval[{100*compare['ci95'][0]:+.2f},{100*compare['ci95'][1]:+.2f}]). " + ('Two-benchmark superiority is not established.' if rx<=556 or qa<=208 else 'This is an exploratory improvement over these completed controls, not a global SOTA claim.')
 evolution=f"Across the final four-round experiment,{sum(s['accepted'] for s in states)} updates are retained. Initial-to-final changes are{rxdelta['fixes']} fixes/{rxdelta['regressions']} regressions on RxSafe and{delta['fixes']}/{delta['regressions']} on RxQA. "
 if ncard==0:evolution+='The memory, retrieval configuration and vocabulary remain unchanged; accumulation of root records therefore does not demonstrate successful agent evolution.'
 else:evolution+='The retained changes, not merely proposed cards or longer reflection text, define the measured learned state.'
 independent=f"On the independent task the final state scores{z['metrics']['correct']}/467 ({fmt(z['metrics'])}\\%):{gf['correct']}/{gf['n']} guideline-following and{cf['correct']}/{cf['n']} counterfactual, with both members correct in{ip['both_correct']}/{ip['n']} strict pairs. The initial state scores{ind['trajectory'][0]['metrics']['correct']}/467. "
 if z['state_sha256']==ind['trajectory'][0]['state_sha256']:independent+='These are identical states sharing cached predictions. A flat curve provides no evidence of positive transfer.'
 rows=[]
 for k,n in [('grasp','GRASP'),('medagents','MedAgents'),('mdagents','MDAgents')]:
  for sp,ds in [('test','RxSafe'),('rxqa','RxQA')]:
   r=old[k][sp];rows.append(f"{n} & {ds} & {r['input_tokens']:,} & {r['output_tokens']:,} & {r['logical_cost_usd']:.3f}"+r'\\')
 for r,ds in [(x,'RxSafe'),(y,'RxQA'),(z['metrics'],'MedPIC')]:rows.append(f"RxRSIAgent & {ds} & {r['input_tokens']:,} & {r['output_tokens']:,} & {r['logical_cost_usd']:.3f}"+r'\\')
 compute=table('Logical inference use from successful saved response receipts. Reused receipts count as logical use; new billed usage is separately reported.','tab:compute','llrrr','Method & Task & Input tokens & Output tokens & Logical USD',rows)
 refs=REFERENCES.replace(r'\end{thebibliography}',r'\bibitem[Jin et al.(2020)]{medqa} Di Jin et al. 2020. What Disease does this Patient Have? A Large-scale Open Domain Question Answering Dataset from Medical Exams. \emph{arXiv:2009.13081}. \url{https://github.com/jind11/MedQA}.'+'\n'+r'\bibitem[Hou et al.(2026)]{medpic} Zhitian Hou, Yuhang Liu, Pengkai Wang, Zeyu Liu, Guanghao Zhu, Zheng Liu, Shuo Cai, Congkai Xie, Zhijie Sang, Kun Zeng, and Hongxia Yang. 2026. Evaluating Counterfactual Sensitivity to Patient Information in Medication-Safety Reasoning. \emph{arXiv:2608.03028}. \url{https://arxiv.org/abs/2608.03028}.'+'\n'+r'\end{thebibliography}')
 repl={'ABSTRACT_RESULTS':abstract,'DATA_TABLE':dt,'AGENT_TABLE':main,'NATIVE_TABLE':nt,'MAIN_RESULTS':maintext,'TRAJECTORY_TABLE':traj,'EVOLUTION_RESULTS':evolution,'UPDATER_TABLE':upd,'INDEPENDENT_RESULTS':independent,'SHORTCUT_TABLE':shortcut,'CONCLUSION_RESULTS':('The current trajectory does not demonstrate positive procedural evolution or superiority on both main tasks.' if ncard==0 else 'Retained module changes are evaluated separately from researcher repairs and numerical calibration.'),'COMPUTE_TABLE':compute,'AUDIT_DETAILS':f"The new audit checks{audit['source_spans_checked']:,} exact source spans across{audit['unique_evaluated_rows_audited']:,} distinct saved evaluation rows. The shared new successful-response ledger increment for updater development and evaluation is USD{audit['ledger_increment_usd_shared_37_38']:.3f}. Cross-process locks protect identical model requests. Source failures, query limits and incomplete clinical checks are retained as limitations.",'CLINICAL_METRICS_TABLE':clinical(),'REFERENCES':refs}
 prescription_gap,total_spend=render_research_assessment(read)
 repl.update(PRESCRIPTION_GAP=prescription_gap,TOTAL_SPEND=total_spend)
 failure_cases,mimic_status=render_failure_sections(read,table)
 repl.update(FAILURE_CASES=failure_cases,MIMIC_STATUS=mimic_status)
 repl.update(render_local_prescription(read,table))
 text=MANUSCRIPT
 for k,v in repl.items():text=text.replace('@@'+k+'@@',v)
 assert '@@' not in text
 # Normalize attached prose counts without rewriting model/metric names or citation keys.
 parts=re.split(r'(\\(?:texttt|url|citep|citet|label|ref)\{[^}]*\})',text)
 words='across|after|before|with|within|without|all|on|in|to|from|than|only|per|of|for|by|at|is|has|have|contains|contain|retains|retain|uses|using|process|frozen|initial|final|first|last|complete|compared|over|under|between|and|or|cases|case|round|rounds|call|calls|table|figure|source|score|scores|budget|allowance|cap|caps|test|evaluation|patients|items|covers|finds|answers|are|use|permit|paired|same|guard|proposal|January|October|Phase|other|reveal|produce|existing|sample|its|Another|mixes|designated|identifies|remains|fixing|regressing|reaches|reducing|changes|hours|hour|proposes|original|USD|adding|fixed|difference|cover|reach|identify|the|fixes|regresses|disjoint|different|an|baseline|Sonnet'
 for i in range(0,len(parts),2):
  parts[i]=re.sub(r'\b('+words+r')(?=\d)',r'\1 ',parts[i],flags=re.I)
  parts[i]=re.sub(r'\ba(?=\d)',r'a ',parts[i])
  parts[i]=re.sub(r'\b(RxSafe|RxQA|MedQA)(?=\d)',r'\1 ',parts[i])
  parts[i]=parts[i].replace('patient-cluster95','patient-cluster 95').replace("'s2,443","'s 2,443")
 text=''.join(parts)
 original=TARGET.read_text();prefix=original[:original.index(r'\documentclass')];start=prefix.index(r'\begin{filecontents*}[overwrite]{acl.sty}')+len(r'\begin{filecontents*}[overwrite]{acl.sty}')+1;end=prefix.index(r'\end{filecontents*}',start);provenance=read('paper/latex/v0.3/acl_template_provenance.json');assert hashlib.sha256((prefix[start:end].rstrip()+'\n').encode()).hexdigest()==provenance['acl_sty_sha256'];TARGET.write_text('\n'.join(line.rstrip() for line in (prefix+text.lstrip()).splitlines()).rstrip()+'\n')
 manifest={'snapshot':'2026-10-17 local prescriptions, controlled interface repair and frozen sequential evaluation','method':'RxRSIAgent','paper_path':str(TARGET.relative_to(ROOT)),'paper_sha256':sha(TARGET),'generator_sha256':sha(__file__),'failure_sections_sha256':sha(ROOT/'paper/failure_case_sections.py'),'research_assessment_sections_sha256':sha(ROOT/'paper/research_assessment_sections.py'),'local_prescription_sections_sha256':sha(ROOT/'paper/local_prescription_sections.py'),'narrative_sha256':sha(ROOT/'paper/acl_manuscript_text.py'),'sources':SOURCES,'acl_style_sha256':provenance['acl_sty_sha256'],'main_counts':{'rxsafe':rx,'rxqa':qa},'independent':z['metrics']['correct'],'historical_versions_in_manuscript':False,'calibration_is_separate_baseline':True};(TARGET.parent/'manuscript_evidence.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest['main_counts']))
if __name__=='__main__':run()
