# v0.32 固定开药数量的排序诊断

## 1. 这次回答什么

空输出修复后，模型是否已经学会选择更合适的药物？这次让每个模型都根据已保存的概率，从相同20个候选中恰好选择8个，与原检索前8个使用相同开药数量。真值只参与评分。没有新增训练、模型推理、API请求、检查点／阈值选择，也未打开测试集。

本诊断在看到原proposal结果后提出，协议和实现先提交，再计算新端点。它属于事后提出的开发分析，不是原实验预先登记的端点或独立确认。原固定0.5及校准结果保持原样。“每例8个”只用于隔离排序能力，不是临床开药数量规则。

同分时，主分析按药物身份的SHA-256键排序；另报告按药名词典顺序处理同分的敏感性分析。两种规则均不使用真值、展示位置或检索名次；同一药物分数不变时，候选换序不会改变同分处理。

[Protocol](rank_diagnostic_protocol.json) · [Frozen implementation](results/rank_diagnostic_lock.json) · [Original repair experiment](RESULTS.zh.md)

## 2. proposal: 100 admissions / 97 patients

**结论：** 在全部已报告排序和两种同分规则下，没有神经模型的药物或核心订单F1超过检索。固定开药数量后仍未形成胜出的修复。

### 主分析：药物身份哈希处理同分

| 候选排序 | 方法 | 药物F1 | 核心订单F1 | 病例内AUROC（有效病例数） | 截断同分病例数 |
|---|---|---:|---:|---:|---:|
| ranked | 基础模型 | 0.27096 | 0.18111 | 0.68006 (67) | 14/100 |
| ranked | 原失败适配器 | 0.28571 | 0.19405 | 0.70017 (67) | 13/100 |
| ranked | 真实前缀／普通损失 | 0.28706 | 0.19405 | 0.69818 (67) | 9/100 |
| ranked | 全零前缀／普通损失 | 0.23877 | 0.16171 | 0.56853 (67) | 93/100 |
| ranked | 真实前缀／平衡损失 | 0.28437 | 0.19405 | 0.68927 (67) | 12/100 |
| ranked | 全零前缀／平衡损失 | 0.22401 | 0.14877 | 0.56036 (67) | 84/100 |
| ranked | 直接检索前8 | 0.28706 | 0.20181 | — | — |
| permuted | 基础模型 | 0.21462 | 0.14489 | 0.55057 (67) | 8/100 |
| permuted | 原失败适配器 | 0.20926 | 0.14101 | 0.53655 (67) | 14/100 |
| permuted | 真实前缀／普通损失 | 0.20389 | 0.13713 | 0.51945 (67) | 12/100 |
| permuted | 全零前缀／普通损失 | 0.23877 | 0.16041 | 0.54811 (67) | 89/100 |
| permuted | 真实前缀／平衡损失 | 0.20523 | 0.13842 | 0.54082 (67) | 15/100 |
| permuted | 全零前缀／平衡损失 | 0.20255 | 0.14618 | 0.49068 (67) | 80/100 |
| permuted | 直接检索前8 | 0.28706 | 0.20181 | — | — |

病例内AUROC比较同一病例的阳性与阴性候选，同分计半分；没有两类候选的病例只从AUROC中排除，仍计入处方F1。机器可读汇总保留纳入／排除数、精确率、召回率及全部配对差值。F1分母保留20个候选之外的真值药物。核心订单F1要求药物、途径、剂量值和单位同时匹配，沿用原完整字段订单分母。

### 敏感性：药名词典顺序处理同分

| 候选排序 | 方法 | 药物F1 | 核心订单F1 | 病例内AUROC（有效病例数） | 截断同分病例数 |
|---|---|---:|---:|---:|---:|
| ranked | 基础模型 | 0.26962 | 0.17982 | 0.68006 (67) | 14/100 |
| ranked | 原失败适配器 | 0.28303 | 0.19146 | 0.70017 (67) | 13/100 |
| ranked | 真实前缀／普通损失 | 0.28571 | 0.19276 | 0.69818 (67) | 9/100 |
| ranked | 全零前缀／普通损失 | 0.20255 | 0.13972 | 0.56853 (67) | 93/100 |
| ranked | 真实前缀／平衡损失 | 0.28706 | 0.19534 | 0.68927 (67) | 12/100 |
| ranked | 全零前缀／平衡损失 | 0.19852 | 0.13325 | 0.56036 (67) | 84/100 |
| ranked | 直接检索前8 | 0.28706 | 0.20181 | — | — |
| permuted | 基础模型 | 0.21462 | 0.14489 | 0.55057 (67) | 8/100 |
| permuted | 原失败适配器 | 0.20791 | 0.14101 | 0.53655 (67) | 14/100 |
| permuted | 真实前缀／普通损失 | 0.20389 | 0.13713 | 0.51945 (67) | 12/100 |
| permuted | 全零前缀／普通损失 | 0.21060 | 0.14101 | 0.54811 (67) | 89/100 |
| permuted | 真实前缀／平衡损失 | 0.20657 | 0.13972 | 0.54082 (67) | 15/100 |
| permuted | 全零前缀／平衡损失 | 0.17975 | 0.12678 | 0.49068 (67) | 80/100 |
| permuted | 直接检索前8 | 0.28706 | 0.20181 | — | — |

病例内AUROC比较同一病例的阳性与阴性候选，同分计半分；没有两类候选的病例只从AUROC中排除，仍计入处方F1。机器可读汇总保留纳入／排除数、精确率、召回率及全部配对差值。F1分母保留20个候选之外的真值药物。核心订单F1要求药物、途径、剂量值和单位同时匹配，沿用原完整字段订单分母。

### 分数跟随药物还是展示位置

| 变化后的排序 | 模型 | 按药物身份对齐的相关性 | 按展示位置对齐的相关性 | 前8药物集合完全一致率 | 前8集合Jaccard |
|---|---|---:|---:|---:|---:|
| permuted | 基础模型 | 0.24291 | 0.72743 | 0.0% | 0.37712 |
| permuted | 原失败适配器 | 0.21228 | 0.79617 | 0.0% | 0.34197 |
| permuted | 真实前缀／普通损失 | 0.19792 | 0.81688 | 0.0% | 0.33767 |
| permuted | 全零前缀／普通损失 | 0.12379 | 0.18125 | 0.0% | 0.35949 |
| permuted | 真实前缀／平衡损失 | 0.24096 | 0.76418 | 0.0% | 0.34778 |
| permuted | 全零前缀／平衡损失 | -0.00186 | 0.15051 | 0.0% | 0.27992 |

相关性为病例内Spearman的平均值。身份对齐比较同一药物；位置对齐比较同一展示位置，该位置通常已经换成另一种药物。较高的位置相关性与位置依赖一致，但不单独证明其成因。恒定分数的相关性记为未定义，数量在汇总中保留。固定前8的集合一致性不会被“全空”或“全选20个”抬高。

### 配对差值：drug_sha256

| View | Contrast | Drug Δ [95% CI] | Core-order Δ [95% CI] |
|---|---|---:|---:|
| ranked | frozen_base_minus_retrieval | -0.01610 [-0.03274, +0.00133] | -0.02070 [-0.03686, -0.00395] |
| ranked | original_failed_adapter_minus_retrieval | -0.00134 [-0.01516, +0.01240] | -0.00776 [-0.01969, +0.00411] |
| ranked | teacher_uniform_minus_retrieval | +0.00000 [-0.01184, +0.01159] | -0.00776 [-0.01759, +0.00249] |
| ranked | zero_uniform_minus_retrieval | -0.04829 [-0.07728, -0.01862] | -0.04010 [-0.06547, -0.01518] |
| ranked | teacher_balanced_minus_retrieval | -0.00268 [-0.01533, +0.01029] | -0.00776 [-0.01888, +0.00377] |
| ranked | zero_balanced_minus_retrieval | -0.06304 [-0.09080, -0.03552] | -0.05304 [-0.07792, -0.02642] |
| ranked | teacher_uniform_minus_frozen_base | +0.01610 [+0.00263, +0.02941] | +0.01294 [+0.00131, +0.02461] |
| ranked | teacher_uniform_minus_original_failed_adapter | +0.00134 [-0.00755, +0.01004] | +0.00000 [-0.00908, +0.00896] |
| ranked | zero_uniform_minus_frozen_base | -0.03219 [-0.06010, -0.00282] | -0.01940 [-0.04065, +0.00297] |
| ranked | zero_uniform_minus_original_failed_adapter | -0.04695 [-0.07351, -0.01802] | -0.03234 [-0.05292, -0.00946] |
| ranked | teacher_balanced_minus_frozen_base | +0.01341 [+0.00000, +0.02658] | +0.01294 [+0.00000, +0.02598] |
| ranked | teacher_balanced_minus_original_failed_adapter | -0.00134 [-0.00935, +0.00667] | +0.00000 [-0.00645, +0.00633] |
| ranked | zero_balanced_minus_frozen_base | -0.04695 [-0.07542, -0.01911] | -0.03234 [-0.05629, -0.00750] |
| ranked | zero_balanced_minus_original_failed_adapter | -0.06170 [-0.08892, -0.03296] | -0.04528 [-0.06671, -0.02094] |
| permuted | frozen_base_minus_retrieval | -0.07243 [-0.09826, -0.04536] | -0.05692 [-0.08275, -0.03003] |
| permuted | original_failed_adapter_minus_retrieval | -0.07780 [-0.10609, -0.04798] | -0.06080 [-0.08784, -0.03214] |
| permuted | teacher_uniform_minus_retrieval | -0.08317 [-0.11155, -0.05409] | -0.06468 [-0.09170, -0.03649] |
| permuted | zero_uniform_minus_retrieval | -0.04829 [-0.07450, -0.02060] | -0.04140 [-0.06376, -0.01867] |
| permuted | teacher_balanced_minus_retrieval | -0.08182 [-0.11053, -0.05307] | -0.06339 [-0.09172, -0.03472] |
| permuted | zero_balanced_minus_retrieval | -0.08451 [-0.11097, -0.05799] | -0.05563 [-0.08090, -0.02959] |
| permuted | teacher_uniform_minus_frozen_base | -0.01073 [-0.02183, +0.00000] | -0.00776 [-0.01826, +0.00262] |
| permuted | teacher_uniform_minus_original_failed_adapter | -0.00537 [-0.01289, +0.00139] | -0.00388 [-0.01065, +0.00261] |
| permuted | zero_uniform_minus_frozen_base | +0.02414 [+0.00000, +0.04759] | +0.01552 [-0.00257, +0.03246] |
| permuted | zero_uniform_minus_original_failed_adapter | +0.02951 [+0.00630, +0.05111] | +0.01940 [+0.00000, +0.03730] |
| permuted | teacher_balanced_minus_frozen_base | -0.00939 [-0.02001, +0.00125] | -0.00647 [-0.01613, +0.00272] |
| permuted | teacher_balanced_minus_original_failed_adapter | -0.00402 [-0.01117, +0.00269] | -0.00259 [-0.00889, +0.00359] |
| permuted | zero_balanced_minus_frozen_base | -0.01207 [-0.03408, +0.01049] | +0.00129 [-0.02032, +0.02202] |
| permuted | zero_balanced_minus_original_failed_adapter | -0.00671 [-0.03094, +0.01787] | +0.00517 [-0.01747, +0.02708] |

### 配对差值：drug_lexical

| View | Contrast | Drug Δ [95% CI] | Core-order Δ [95% CI] |
|---|---|---:|---:|
| ranked | frozen_base_minus_retrieval | -0.01744 [-0.03405, +0.00000] | -0.02199 [-0.03788, -0.00525] |
| ranked | original_failed_adapter_minus_retrieval | -0.00402 [-0.01743, +0.00959] | -0.01035 [-0.02199, +0.00126] |
| ranked | teacher_uniform_minus_retrieval | -0.00134 [-0.01321, +0.01016] | -0.00906 [-0.01844, +0.00000] |
| ranked | zero_uniform_minus_retrieval | -0.08451 [-0.11222, -0.05585] | -0.06210 [-0.08759, -0.03634] |
| ranked | teacher_balanced_minus_retrieval | +0.00000 [-0.01303, +0.01340] | -0.00647 [-0.01819, +0.00520] |
| ranked | zero_balanced_minus_retrieval | -0.08853 [-0.11666, -0.06195] | -0.06856 [-0.09362, -0.04381] |
| ranked | teacher_uniform_minus_frozen_base | +0.01610 [+0.00262, +0.02989] | +0.01294 [+0.00124, +0.02495] |
| ranked | teacher_uniform_minus_original_failed_adapter | +0.00268 [-0.00442, +0.01040] | +0.00129 [-0.00640, +0.00925] |
| ranked | zero_uniform_minus_frozen_base | -0.06707 [-0.09174, -0.04087] | -0.04010 [-0.06279, -0.01657] |
| ranked | zero_uniform_minus_original_failed_adapter | -0.08048 [-0.10625, -0.05296] | -0.05175 [-0.07325, -0.03001] |
| ranked | teacher_balanced_minus_frozen_base | +0.01744 [+0.00418, +0.03026] | +0.01552 [+0.00265, +0.02811] |
| ranked | teacher_balanced_minus_original_failed_adapter | +0.00402 [-0.00267, +0.01095] | +0.00388 [-0.00132, +0.00979] |
| ranked | zero_balanced_minus_frozen_base | -0.07109 [-0.09980, -0.04396] | -0.04657 [-0.07059, -0.02348] |
| ranked | zero_balanced_minus_original_failed_adapter | -0.08451 [-0.11175, -0.05815] | -0.05821 [-0.07927, -0.03682] |
| permuted | frozen_base_minus_retrieval | -0.07243 [-0.09826, -0.04536] | -0.05692 [-0.08275, -0.03003] |
| permuted | original_failed_adapter_minus_retrieval | -0.07914 [-0.10674, -0.05014] | -0.06080 [-0.08668, -0.03312] |
| permuted | teacher_uniform_minus_retrieval | -0.08317 [-0.11155, -0.05409] | -0.06468 [-0.09170, -0.03649] |
| permuted | zero_uniform_minus_retrieval | -0.07646 [-0.10408, -0.04701] | -0.06080 [-0.08754, -0.03366] |
| permuted | teacher_balanced_minus_retrieval | -0.08048 [-0.10912, -0.05142] | -0.06210 [-0.09001, -0.03315] |
| permuted | zero_balanced_minus_retrieval | -0.10731 [-0.13470, -0.07828] | -0.07503 [-0.10187, -0.04776] |
| permuted | teacher_uniform_minus_frozen_base | -0.01073 [-0.02183, +0.00000] | -0.00776 [-0.01826, +0.00262] |
| permuted | teacher_uniform_minus_original_failed_adapter | -0.00402 [-0.01088, +0.00266] | -0.00388 [-0.01049, +0.00256] |
| permuted | zero_uniform_minus_frozen_base | -0.00402 [-0.02823, +0.02185] | -0.00388 [-0.02384, +0.01529] |
| permuted | zero_uniform_minus_original_failed_adapter | +0.00268 [-0.02038, +0.02648] | +0.00000 [-0.01921, +0.01893] |
| permuted | teacher_balanced_minus_frozen_base | -0.00805 [-0.01919, +0.00283] | -0.00517 [-0.01548, +0.00528] |
| permuted | teacher_balanced_minus_original_failed_adapter | -0.00134 [-0.00820, +0.00539] | -0.00129 [-0.00790, +0.00521] |
| permuted | zero_balanced_minus_frozen_base | -0.03488 [-0.05974, -0.01039] | -0.01811 [-0.04110, +0.00372] |
| permuted | zero_balanced_minus_original_failed_adapter | -0.02817 [-0.05260, -0.00520] | -0.01423 [-0.03763, +0.00764] |

区间使用4,000次患者聚类配对重采样，未作多重比较校正，只描述这一训练种子的开发样本，不包含训练种子不确定性。全部模型与两种同分规则均保留，不据此选择新模型。

**独立核验：** 复核1,200个概率绑定、2,800组病例选择，并独立复算订单指标、病例内AUROC、排序相关性和配对区间。没有重跑优化器或神经前向。

[Machine-readable results](results/proposal_rank_diagnostic.json) · [Independent audit](results/proposal_rank_diagnostic_audit.json)

## 3. 这对下一次改进意味着什么

仅调阈值仍未解决排序失败。截断位置频繁同分还需要单独检查数值读出精度，才能判断是否源于学到的表示。后续逐药物读出应在候选换序时保留药物身份，并与相同检索证据、相同输出预算的对照比较。这里列的是下一步调查方向，尚未实现或验证为有效修复。现有多轮试验及选择门槛继续保持。

原guard尚未开放或尚待父实验核验，本诊断没有guard分数。
