"""Recount frozen-skill transfer after all four same-backbone methods finish."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
LOCAL=Path.home()/'Desktop/PRISMATIC/upgrade_v2/.local/rxrsi-v8'
sys.path.insert(0,str(ROOT/'upgrade_v17'))
from summarize import interval

def read(p):return json.loads(p.read_text())

def main():
    report=read(HERE/'results/method_results.json')
    if report['status']!='complete':raise SystemExit('All four methods must complete before comparative reporting.')
    frozen=read(HERE/'results/frozen_transfer.json');assert not frozen['test_labels_used']
    for name,path in [('author_skill_hashes',LOCAL/'official-grasp-seed-42/skills/best'),('grounded_skill_hashes',LOCAL/'grounded-grasp-v17-seed-42/skills/best')]:
        assert {str(p.relative_to(path)):hashlib.sha256(p.read_bytes()).hexdigest() for p in path.rglob('*') if p.is_file()}==frozen[name]
    cases=read(LOCAL/'data.json')['parts']['test'];correct={};methods={};audit=[];saved_rows={}
    for name,expected in report['methods'].items():
        rows=read(LOCAL/'backbone-transfer-v18'/f'{name}-test.json')
        assert [r['case_id'] for r in rows]==[c['id'] for c in cases]
        values=np.array([r['prediction']==c['gold'] for r,c in zip(rows,cases)],dtype=int)
        assert all(bool(r['correct'])==bool(v) for r,v in zip(rows,values))
        assert values.sum()==expected['correct'] and len(rows)==expected['n']==988
        assert sum(r['prediction'] is None for r in rows)==expected['invalid']
        assert abs(sum(r.get('cost_usd') or 0 for r in rows)-expected['cost_usd'])<1e-10
        correct[name]=values;methods[name]=expected;saved_rows[name]=rows;audit.append({'method':name,'count_alignment_cost_recount':'passed'})
    pairs={}
    for left,right in [('frozen_author_grasp','cot'),('fixed_grounded','cot'),('frozen_grounded_grasp','cot'),('frozen_grounded_grasp','fixed_grounded'),('frozen_grounded_grasp','frozen_author_grasp')]:
        delta=correct[left]-correct[right]
        pairs[left+'__minus__'+right]={**interval(delta,cases),'fixes':int((delta>0).sum()),'regressions':int((delta<0).sum())}
    a=saved_rows['fixed_grounded'];b=saved_rows['frozen_grounded_grasp']
    diagnostic={'scope':'Post-hoc diagnostic only; no generation/selection changes. Received invalid answers remain wrong in the main table.',
      'newly_invalid':sum(x['prediction'] is not None and y['prediction'] is None for x,y in zip(a,b)),
      'fixed_correct_became_invalid':sum(x['correct'] and y['prediction'] is None for x,y in zip(a,b)),
      'invalid_repaired':sum(x['prediction'] is None and y['prediction'] is not None for x,y in zip(a,b)),
      'grounded_skill_invalid_and_finish_length':sum(y['prediction'] is None and y['finish_reason']=='length' for y in b),
      'both_valid_cases':sum(x['prediction'] is not None and y['prediction'] is not None for x,y in zip(a,b)),
      'both_valid_fixed_correct':sum(x['correct'] and x['prediction'] is not None and y['prediction'] is not None for x,y in zip(a,b)),
      'both_valid_skill_correct':sum(y['correct'] and x['prediction'] is not None and y['prediction'] is not None for x,y in zip(a,b)),
      'mean_input_tokens_fixed':sum(x['input_tokens'] for x in a)/len(a),'mean_input_tokens_skill':sum(x['input_tokens'] for x in b)/len(b)}
    (HERE/'results/transfer_failure_audit.json').write_text(json.dumps(diagnostic,indent=2)+'\n')
    interaction=correct['frozen_grounded_grasp']-correct['fixed_grounded']-correct['frozen_author_grasp']+correct['cot']
    summary={'status':'complete','methods':methods,'paired':pairs,'factorial_interaction':interval(interaction,cases),'audits':audit,
      'protocol':frozen['protocol'],'interpretation':'Frozen skill transfer, not Gemini skill training or checkpoint selection. One seed/artifact path; exploratory intervals.',
      'cost_scope':'Logical successful-response usage, including cache reuse; learning cost belongs to the original DeepSeek study. The local ledger records returned usage, not provider-reconciled billing. Timed-out or retried requests may incur additional charges without returned usage.'}
    (HERE/'results/summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    labels={'cot':'CoT','frozen_author_grasp':'Frozen author-GRASP skills','fixed_grounded':'Fixed grounded harness','frozen_grounded_grasp':'Frozen grounded skills'}
    table='| Method | Correct / 988 | Accuracy (%) | Invalid | Logical inference USD |\n|---|---:|---:|---:|---:|\n'
    for k,label in labels.items():
        r=methods[k];table+=f"| {label} | {r['correct']} | {100*r['accuracy']:.2f} | {r['invalid']} | {r['cost_usd']:.4f} |\n"
    contrasts='| Contrast | Difference (pp) | Scenario-cluster 95% interval (pp) | Fixes / regressions |\n|---|---:|---:|---:|\n'
    for key,row in pairs.items():contrasts+=f"| {key} | {100*row['difference']:.2f} | [{100*row['ci95'][0]:.2f}, {100*row['ci95'][1]:.2f}] | {row['fixes']} / {row['regressions']} |\n"
    for lang in ['en','zh']:
        intro='''# v0.18 — Cross-backbone frozen-skill transfer

## Research question and protocol

Do DeepSeek-learned skills improve a different backbone without additional learning? Four methods use Gemini-3.8-Flash, the same 988 derived RxSafeBench questions, one call per case, low reasoning and a 2,048-token completion cap. This configuration was frozen using development results before test inference. Skill files and the openFDA snapshot are unchanged from v0.10/v0.17, with hashes checked before and after evaluation. Gemini test labels do not select skills or prompts.

## Same-backbone method comparison

''' if lang=='en' else '''# v0.18：跨基座的冻结技能迁移

## 研究问题与协议

在 DeepSeek 上学到的技能，直接交给 Gemini 后是否仍有帮助？四种方法共用 Gemini-3.8-Flash、同一 988 题 RxSafeBench 衍生任务、每题一次调用、低 reasoning 和 2,048-token 上限。调用设置在测试前用开发集冻结。技能和 openFDA 说明书快照沿用 v0.10/v0.17，前后核对文件哈希。没有用 Gemini 测试标签改技能或提示。

## 同一基座的方法主表

'''
        end='''
## Interpretation and verification

This tests transfer of persistent language artifacts. LLM weights, tool code and skill text do not evolve during this test. Completion cap and call count match within this table; input lengths and returned usage differ. Costs are logical successful-response usage, including cache reuse, rather than reconciled provider bills; transport retries can add charges with no returned usage. The DeepSeek source studies used a different completion cap, so raw cross-backbone scores are not an equal-compute comparison. One frozen skill-learning path does not establish seed robustness.

Every prediction was aligned to its case and independently rescored. Received malformed answers count as wrong; incomplete transport responses cannot enter the table. Paired intervals resample source-scenario clusters (4,000 draws); they are descriptive and not corrected for multiple comparisons. Negative transfers and regressions are retained. The repository contains aggregates and code; no restricted patient data entered these requests.
''' if lang=='en' else '''
## 如何解读与核验

本轮验证持久技能的迁移能力；测试时没有修改模型权重、工具代码或技能文本。表内调用数和输出上限相同，输入长度和返回用量不同。费用按成功返回的逻辑请求计算，包含缓存复用，并非已经与供应商账单对账的实付总额；超时或重试可能产生未返回用量的额外收费。DeepSeek 源实验的输出上限不同，因此跨模型原始分数不属于等算力比较。这里只有一条冻结技能学习轨迹，不能替代多种子稳健性实验。

所有预测已逐例对齐并独立重算。收到但格式不合格的答案计错；未完成的网络请求不得填表。配对区间按源场景聚类重采样 4,000 次，属于描述性区间，没有做多重比较校正。保留负迁移和退化。仓库发布代码与汇总；请求未使用受限患者数据。
'''
        detail=('\n## Post-hoc failure diagnosis\n\nGrounded skills regress by 2.83 percentage points versus fixed grounding, with paired interval [-4.85,-0.81]. Of 24 invalid skill outputs, 23 end at the length cap. Ten formerly correct cases become invalid. However, among 961 cases where both outputs are valid, correct answers still fall from 528 to 508; truncation alone does not explain the loss. This conditional subset is diagnostic, not a replacement leaderboard. Mean prompt length rises from 1,666.81 to 2,831.81 tokens. No test-driven change is applied to this frozen comparison.\n' if lang=='en' else '\n## 事后失败诊断\n\n证据技能相对固定证据下降2.83个百分点，配对区间[-4.85,-0.81]。24个无效技能输出中23个以长度截断结束；10个原本正确病例变为无效。但在双方输出都有效的961题中，正确数仍从528降到508，不能只归因于截断。这个条件子集用于诊断，不替换主表。平均输入长度从1,666.81增至2,831.81 token。本轮冻结比较未根据测试结果改动。\n')
        (HERE/f'RESULTS.{lang}.md').write_text(intro+table+'\n## Paired contrasts / 配对差异\n\n'+contrasts+detail+end)
    print(json.dumps({'methods':methods,'paired':pairs}),flush=True)

if __name__=='__main__':main()
