"""Separate audited numerical preflight evidence from clinical precision effects."""
import hashlib
import json
from pathlib import Path

from report_rank_diagnostic import LABELS, ci

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    probe = json.loads((HERE/'results/precision_probe.json').read_text())
    audit = json.loads((HERE/'results/precision_probe_audit.json').read_text())
    assert audit['status']=='passed' and audit['probe_sha256']==sha(HERE/'results/precision_probe.json')
    assert audit['auditor_sha256']==sha(HERE/'audit_precision_probe.py')
    reports = {}
    for split in ['proposal','guard']:
        score_path=HERE/f'results/{split}_precision.json';audit_path=HERE/f'results/{split}_precision_audit.json'
        if not audit_path.exists():continue
        proof=json.loads(audit_path.read_text());assert proof['status']=='passed' and proof['summary_sha256']==sha(score_path)
        assert proof['auditor_sha256']==sha(HERE/'audit_precision.py')
        reports[split]=(json.loads(score_path.read_text()),proof)
    for lang in ['zh','en']:
        en=lang=='en'
        lines=['# '+('v0.32 frozen readout precision comparison' if en else 'v0.32 固定权重的读出精度对照'),'',
               ('## 1. What changes' if en else '## 1. 具体改变什么'),'',
               ('All three readouts share the same frozen backbone hidden states. Native uses the original quantized vocabulary projection. FP32 reconstructs only the two output-token rows from the same stored four-bit weights/scales/offsets and projects in float32. Re-rounded casts those FP32 logits to bfloat16 and back before softmax. Memory, tools, backbone/adapter weights and candidate templates remain unchanged.' if en else
                '三路读出共享同一次冻结骨干前向产生的隐藏状态。Native使用原量化词表投影；FP32用相同的四位权重、缩放和偏移，重建两个输出词元对应的行并用float32投影；Re-rounded把这些FP32 logits重新舍入为bfloat16后再计算概率。记忆、工具、骨干／适配器权重与候选模板均未更新。'),'',
               ('FP32 versus re-rounded isolates final-logit rounding within the new dense projection. Native versus FP32 also changes projection arithmetic, so its entire effect cannot be assigned to final rounding. Any benefit is a numerical implementation effect; it does not demonstrate learned RSI. The backbone remains quantized.' if en else
                'FP32与Re-rounded的差异用于隔离新稠密投影中最后一步logit舍入。Native与FP32还包含投影运算差异，因此不能把全部差异归因于最后一步舍入。若有收益，应归因于数值实现；这项对照本身不证明学得的RSI收益。骨干仍为量化模型。'),'',
               '[Protocol](precision_protocol.json) · [Frozen clinical implementation](results/precision_execution_lock.json) · [Earlier ranking diagnosis](RANKING_DIAGNOSTIC.'+lang+'.md)','',
               ('## 2. Completed engineering preflight' if en else '## 2. 已完成的工程核验'),'',
               ('Six actual frozen model states, two synthetic prompts each, twenty binary decisions per prompt. These twelve backbone case-forwards contain no clinical cases or target labels. Distinct-score counts below are numerical diagnostics, not prescription performance.' if en else
                '六个真实冻结模型状态，每个使用两条合成输入，每条含20个二元决策。这个阶段的12次骨干病例前向不含临床病例或真值标签。下表是不同分数的数量，属于数值诊断，不是处方性能。'),'',
               ('| State | Native: prompt 1 / 2 | FP32: prompt 1 / 2 | Re-rounded: prompt 1 / 2 |' if en else
                '| 状态 | Native：输入1／2 | FP32：输入1／2 | 重新舍入：输入1／2 |'), '|---|---:|---:|---:|']
        for state in probe['states']:
            values=state['unique_scores_per_synthetic_prompt']
            lines.append('| '+LABELS[state['state']][int(en)]+' | '+' | '.join('/'.join(str(n) for n in values[k]) for k in ['native','fp32_binary','fp32_rerounded'])+' |')
        residual=audit['maximum_numeric_residuals'];native_delta=max(s['native_vs_rerounded_max_probability_delta'] for s in probe['states'])
        lines+=['', (f"Independent byte-level extraction of the two embedding rows and NumPy reconstruction pass. Maximum float64-reference logit difference: {residual['dense_logit']:.3e}; probability difference: {residual['binary_probability']:.3e}; re-rounding difference: {residual['rounding']:.1f}. All six states have bfloat16 hidden states and native projection outputs. Native versus re-rounded probabilities differ by up to {native_delta:.5f}, confirming that the two projection implementations are not numerically identical." if en else
                     f"已直接读取模型文件中两个嵌入行的字节，并用NumPy独立重建。相对float64参照，logit最大差值为{residual['dense_logit']:.3e}，概率最大差值为{residual['binary_probability']:.3e}，重新舍入差值为{residual['rounding']:.1f}。六个状态的隐藏状态与原投影输出均为bfloat16。Native与重新舍入概率的最大差值达{native_delta:.5f}，说明两套投影实现并非数值完全一致。"),'',
                ('This preflight confirms that final-logit rounding can collapse distinct synthetic scores. It does not establish improved medication ranking, prescription F1 or clinical benefit.' if en else
                 '该预检确认，最后一步logit舍入可以把不同的合成分数压成同分。它尚不能证明药物排序、处方F1或临床效果提高。'),'',
                '[Preflight receipt](results/precision_probe.json) · [Independent raw-weight audit](results/precision_probe_audit.json) · [Synthetic scoring-pipeline audit](results/precision_pipeline_probe.json)','']
        if not reports:
            lines += [('## 3. Clinical comparison: awaiting independent audit' if en else '## 3. 病例对照：等待独立核验'),'',
                      ('The dedicated evaluator and independent auditor are implemented and frozen. The proposal run has been launched for all six states, ranked/permuted views, three shared-hidden-state readouts and both identity-based tie rules. No independently audited clinical precision score is available yet. Original model/threshold selection and test gates remain unchanged.' if en else
                       '专用评价器与独立复算器已实现并冻结。已启动全部六个状态在proposal病例上的评价，覆盖原排序／随机排序、三路共享隐藏状态的读出和两种基于药物身份的同分规则。尚无通过独立核验的病例精度对照成绩。原模型／阈值选择与测试门槛继续保持。'),'']
        for split,(data,proof) in reports.items():
            lines += [f'## 3. {split}: {data["cases"]} admissions / {data["patients"]} patients','',
                      ('Post-proposal descriptive development diagnosis, one training seed. Each scored policy selects eight candidate templates. All reference drugs are retained. No new threshold, checkpoint, arm or promotion is selected. Case-level AUROC omits only admissions without both positive and negative candidates; their F1 remains included.' if en else
                       '事后提出的描述性开发诊断，一个训练种子。每个被评分策略选择8个候选模板，保留全部真值药物。未重新选择阈值、检查点、试验组或接纳状态。病例内AUROC只排除候选中不同时含阳性和阴性的病例；这些病例仍参与F1。'),'']
            lines += [('### Main comparison: fixed eight medications' if en else '### 主要对照：固定选择8个药物'),'',
                      ('Cells show drug/core-order micro-F1. The primary drug-identity-hash tie rule is used here; the complete tables below retain the re-rounded readout, both tie rules and paired intervals.' if en else
                       '表格为药物／核心订单micro-F1，使用预先声明的药物身份哈希同分规则。下文保留重新舍入读出、两种同分规则和配对区间。'),'',
                      '| State | Ranked native | Ranked FP32 | Permuted native | Permuted FP32 |', '|---|---:|---:|---:|---:|']
            primary=data['panels']['drug_sha256']
            for name in list(data['state_versions'])+['original_retrieval_top8']:
                cells=[LABELS[name][int(en)]]
                for kind in ['ranked','permuted']:
                    for readout in ['native','fp32_binary']:
                        m=primary[kind][readout]['methods'][name]
                        cells.append(f"{m['drug_micro_f1']:.5f}/{m['core_order_micro_f1']:.5f}")
                lines.append('| '+' | '.join(cells)+' |')
            lines += ['',('The retrieval row is unchanged across readouts. These are shared-case implementation contrasts; a higher F1 here is not evidence that an agent learned or evolved.' if en else
                           '检索对照在不同读出下保持相同。这是同病例的实现对照；此处F1提高不等于agent学到了新知识或发生了进化。'),'']
            if split=='proposal':
                m=primary['ranked']['fp32_binary']['methods']['teacher_uniform'];control=primary['ranked']['fp32_binary']['methods']['original_retrieval_top8']
                delta=primary['ranked']['fp32_binary']['contrasts_vs_retrieval']['teacher_uniform']['drug']
                low,high=delta['micro_f1_patient_ci95']
                lines += [('**Interpretation:** FP32 removes every cutoff tie in this panel, but the six neural states still have 0% exact drug-set agreement after candidate permutation. Only teacher-prefix/uniform loss in the ranked view has a drug-F1 point estimate above retrieval: '
                           f"{m['drug_micro_f1']:.5f} versus {control['drug_micro_f1']:.5f}, paired difference {delta['micro_f1_difference']:+.5f} [{low:+.5f}, {high:+.5f}]. Its order F1 remains lower ({m['core_order_micro_f1']:.5f} versus {control['core_order_micro_f1']:.5f}). Every permuted-view neural configuration remains below retrieval in both endpoints. These exploratory intervals do not establish superiority. Higher readout precision does not resolve the candidate-position failure." if en else
                           '**结果解读：** FP32消除了本组全部选取边界同分，但六个神经状态在候选打乱后，药物集合完全一致率仍为0%。只有真实前缀／普通损失在原排序下的药物F1点估计高于检索：'
                           f"{m['drug_micro_f1']:.5f} 对 {control['drug_micro_f1']:.5f}，配对差值{delta['micro_f1_difference']:+.5f} [{low:+.5f}, {high:+.5f}]；订单F1仍较低（{m['core_order_micro_f1']:.5f} 对 {control['core_order_micro_f1']:.5f}）。所有随机排序神经配置的两个端点均低于检索。探索性区间不能支持优越性结论。提高读出精度没有解决候选位置依赖。"),'']
            lines += [('### Position dependence after the precision change' if en else '### 改变精度后的位置依赖'),'',
                      ('Spearman correlations compare drug-identity alignment with unchanged display slots. Agreement is the fraction of admissions whose complete top-eight drug set is identical after candidate permutation; the primary tie rule is used.' if en else
                       'Spearman相关分别按药物身份对齐和按展示槽位对齐。一致率为候选打乱后完整前8药物集合相同的病例比例，使用主要同分规则。'),'',
                      '| State | Readout | Drug-identity ρ | Display-slot ρ | Exact set agreement |', '|---|---|---:|---:|---:|']
            for name in data['state_versions']:
                for readout in ['native','fp32_binary','fp32_rerounded']:
                    a=data['score_rank_alignment'][readout]['permuted'][name]
                    vals=[a[key]['mean_spearman'] for key in ['drug_identity_aligned','same_display_slots_unaligned']]
                    cells=[f'{v:.5f}' if v is not None else 'undefined' for v in vals]
                    agree=data['top8_view_invariance']['drug_sha256']['permuted'][readout][name]['drug_set_agreement']
                    lines.append('| '+LABELS[name][int(en)]+' | '+readout+' | '+' | '.join(cells)+f' | {agree:.1%} |')
            lines += ['']
            for rule,views in data['panels'].items():
                lines += ['### '+rule,'','| View | State | Readout | Drug F1 | Core-order F1 | AUROC (n) | Mean distinct scores | Cutoff tie cases |','|---|---|---|---:|---:|---:|---:|---:|']
                for kind,reads in views.items():
                    for name in data['state_versions']:
                        for readout,panel in reads.items():
                            m=panel['methods'][name];a=m['within_case_auroc_mean'];cell=f"{a:.5f} ({m['within_case_auroc_eligible_cases']})" if a is not None else 'undefined'
                            lines.append(f"| {kind} | {LABELS[name][int(en)]} | {readout} | {m['drug_micro_f1']:.5f} | {m['core_order_micro_f1']:.5f} | {cell} | {m['mean_unique_scores']:.2f} | {m['boundary_tie_cases']} |")
                    m=reads['native']['methods']['original_retrieval_top8']
                    lines.append(f"| {kind} | {LABELS['original_retrieval_top8'][int(en)]} | — | {m['drug_micro_f1']:.5f} | {m['core_order_micro_f1']:.5f} | — | — | — |")
                lines+=['','| View | State | Contrast | Drug Δ [95% CI] | Core-order Δ [95% CI] |','|---|---|---|---:|---:|']
                for kind,states in data['readout_contrasts'][rule].items():
                    for name,contrasts in states.items():
                        for label,value in contrasts.items():lines.append(f"| {kind} | {LABELS[name][int(en)]} | {label} | {ci(value['drug'])} | {ci(value['core_order'])} |")
                lines += ['']
            maximum=max(v['max_native_probability_difference_from_parent'] for states in data['native_replay'].values() for v in states.values())
            changed=sum(v['native_top8_changed_from_parent_cases'] for states in data['native_replay'].values() for v in states.values())
            lines += [(f"Native replay maximum probability difference from the parent cache: {maximum:.7f}; changed native top-eight sets: {changed}. Independently replayed shared hidden states: {proof['shared_hidden_state_receipts_replayed']}; completed actual case-forwards: {proof['completed_actual_case_forwards']}; unresolved forward attempts: {proof['unresolved_forward_attempts']}. All three readouts share each backbone forward. The auditor reexecutes the dense readout, rounding and metric arithmetic, not the backbone/native projection kernel." if en else
                       f"原生读出重放相对父缓存的最大概率差为{maximum:.7f}，原生前8集合改变{changed}组。已独立重放{proof['shared_hidden_state_receipts_replayed']}组共享隐藏状态；实际完成{proof['completed_actual_case_forwards']}次病例前向；仍未确认完成的前向尝试{proof['unresolved_forward_attempts']}次。三路读出共享每次骨干前向。审计重执行稠密读出、舍入和指标运算，未重跑骨干／原生投影内核。"),'',
                      ('All intervals use 4,000 paired patient draws without multiplicity adjustment or seed-population uncertainty. Full retrieval contrasts, identity alignment, set agreement, source hashes and costs remain in the machine-readable summary.' if en else
                       '全部区间使用4,000次患者配对重采样，未作多重比较校正，也不包含训练种子总体的不确定性。完整检索差值、身份对齐、集合一致性、源哈希与成本保留在机器可读汇总中。'),'',
                      f'[Full scores and costs](results/{split}_precision.json) · [Independent recount](results/{split}_precision_audit.json)','']
        (HERE/f'PRECISION.{lang}.md').write_text('\n'.join(lines))
    print(json.dumps({'synthetic_probe_audited':True,'clinical_audited_splits':list(reports),'reports_written':['zh','en']}))


if __name__=='__main__':main()
