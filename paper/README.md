# PRISMATIC 论文版本索引 / Versioned manuscript index

**当前版本 / Current version: v0.3（2026-10-14）**

## 主表在哪里？/ Where is the main table?

- **主表：**[v0.3 中文 LaTeX，表 2](latex/v0.3/prismatic_v03_zh.tex) / [v0.3 English LaTeX, Table 2](latex/v0.3/prismatic_v03_en.tex)。两份源文件已用 Codex 内置 LaTeX 编译器成功编译。
- **主表行是方法：**训练集流行度、病例检索、直接预测、GAMENet、SafeDrug、SafeRx-Agent、PRISMATIC 完整 harness。现有前三行来自同一 MIMIC 测试集的本地实跑；后四行没有可比结果，故留空。
- **主表数据集：**受限 MIMIC-IV v3.1 + MIMIC-IV-ED v2.2；201,750 次符合急诊入院时间条件的记录全部保留，不按未来医嘱筛人；入院时点可见信息预测后六小时医嘱；ATC-L4 编码；按患者不交叉切分。初试共用 40,000/4,000/4,000 入院记录和每例五个预测。映射只覆盖 45.652% 的六小时医嘱，因此这是历史医嘱重合初试，尚非临床安全主张。
- **公开次级集：**RxSafeBench 去重全量 2,000 题及 RxQA OpenFDA 全量 300 题。选择题模型结果、v0.2 的轻量 harness 试验均不进入处方主表。
- **双人临床盲评：**[中英文规程](../upgrade_v3/CLINICAL_REVIEW_PROTOCOL.md)及共同测试集 200 例的本地受限清单已准备；实际处方输出和双人评分尚未完成。

## 版本 / Releases

| 版本 | 日期 | 中文 | English | 主表性质 |
| --- | --- | --- | --- | --- |
| v0.3 | 2026-10-14 | [LaTeX 论文](latex/v0.3/prismatic_v03_zh.tex) | [LaTeX paper](latex/v0.3/prismatic_v03_en.tex) | 以方法为行的 MIMIC ATC-L4 处方主表；已跑三行、四行待复现 |
| v0.2 | 2026-10-14 | [Markdown 归档](versions/v0.2-2026-10-14.zh.md) | [Markdown archive](versions/v0.2-2026-10-14.en.md) | RxSafeBench 60 题、按基础模型对比的轻量 harness 试验 |
| v0.1 | 2026-10-14 | [Markdown 初版](versions/v0.1-2026-10-14.zh.md) | [Markdown first report](versions/v0.1-2026-10-14.en.md) | 病例增长和初期模型测试 |

## 更新规则 / Update contract

1. 新实验保留旧版，新增独立编号的中英文 LaTeX 源文件；两份必须成功编译，并在[变更记录](CHANGELOG.md)中写明新增结果、协议变化和未完成项。
2. 主表只写同一数据、时间冻结输入、患者切分、药物空间和指标下重跑的结果。其他论文报告的原始分数放相关工作，永不抄进主表。
3. 每个数字须可追溯到[映射审计](../upgrade_v3/results/atc4_mapping_audit.json)、[方法初试](../upgrade_v3/results/atc4_method_pilot.json)或[公开全量结果](../upgrade_v3/results)。受限逐例数据留在本地授权目录。
4. 临床适宜性、DDI、肾功能及盐水剂量/速度只在完整订单输出和双人审定后填入；历史医嘱重合率不替代这些终点。
