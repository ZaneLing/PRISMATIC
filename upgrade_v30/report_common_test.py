"""Publish the audited common comparison; never fill unfinished table cells."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def value(m,key):
    a=m[key];return f"{a['mean']:.5f} ± {a['seed_sd']:.5f}" if a['seed_sd'] is not None else f"{a['mean']:.5f}"
def main():
    path=HERE/'results/common_test_summary.json';audit=HERE/'results/common_test_audit.json';ready=False
    if path.exists() and audit.exists():
        a=json.loads(audit.read_text());ready=a['status']=='passed' and a['source_report_sha256']==sha(path) and a['auditor_sha256']==sha(HERE/'audit_program_tests.py')
    for lang in ('en','zh'):
        text=('# Common frozen ATC-L4 method comparison\n\n' if lang=='en' else '# 同一冻结ATC-L4测试集的方法主表\n\n')
        text+=('## Protocol and interpretation\n\nExactly 2,422 test visits from 890 patients, with separate 271-class full and 219-class molecular panels. All methods share source partition, observed inputs, case order and the within-panel label space. The source mapping covers 27.23% of selected prescription rows; these are retrospective mapped-class sets, not complete prospective prescriptions. Known earlier test-patient overlap makes this exploratory. No paper-reported score is mixed into the executed table.\n\n' if lang=='en' else '## 协议与解释范围\n\n同一890位患者的2,422次测试就诊，分别报告271类完整映射空间与219类分子覆盖空间。所有方法共享源划分、可见输入、病例顺序和各表内药物空间。源映射覆盖所选处方行的27.23%；本任务为回顾性映射药物集合，不是完整前瞻处方。与早期测试患者存在已知交叉，因此属于探索性结果。不混入论文原报分数。\n\n')
        text+=('v29/v30 fit policies on 5,692 patients and reserve 1,423 for rule verification. v27 methods follow their published adaptations and registered budgets. Exposure to the source training pool is shared, while optimization and API/FLOP budgets differ. v30 reuses the exact v29 fits. All thresholds, rules and checkpoint choices freeze before this evaluation.\n\n' if lang=='en' else 'v29/v30用5,692人拟合策略，另留1,423人验证规则；v27方法遵循已登记的作者代码适配和预算。源训练池一致，优化、API及计算量不同；v30原样复用v29拟合。所有阈值、规则和检查点选择先冻结，再执行本表。\n\n')
        if not ready:
            text+=('**Status: waiting for every frozen selection and independent audit. No test score is published yet.**\n\n' if lang=='en' else '**状态：等待全部选择冻结和独立核验；尚未发布测试分数。**\n\n')
        else:
            report=json.loads(path.read_text())
            for panel,z in report['panels'].items():
                text+=f'## {panel}: proposal-selected methods\n\n| Method | Runs | Patient F1 | Patient Jaccard | Micro F1 | Empty fraction |\n|---|---:|---:|---:|---:|---:|\n'
                selected=z['endpoints']['selected']
                for method,r in selected['v27_methods'].items():
                    m=r['metrics'];text+=f"| v27 / {method} | {r['runs']} | "+' | '.join(value(m,k) for k in ['patient_f1','patient_jaccard','micro_f1','empty_prediction_fraction'])+' |\n'
                for method,m in selected['methods'].items():text+=f'| {method} | 3 | '+' | '.join(value(m,k) for k in ['patient_f1','patient_jaccard','micro_f1','empty_prediction_fraction'])+' |\n'
                text+=f'\n### {panel}: raw final-round endpoints\n\n| Method | Patient F1 | Patient Jaccard | Micro F1 |\n|---|---:|---:|---:|\n'
                for method,m in z['endpoints']['final']['methods'].items():text+=f'| {method} | '+' | '.join(value(m,k) for k in ['patient_f1','patient_jaccard','micro_f1'])+' |\n'
                text+=('\n### Prespecified paired comparisons\n\n' if lang=='en' else '\n### 预先登记的配对对照\n\n')
                text+='| Endpoint | Comparison | Patient F1 difference [95% CI] |\n|---|---|---:|\n'
                for endpoint,e in z['endpoints'].items():
                    comparisons=dict(e['within_program_contrasts'])
                    for own,comparators in e.get('versus_v27',{}).items():
                        comparisons.update({own+'_minus_v27-'+m:v for m,v in comparators.items()})
                    for name,d in comparisons.items():
                        a=d['patient_f1'];lo,hi=a['patient_ci95'];text+=f"| {endpoint} | {name} | {a['difference']:.5f} [{lo:.5f}, {hi:.5f}] |\n"
            text+=('\nIntervals are descriptive patient-cluster resamples conditional on observed seeds, without multiplicity correction. Raw/accepted five-round curves, improved/regressed visit counts, all set metrics and DDI source coverage remain in the machine-readable report. Increased set F1 is not a clinical safety judgement.\n\n' if lang=='en' else '\n区间为条件于已执行种子的患者聚类重抽样，属于未校正多重比较的描述性结果。机器可读报告保留原始／接纳五轮曲线、改善／退化就诊数、全部集合指标及DDI来源覆盖。集合F1上升不等于临床安全改善。\n\n')
        text+='[Frozen test addendum](common_test_addendum.json) · [Test gate](common_test_gate.py)\n'
        if ready:text+='\n[Complete scores and curves](results/common_test_summary.json) · [Independent reexecution audit](results/common_test_audit.json)\n'
        (HERE/f'COMMON_TEST.{lang}.md').write_text(text)
if __name__=='__main__':main()
