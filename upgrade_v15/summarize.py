"""Apply the same independent scorer to the predeclared binary intervention."""
import importlib.util,json,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent
PRIVATE=Path.home()/'Desktop/MedTreeBench/dataset/restricted/prismatic-v15'
PREVIOUS=PRIVATE.parent/'prismatic-v9'

def main():
    a=json.loads((PRIVATE/'cases.json').read_text())['test'];b=json.loads((PREVIOUS/'cases.json').read_text())['test']
    assert [(c['case_id'],c['gold'],c['catalogue']) for c in a]==[(c['case_id'],c['gold'],c['catalogue']) for c in b]
    controls=json.loads((HERE.parent/'upgrade_v9/results/tool_control_results.json').read_text())
    (HERE/'results/tool_control_results.json').write_text(json.dumps(controls,indent=2)+'\n')
    for name in controls:shutil.copyfile(PREVIOUS/(name+'-test.json'),PRIVATE/(name+'-test.json'))
    spec=importlib.util.spec_from_file_location('independent_scorer',HERE.parent/'upgrade_v9/summarize.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.HERE=HERE;module.PRIVATE=PRIVATE;module.main()
    for lang in ['en','zh']:
        path=HERE/f'RESULTS.{lang}.md';text=path.read_text().replace('v0.9','v0.15')
        note='\n## Predeclared intervention\n\nThe output is an exact 20-position inclusion mask, adding explicit negative supervision. Both arms restart the original backbone. Patient membership, candidate tools and step/example budgets match v0.9; target-token counts differ. Protocol was frozen before v0.9 test scoring. The direct tool controls are reused only after exact test case, GT and catalogue equality checks.\n' if lang=='en' else '\n## 事先固定的干预\n\n输出改为 20 位纳入/排除掩码，显式监督负候选。两臂均从原始模型重新开始；患者、候选工具、训练步数/样本数与 v0.9 一致，但目标 token 数不同。协议在 v0.9 测试前冻结。仅在逐例检查测试 ID、GT、候选目录完全相等后复用直接工具对照。\n'
        path.write_text(text+note)

if __name__=='__main__':main()
