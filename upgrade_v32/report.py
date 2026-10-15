# -*- coding: utf-8 -*-
"""Publish only independently recounted repair scores; retain every registered arm."""
import hashlib
import json
from pathlib import Path

from evaluation_gate import check

HERE = Path(__file__).resolve().parent
PRIVATE = Path.home() / 'Desktop/MedTreeBench/dataset/restricted/prismatic-v32'
METHODS = ['frozen_base', 'original_failed_adapter', 'teacher_uniform', 'zero_uniform',
           'teacher_balanced', 'zero_balanced', 'original_retrieval_top8', 'all20_candidate_tools']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audited(split):
    path = HERE / f'results/{split}_summary.json'
    receipt = HERE / f'results/{split}_audit.json'
    if not path.exists() or not receipt.exists():
        return None
    audit = json.loads(receipt.read_text())
    assert audit['status'] == 'passed'
    assert audit['summary_sha256'] == sha(path)
    assert audit['auditor_sha256'] == sha(HERE / 'audit_evaluation.py')
    assert audit['evaluation_lock_sha256'] == sha(PRIVATE / 'evaluation_lock.json')
    assert audit['frozen_thresholds_sha256'] == sha(PRIVATE / 'frozen_thresholds.json')
    return json.loads(path.read_text())


def number(value):
    return 'N/A' if value is None else f'{value:.5f}'


def main():
    spec = json.loads((HERE / 'protocol.json').read_text())
    completed = {}
    for arm in spec['arms']:
        path = PRIVATE / arm / 'training_complete.json'
        if path.exists():
            z = json.loads(path.read_text())
            assert sha(PRIVATE / arm / 'adapter/adapters.safetensors') == z['adapter_sha256']
            completed[arm] = {'optimizer_steps': z['optimizer_steps'], 'seconds': z['seconds'],
                              'adapter_sha256': z['adapter_sha256']}
    reports = {split: audited(split) for split in ['proposal', 'guard']}
    gates = {split: check(split) for split in reports}
    progress = {'completed_optimizer_fits': len(completed), 'registered_fits': 4,
                'completed_arms': completed, 'audited_splits': [s for s, z in reports.items() if z],
                'gates': gates, 'clinical_scores_require_independent_recount': True,
                'api_calls': 0, 'old_test_inference': False}
    (HERE / 'results/progress.json').write_text(json.dumps(progress, indent=2) + '\n')
    for lang in ['en', 'zh']:
        en = lang == 'en'
        lines = [('# v0.32 — Controlled binary-decision repair: execution and results' if en else
                  '# v0.32：二元处方决策受控修复——执行与结果'), '',
                 ('## 1. What this experiment tests' if en else '## 1. 本实验回答什么'), '',
                 ('The failed first v31 update emits valid all-zero prescriptions. This four-arm pilot tests training-prefix exposure and class imbalance with the same 400 training examples and 100 optimizer steps per arm. All four new adapters, the frozen backbone and the failed adapter use the same label-free zero-prefix scorer. Original retrieval top-8 and all-20 candidates are direct controls.' if en else
                  'v31 首次更新生成了格式合法、内容全零的处方。本试验用相同 400 例、每组 100 步，交叉检验训练前缀和类别不平衡。四个新适配器、基础模型和原失败适配器均采用不含标签的全零前缀评分；另保留原检索前 8 个和全部 20 个候选的直接对照。'), '',
                 ('A fixed 0.5 threshold measures the uncalibrated decision behavior. A second endpoint calibrates one global threshold on the 100 proposal admissions, shared across ranked and permuted views. It applies the same calibration to every neural state. Calibration-only gains are reported separately from weight-update contrasts. Both endpoints retain drug precision, recall and mean prescription size alongside F1 and empty outputs, so selecting more medications cannot be mistaken for an unqualified improvement.' if en else
                  '固定 0.5 阈值反映未经校准的决策表现。另一组结果在 100 例 proposal 上选择一个全局阈值，两种候选排序共享该值；六个模型状态接受相同校准。单纯调阈值的收益与更新权重的收益分别报告。两组均在 F1、空输出率之外展示药物精确率、召回率和平均开药数，避免把多选药物直接当成全面改善。'), '',
                 ('## 2. Actual completion' if en else '## 2. 真实完成情况'), '',
                 f"- {'Completed fits' if en else '已完成训练'}: **{len(completed)}/4**",
                 f"- {'Independently audited score panels' if en else '已独立复算成绩分组'}: **{', '.join(progress['audited_splits']) or ('none yet' if en else '暂无')}**",
                 f"- {'API requests' if en else 'API 请求'}: **0**", '',
                 '| Arm | Steps | Fit seconds | Adapter SHA-256 (prefix) |', '|---|---:|---:|---|']
        for arm in spec['arms']:
            z = completed.get(arm)
            lines.append(f"| {arm} | {z['optimizer_steps'] if z else 'pending'} | {z['seconds']:.1f} | {z['adapter_sha256'][:12]} |" if z else f'| {arm} | pending | — | — |')
        lines += ['', ('Fit completion is checked against the saved original adapter hash. A separate audit reconstructs all 8,000 binary labels and checks all four training receipts before proposal inference. The scoring preflight passed 120 synthetic case/probability bindings, all threshold choices, source recounting and byte-identical resume; these synthetic checks are not clinical results.' if en else
                       '训练完成状态与原始适配器哈希逐项核对。独立核验重建全部 8,000 个二元标签，并在四组训练回执均通过后开放 proposal 评分。评分预检已通过 120 个合成病例／概率绑定、完整阈值选择、源数据复算及逐字节一致的断点恢复；这些合成检查不属于临床实验成绩。'), '']
        if 'training_audit_sha256' in gates['proposal']['proof']:
            lines += [('**Training audit passed for all four arms.** It reconstructed the 8,000 targets (1,604 positives), checked the 100-step training logs, verified 3,670,016 finite adapter parameters and a nonzero LoRA update per arm, and confirmed no patient overlap between the 400 training examples and 100 proposal cases. Optimizer trajectories were not independently replayed. Proposal inference is now permitted; completed training is not evidence of improved prescribing.' if en else
                       '**四组训练均通过独立核验。** 已重建 8,000 个目标（其中 1,604 个阳性），逐组核对 100 步训练日志，确认 3,670,016 个适配器参数均为有限值、LoRA 存在非零更新，并确认 400 个训练样本与 100 个 proposal 病例之间没有患者重叠。该核验没有独立重跑优化轨迹。目前已开放 proposal 推理；训练完成不等于处方效果已经提高。'), '',
                      '[Training audit](results/training_audit.json)', '']
        for split, z in reports.items():
            lines += [f"## {'3' if split == 'proposal' else '4'}. {split}", '']
            if z is None:
                lines += [('No independently audited score is available. Pending prerequisites: ' if en else '尚无通过独立复算的成绩。当前前置条件：') + ', '.join(gates[split]['pending'] or ['evaluation_and_recount']) + '.', '']
                continue
            lines += [f"{z['cases']} admissions / {z['patients']} patients. " + ('Proposal is used to select thresholds; the reused guard is report-only development data. This is not an untouched test.' if en else 'proposal 用于选择阈值；复用的 guard 只报告开发结果，不是未经查看的测试集。'), '']
            fixes = list(spec['arms'])
            if all(panel['methods'][arm]['drug_micro_f1'] < panel['methods']['original_retrieval_top8']['drug_micro_f1']
                   and panel['methods'][arm]['core_order_micro_f1'] < panel['methods']['original_retrieval_top8']['core_order_micro_f1']
                   for views in z['endpoints'].values() for panel in views.values() for arm in fixes):
                lines += [('**Main finding:** every new repair has lower drug and core-order F1 point estimates than direct retrieval top-8 in every reported view, both at threshold 0.5 and after the registered calibration. Reduced empty outputs do not establish a winning repair. All registered paired intervals are reported in the tables below.' if en else
                           '**主要发现：** 在全部已报告排序、固定 0.5 阈值及已登记校准下，四种新修复的药物和核心订单 F1 点估计都低于直接检索前 8 个候选。空输出减少仍未形成胜出的修复；全部配对区间保留在下方。'), '']
            calibrated = z['endpoints']['proposal_calibrated']
            if all(panel['methods']['zero_balanced']['mean_predicted_drugs'] >= 19.5 for panel in calibrated.values()):
                description = '; '.join(f"{kind}: {panel['methods']['zero_balanced']['mean_predicted_drugs']:.2f} / 20, precision {panel['methods']['zero_balanced']['drug_precision']:.5f}" for kind, panel in calibrated.items())
                lines += [('**Over-selection after calibration:** zero-prefix/balanced selects nearly every candidate (' + description + '). Its high nonempty position agreement can therefore reflect nearly full candidate sets, not improved discrimination. The all-20 control makes this behavior visible.' if en else
                           '**校准后的过度选择：** 全零前缀／平衡损失几乎选中全部候选（' + description + '）。较高的非空位置一致性因此可能来自几乎全选，不能证明区分药物的能力改善；全部 20 个候选直接输出的对照揭示了这一点。'), '']
            boundary = [name for name, choice in z['selected_thresholds'].items() if choice['threshold'] in [.01, .99]]
            if boundary:
                lines += [('**Calibration boundary:** ' + ', '.join(boundary) + ' select an endpoint of the fixed 0.01–0.99 grid. These are the registered grid results, not evidence of a globally optimal threshold or exhaustive ordinary calibration. The grid and selected values remain frozen.' if en else
                           '**校准边界：** ' + ', '.join(boundary) + ' 选择了固定 0.01–0.99 网格的端点。这里报告的是已登记网格结果，不代表全局最优阈值或穷尽普通校准方案；网格与选择保持冻结。'), '']
            figure_path = HERE / f'results/{split}_figure.json'
            if figure_path.exists():
                fig = json.loads(figure_path.read_text())
                assert fig['summary_sha256'] == sha(HERE / f'results/{split}_summary.json')
                assert fig['audit_sha256'] == sha(HERE / f'results/{split}_audit.json')
                assert fig['script_sha256'] == sha(HERE / 'plot_results.py')
                assert fig['png_sha256'] == sha(HERE / f'{split}_repair.png')
                lines += [f'![Fixed and calibrated scores for every method]({split}_repair.png)', '',
                          ('Points show the same frozen model before/after ordinary threshold calibration. All controls remain visible; uncertainty and precision/recall are reported in the tables below.' if en else
                           '每对点表示同一冻结模型采用固定阈值／普通校准后的表现，保留全部对照；配对不确定性及精确率／召回率见下表。'), '']
            for endpoint, views in z['endpoints'].items():
                lines += [f'### {endpoint}', '', '| View | Method | Threshold | Drug micro-F1 | Core-order micro-F1 | Empty % | Binary AUROC |', '|---|---|---:|---:|---:|---:|---:|']
                for kind, panel in views.items():
                    for name in METHODS:
                        m = panel['methods'][name]
                        lines.append(f"| {kind} | {name} | {number(m.get('threshold'))} | {m['drug_micro_f1']:.5f} | {m['core_order_micro_f1']:.5f} | {100*m['empty_fraction']:.1f} | {number(m.get('binary_auroc'))} |")
                lines += ['', ('#### Missed and extra recorded medications' if en else '#### 相对记录处方的漏项与额外药物'), '',
                          '| View | Method | Drug precision | Drug recall | Mean predicted drugs |', '|---|---|---:|---:|---:|']
                for kind, panel in views.items():
                    for name in METHODS:
                        m = panel['methods'][name]
                        lines.append(f"| {kind} | {name} | {m['drug_precision']:.5f} | {m['drug_recall']:.5f} | {m['mean_predicted_drugs']:.2f} |")
                lines += ['', ('Precision and recall use the recorded medication set, including ground-truth medications outside the candidate list. Mean prescription size makes over-selection visible alongside the empty-output rate. An extra medication relative to this reference is not by itself a clinical adjudication of inappropriate prescribing. These are existing independently recounted metrics; they do not change threshold or model selection.' if en else
                               '精确率和召回率以记录处方为参照，召回率分母保留候选之外的真值药物。平均开药数与空输出率一起展示，便于发现过度选择。相对记录处方的额外药物，不等同于经过临床判定的不合理用药。这些指标已经计算并独立复算，展示它们不改变阈值或模型选择。')]
                lines += ['', ('Core-order matching requires drug, route, dose value and dose unit. The compiler copies supplied order templates; it does not generate novel doses. Binary AUROC covers the 20 candidate decisions; drug/order F1 retains unreachable ground-truth medications.' if en else
                               '核心订单匹配要求药物、途径、剂量值和剂量单位同时一致。编译器复制候选订单模板，不生成新剂量。二元 AUROC 只覆盖 20 个候选决策；药物／订单 F1 分母仍保留候选之外的真值药物。'), '',
                          ('#### All registered contrasts' if en else '#### 全部预先登记的差值'), '',
                          '| View | Contrast | Drug Δ [95% CI] | Core-order Δ [95% CI] |', '|---|---|---:|---:|']
                for kind, panel in views.items():
                    for name, result in panel['contrasts'].items():
                        cells = []
                        for metric in ['drug', 'core_order']:
                            r = result[metric]; lo, hi = r['micro_f1_patient_ci95']
                            cells.append(f"{r['micro_f1_difference']:+.5f} [{lo:+.5f}, {hi:+.5f}]")
                        lines.append(f'| {kind} | {name} | ' + ' | '.join(cells) + ' |')
            lines += ['', ('### Calibration-only changes' if en else '### 仅改变阈值的变化'), '',
                      '| View | Model state | Drug Δ [95% CI] | Core-order Δ [95% CI] |', '|---|---|---:|---:|']
            for kind, states in z['calibration_only_contrasts'].items():
                for name, result in states.items():
                    cells = []
                    for metric in ['drug', 'core_order']:
                        r = result[metric]; lo, hi = r['micro_f1_patient_ci95']
                        cells.append(f"{r['micro_f1_difference']:+.5f} [{lo:+.5f}, {hi:+.5f}]")
                    lines.append(f'| {kind} | {name} | ' + ' | '.join(cells) + ' |')
            lines += ['', ('### Candidate-position invariance' if en else '### 候选位置不变性'), '',
                      '| Endpoint | View vs ranked | Method | Equal sets % | Nonempty union cases | Nonempty Jaccard |', '|---|---|---|---:|---:|---:|']
            for endpoint, views in z['view_invariance'].items():
                for kind, states in views.items():
                    for name, r in states.items():
                        lines.append(f"| {endpoint} | {kind} | {name} | {100*r['drug_set_agreement']:.1f} | {r['nonempty_union_cases']} | {number(r['nonempty_union_mean_jaccard'])} |")
            lines += ['', ('An all-empty predictor can have perfect set agreement. Nonempty-union counts and Jaccard therefore accompany it. All intervals use 4,000 paired patient-cluster resamples; they are descriptive, unadjusted for multiple comparisons and do not capture seed uncertainty.' if en else
                           '全空预测也可能获得 100% 集合一致率，因此同时报告非空并集病例数与其 Jaccard。所有区间采用 4,000 次患者聚类配对重采样，是未作多重比较校正的描述性区间，不能反映不同随机种子的波动。'), '',
                      f"[Full {split} scores and contrasts](results/{split}_summary.json) · [Independent recount](results/{split}_audit.json)", '']
        lines += [('## 5. Interpretation boundary' if en else '## 5. 结论边界'), '',
                  ('This pilot is one-seed, one-round supervised repair. It does not by itself show recursive self-improvement. Fixed candidate retrieval and dose templates do not evolve. After the four training states and ordinary thresholds freeze, the guard waits for all original v31 seed42 selections to freeze as well; guard scores cannot choose a winning repair. Multi-round own-error, shuffled-error and uniform controls remain necessary.' if en else
                   '本版是单种子、单轮的监督修复，不能单独证明递归自进化。候选检索工具与剂量模板保持固定。四组训练状态和普通校准阈值冻结后，guard 仍须等待原 v31 seed42 全部选择冻结；guard 成绩不能用于挑选优胜修复。后续仍需多轮自身错误、打乱错误和普通训练对照。'), '',
                  '[Protocol](protocol.json) · [Evaluation addendum](evaluation_addendum.json) · [Execution progress](results/progress.json) · [Synthetic scoring preflight](results/evaluation_probe.json) · [Earlier collapse diagnosis](../upgrade_v31/COLLAPSE.' + lang + '.md)', '']
        if (HERE / 'results/proposal_rank_diagnostic_audit.json').exists():
            lines += [('A separate post-proposal diagnosis fixes every output to eight medications and independently recounts drug-identity ranking, position sensitivity and cutoff ties. It changes no original selection. ' if en else
                       '另已完成事后提出的固定8药诊断，独立复算按药物身份对齐的排序、位置依赖和截断同分；不改变原有选择。') +
                      f'[Fixed-cardinality ranking diagnosis](RANKING_DIAGNOSTIC.{lang}.md)', '']
        if (HERE/'results/precision_probe_audit.json').exists():
            lines += [('The frozen-readout precision comparison has passed its numerical preflight and has a separate clinical evaluation/audit pipeline. ' if en else
                       '固定权重读出精度对照已通过数值预检，并具有单独的病例评价／复算流程。')+f'[Precision comparison](PRECISION.{lang}.md)', '']
        (HERE / f'RESULTS.{lang}.md').write_text('\n'.join(lines))
    print(json.dumps({'completed_fits': len(completed), 'audited_splits': progress['audited_splits']}), flush=True)


if __name__ == '__main__':
    main()
