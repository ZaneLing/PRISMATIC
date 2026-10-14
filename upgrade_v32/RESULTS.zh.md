# v0.32：二元处方决策受控修复——执行与结果

## 1. 本实验回答什么

v31 首次更新生成了格式合法、内容全零的处方。本试验用相同 400 例、每组 100 步，交叉检验训练前缀和类别不平衡。四个新适配器、基础模型和原失败适配器均采用不含标签的全零前缀评分；另保留原检索前 8 个和全部 20 个候选的直接对照。

固定 0.5 阈值反映未经校准的决策表现。另一组结果在 100 例 proposal 上选择一个全局阈值，两种候选排序共享该值；六个模型状态接受相同校准。单纯调阈值的收益与更新权重的收益分别报告。两组均在 F1、空输出率之外展示药物精确率、召回率和平均开药数，避免把多选药物直接当成全面改善。

## 2. 真实完成情况

- 已完成训练: **4/4**
- 已独立复算成绩分组: **proposal**
- API 请求: **0**

| Arm | Steps | Fit seconds | Adapter SHA-256 (prefix) |
|---|---:|---:|---|
| teacher_uniform | 100 | 1739.2 | 03e345d3b72d |
| zero_uniform | 100 | 1505.8 | 200340a805f8 |
| teacher_balanced | 100 | 1569.2 | a852a5c31571 |
| zero_balanced | 100 | 1579.0 | d1e56ac1bd2c |

训练完成状态与原始适配器哈希逐项核对。独立核验重建全部 8,000 个二元标签，并在四组训练回执均通过后开放 proposal 评分。评分预检已通过 120 个合成病例／概率绑定、完整阈值选择、源数据复算及逐字节一致的断点恢复；这些合成检查不属于临床实验成绩。

**四组训练均通过独立核验。** 已重建 8,000 个目标（其中 1,604 个阳性），逐组核对 100 步训练日志，确认 3,670,016 个适配器参数均为有限值、LoRA 存在非零更新，并确认 400 个训练样本与 100 个 proposal 病例之间没有患者重叠。该核验没有独立重跑优化轨迹。目前已开放 proposal 推理；训练完成不等于处方效果已经提高。

[Training audit](results/training_audit.json)

## 3. proposal

100 admissions / 97 patients. proposal 用于选择阈值；复用的 guard 只报告开发结果，不是未经查看的测试集。

**主要发现：** 在全部已报告排序、固定 0.5 阈值及已登记校准下，四种新修复的药物和核心订单 F1 点估计都低于直接检索前 8 个候选。空输出减少仍未形成胜出的修复；全部配对区间保留在下方。

**校准后的过度选择：** 全零前缀／平衡损失几乎选中全部候选（ranked: 20.00 / 20, precision 0.17700; permuted: 19.91 / 20, precision 0.17780）。较高的非空位置一致性因此可能来自几乎全选，不能证明区分药物的能力改善；全部 20 个候选直接输出的对照揭示了这一点。

**校准边界：** frozen_base, original_failed_adapter, teacher_uniform 选择了固定 0.01–0.99 网格的端点。这里报告的是已登记网格结果，不代表全局最优阈值或穷尽普通校准方案；网格与选择保持冻结。

![Fixed and calibrated scores for every method](proposal_repair.png)

每对点表示同一冻结模型采用固定阈值／普通校准后的表现，保留全部对照；配对不确定性及精确率／召回率见下表。

### fixed_half

| View | Method | Threshold | Drug micro-F1 | Core-order micro-F1 | Empty % | Binary AUROC |
|---|---|---:|---:|---:|---:|---:|
| ranked | frozen_base | 0.50000 | 0.14173 | 0.08898 | 1.0 | 0.65109 |
| ranked | original_failed_adapter | 0.50000 | 0.00000 | 0.00000 | 100.0 | 0.67394 |
| ranked | teacher_uniform | 0.50000 | 0.00000 | 0.00000 | 100.0 | 0.66827 |
| ranked | zero_uniform | 0.50000 | 0.00000 | 0.00000 | 100.0 | 0.57545 |
| ranked | teacher_balanced | 0.50000 | 0.15629 | 0.09382 | 3.0 | 0.66331 |
| ranked | zero_balanced | 0.50000 | 0.21957 | 0.14327 | 0.0 | 0.52779 |
| ranked | original_retrieval_top8 | N/A | 0.28706 | 0.20181 | 0.0 | N/A |
| ranked | all20_candidate_tools | N/A | 0.26310 | 0.18427 | 0.0 | N/A |
| permuted | frozen_base | 0.50000 | 0.11765 | 0.06816 | 4.0 | 0.54749 |
| permuted | original_failed_adapter | 0.50000 | 0.00000 | 0.00000 | 100.0 | 0.55061 |
| permuted | teacher_uniform | 0.50000 | 0.00000 | 0.00000 | 100.0 | 0.53469 |
| permuted | zero_uniform | 0.50000 | 0.00000 | 0.00000 | 100.0 | 0.55301 |
| permuted | teacher_balanced | 0.50000 | 0.12978 | 0.07407 | 5.0 | 0.55895 |
| permuted | zero_balanced | 0.50000 | 0.19153 | 0.13539 | 0.0 | 0.48469 |
| permuted | original_retrieval_top8 | N/A | 0.28706 | 0.20181 | 0.0 | N/A |
| permuted | all20_candidate_tools | N/A | 0.26310 | 0.18427 | 0.0 | N/A |

#### 相对记录处方的漏项与额外药物

| View | Method | Drug precision | Drug recall | Mean predicted drugs |
|---|---|---:|---:|---:|
| ranked | frozen_base | 0.31818 | 0.09117 | 1.98 |
| ranked | original_failed_adapter | 0.00000 | 0.00000 | 0.00 |
| ranked | teacher_uniform | 0.00000 | 0.00000 | 0.00 |
| ranked | zero_uniform | 0.00000 | 0.00000 | 0.00 |
| ranked | teacher_balanced | 0.35938 | 0.09986 | 1.92 |
| ranked | zero_balanced | 0.18680 | 0.26628 | 9.85 |
| ranked | original_retrieval_top8 | 0.26750 | 0.30970 | 8.00 |
| ranked | all20_candidate_tools | 0.17700 | 0.51230 | 20.00 |
| permuted | frozen_base | 0.26943 | 0.07525 | 1.93 |
| permuted | original_failed_adapter | 0.00000 | 0.00000 | 0.00 |
| permuted | teacher_uniform | 0.00000 | 0.00000 | 0.00 |
| permuted | zero_uniform | 0.00000 | 0.00000 | 0.00 |
| permuted | teacher_balanced | 0.32558 | 0.08104 | 1.72 |
| permuted | zero_balanced | 0.16631 | 0.22576 | 9.38 |
| permuted | original_retrieval_top8 | 0.26750 | 0.30970 | 8.00 |
| permuted | all20_candidate_tools | 0.17700 | 0.51230 | 20.00 |

精确率和召回率以记录处方为参照，召回率分母保留候选之外的真值药物。平均开药数与空输出率一起展示，便于发现过度选择。相对记录处方的额外药物，不等同于经过临床判定的不合理用药。这些指标已经计算并独立复算，展示它们不改变阈值或模型选择。

核心订单匹配要求药物、途径、剂量值和剂量单位同时一致。编译器复制候选订单模板，不生成新剂量。二元 AUROC 只覆盖 20 个候选决策；药物／订单 F1 分母仍保留候选之外的真值药物。

#### 全部预先登记的差值

| View | Contrast | Drug Δ [95% CI] | Core-order Δ [95% CI] |
|---|---|---:|---:|
| ranked | zero_uniform_minus_teacher_uniform | +0.00000 [+0.00000, +0.00000] | +0.00000 [+0.00000, +0.00000] |
| ranked | zero_balanced_minus_teacher_balanced | +0.06329 [+0.02389, +0.10091] | +0.04945 [+0.01916, +0.07765] |
| ranked | zero_balanced_minus_zero_uniform | +0.21957 [+0.18714, +0.25144] | +0.14327 [+0.11543, +0.17046] |
| ranked | teacher_balanced_minus_teacher_uniform | +0.15629 [+0.12485, +0.18719] | +0.09382 [+0.06673, +0.12390] |
| ranked | prefix_by_balance_interaction | +0.06329 [+0.02389, +0.10091] | +0.04945 [+0.01916, +0.07765] |
| ranked | teacher_uniform_minus_frozen_base | -0.14173 [-0.17087, -0.11414] | -0.08898 [-0.11439, -0.06557] |
| ranked | teacher_uniform_minus_original_failed_adapter | +0.00000 [+0.00000, +0.00000] | +0.00000 [+0.00000, +0.00000] |
| ranked | teacher_uniform_minus_original_retrieval_top8 | -0.28706 [-0.32553, -0.24658] | -0.20181 [-0.23686, -0.16678] |
| ranked | teacher_uniform_minus_all20_candidate_tools | -0.26310 [-0.29905, -0.22367] | -0.18427 [-0.21295, -0.15462] |
| ranked | zero_uniform_minus_frozen_base | -0.14173 [-0.17087, -0.11414] | -0.08898 [-0.11439, -0.06557] |
| ranked | zero_uniform_minus_original_failed_adapter | +0.00000 [+0.00000, +0.00000] | +0.00000 [+0.00000, +0.00000] |
| ranked | zero_uniform_minus_original_retrieval_top8 | -0.28706 [-0.32553, -0.24658] | -0.20181 [-0.23686, -0.16678] |
| ranked | zero_uniform_minus_all20_candidate_tools | -0.26310 [-0.29905, -0.22367] | -0.18427 [-0.21295, -0.15462] |
| ranked | teacher_balanced_minus_frozen_base | +0.01455 [-0.00876, +0.03872] | +0.00483 [-0.01274, +0.02299] |
| ranked | teacher_balanced_minus_original_failed_adapter | +0.15629 [+0.12485, +0.18719] | +0.09382 [+0.06673, +0.12390] |
| ranked | teacher_balanced_minus_original_retrieval_top8 | -0.13077 [-0.17645, -0.08429] | -0.10799 [-0.14141, -0.07264] |
| ranked | teacher_balanced_minus_all20_candidate_tools | -0.10681 [-0.15301, -0.05865] | -0.09045 [-0.12462, -0.05433] |
| ranked | zero_balanced_minus_frozen_base | +0.07784 [+0.03741, +0.11498] | +0.05429 [+0.02263, +0.08357] |
| ranked | zero_balanced_minus_original_failed_adapter | +0.21957 [+0.18714, +0.25144] | +0.14327 [+0.11543, +0.17046] |
| ranked | zero_balanced_minus_original_retrieval_top8 | -0.06749 [-0.09636, -0.03973] | -0.05854 [-0.08645, -0.03008] |
| ranked | zero_balanced_minus_all20_candidate_tools | -0.04353 [-0.06687, -0.02102] | -0.04100 [-0.06109, -0.02104] |
| permuted | zero_uniform_minus_teacher_uniform | +0.00000 [+0.00000, +0.00000] | +0.00000 [+0.00000, +0.00000] |
| permuted | zero_balanced_minus_teacher_balanced | +0.06175 [+0.02071, +0.10222] | +0.06132 [+0.03059, +0.09099] |
| permuted | zero_balanced_minus_zero_uniform | +0.19153 [+0.15886, +0.22338] | +0.13539 [+0.10832, +0.16245] |
| permuted | teacher_balanced_minus_teacher_uniform | +0.12978 [+0.10585, +0.15385] | +0.07407 [+0.05549, +0.09469] |
| permuted | prefix_by_balance_interaction | +0.06175 [+0.02071, +0.10222] | +0.06132 [+0.03059, +0.09099] |
| permuted | teacher_uniform_minus_frozen_base | -0.11765 [-0.14146, -0.09480] | -0.06816 [-0.08912, -0.04883] |
| permuted | teacher_uniform_minus_original_failed_adapter | +0.00000 [+0.00000, +0.00000] | +0.00000 [+0.00000, +0.00000] |
| permuted | teacher_uniform_minus_original_retrieval_top8 | -0.28706 [-0.32553, -0.24658] | -0.20181 [-0.23686, -0.16678] |
| permuted | teacher_uniform_minus_all20_candidate_tools | -0.26310 [-0.29905, -0.22367] | -0.18427 [-0.21295, -0.15462] |
| permuted | zero_uniform_minus_frozen_base | -0.11765 [-0.14146, -0.09480] | -0.06816 [-0.08912, -0.04883] |
| permuted | zero_uniform_minus_original_failed_adapter | +0.00000 [+0.00000, +0.00000] | +0.00000 [+0.00000, +0.00000] |
| permuted | zero_uniform_minus_original_retrieval_top8 | -0.28706 [-0.32553, -0.24658] | -0.20181 [-0.23686, -0.16678] |
| permuted | zero_uniform_minus_all20_candidate_tools | -0.26310 [-0.29905, -0.22367] | -0.18427 [-0.21295, -0.15462] |
| permuted | teacher_balanced_minus_frozen_base | +0.01213 [-0.00401, +0.02805] | +0.00592 [-0.00573, +0.01789] |
| permuted | teacher_balanced_minus_original_failed_adapter | +0.12978 [+0.10585, +0.15385] | +0.07407 [+0.05549, +0.09469] |
| permuted | teacher_balanced_minus_original_retrieval_top8 | -0.15728 [-0.19799, -0.11347] | -0.12774 [-0.16341, -0.09161] |
| permuted | teacher_balanced_minus_all20_candidate_tools | -0.13332 [-0.17549, -0.08933] | -0.11019 [-0.14166, -0.07714] |
| permuted | zero_balanced_minus_frozen_base | +0.07388 [+0.03553, +0.11125] | +0.06723 [+0.03885, +0.09543] |
| permuted | zero_balanced_minus_original_failed_adapter | +0.19153 [+0.15886, +0.22338] | +0.13539 [+0.10832, +0.16245] |
| permuted | zero_balanced_minus_original_retrieval_top8 | -0.09553 [-0.12151, -0.06998] | -0.06642 [-0.09001, -0.04216] |
| permuted | zero_balanced_minus_all20_candidate_tools | -0.07157 [-0.09660, -0.04744] | -0.04888 [-0.06522, -0.03181] |
### proposal_calibrated

| View | Method | Threshold | Drug micro-F1 | Core-order micro-F1 | Empty % | Binary AUROC |
|---|---|---:|---:|---:|---:|---:|
| ranked | frozen_base | 0.01000 | 0.23439 | 0.15850 | 0.0 | 0.65109 |
| ranked | original_failed_adapter | 0.01000 | 0.27879 | 0.19352 | 0.0 | 0.67394 |
| ranked | teacher_uniform | 0.01000 | 0.26502 | 0.18536 | 0.0 | 0.66827 |
| ranked | zero_uniform | 0.21000 | 0.26480 | 0.18506 | 0.0 | 0.57545 |
| ranked | teacher_balanced | 0.04000 | 0.26986 | 0.18828 | 0.0 | 0.66331 |
| ranked | zero_balanced | 0.40000 | 0.26310 | 0.18427 | 0.0 | 0.52779 |
| ranked | original_retrieval_top8 | N/A | 0.28706 | 0.20181 | 0.0 | N/A |
| ranked | all20_candidate_tools | N/A | 0.26310 | 0.18427 | 0.0 | N/A |
| permuted | frozen_base | 0.01000 | 0.17663 | 0.10683 | 0.0 | 0.54749 |
| permuted | original_failed_adapter | 0.01000 | 0.24955 | 0.17346 | 0.0 | 0.55061 |
| permuted | teacher_uniform | 0.01000 | 0.26103 | 0.18330 | 0.0 | 0.53469 |
| permuted | zero_uniform | 0.21000 | 0.26383 | 0.18333 | 0.0 | 0.55301 |
| permuted | teacher_balanced | 0.04000 | 0.25979 | 0.18145 | 0.0 | 0.55895 |
| permuted | zero_balanced | 0.40000 | 0.26398 | 0.18487 | 0.0 | 0.48469 |
| permuted | original_retrieval_top8 | N/A | 0.28706 | 0.20181 | 0.0 | N/A |
| permuted | all20_candidate_tools | N/A | 0.26310 | 0.18427 | 0.0 | N/A |

#### 相对记录处方的漏项与额外药物

| View | Method | Drug precision | Drug recall | Mean predicted drugs |
|---|---|---:|---:|---:|
| ranked | frozen_base | 0.28661 | 0.19826 | 4.78 |
| ranked | original_failed_adapter | 0.19735 | 0.47467 | 16.62 |
| ranked | teacher_uniform | 0.17892 | 0.51085 | 19.73 |
| ranked | zero_uniform | 0.17943 | 0.50507 | 19.45 |
| ranked | teacher_balanced | 0.18633 | 0.48915 | 18.14 |
| ranked | zero_balanced | 0.17700 | 0.51230 | 20.00 |
| ranked | original_retrieval_top8 | 0.26750 | 0.30970 | 8.00 |
| ranked | all20_candidate_tools | 0.17700 | 0.51230 | 20.00 |
| permuted | frozen_base | 0.24242 | 0.13893 | 3.96 |
| permuted | original_failed_adapter | 0.18087 | 0.40232 | 15.37 |
| permuted | teacher_uniform | 0.17653 | 0.50072 | 19.60 |
| permuted | zero_uniform | 0.18004 | 0.49349 | 18.94 |
| permuted | teacher_balanced | 0.18166 | 0.45586 | 17.34 |
| permuted | zero_balanced | 0.17780 | 0.51230 | 19.91 |
| permuted | original_retrieval_top8 | 0.26750 | 0.30970 | 8.00 |
| permuted | all20_candidate_tools | 0.17700 | 0.51230 | 20.00 |

精确率和召回率以记录处方为参照，召回率分母保留候选之外的真值药物。平均开药数与空输出率一起展示，便于发现过度选择。相对记录处方的额外药物，不等同于经过临床判定的不合理用药。这些指标已经计算并独立复算，展示它们不改变阈值或模型选择。

核心订单匹配要求药物、途径、剂量值和剂量单位同时一致。编译器复制候选订单模板，不生成新剂量。二元 AUROC 只覆盖 20 个候选决策；药物／订单 F1 分母仍保留候选之外的真值药物。

#### 全部预先登记的差值

| View | Contrast | Drug Δ [95% CI] | Core-order Δ [95% CI] |
|---|---|---:|---:|
| ranked | zero_uniform_minus_teacher_uniform | -0.00022 [-0.00375, +0.00298] | -0.00030 [-0.00356, +0.00256] |
| ranked | zero_balanced_minus_teacher_balanced | -0.00676 [-0.01264, -0.00077] | -0.00401 [-0.00882, +0.00119] |
| ranked | zero_balanced_minus_zero_uniform | -0.00170 [-0.00460, +0.00169] | -0.00079 [-0.00331, +0.00234] |
| ranked | teacher_balanced_minus_teacher_uniform | +0.00485 [-0.00098, +0.01064] | +0.00292 [-0.00214, +0.00777] |
| ranked | prefix_by_balance_interaction | -0.00654 [-0.01337, +0.00096] | -0.00371 [-0.00957, +0.00282] |
| ranked | teacher_uniform_minus_frozen_base | +0.03063 [-0.00669, +0.06849] | +0.02687 [-0.00328, +0.05864] |
| ranked | teacher_uniform_minus_original_failed_adapter | -0.01378 [-0.02184, -0.00468] | -0.00816 [-0.01555, +0.00080] |
| ranked | teacher_uniform_minus_original_retrieval_top8 | -0.02204 [-0.04319, +0.00105] | -0.01645 [-0.03629, +0.00444] |
| ranked | teacher_uniform_minus_all20_candidate_tools | +0.00192 [+0.00039, +0.00335] | +0.00109 [-0.00039, +0.00228] |
| ranked | zero_uniform_minus_frozen_base | +0.03041 [-0.00647, +0.06817] | +0.02656 [-0.00355, +0.05831] |
| ranked | zero_uniform_minus_original_failed_adapter | -0.01400 [-0.02262, -0.00467] | -0.00846 [-0.01635, +0.00084] |
| ranked | zero_uniform_minus_original_retrieval_top8 | -0.02226 [-0.04318, +0.00039] | -0.01675 [-0.03630, +0.00381] |
| ranked | zero_uniform_minus_all20_candidate_tools | +0.00170 [-0.00169, +0.00460] | +0.00079 [-0.00234, +0.00331] |
| ranked | teacher_balanced_minus_frozen_base | +0.03547 [-0.00186, +0.07385] | +0.02978 [+0.00025, +0.06135] |
| ranked | teacher_balanced_minus_original_failed_adapter | -0.00893 [-0.01562, -0.00194] | -0.00524 [-0.01114, +0.00132] |
| ranked | teacher_balanced_minus_original_retrieval_top8 | -0.01720 [-0.03755, +0.00511] | -0.01353 [-0.03142, +0.00549] |
| ranked | teacher_balanced_minus_all20_candidate_tools | +0.00676 [+0.00077, +0.01264] | +0.00401 [-0.00119, +0.00882] |
| ranked | zero_balanced_minus_frozen_base | +0.02871 [-0.00863, +0.06659] | +0.02577 [-0.00408, +0.05747] |
| ranked | zero_balanced_minus_original_failed_adapter | -0.01569 [-0.02412, -0.00646] | -0.00925 [-0.01679, -0.00023] |
| ranked | zero_balanced_minus_original_retrieval_top8 | -0.02396 [-0.04524, -0.00084] | -0.01754 [-0.03743, +0.00333] |
| ranked | zero_balanced_minus_all20_candidate_tools | +0.00000 [+0.00000, +0.00000] | +0.00000 [+0.00000, +0.00000] |
| permuted | zero_uniform_minus_teacher_uniform | +0.00280 [-0.00304, +0.00853] | +0.00004 [-0.00502, +0.00506] |
| permuted | zero_balanced_minus_teacher_balanced | +0.00419 [-0.00385, +0.01216] | +0.00342 [-0.00345, +0.01081] |
| permuted | zero_balanced_minus_zero_uniform | +0.00015 [-0.00488, +0.00578] | +0.00154 [-0.00274, +0.00604] |
| permuted | teacher_balanced_minus_teacher_uniform | -0.00124 [-0.00859, +0.00601] | -0.00184 [-0.00842, +0.00462] |
| permuted | prefix_by_balance_interaction | +0.00139 [-0.00681, +0.00955] | +0.00339 [-0.00435, +0.01114] |
| permuted | teacher_uniform_minus_frozen_base | +0.08440 [+0.04778, +0.11812] | +0.07647 [+0.04554, +0.10572] |
| permuted | teacher_uniform_minus_original_failed_adapter | +0.01148 [+0.00015, +0.02263] | +0.00984 [+0.00056, +0.01937] |
| permuted | teacher_uniform_minus_original_retrieval_top8 | -0.02602 [-0.04704, -0.00338] | -0.01851 [-0.03761, +0.00218] |
| permuted | teacher_uniform_minus_all20_candidate_tools | -0.00207 [-0.00546, +0.00088] | -0.00097 [-0.00396, +0.00158] |
| permuted | zero_uniform_minus_frozen_base | +0.08720 [+0.04946, +0.12223] | +0.07650 [+0.04556, +0.10637] |
| permuted | zero_uniform_minus_original_failed_adapter | +0.01428 [+0.00090, +0.02775] | +0.00988 [-0.00125, +0.02093] |
| permuted | zero_uniform_minus_original_retrieval_top8 | -0.02323 [-0.04532, +0.00060] | -0.01848 [-0.03849, +0.00290] |
| permuted | zero_uniform_minus_all20_candidate_tools | +0.00073 [-0.00499, +0.00574] | -0.00093 [-0.00555, +0.00330] |
| permuted | teacher_balanced_minus_frozen_base | +0.08316 [+0.04747, +0.11652] | +0.07462 [+0.04460, +0.10260] |
| permuted | teacher_balanced_minus_original_failed_adapter | +0.01024 [+0.00126, +0.01953] | +0.00800 [-0.00025, +0.01647] |
| permuted | teacher_balanced_minus_original_retrieval_top8 | -0.02726 [-0.04951, -0.00321] | -0.02036 [-0.04082, +0.00087] |
| permuted | teacher_balanced_minus_all20_candidate_tools | -0.00331 [-0.01100, +0.00454] | -0.00282 [-0.01012, +0.00395] |
| permuted | zero_balanced_minus_frozen_base | +0.08735 [+0.05055, +0.12127] | +0.07804 [+0.04712, +0.10736] |
| permuted | zero_balanced_minus_original_failed_adapter | +0.01443 [+0.00251, +0.02628] | +0.01142 [+0.00162, +0.02165] |
| permuted | zero_balanced_minus_original_retrieval_top8 | -0.02307 [-0.04442, +0.00001] | -0.01694 [-0.03691, +0.00399] |
| permuted | zero_balanced_minus_all20_candidate_tools | +0.00088 [+0.00038, +0.00148] | +0.00061 [+0.00026, +0.00100] |

### 仅改变阈值的变化

| View | Model state | Drug Δ [95% CI] | Core-order Δ [95% CI] |
|---|---|---:|---:|
| ranked | frozen_base | +0.09266 [+0.06317, +0.11832] | +0.06951 [+0.04622, +0.09032] |
| ranked | original_failed_adapter | +0.27879 [+0.23764, +0.31614] | +0.19352 [+0.16167, +0.22369] |
| ranked | teacher_uniform | +0.26502 [+0.22524, +0.30144] | +0.18536 [+0.15513, +0.21426] |
| ranked | zero_uniform | +0.26480 [+0.22553, +0.30088] | +0.18506 [+0.15496, +0.21484] |
| ranked | teacher_balanced | +0.11357 [+0.06645, +0.16023] | +0.09446 [+0.05817, +0.12863] |
| ranked | zero_balanced | +0.04353 [+0.02102, +0.06687] | +0.04100 [+0.02104, +0.06109] |
| permuted | frozen_base | +0.05899 [+0.03448, +0.08224] | +0.03867 [+0.02034, +0.05760] |
| permuted | original_failed_adapter | +0.24955 [+0.21218, +0.28400] | +0.17346 [+0.14387, +0.20206] |
| permuted | teacher_uniform | +0.26103 [+0.22204, +0.29738] | +0.18330 [+0.15331, +0.21156] |
| permuted | zero_uniform | +0.26383 [+0.22482, +0.30044] | +0.18333 [+0.15342, +0.21218] |
| permuted | teacher_balanced | +0.13001 [+0.08639, +0.17205] | +0.10738 [+0.07506, +0.13854] |
| permuted | zero_balanced | +0.07245 [+0.04832, +0.09745] | +0.04948 [+0.03248, +0.06596] |

### 候选位置不变性

| Endpoint | View vs ranked | Method | Equal sets % | Nonempty union cases | Nonempty Jaccard |
|---|---|---|---:|---:|---:|
| fixed_half | permuted | frozen_base | 3.0 | 100 | 0.21667 |
| fixed_half | permuted | original_failed_adapter | 100.0 | 0 | N/A |
| fixed_half | permuted | teacher_uniform | 100.0 | 0 | N/A |
| fixed_half | permuted | zero_uniform | 100.0 | 0 | N/A |
| fixed_half | permuted | teacher_balanced | 6.0 | 100 | 0.24033 |
| fixed_half | permuted | zero_balanced | 0.0 | 100 | 0.31703 |
| fixed_half | permuted | original_retrieval_top8 | 100.0 | 100 | 1.00000 |
| fixed_half | permuted | all20_candidate_tools | 100.0 | 100 | 1.00000 |
| proposal_calibrated | permuted | frozen_base | 0.0 | 100 | 0.28679 |
| proposal_calibrated | permuted | original_failed_adapter | 0.0 | 100 | 0.67948 |
| proposal_calibrated | permuted | teacher_uniform | 58.0 | 100 | 0.96650 |
| proposal_calibrated | permuted | zero_uniform | 25.0 | 100 | 0.92221 |
| proposal_calibrated | permuted | teacher_balanced | 2.0 | 100 | 0.80320 |
| proposal_calibrated | permuted | zero_balanced | 91.0 | 100 | 0.99550 |
| proposal_calibrated | permuted | original_retrieval_top8 | 100.0 | 100 | 1.00000 |
| proposal_calibrated | permuted | all20_candidate_tools | 100.0 | 100 | 1.00000 |

全空预测也可能获得 100% 集合一致率，因此同时报告非空并集病例数与其 Jaccard。所有区间采用 4,000 次患者聚类配对重采样，是未作多重比较校正的描述性区间，不能反映不同随机种子的波动。

[Full proposal scores and contrasts](results/proposal_summary.json) · [Independent recount](results/proposal_audit.json)

## 4. guard

尚无通过独立复算的成绩。当前前置条件：v31_seed42_frozen_selection.

## 5. 结论边界

本版是单种子、单轮的监督修复，不能单独证明递归自进化。候选检索工具与剂量模板保持固定。四组训练状态和普通校准阈值冻结后，guard 仍须等待原 v31 seed42 全部选择冻结；guard 成绩不能用于挑选优胜修复。后续仍需多轮自身错误、打乱错误和普通训练对照。

[Protocol](protocol.json) · [Evaluation addendum](evaluation_addendum.json) · [Execution progress](results/progress.json) · [Synthetic scoring preflight](results/evaluation_probe.json) · [Earlier collapse diagnosis](../upgrade_v31/COLLAPSE.zh.md)
