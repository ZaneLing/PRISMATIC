"""Archive completed negative results; the interrupted comparison is not complete."""
import json
from common import *
def main():
    d=json.loads((HERE/'results/comparison.json').read_text());assert not d['complete']
    p=json.loads((HERE/'results/schema_probe.json').read_text());assert p['complete']
    rows=['| Completed method | Drug F1 | Core4 F1 | Core5 F1 |','|---|---:|---:|---:|']
    for name,m in d['methods'].items():rows.append('| '+name+' | '+' | '.join(f'{100*m[k]:.2f}%' for k in ['drug_micro_f1','core_order_micro_f1','core5_micro_f1'])+' |')
    table='\n'.join(rows)
    probe='''| Format / 格式示例 | Drug F1 | A1 selected | A23 selected |
|---|---:|---:|---:|
| Original A1/A2 | 3.57% | 36 | 5 |
| A23/A24 example | 3.39% | 0 | 46 |
| Descriptive schema | 7.57% | 8 | 3 |'''
    en=f'''# Literal-schema prescription experiment: completed negative results

The complete 1,082-admission RxRSIAgent runs finished. The broader method comparison was **interrupted** after a controlled training probe identified format-example anchoring. SafeRx/SkeMex/FLAME results are not claimed here. The corrected experiment is in [upgrade_v50](../upgrade_v50/README.md).

{table}

One conditional fact-scope update passed development but failed on test: drug F1 7.34→7.27%, Core4 F1 3.53→3.33%. It adds 3 correctly predicted drugs and 138 extras. Patient-cluster 95% drug-F1 difference interval: [-0.592,+0.439] pp. Acceptance is not generalization.

The frozen supervised top-8 initializer plus common order tool reaches drug/Core4 F1 17.57/10.58%. RxRSIAgent does not beat it. Targets outside the fixed candidate catalogue remain in recall.

## Controlled training probe

The same 48 training cases, unchanged candidate contents and batch layout:

{probe}

This confirms an interface shortcut in this adapter. Descriptive-schema repair is researcher engineering, not RSI, and is applied to all common local controls. The small-sample F1 interval includes zero; test gains are not implied. See `results/schema_probe.json` and `schema_probe_protocol.json`.

No patient records or generated clinical text are published. New paid API expenditure: USD0. The test is historically exposed and exploratory.
'''
    zh=f'''# 编号示例版本处方实验：已完成的负结果

RxRSIAgent 两个全量1,082例实验已完成。训练探针发现共用接口存在格式示例锚定后，**中止此接口下的后续方法对比**；本版没有完成 SafeRx/SkeMex/FLAME。修复后共同对照见 [upgrade_v50](../upgrade_v50/README.md)。

{table}

事实范围规则通过开发集，但测试药物F1从7.34降至7.27%，四字段F1从3.53降至3.33%。只多命中3个药，却增加138个额外药物。患者聚类95%变化区间[-0.592,+0.439]pp，不能称为有效进化。

冻结监督候选器top-8加共同订单工具的药物/四字段F1为17.57/10.58%，高于当前agent。候选库外GT仍计入召回分母。

## 训练病例上的受控干预

固定48例、候选内容及分批方式，仅改变输出格式示例：

{probe}

这是本地适配器接口捷径的因果证据。去掉示例属于研究者工程修复，不计为RSI，并应用于下一版所有共同对照。小样本F1变化区间仍包含零，不能据此推断测试集提升。

患者记录和生成临床内容不公开。本次新增付费API费用0美元。测试集已被历史实验暴露，属于探索性结果。
'''
    for lang,text in [('en',en),('zh',zh)]:
        (HERE/f'RESULTS.{lang}.md').write_text(text)
        (ROOT/f'paper/versions/v0.49-2026-10-16.{lang}.md').write_text(text)
if __name__=='__main__':main()
