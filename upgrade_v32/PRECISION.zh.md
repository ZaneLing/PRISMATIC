# v0.32 固定权重的读出精度对照

## 1. 具体改变什么

三路读出共享同一次冻结骨干前向产生的隐藏状态。Native使用原量化词表投影；FP32用相同的四位权重、缩放和偏移，重建两个输出词元对应的行并用float32投影；Re-rounded把这些FP32 logits重新舍入为bfloat16后再计算概率。记忆、工具、骨干／适配器权重与候选模板均未更新。

FP32与Re-rounded的差异用于隔离新稠密投影中最后一步logit舍入。Native与FP32还包含投影运算差异，因此不能把全部差异归因于最后一步舍入。若有收益，应归因于数值实现；这项对照本身不证明学得的RSI收益。骨干仍为量化模型。

[Protocol](precision_protocol.json) · [Frozen clinical implementation](results/precision_execution_lock.json) · [Earlier ranking diagnosis](RANKING_DIAGNOSTIC.zh.md)

## 2. 已完成的工程核验

六个真实冻结模型状态，每个使用两条合成输入，每条含20个二元决策。这个阶段的12次骨干病例前向不含临床病例或真值标签。下表是不同分数的数量，属于数值诊断，不是处方性能。

| 状态 | Native：输入1／2 | FP32：输入1／2 | 重新舍入：输入1／2 |
|---|---:|---:|---:|
| 基础模型 | 18/18 | 20/20 | 18/18 |
| 原失败适配器 | 16/15 | 20/20 | 16/14 |
| 真实前缀／普通损失 | 16/12 | 20/20 | 16/12 |
| 全零前缀／普通损失 | 3/4 | 20/20 | 4/4 |
| 真实前缀／平衡损失 | 15/13 | 20/20 | 14/13 |
| 全零前缀／平衡损失 | 3/3 | 20/20 | 3/3 |

已直接读取模型文件中两个嵌入行的字节，并用NumPy独立重建。相对float64参照，logit最大差值为8.944e-06，概率最大差值为2.713e-06，重新舍入差值为0.0。六个状态的隐藏状态与原投影输出均为bfloat16。Native与重新舍入概率的最大差值达0.01562，说明两套投影实现并非数值完全一致。

该预检确认，最后一步logit舍入可以把不同的合成分数压成同分。它尚不能证明药物排序、处方F1或临床效果提高。

[Preflight receipt](results/precision_probe.json) · [Independent raw-weight audit](results/precision_probe_audit.json) · [Synthetic scoring-pipeline audit](results/precision_pipeline_probe.json)

## 3. 病例对照：等待独立核验

专用评价器与独立复算器已实现并冻结。已启动全部六个状态在proposal病例上的评价，覆盖原排序／随机排序、三路共享隐藏状态的读出和两种基于药物身份的同分规则。尚无通过独立核验的病例精度对照成绩。原模型／阈值选择与测试门槛继续保持。
