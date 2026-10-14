# v0.19：真实 FHIR 执行——完整跨方法结果

## 1. 结果与结论

**技能学习提高了本次同类任务分数，却损害未见任务类型；不能称为整体进化成功。** 各方法共用模型、八次调用上限、actor512token和真实本地FHIR服务。固定harness还添加流程指令，因此直接工具与固定harness的差异不能只归因于订单编译器。

| 方法 | 同类正确数（64） | 未见类型正确数（60） | 同类／迁移模型调用数 |
|---|---:|---:|---:|
| 直接工具 | 39 | 27 | 133 / 120 |
| 固定编译harness | 38 | 17 | 174 / 139 |
| 进化技能＋编译harness | 45 | 10 | 207 / 124 |

同类任务相对固定流程提高10.94个百分点，但患者聚类区间包含零。未见类型相对固定流程下降11.67个百分点，相对直接工具下降28.33个百分点，两个区间均为负。未见task7中，技能版0/30、固定版5/30、直接工具14/30。三臂在未见类型上都没有写入操作，因此不能用写入序列化解释这部分退化。

| Split | Contrast | Difference (pp) | Patient-cluster 95% interval (pp) | Fixes / regressions |
|---|---|---:|---:|---:|
| id_test | fixed compiled  minus  direct tools | -1.56 | [-11.86, +8.70] | 5 / 6 |
| id_test | evolving compiled  minus  fixed compiled | +10.94 | [+0.00, +20.55] | 9 / 2 |
| id_test | evolving compiled  minus  direct tools | +9.38 | [-1.72, +19.30] | 11 / 5 |
| test | fixed compiled  minus  direct tools | -16.67 | [-26.23, -8.20] | 0 / 10 |
| test | evolving compiled  minus  fixed compiled | -11.67 | [-22.95, -1.64] | 2 / 9 |
| test | evolving compiled  minus  direct tools | -28.33 | [-40.68, -16.67] | 1 / 18 |

区间使用4,000次描述性患者聚类配对重采样：同类测试47人、迁移测试53人。只有一个学习种子，各划分存在患者重叠，未校正多重比较。逐任务区间另保存在JSON中。这是修订执行终点，不能冒充原版官方榜单成绩。

## 2. 到底进化了什么

原版GRASP优化器处理96例训练任务，分四批、每批24例，四个提议名额、12例训练探针。第1轮新增姓名检索技能，第2轮新增检验代码/文本回退技能，第3/4轮没有新增接纳。80例验证从45/80升至53/80，冻结后才测64例同类及60例未见类型。改变的是持久语言技能文件；模型参数、编译器、流程反馈、评分器固定，没有证明自主进化工具代码。

[原始技能文件](artifacts/model_authored_skills/README.md)保留原哈希。技能中的示例观察是模型写的示例，不能充当执行证据。测试后的只读核查发现：原工具已经自动编码空格，原始姓名与显式编码产生完全相同的URL，也都没有找到该示例患者；因此技能的因果解释在本工具中不成立。全库A1C代码/文本查询分别244/258条，MG均3538条，这不能证明特定患者的回退有效；药物途径转换也不能推导检验编码形式。技能仍保留姓名/日期示例，违反更新指引；核查没有据此重新选择技能。

## 3. 冻结技能消融

单技能实验在各自执行前登记，但登记时已经看过直接/固定方法测试结果。比较无技能、仅姓名、仅检验、二者组合，预算一致，不重新训练或修改提示。这是探索性归因，不是新的未触碰确认。

Status: **complete**. Each numeric cell below has finished and passed the independent reference/receipt audit; unfinished cells stay pending.

| 技能状态 | 同类（64） | 未见类型（60） |
|---|---:|---:|
| 仅姓名技能 | 44 | 14 |
| 仅检验技能 | 39 | 11 |
| 无技能 | 38 | 17 |
| 两项技能 | 45 | 10 |

| Split | Contrast | Difference (pp) | Patient-cluster interval (pp) |
|---|---|---:|---:|
| id_test | both_minus_name_only | +1.56 | [-6.35, +9.68] |
| id_test | both_minus_lab_only | +9.38 | [+0.00, +17.74] |
| id_test | name_only_minus_neither | +9.38 | [-3.13, +20.31] |
| id_test | lab_only_minus_neither | +1.56 | [-3.33, +6.85] |
| id_test | interaction | +0.00 | [-10.35, +10.77] |
| test | both_minus_name_only | -6.67 | [-15.00, +1.52] |
| test | both_minus_lab_only | -1.67 | [-8.62, +5.26] |
| test | name_only_minus_neither | -5.00 | [-14.52, +4.84] |
| test | lab_only_minus_neither | -10.00 | [-20.69, +0.00] |
| test | interaction | +3.33 | [-8.62, +15.25] |

ID interaction is0.00 pp and transfer interaction+3.33 pp; both patient intervals include zero. Individual removal contrasts likewise have intervals containing zero. The observed counts do not establish robust synergy or a universally beneficial skill. / 同类交互0.00个百分点，迁移交互+3.33个百分点，两个患者区间均含零；单项移除的区间同样含零，不能据此宣称稳健协同或某项技能普遍有效。

## 4. 真实执行与评分修订

官方公开MedAgentBench程序和数据库在本地HAPI FHIR7.6.0运行，原五项CRUD/原子失败检查通过。合成订单曾出现HTTP201但剂量字段丢失；把途径转为CodeableConcept文本后保留完整，主动触发丢字段也验证了回滚与反馈。这些是固定工程修复，不是进化成果。

初次学习在开发阶段发现旧评分器将合法注释数组判错，造成13次假阴性，随后停止。修订从空技能重启，对所有方法采用同一无损note/route格式视图，保留原始评分。最终完整主实验中，原始轨迹、实际回读及修订参考分数恰好一致。独立复评分及回执审计全部通过：同类测试直接/固定/技能版分别14/23/21次写入，无回读失败，资源数全部恢复；旧数据速度单位的临床语义仍未验证。

JSON费用是逻辑轨迹费用；相同代码/病例/技能允许精确缓存重放，保留首次物理回执，清理操作单独计数。对象为公开基准研究任务，不是临床部署。

## 5. task7为什么0/30：答案协议与数值错误分开看

测试后只读审计读取完整原参考记录。技能版30例都返回`[数值, 时间]`，但task7要求仅含一个数值的列表；其中15例首个数值正确，只因额外时间戳判错，另外15例数值也错误。仅姓名技能则30例都返回文字字符串。因此0/30不等于30次血糖数值都错；只校验JSON合法性修不好这个输出协议问题。

把保存答案投影到首个数值只是诊断，不替换主表，也不冒充实际修复agent成绩。下一登记干预应加入明确答案schema和动作预算核算，各方法统一评价。[独立格式/数值审计](results/answer_contract_audit.json)。

## Evidence / 证据

- [Complete scores, paired intervals, task types and independent audits](results/summary.json)
- [Frozen skills and original selection protocol](results/frozen_skills.json)
- [Read-only claim audit](results/skill_claim_audit.json)
- [Skill attribution protocol](ablation_protocol.json)
- [Development grading revision](results/grading_revision.json)
