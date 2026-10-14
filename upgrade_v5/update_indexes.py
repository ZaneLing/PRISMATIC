"""Append executed v0.5 evidence to the long-lived bilingual plan and indexes."""
from pathlib import Path
import json
from render_results import HERE,read

def append_once(path,title,text):
    source=path.read_text()
    if title in source:source=source[:source.index(title)].rstrip()+'\n'
    path.write_text((source+'\n'+title+'\n\n'+text).rstrip()+'\n')

def run():
    root=HERE.parent;paper=root/'paper';r=read('llm_repair_results.json')
    m=r['test']['metrics'];fixed=m['repaired_review'];gated=m['gated_harness']
    zh=f'''已执行并交付 [v0.5 真实实验结果](../upgrade_v5/RESULTS.zh.md) 与[结构图](../upgrade_v5/ARCHITECTURE.md)。

- **E01 修复完成（工程层）：**逐例追踪 50 例；25 次空输出均为合法数组，20 次删光已有检索候选；缺失临床证据与历史预测状态已分离，解析器增加合法项保留和失败恢复。
- **E01 实测：**自由复核 F1={fixed['observed_micro_f1']:.5f}，空输出率={fixed['empty_output_fraction']:.0%}；旧版 0.20820 / 50%。验证门控 harness F1={gated['observed_micro_f1']:.5f}；这行不能替代临床完整订单结果。
- **E02/E03 条件记忆实验完成：**冻结 8,000 例基础模型，经验 250/1,000/4,000/16,000/32,000，固定 30 邻居和验证选择。基础 F1 0.34727，最终 0.35281；曲线非单调。词表/映射预先固定自 40,000 训练例，不是端到端低数据实验。
- **强基线与负消融：**词/字符静态排序三种子均值 0.39176；10% 记忆融合 0.39022 低于 seed-42 静态 0.39185。50 例验证表明 LLM 改写较差，门控保留排序候选。保留所有负结果。
- **工程验证：**8 项契约测试；病例级轨迹与 4,000 例聚合重算；旧版模板内容保持；英文源原位更新并使用内置编译器检查。
- **仍未完成：**医生评审经验、辅助药/盐水完整订单学习、成分级临床知识、SafeDrug/SafeRx 兼容复现、新患者确认及真实 FHIR。没有宣称超过这些原始方法。
'''
    en=f'''Delivered [v0.5 executed results](../upgrade_v5/RESULTS.en.md) and the [architecture diagram](../upgrade_v5/ARCHITECTURE.md).

- **E01 engineering repair:** trace all 50 cases; all 25 empty arrays are valid and 20 erase nonempty proposals. Separate historical predictions from clinical unknowns; preserve valid code members and recover invalid revisions.
- **E01 measurements:** free review F1={fixed['observed_micro_f1']:.5f}, empty rate={fixed['empty_output_fraction']:.0%}, versus v4 0.20820 / 50%. Validation-gated harness F1={gated['observed_micro_f1']:.5f}; not a clinically complete order result.
- **E02/E03 conditional memory:** freeze an 8,000-case base, replay 250/1,000/4,000/16,000/32,000 episodes with 30 neighbors and validation-selected updates. Base/final F1=0.34727/0.35281, non-monotonic. Vocabulary/mapping fixed from the common 40k training cohort; not end-to-end low-data learning.
- **Strong baseline and negative ablations:** static ensemble three-seed mean 0.39176; 10% memory fusion 0.39022 is worse than seed-42 static 0.39185. Validation also rejects LLM candidate edits. All failures are retained.
- **Verification:** eight contract tests; independent recalculation of LLM and 4k aggregates; embedded class unchanged; active English source updated in place and checked with the built-in compiler.
- **Outstanding:** clinician-rated experience, supportive/fluid full orders, ingredient-level knowledge, compatible SafeDrug/SafeRx implementations, independent patient confirmation and live FHIR. No claim of surpassing these original methods.
'''
    append_once(paper/'COMPLETION_PLAN.md','### v0.5 已执行：空输出修复、排序与经验更新（2026-10-14）',zh)
    append_once(paper/'COMPLETION_PLAN.en.md','### v0.5 executed: empty-output repair, ranking and experience updates (2026-10-14)',en)
    append_once(paper/'CHANGELOG.md','## v0.5-r1 — 2026-10-14',en+'\n'+zh)
    index=paper/'README.md';text=index.read_text().replace('**Active draft: v0.4-dev','**Active draft: v0.5-dev')
    start=text.index('**Latest executed batch:');end=text.index('\n## 下一步',start)
    text=text[:start]+'''**Latest executed batch: v0.5 r1. [真实实验结果（中文）](../upgrade_v5/RESULTS.zh.md) / [English results](../upgrade_v5/RESULTS.en.md) / [Architecture / 结构图](../upgrade_v5/ARCHITECTURE.md).** Table 2 retains the original failures and adds repaired LLM review, validation-gated inference and stronger 4,000-case candidate rankers. Training-only residual-memory growth is measured separately; its fusion negative result is preserved. SafeDrug, SafeRx-Agent and clinically complete orders remain unscored.
'''+text[end:]
    text=text.replace('The latest increment executes timestamp and route-mapping audits, freezes the development input/unknown-label/order protocol, and runs method comparisons and an order probe.',
        'The latest increment repairs excessive empty outputs, executes validation-selected ranking, runs a training-only residual-memory curve and evaluates the local LLM on the same 50 cases.')
    text=text.replace('See the [execution report](../upgrade_v4/RESULTS.en.md).','See the [execution report](../upgrade_v5/RESULTS.en.md).')
    if '| v0.5-dev |' not in text:
        text=text.replace('| v0.4-dev |','| v0.5-dev | [Active English source](latex/v0.3/prismatic_v03_en.tex), [executed evidence](../upgrade_v5/RESULTS.en.md) | Empty-output repair; conditional memory growth; stronger ranking; negative fusion ablation |\n| v0.4-dev |')
    text=text.replace('Panel A contains prevalence, retrieval, SGD and GAMENet text adaptation on 4,000 admissions.',
        'Panel A contains prevalence, retrieval, SGD, GAMENet text adaptation and v5 static/memory ranking on 4,000 admissions.')
    text=text.replace('Panel B uses the identical nested 50 cases for those methods and four fixed-backbone LLM approaches including bounded PRISMATIC.',
        'Panel B uses identical nested 50 cases for the original methods plus parser-only repair, revised review and validation-gated PRISMATIC.')
    index.write_text(text)

if __name__=='__main__':run()
