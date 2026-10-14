"""Report only completed evidence-tool rows, keeping transport gaps explicit."""
import json, sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'upgrade_v8'))
from public_client import LOCAL as DATA_LOCAL
from evidence_tool import LOCAL


def main():
    data=json.loads((DATA_LOCAL/'data.json').read_text())['parts']['test']
    rows=json.loads((LOCAL/'test-review-actions.json').read_text())
    report=json.loads((HERE/'results/router_seed_42.json').read_text())
    out={'status':'partial','complete_test_methods':{},'unscored':{},'test_n':len(data)}
    correct={}
    for name,preds in rows.items():
        assert [r['case_id'] for r in preds]==[c['id'] for c in data]
        errors=sum(bool(r.get('error')) for r in preds)
        if errors:
            out['unscored'][name]={'missing_responses':errors,'received_responses':len(preds)-errors,'accuracy':None}
            continue
        correct[name]=np.array([r['prediction']==c['gold'] for r,c in zip(preds,data)],dtype=int)
        assert int(correct[name].sum())==report['methods'][name]['correct']
        out['complete_test_methods'][name]=report['methods'][name]
    groups=sorted({c['group_id'] for c in data});lookup={g:i for i,g in enumerate(groups)}
    ix=np.array([lookup[c['group_id']] for c in data]);n=np.bincount(ix)
    for name in [a for a in ['balanced','safety','indication'] if a in correct]:
        delta=correct[name]-correct['cot'];totals=np.bincount(ix,weights=delta)
        rng=np.random.default_rng(42);draws=[]
        for _ in range(4000):
            b=rng.integers(0,len(groups),len(groups));draws.append(totals[b].sum()/n[b].sum())
        out['complete_test_methods'][name]['versus_cot']={'fixes':int((delta>0).sum()),'regressions':int((delta<0).sum()),
            'difference':float(delta.mean()),'scenario_cluster_ci95':np.quantile(draws,[.025,.975]).tolist()}
    out['verification']='Independent counts and exact case alignment passed; transport failures excluded from scoring.'
    out['status']='partial' if out['unscored'] else 'complete_deepseek_study'
    gemini=json.loads((HERE/'results/backbone_development_pilot.json').read_text())
    gemini_done=all(gemini.get('methods',{}).get(k,{}).get('accuracy') is not None for k in ['cot','safety_evidence'])
    out['second_backbone_status']='complete_development_pilot' if gemini_done else 'incomplete'
    (HERE/'results/summary.json').write_text(json.dumps(out,indent=2)+'\n')
    table='| Method | Correct / 988 | Accuracy (%) | Model calls | Fixes / regressions vs CoT |\n|---|---:|---:|---:|---:|\n'
    for name in [a for a in ['cot','balanced','safety','indication'] if a in correct]:
        m=out['complete_test_methods'][name];d=m.get('versus_cot',{})
        table+=f"| {name} | {m['correct']} | {100*m['accuracy']:.2f} | {1 if name=='cot' else 2} | {d.get('fixes',0)} / {d.get('regressions',0)} |\n"
    table+='| RxRSI evidence router, seed 42 | 467 | 47.27 | 1 | 0 / 0 |\n'
    if 'indication' not in correct:table+='| indication review | Incomplete | — | 2 intended | — |\n'
    for lang in ['en','zh']:
        if lang=='en':
            text='''# v0.11 — Drug-label evidence and feedback-selected routing

## Data, tools and budget

The same public RxSafeBench scenario-group split has 625/190/197/988 train/proposal/guard/test questions. DeepSeek-V4.1-Flash receives at most 512 output tokens per call. Each review receives the same initial CoT answer and retrieved label excerpts for all options. The fixed balanced review was selected on proposal data. This is a method comparison within one backbone and one derived task.

The openFDA label snapshot matched 623 of 699 public candidate names; test-option coverage is 92.98%. Retrieval returns up to two exact contiguous excerpts per option with label IDs and source fields. Labels are company-submitted records and are not uniformly FDA-verified. Missing evidence is explicitly retained. No restricted patient data is sent to a service.

## Completed test results

'''+table+'''
The router learns coefficients for evidence-action benefit over CoT from 156/312/468/625 observed training cases. A 190-case proposal set selects from regularization/threshold candidates; a separate 197-case guard checks net repairs. All four updates were rejected, so the active router remains CoT. The fixed evidence tool improves the point estimate, but this does not demonstrate an evolving-agent advantage. Paired scenario-cluster intervals are released in `results/summary.json` and are descriptive, without multiple-comparison correction.

## Incomplete evaluations and repair

The indication review received 835/988 answers; 153 requests failed with HTTP 402 after account credits were exhausted. Its accuracy is unreported. The Gemini development pilot received zero of its 380 planned answers, so it has no model score. Earlier incomplete numeric summaries are retained only in explicitly invalidated archives. The client now stops on authentication/credit errors and the scorer rejects any result with transport errors. A genuinely received malformed answer still counts wrong.

## Next controlled increment

[v0.12](../upgrade_v12/RESULTS.en.md) compares two gates across three seeds using only complete cached action traces. It makes zero new requests and distinguishes routing-parameter updates from backbone or executable-tool updates.
'''
        else:
            text='''# v0.11：药物说明书证据与反馈选工具

## 数据、工具与预算

共用公开 RxSafeBench 场景组切分：625/190/197/988 训练/候选选择/退化检查/测试题。固定 DeepSeek-V4.1-Flash，每次最多 512 输出 token。证据复核均收到相同 CoT 初稿，以及所有选项的说明书片段。balanced 固定工具仅由候选选择集选定。这是同基座、同衍生任务的方法比较。

openFDA 快照匹配了 699 个公开候选药名中的 623 个，测试选项覆盖率 92.98%。每个选项最多返回两个连续原文片段，保留说明书 ID 与来源字段。说明书为企业提交记录，不是全部经 FDA 核实的内容；缺失证据显式保留。未向服务发送受限患者数据。

## 已完整完成的测试结果

'''+table+'''
路由器从 156/312/468/625 个已见训练病例学习“某证据动作相对 CoT 是否获益”的参数。190 题选择正则系数/阈值，197 题独立检查净修复。四轮更新均被拒绝，因此最终仍为 CoT。固定证据工具的点估计提高，但未证明进化方案更优。场景组聚类配对区间见 `results/summary.json`，为未作多重比较校正的描述性区间。

## 未完成结果及修复

适应证证据复核仅收到 835/988 个回答，其余 153 个在账户余额耗尽后返回 HTTP 402，因此不报告准确率。Gemini 开发试验计划的 380 个回答全部未收到，也没有模型分数。此前不完整数字仅保留在明确作废的归档中。客户端现在遇到鉴权/余额错误会停止，评分器拒绝包含传输错误的结果；已收到但格式错误的回答仍计错。

## 后续已执行对照

[v0.12](../upgrade_v12/RESULTS.zh.md) 用完整缓存轨迹，在三个种子上比较两种门控，没有新增网络请求，并区分路由参数更新、模型权重更新与工具代码更新。
'''
        if not out['unscored']:
            text=text.replace('The indication review received 835/988 answers; 153 requests failed with HTTP 402 after account credits were exhausted. Its accuracy is unreported.',
                'The indication review initially missed 153 replies after HTTP 402. After the user restored credits, all missing requests were resumed from cache: the complete row is 478/988 (48.38%), including one received malformed answer. The selection protocol was unchanged.')
            text=text.replace('适应证证据复核仅收到 835/988 个回答，其余 153 个在账户余额耗尽后返回 HTTP 402，因此不报告准确率。',
                '适应证证据复核最初有 153 个请求返回 HTTP 402。用户充值后已沿用缓存及原协议补齐，完整结果为 478/988（48.38%），其中一个已收到但格式错误的回答计错。')
        if gemini_done:
            a=gemini['methods']['cot'];b=gemini['methods']['safety_evidence']
            text=text.replace('The Gemini development pilot received zero of its 380 planned answers, so it has no model score.',
                f"The resumed Gemini development pilot is complete: CoT {a['correct']}/190 ({100*a['accuracy']:.2f}%) and safety evidence {b['correct']}/190 ({100*b['accuracy']:.2f}%). This is development-only, not test or transfer evidence.")
            text=text.replace('Gemini 开发试验计划的 380 个回答全部未收到，也没有模型分数。',
                f"Gemini 开发试验也已补齐：CoT {a['correct']}/190（{100*a['accuracy']:.2f}%），安全证据 {b['correct']}/190（{100*b['accuracy']:.2f}%）。这是开发集结果，不充当测试或迁移结果。")
        (HERE/f'RESULTS.{lang}.md').write_text(text)
    print(json.dumps({'completed':list(correct),'unscored':out['unscored']}))


if __name__=='__main__':main()
