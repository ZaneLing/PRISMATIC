# v0.20：真实开单时间审计

## 为什么要检查

之前的标签按处方预定 starttime 选入。provider `ordertime` 是医嘱开立时间，药房 `entertime` 是药房录入时间，两者与开始给药时间含义不同，未来开始用药不一定意味着未来才做处方决策。[医嘱表文档](https://mimic.mit.edu/docs/iv/modules/hosp/poe.html)、[药房表文档](https://mimic.mit.edu/docs/iv/modules/hosp/pharmacy.html)。

## 已执行的全体目标行审计

连接原目标的全部 1,788,195 行，涉及至少有一条目标的 142,768 次住院。只有患者和住院编号同时相符，才使用关联时间。

| Timestamp finding | Order rows | Fraction of all target rows |
|---|---:|---:|
| Exact-identity provider time available | 1,743,666 | 97.51% |
| Provider order before admission | 42,005 | 2.35% |
| Provider order within next 6 hours | 1,425,392 | 79.71% |
| Provider order at/after hour 6 | 276,269 | 15.45% |
| Pharmacy entry within next 6 hours | 1,777,546 | 99.40% |

provider 关联中有 438 行住院编号冲突、0 行患者编号冲突，冲突行不提供可信时间；药房关联的患者/住院编号均一致，两张关联键表都没有重复键。无法可靠关联的开单时间保留为未知。逐行数据及联表只留在本地受限目录。

两个时钟差异明显：99.40% 的药房录入在原窗口内，只有 79.71% 的匹配 provider 开单在窗口内。本审计尚不能解释全部差异原因，也不选择数值更有利的时钟。旧成绩仍对应其声明的回顾性开始时间任务，不能用于证明严格前瞻性的新订单预测效果。

## 下一协议必须怎么修复

从完整处方/录入表重新构建队列，固定决策点、分来源定义可用时间，并明确处理相互冲突的时钟。不能只筛旧的 starttime 标签文件，否则会漏掉实际在窗口内开立、但预定开始在旧窗口外的订单。严格可用性主分析排除无录入时间的分诊/用药核对字段；检验同时限制 charttime 和 storetime。旧试验独立保留，新确认病例保持患者切分。此审计不冒充新任务上的预测分数。
