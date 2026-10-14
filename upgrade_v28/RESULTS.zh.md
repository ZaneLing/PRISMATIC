# v0.28：答案协议与保留证据的工具汇总

## 1. 问题与已登记对照

针对v0.19失败实现两项固定修复：**C**＝从任务文字确定答案schema，不合规时在原预算内反馈重答；**S**＝分页获取Observation，再按编码和单位分别计算最近值／24小时统计，绑定真实来源。**K**＝原样冻结的v0.19两项技能。八种组合在各自执行前登记，C/S不冒充自主进化代码。

各方法保持相同模型、最多八次actor调用、每次512输出token、真实FHIR服务与原任务/评分逻辑。额外分页HTTP调用及token成本另报。schema失败会要求模型再次决策，不在评分后提取有利答案；统计绑定完整分页回执，缺单位/时间、未来/非数值记录明确标记，不推导新剂量或临床指南。

各划分此前已使用，因此这是由已见错误启发的探索性修复；所有组合固定，不根据验证/测试挑选胜者。精确API缓存可复用，逻辑费用不等于新增物理支出，共享账本还包含同时运行的其他试验。

## 2. 已独立核验的真实结果

Status / 状态：**partial**. Pending / 未完成 cells are not scored as zero.

**API中断：** 新请求返回HTTP402；未完成单元保留可续跑回执，等待补充额度。已完成并核验的分数保持有效。

| C: schema | S: statistics | K: frozen skills | Validation /80 | ID /64 | Held-out types /60 |
|---|---|---|---:|---:|---:|
| 0 | 0 | 0 | 45 | 38 | 18 |
| 0 | 0 | 1 | 53 | 45 | 10 |
| 0 | 1 | 0 | 49 | 36 | 43 |
| 0 | 1 | 1 | 59 | 46 | 50 |
| 1 | 0 | 0 | 52 | 46 | 29 |
| 1 | 0 | 1 | 54 | 49 | pending |
| 1 | 1 | 0 | 57 | 47 | pending |
| 1 | 1 | 1 | 66 | 54 | pending |

| Split | Declared contrast | Difference (pp) | Patient/query-cluster interval (pp) |
|---|---|---:|---:|
| val | contract_main_effect | +7.19 | [+1.51, +13.13] |
| val | statistics_main_effect | +8.44 | [+4.69, +12.18] |
| val | frozen_skills_main_effect | +9.06 | [+2.74, +15.82] |
| val | skills_on_full_repair | +11.25 | [+2.47, +20.00] |
| val | full_repair_no_skills_minus_original_fixed | +15.00 | [+6.94, +23.26] |
| val | contract_statistics_interaction | +4.38 | [-2.56, +10.44] |
| id_test | contract_main_effect | +12.11 | [+5.33, +19.72] |
| id_test | statistics_main_effect | +1.95 | [-2.87, +6.15] |
| id_test | frozen_skills_main_effect | +10.55 | [+1.67, +18.49] |
| id_test | skills_on_full_repair | +10.94 | [+0.00, +20.29] |
| id_test | full_repair_no_skills_minus_original_fixed | +14.06 | [+4.55, +24.24] |
| id_test | contract_statistics_interaction | +5.47 | [-0.81, +12.12] |

验证集包含62位显式患者及两道特意查询不存在患者的题目；两题各作独立查询重采样单元，共64个单元，不虚构患者编号。两个测试划分均有完整显式患者编号。

上表只填已完成且通过独立复评分、字段回读/清理及原始分页算术重建的单元。每组合一次固定运行、患者重叠和描述性区间不能证明普遍RSI优势。v0.19原主表不变。

## Evidence / 证据

- [Preregistered factorial](protocol.json)
- [Executed runtime probes](results/runtime_probe.json)
- [Independent cell audits and contrasts](results/summary.json)
- [Full execution counts](results/method_results.json)
