"""Generate bilingual versioned reports from executed aggregate result files."""
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
def read(name):return json.loads((HERE/'results'/name).read_text())
def table(headers,rows):
    return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+''.join('| '+' | '.join(map(str,r))+' |\n' for r in rows)
def f(x):return f'{x:.5f}'

def run():
    rank=read('ranker_memory_results.json');fusion=read('memory_fusion_results.json')
    llm=read('llm_repair_results.json');seeds=read('seed_robustness.json');audit=read('empty_audit.json')
    old=json.loads((HERE.parent/'upgrade_v4/results/local_harness_results.json').read_text())
    parser=read('parser_ablation.json')['metrics']
    main=[['Training prevalence',4000,'0.28390','5','v4 fixed'],
          ['Case retrieval (30 neighbors)',4000,'0.32813','5','v4 fixed'],
          ['TF-IDF/SGD',4000,'0.38635 ± 0.00067','5','3 seeds'],
          ['GAMENet text/single-visit adaptation',4000,'0.34357 ± 0.00219','5','3 seeds; NOT original reproduction'],
          ['Static word + character ensemble',4000,f(seeds['f1_mean'])+' ± '+f(seeds['f1_sample_sd']),'5','3 seeds; validation-selected configuration'],
          ['Static ensemble, seed 42',4000,f(rank['metrics']['validation_selected_anchor']['micro_f1_at_5']),'5','ablation: no growing memory'],
          ['PRISMATIC candidate ranker + residual memory',4000,f(fusion['test']['micro_f1_at_5']),'5','seed 42; 10% memory fusion; no LLM at 4k'],
          ['SafeDrug compatible reproduction','—','—','—','not executed'],
          ['SafeRx-Agent compatible reproduction','—','—','—','not executed'],
          ['Clinically complete PRISMATIC','—','—','—','clinical ratings and full-order evidence missing']]
    base=json.loads((HERE.parent/'upgrade_v4/results/protocol_method_results.json').read_text())['same_50_case_baselines']
    gamenet=json.loads((HERE.parent/'upgrade_v4/results/gamenet_adaptation_results.json').read_text())['same_50_case_seed42']
    pilot=[]
    for name,z in [('Training prevalence',base['prevalence']),('30-neighbor voting',base['case_retrieval']),
                   ('v4 TF-IDF/SGD seed 42',base['direct_sgd']),('GAMENet text adaptation seed 42',gamenet)]:
        pilot.append([name,f(z['micro_f1_at_5']),f(z['precision_at_5']),f(z['micro_recall_at_5']),'0%','N/A (structured)','5.00'])
    for name,key in [('v4 direct','direct'),('v4 ordinary repeat','ordinary_repeat'),('v4 RAG','case_retrieval'),('v4 bounded harness','bounded_harness')]:
        m=old['metrics'][key]
        pilot.append([name,f(m['observed_micro_f1']),f(m['observed_precision']),f(m['observed_recall']),f"{m['empty_output_fraction']:.0%}",f"{m['valid_json_fraction']:.0%}",f"{m['mean_predicted_classes']:.2f}"])
    for name,key in [('v5 repaired RAG review','repaired_review'),('v5 candidate ranker + memory only','anchor_only'),('v5 unrestricted anchor LLM revision','anchor_llm_revision'),('v5 validation-gated harness','gated_harness')]:
        m=llm['test']['metrics'][key]
        pilot.append([name,f(m['observed_micro_f1']),f(m['observed_precision']),f(m['observed_recall']),f"{m['empty_output_fraction']:.0%}",f"{m['valid_json_fraction']:.0%}",f"{m['mean_predicted_classes']:.2f}"])
    z=parser['v4_retrieval_salvage']
    pilot.append(['v4 RAG + parser repair only (no new call)',f(z['observed_micro_f1']),f(z['observed_precision']),f(z['observed_recall']),'0%','90% raw unchanged',f"{z['mean_predicted_classes']:.2f}"])
    growth=[[r['memory_size'],r.get('beta',0),f(r['validation_f1']),f(r['test']['micro_f1_at_5'])] for r in rank['growth']]
    gate=llm['gate']; repaired=llm['test']['metrics']['repaired_review'];final=llm['test']['metrics']['gated_harness']
    costs=[]
    for a in ['retrieval_proposal','repaired_review','anchor_llm_revision','gated_harness']:
        m=llm['test']['metrics'][a];costs.append([a,m['input_tokens'],m['generated_tokens'],m['arm_seconds']])
    tables='\n## Table 1. Same-cohort method comparison / 同队列跨方法主表\n\n'+table(
        ['Method / 方法','N','Observed micro-F1@5','Classes/case','Scope / 范围'],main)
    tables+='\n## Table 2. Same 50-case local-LLM comparison / 相同 50 例本地模型对照\n\n'+table(
        ['Method / 方法','F1','Precision','Recall','Empty','Raw valid','Mean classes'],pilot)
    tables+='\n## Table 3. Frozen-base memory growth / 冻结模型病例记忆增长\n\n'+table(
        ['Memory episodes','Residual weight','Validation F1','Development test F1'],growth)
    tables+='\n![Memory growth / 记忆增长](results/memory_growth.png)\n'
    tables+='\n## Table 4. Actual LLM budget / 实际模型预算\n\n'+table(['Arm','Input tokens','Output tokens','Seconds (sum)'],costs)
    ci=lambda r: f"{r['delta']:+.5f}, 95% CI [{r['patient_bootstrap_95pct'][0]:+.5f}, {r['patient_bootstrap_95pct'][1]:+.5f}]"
    zh=f'''# PRISMATIC v0.5 执行结果：空输出修复与经验更新

版本：2026-10-14，v5-r1。保留 v4 原始负结果；本文由真实结果 JSON 自动生成。

## 摘要

**旧版确有设计问题。** 50 例中 25 次空输出全部是合法空数组；其中 20 次清空非空检索候选，19 例有已映射历史处方。主要原因是把缺失临床信息解释为统一删药条件。旧解析器另有单项非法导致整单丢失的问题。

修复后，自由输出的 RAG 复核 F1 为 **{repaired['observed_micro_f1']:.5f}**，空输出率 **{repaired['empty_output_fraction']:.0%}**；旧版为 0.20820 和 50%。这一行没有强制补满五项。独立的验证门控 harness F1 为 **{final['observed_micro_f1']:.5f}**。它使用监督排序与记忆候选，资源条件与纯 LLM 不同，必须结合消融解释。

4,000 例上，静态词/字符集成 seed 42 F1=0.39185，旧 SGD seed 42=0.38701，配对差值 +0.00484，患者聚类 bootstrap 95% CI [0.00160,0.00803]。三种固定种子结果见主表。残差记忆独立实验从 0.34727 升至 0.35281，差值 +0.00554，CI [0.00282,0.00833]；但最终融合比强静态排序器低 0.00163。这不是所有迭代都会提高的证据。

## 数据、协议与可比性

- MIMIC-IV v3.1 + MIMIC-IV-ED v2.2；入院时刻，预测未来六小时全途径历史处方的 ATC-L4 集合。
- 训练 40,000、验证 4,000、开发测试 4,000 例，患者不跨划分；80 个训练高频类别。50 例 LLM 测试是此前相同开发病例，另用 50 验证例决定接受或拒绝改写。
- 目标映射覆盖 45.535%；盐水名称代理订单未映射。这里是历史记录重叠度，不是合理处方、盐水指征或临床安全率。
- Table 1 固定五类候选，Table 2 的模型自由输出最多五类；不同 N 和输出数量不能直接混比。Table 1 的 4,000 例没有运行 LLM。
- 验证集选择所有新参数；测试结果不用于选择。测试集此前已反复查看，不能声称独立确认。
- 新模型仍为本地固定 Qwen3-4B-Instruct-2507 4bit；没有受限病例上传 OpenRouter。原 v4 每次生成上限 192，新复核上限 384，实际 token 在 Table 4 报告，非严格等成本实验。
'''
    en=f'''# PRISMATIC v0.5 executed results: empty-output repair and experience updates

Version: 14 October 2026, v5-r1. Generated from executed result JSON; original v4 negative results are preserved.

## Abstract

**The v4 design had a genuine failure.** All 25 empty responses among 50 cases were valid arrays; 20 erased nonempty retrieval proposals, and 19 had observed mapped targets. The main cause was a blanket removal instruction conflating unavailable clinical evidence with historical-order prediction. The parser also had an independent all-or-nothing invalid-member failure.

The repaired free-output RAG review achieves **{repaired['observed_micro_f1']:.5f} F1** with **{repaired['empty_output_fraction']:.0%} empty responses**, versus 0.20820 and 50% for v4. This arm does not force five predictions. The separate validation-gated harness achieves **{final['observed_micro_f1']:.5f} F1** with supervised ranking and memory candidates; it has different training resources from the pure LLM arms.

On 4,000 cases, the static word/character ensemble reaches seed-42 F1=0.39185 versus 0.38701 for the old seed-42 SGD, a paired gain of 0.00484 (patient-bootstrap 95% CI [0.00160,0.00803]). Three frozen-configuration seeds appear below. The independent residual-memory experiment improves from 0.34727 to 0.35281, delta 0.00554 (CI [0.00282,0.00833]); however, fusing memory into the stronger static ranker reduces F1 by 0.00163. More experience does not guarantee monotonic improvement.

## Dataset, protocol and comparability

- MIMIC-IV v3.1 + MIMIC-IV-ED v2.2; admission snapshot; six-hour all-route historical ATC-L4 targets.
- Patient-disjoint 40,000/4,000/4,000 train/validation/development-test admissions, 80 training-selected classes. The LLM uses the same old 50 test cases and a separate 50 validation cases for revision gating.
- Mapping coverage is 45.535%; saline-name proxy orders are absent from the map. Scores measure observed historical agreement, not appropriate indications, fluid quality or safety.
- Table 1 fixes five candidates; Table 2 permits up to five LLM outputs. Different sample sizes and set-size budgets are not interchangeable. No LLM was run on the 4,000-case panel.
- All new policy choices use validation only. The repeatedly inspected test is developmental, not independent confirmation.
- Same local frozen Qwen3-4B-Instruct-2507 4bit; no restricted data sent to OpenRouter. v4 generation cap was 192; v5 revision cap is 384. Actual tokens are reported; this is not an exactly cost-matched experiment.
'''
    detail_en=f'''
## Parser-only ablation: the extra review has little demonstrated benefit

Replaying the old RAG generations through the repaired parser, with **zero additional LLM calls**, gives F1={parser['v4_retrieval_salvage']['observed_micro_f1']:.5f} and no empty outputs. This is almost the same as the new review's {repaired['observed_micro_f1']:.5f}. With the old strict parser, the new review reaches {parser['v5_repaired_generation_strict']['observed_micro_f1']:.5f} with 8% empty outputs. The old bounded review remains 0.20820 / 50% under either parser. Thus the repair recovers the damage caused by the old reviewer; it does not establish a useful reasoning gain over RAG plus robust parsing. New per-call generations use at most 32 tokens, so the higher 384-token cap is inactive in this run.

The selected 50-case harness (0.41015) still trails the old supervised SGD (0.42706). The unrestricted LLM edit arm happens to perform better on this test than the gated arm, despite being worse on validation. We do not change the frozen gate after seeing this result.

## Paired repair effects and gate outcome

- Repaired review minus old bounded harness: {ci(llm['paired_repaired_minus_v4'])}.
- Repaired review minus original RAG: {ci(llm['paired_repaired_minus_retrieval'])}.
- Validation F1: candidate ranker {gate['validation_anchor_f1']:.5f}, unrestricted LLM revision {gate['validation_llm_revision_f1']:.5f}. LLM prediction edits accepted: **{gate['use_llm_prediction_revision']}**.
- The gated arm still executes and charges the LLM review even if edits are rejected. A retained five-class ranker has zero empty outputs by construction; this does not establish drug need or clinical correctness.

## Implemented changes and evolution

See [bilingual architecture with diagram](ARCHITECTURE.md). v4 did not update experience. v5 freezes a base ranker trained on 8,000 admissions, stores residual feedback from up to 32,000 disjoint training-patient admissions, retrieves 30 episodes, and versions validation-promoted corrections. There are no LLM weight updates. Vocabulary/mapping remain fixed from the shared 40k cohort, so growth is conditional on that representation. Historical records are not clinician-rated prescriptions.

The static ensemble and growing memory are reported separately. The small validation fusion gain failed to transfer to the test; the selected 10% memory policy is retained and reported, rather than switched after inspecting test results. Only the 50-case panel executes the LLM/state/flag pipeline.

## Literature-informed scope

SafeRx-Agent motivates separating flag collection from case-specific verification; MedAgentSim motivates experience replay; MedAgentBench motivates checking real tool state. [Architecture and primary sources](ARCHITECTURE.md#4-what-we-borrowed-from-the-literature--从相关工作借鉴什么) explain the implementation boundaries. None was faithfully reproduced in this increment. Original cross-paper scores are never pasted into the method table. Beating our GAMENet adaptation does not establish superiority over the original GAMENet, SafeRx-Agent or current state of the art.

## Remaining work and acceptance criteria

1. **Full-order feedback:** obtain the two blinded reviewers' indication/fluid-role/volume/rate/renal/DDI ratings; preserve unknowns and disputed ratings. ATC-only gains do not close this endpoint.
2. **Validated knowledge:** ingredient/RxNorm mapping, timestamp-valid renal/weight/allergy facts, sourced indication/contraindication rules; coarse graph flags cannot authorize orders.
3. **Experience quality:** clinician-accepted correction episodes, fixed promotion margins, patient-disjoint nested validation and harmful-regression endpoints; compare raw case retrieval, residual memory and clinically reviewed memory.
4. **Cross-method evidence:** compatible SafeDrug molecules and independently executable SafeRx architecture; same data/input/budget, clearly named adaptations.
5. **Confirmation:** freeze the final policy and evaluate a new patient cohort; live FHIR MedAgentBench tasks and complete public secondary ablations remain required.

## Reproduction and artifacts

See [commands and file map](README.md). Aggregate JSON is in `results/`; patient-level inputs, traces, fitted models and predictions remain under the restricted `prismatic-v5` directory. Eight contract tests cover parser recovery, unknown/contradiction semantics, train-only feedback, replay and rollback. Prior v4 outputs are unchanged.
'''
    detail_zh=f'''
## 仅修解析器的消融：额外复核尚无明显收益

把旧 RAG 原始回答直接交给新解析器，**不增加任何 LLM 调用**，F1 就达到 {parser['v4_retrieval_salvage']['observed_micro_f1']:.5f}，空输出为零，几乎等于新复核的 {repaired['observed_micro_f1']:.5f}。新复核若仍用旧严格解析器，则 F1={parser['v5_repaired_generation_strict']['observed_micro_f1']:.5f}、空输出 8%。旧 bounded harness 在两种解析器下都维持 0.20820 / 50%。因此，本轮主要恢复了旧复核造成的损失，尚未证明额外复核优于“RAG＋可靠解析”。新增调用最多生成 32 token，因此本次没有触及提高后的 384 token 上限。

最终 50 例 harness 的 0.41015 仍低于旧监督 SGD 的 0.42706。自由 LLM 改写在测试上偶然高于门控结果，但在验证上更差；不能看到测试结果后反过来更换已冻结门控。

## 配对差值与门控结果

- 新复核减旧 harness：{ci(llm['paired_repaired_minus_v4'])}。
- 新复核减原 RAG：{ci(llm['paired_repaired_minus_retrieval'])}。
- 验证 F1：候选排序 {gate['validation_anchor_f1']:.5f}，自由 LLM 改写 {gate['validation_llm_revision_f1']:.5f}；是否接受改写：**{gate['use_llm_prediction_revision']}**。
- 门控拒绝改写时，仍执行并计入 LLM 成本。固定五类排序器的零空输出是构造性质，不能当作临床正确性提升。

## 已实现的修复、自进化和迭代

详见[中英结构图与模块说明](ARCHITECTURE.md)。旧版没有经验更新；本轮冻结 8,000 例训练的基础排序器，用其他训练患者的最多 32,000 例历史记录建立残差经验记忆，每次检索 30 条，用验证集回放决定版本升级或保留。没有更新大模型权重。词表和映射固定自共同 40,000 例，因此是条件记忆增长实验，历史记录也不等于医生认可的处方。

静态排序改进和记忆贡献分开报告。融合在验证集上有微弱提高，但没有迁移到测试集；保留验证集选中的 10% 记忆比例，不看测试结果换成另一配置。完整的本地 LLM、状态、风险标记链路仅在 50 例面板执行。

## 与相关方法的关系

SafeRx-Agent 启发先收集风险再逐项核验，MedAgentSim 启发经验回放，MedAgentBench 要求验证真实工具状态。[结构文档及原始来源](ARCHITECTURE.md)记录具体边界。这一轮没有完整复现这些方法，不能把对方论文分数贴进我们的表，也不能因为超过本地 GAMENet 改编版，就宣称超过原始 GAMENet、SafeRx-Agent 或最新最佳方法。

## 下一轮逐项交付与验收

1. **完整订单反馈：**收取两位盲评者对指征、盐水用途/量/速度、漏开、误报、DDI、肾功能调整的独立评分；保留未知与分歧。ATC 提升不能替代这一项。
2. **有效知识：**补齐成分/RxNorm 映射，以及时间可用的肾功能、体重、过敏事实和带来源的指征/禁忌证据；类级 DDI 标记不能用于自动处方授权。
3. **经验质量：**加入医生接受的纠错经验、预先固定的升级幅度门槛、患者独立的嵌套验证和严重退化指标；比较普通病例检索、残差记忆、临床评审记忆。
4. **真正跨方法：**补齐 SafeDrug 兼容成分和 SafeRx 可执行架构，在同数据、同输入、同预算下测量，独立改编必须标注。
5. **确认实验：**冻结最终配置，在新患者队列验证；补真实 FHIR 的 MedAgentBench 和公开次级集完整消融。

## 复现与交付

命令与文件索引见 [README](README.md)。`results/` 为可公开汇总，病例、轨迹、权重和预测保存在受限 `prismatic-v5` 目录。8 个契约测试覆盖解析恢复、未知/矛盾状态、训练反馈限制、回放和回滚。旧版 v4 结果未改动。
'''
    (HERE/'RESULTS.zh.md').write_text(zh+tables+detail_zh)
    (HERE/'RESULTS.en.md').write_text(en+tables+detail_en)

if __name__=='__main__':run()
