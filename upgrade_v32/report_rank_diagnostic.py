"""Bilingual report of the independently recounted fixed-cardinality diagnosis."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LABELS = {
    'frozen_base': ('基础模型', 'Frozen base'),
    'original_failed_adapter': ('原失败适配器', 'Original failed adapter'),
    'teacher_uniform': ('真实前缀／普通损失', 'GT prefix / uniform'),
    'zero_uniform': ('全零前缀／普通损失', 'Zero prefix / uniform'),
    'teacher_balanced': ('真实前缀／平衡损失', 'GT prefix / balanced'),
    'zero_balanced': ('全零前缀／平衡损失', 'Zero prefix / balanced'),
    'original_retrieval_top8': ('直接检索前8', 'Original retrieval top-8'),
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ci(value):
    low, high = value['micro_f1_patient_ci95']
    return f"{value['micro_f1_difference']:+.5f} [{low:+.5f}, {high:+.5f}]"


def main():
    reports = {}
    for split in ['proposal', 'guard']:
        path = HERE / f'results/{split}_rank_diagnostic.json'
        audit_path = HERE / f'results/{split}_rank_diagnostic_audit.json'
        if not audit_path.exists():
            continue
        proof = json.loads(audit_path.read_text())
        assert proof['status'] == 'passed' and proof['summary_sha256'] == sha(path)
        assert proof['auditor_sha256'] == sha(HERE / 'audit_rank_diagnostic.py')
        reports[split] = (json.loads(path.read_text()), proof)
    for lang in ['zh', 'en']:
        en = lang == 'en'
        lines = ['# ' + ('v0.32 fixed-cardinality ranking diagnosis' if en else 'v0.32 固定开药数量的排序诊断'), '',
                 ('## 1. Question and scope' if en else '## 1. 这次回答什么'), '',
                 ('Does calibration hide useful medication ranking? Every state selects exactly eight of the same twenty candidate order templates using its saved probabilities. The original retrieval top-eight receives the same eight-drug output budget. Targets are used only for scoring. No training, model forward pass, API request, checkpoint/threshold selection, or test access is added.' if en else
                  '空输出修复后，模型是否已经学会选择更合适的药物？这次让每个模型都根据已保存的概率，从相同20个候选中恰好选择8个，与原检索前8个使用相同开药数量。真值只参与评分。没有新增训练、模型推理、API请求、检查点／阈值选择，也未打开测试集。'), '',
                 ('This diagnosis was specified and committed after the parent proposal outcomes were known, before computing these new endpoints. It is a post-proposal development analysis, not an original preregistered endpoint or independent confirmation. The original fixed-0.5 and calibrated results remain intact. Fixed eight-drug output is a diagnostic, not a clinical prescription-count rule.' if en else
                  '本诊断在看到原proposal结果后提出，协议和实现先提交，再计算新端点。它属于事后提出的开发分析，不是原实验预先登记的端点或独立确认。原固定0.5及校准结果保持原样。“每例8个”只用于隔离排序能力，不是临床开药数量规则。'), '',
                 ('Exact ties use a SHA-256 key derived solely from drug identity. Lexical drug-name order is a declared sensitivity analysis. Neither rule uses target labels, display position, or retrieval rank. Both are invariant to candidate permutation when scores are identical.' if en else
                  '同分时，主分析按药物身份的SHA-256键排序；另报告按药名词典顺序处理同分的敏感性分析。两种规则均不使用真值、展示位置或检索名次；同一药物分数不变时，候选换序不会改变同分处理。'), '',
                 '[Protocol](rank_diagnostic_protocol.json) · [Frozen implementation](results/rank_diagnostic_lock.json) · [Original repair experiment](RESULTS.' + lang + '.md)', '']
        for split, (d, audit) in reports.items():
            lines += [f'## 2. {split}: {d["cases"]} admissions / {d["patients"]} patients', '']
            all_panels = [p for views in d['panels'].values() for p in views.values()]
            if all(m['drug_micro_f1'] <= p['methods']['original_retrieval_top8']['drug_micro_f1']
                   and m['core_order_micro_f1'] <= p['methods']['original_retrieval_top8']['core_order_micro_f1']
                   for p in all_panels for name, m in p['methods'].items() if name != 'original_retrieval_top8'):
                lines += [('**Finding:** no neural state exceeds retrieval in drug or core-order F1 in any reported view under either tie rule. Fixing the number of emitted drugs does not recover a winning repair.' if en else
                           '**结论：** 在全部已报告排序和两种同分规则下，没有神经模型的药物或核心订单F1超过检索。固定开药数量后仍未形成胜出的修复。'), '']
            for rule, views in d['panels'].items():
                lines += ['### ' + ('Primary: drug-identity hash ties' if rule == 'drug_sha256' and en else
                                    '主分析：药物身份哈希处理同分' if rule == 'drug_sha256' else
                                    'Sensitivity: lexical drug-name ties' if en else '敏感性：药名词典顺序处理同分'), '',
                          ('| View | Method | Drug F1 | Core-order F1 | Within-case AUROC (eligible n) | Cutoff ties / cases |' if en else
                           '| 候选排序 | 方法 | 药物F1 | 核心订单F1 | 病例内AUROC（有效病例数） | 截断同分病例数 |'),
                          '|---|---|---:|---:|---:|---:|']
                for kind, panel in views.items():
                    for name, m in panel['methods'].items():
                        a = m.get('within_case_auroc_mean')
                        ties = m.get('boundary_tie_cases')
                        lines.append(f"| {kind} | {LABELS[name][int(en)]} | {m['drug_micro_f1']:.5f} | {m['core_order_micro_f1']:.5f} | {a:.5f} ({m['within_case_auroc_eligible_cases']})" + f" | {ties}/{d['cases']} |" if a is not None else
                                     f"| {kind} | {LABELS[name][int(en)]} | {m['drug_micro_f1']:.5f} | {m['core_order_micro_f1']:.5f} | — | — |")
                lines += ['', ('AUROC compares positive and negative candidates within each admission, with half credit for ties. Cases without both classes are excluded only from AUROC; their prescriptions remain in F1. The machine-readable summary retains eligible/excluded counts, precision, recall and all paired contrasts. F1 retains reference medications absent from the twenty candidates. Core-order F1 matches drug, route, dose value and dose unit, using the parent complete-tuple denominator.' if en else
                               '病例内AUROC比较同一病例的阳性与阴性候选，同分计半分；没有两类候选的病例只从AUROC中排除，仍计入处方F1。机器可读汇总保留纳入／排除数、精确率、召回率及全部配对差值。F1分母保留20个候选之外的真值药物。核心订单F1要求药物、途径、剂量值和单位同时匹配，沿用原完整字段订单分母。'), '']
            lines += [('### Score identity and display position' if en else '### 分数跟随药物还是展示位置'), '',
                      ('| Changed view | Model | Identity-aligned Spearman | Same-slot Spearman | Exact top-8 set agreement | Top-8 Jaccard |' if en else
                       '| 变化后的排序 | 模型 | 按药物身份对齐的相关性 | 按展示位置对齐的相关性 | 前8药物集合完全一致率 | 前8集合Jaccard |'),
                      '|---|---|---:|---:|---:|---:|']
            for kind, states in d['score_rank_alignment'].items():
                for name, values in states.items():
                    a = values['drug_identity_aligned']['mean_spearman']
                    b = values['same_display_slots_unaligned']['mean_spearman']
                    agreement = d['top8_view_invariance']['drug_sha256'][kind][name]
                    fmt = lambda x: f'{x:.5f}' if x is not None else 'undefined'
                    lines.append(f"| {kind} | {LABELS[name][int(en)]} | {fmt(a)} | {fmt(b)} | {agreement['drug_set_agreement']:.1%} | {agreement['mean_jaccard']:.5f} |")
            lines += ['', ('Correlations are within-case averages. Identity alignment compares the same medications; same-slot alignment compares the same displayed positions, usually containing different drugs. The latter is a diagnostic of positional dependence, not proof of its causal origin. Undefined constant-vector correlations are counted in the summary. Top-eight set agreement cannot be inflated by all-empty or all-twenty outputs.' if en else
                           '相关性为病例内Spearman的平均值。身份对齐比较同一药物；位置对齐比较同一展示位置，该位置通常已经换成另一种药物。较高的位置相关性与位置依赖一致，但不单独证明其成因。恒定分数的相关性记为未定义，数量在汇总中保留。固定前8的集合一致性不会被“全空”或“全选20个”抬高。'), '']
            for rule, views in d['panels'].items():
                lines += [('### Paired differences: ' if en else '### 配对差值：') + rule, '',
                          '| View | Contrast | Drug Δ [95% CI] | Core-order Δ [95% CI] |', '|---|---|---:|---:|']
                for kind, panel in views.items():
                    for name, value in panel['contrasts'].items():
                        lines.append(f"| {kind} | {name} | {ci(value['drug'])} | {ci(value['core_order'])} |")
                lines += ['']
            lines += [('Intervals use 4,000 paired patient resamples, without multiplicity correction. They describe this one-seed development sample; they do not include training-seed uncertainty. All states and both tie rules are retained without selecting a new winner.' if en else
                       '区间使用4,000次患者聚类配对重采样，未作多重比较校正，只描述这一训练种子的开发样本，不包含训练种子不确定性。全部模型与两种同分规则均保留，不据此选择新模型。'), '',
                      (f"**Independent audit:** {audit['case_probability_bindings_recounted']:,} probability bindings and {audit['case_selections_recounted']:,} case selections; order metrics, within-case AUROC, rank alignment and paired intervals independently recounted. No optimizer or neural-forward replay." if en else
                       f"**独立核验：** 复核{audit['case_probability_bindings_recounted']:,}个概率绑定、{audit['case_selections_recounted']:,}组病例选择，并独立复算订单指标、病例内AUROC、排序相关性和配对区间。没有重跑优化器或神经前向。"), '',
                      f'[Machine-readable results](results/{split}_rank_diagnostic.json) · [Independent audit](results/{split}_rank_diagnostic_audit.json)', '']
        lines += [('## 3. Next implementation decision' if en else '## 3. 这对下一次改进意味着什么'), '',
                  ('Threshold tuning alone has not resolved the ranking failure. Frequent exact cutoff ties also require a separate numerical-readout precision check before attributing them to the learned representation. A future candidate-specific readout should preserve drug identity across permutations and be compared with the same retrieval evidence and output budget. These are next investigations, not implemented or validated repairs. Existing multi-round studies and their selection gates continue unchanged.' if en else
                   '仅调阈值仍未解决排序失败。截断位置频繁同分还需要单独检查数值读出精度，才能判断是否源于学到的表示。后续逐药物读出应在候选换序时保留药物身份，并与相同检索证据、相同输出预算的对照比较。这里列的是下一步调查方向，尚未实现或验证为有效修复。现有多轮试验及选择门槛继续保持。'), '']
        if 'guard' not in reports:
            lines += [('The original guard is still closed or awaiting its parent audit. No guard score is available for this diagnostic.' if en else
                       '原guard尚未开放或尚待父实验核验，本诊断没有guard分数。'), '']
        (HERE / f'RANKING_DIAGNOSTIC.{lang}.md').write_text('\n'.join(lines))
    print(json.dumps({'audited_splits': list(reports), 'reports_written': ['en', 'zh']}))


if __name__ == '__main__':
    main()
