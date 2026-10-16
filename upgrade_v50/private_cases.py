"""Local bilingual training case illustrations; never write cases into Git."""
import json
from common import *

def orders(values):
    if values is None:return '(not evaluated / 未评估)'
    return '\n'.join('- '+json.dumps(o,ensure_ascii=False) for o in values) or '(empty / 空)'

def main():
    cases=json.loads((PRIVATE/'failure_case_studies.json').read_text());chosen=[];seen=set()
    pools=[('Correction after scoped intervention / 干预后修复',lambda c:c['drug_f1_after'] is not None and c['drug_f1_after']>c['drug_f1_before']),
      ('Regression after scoped intervention / 干预后退步',lambda c:c['drug_f1_after'] is not None and c['drug_f1_after']<c['drug_f1_before']),
      ('Candidate-coverage failure / 候选覆盖失败',lambda c:c['error_counts_before']['catalogue_missing']>0),
      ('Available candidate omitted / 已有候选被漏选',lambda c:c['error_counts_before']['selection_missing']>0),
      ('Drug correct, order fields wrong / 药名正确但联合字段不符',lambda c:c['error_counts_before']['core_reachable_given_drug']>c['error_counts_before']['core_hits'])]
    # Stable, outcome-stratified illustrations; not an estimate of prevalence.
    for label,predicate in pools:
        for c in sorted(cases,key=lambda x:(x['phase']!='instrumented',x['round'],x['case_id'])):
            if c['case_id'] not in seen and predicate(c):chosen.append((label,c));seen.add(c['case_id']);break
    text=['# Restricted training case studies / 受限训练病例分析',
      'These are real training illustrations selected by error category, not random samples or clinical endorsements. This file stays in the credentialed restricted directory. Do not publish it to GitHub. / 以下是真实训练病例，按错误类型选取，并非随机抽样，也不构成临床适宜性证明。本文件仅留在受限目录。',
      'Reference prescriptions record observed actions. An extra or omission is relative to that record; clinical correctness may require information absent from the input. / GT 是记录到的行为；多开、漏开均相对于该记录定义，不能直接推断临床对错。']
    for i,(label,c) in enumerate(chosen,1):
        before=c['error_counts_before'];after=c['error_counts_after']
        text+=['\n## '+str(i)+'. '+label,
          f"Phase / 阶段: {c['phase']}; round / 轮次: {c['round']}; local case key: `{c['case_id']}`.",
          '### Observed context / 当时可见信息','```json\n'+json.dumps(c['available_context'],ensure_ascii=False,indent=2)+'\n```',
          '### Recorded reference / 实际记录的处方',orders(c['reference']),
          '### Before / 干预前',orders(c['before']),
          '### Candidate intervention output / 候选干预后',orders(c['after']),
          '### Trace and hypothesis / 轨迹与根因假设',
          '```json\n'+json.dumps({'before':c['before_trace'],'after':c['after_trace']},ensure_ascii=False,indent=2)+'\n```',
          f"Before: {before['fn']} misses, {before['fp']} reference-relative extras; {before['catalogue_missing']} targets outside catalogue, {before['selection_missing']} candidate targets not selected.",
          ('After: '+str(after['fn'])+' misses and '+str(after['fp'])+' extras.' if after else 'No valid candidate intervention was evaluated for this case.'),
          'A per-case improvement does not imply that its candidate passed the global proposal/guard gate. The gate records in learning_scope.json determine retention. / 单例修复不代表该候选通过全局守门，保留状态以学习轨迹记录为准。']
    text+=['\n## Common patterns / 共性规律',
      '1. A candidate generator can exclude GT before the actor reasons; changing a skill cannot recover a drug outside the supplied action space. / 候选生成先排除了部分 GT，后续技能不能选择库外药物。',
      '2. The checker verifies at most three selected facts while the LLM still sees the full supplied input. All-observed scope changes checker coverage, not underlying available information. / 核验器最多检查三个选中事实，但LLM仍可见完整输入；扩大范围改变核验覆盖，不增加原始可用信息。',
      '3. Source quotation and valid JSON are execution properties, not proof of appropriate drug choice. / 引用真实、JSON 有效均不等于药物选择适宜。',
      '4. A reference discrepancy is feedback, not a runtime predicate. Rules such as “if GT contains X” or copied drug-to-drug actions are rejected. / GT 差距用于反馈，不能成为运行时条件；依赖 GT 或照搬药名的规则被拒绝。']
    (PRIVATE/'CASE_STUDIES.bilingual.md').write_text('\n\n'.join(text)+'\n')
    save(HERE/'results/case_study_manifest.json',{'illustrations':len(chosen),'selection':'stable outcome-stratified training examples; not random',
      'restricted_artifact_sha256':sha(PRIVATE/'CASE_STUDIES.bilingual.md'),'patient_content_published':False})
    print('Wrote restricted bilingual case illustrations:',len(chosen))
if __name__=='__main__':main()
