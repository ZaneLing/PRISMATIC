"""Private paired evidence-intervention examples and public aggregate manifest."""
import json
from common import *

def main():
    cases=load_cases()['proposal'];before=json.loads((PRIVATE/'label-proposal-fresh.json').read_text())['rows'];after=json.loads((PRIVATE/'no-label-proposal.json').read_text())['rows']
    records=[]
    for c,a,b in zip(cases,before,after):
        assert c['case_id']==a['case_id']==b['case_id']
        ma=score([a['orders']],[c['gold']]);mb=score([b['orders']],[c['gold']]);delta=mb['drug_micro_f1']-ma['drug_micro_f1']
        records.append({'case':c,'with_evidence':a,'without_evidence':b,'before_f1':ma['drug_micro_f1'],'after_f1':mb['drug_micro_f1'],'delta':delta})
    chosen=[]
    for label,predicate in [('Reference-agreement correction / 参考匹配改善',lambda r:r['delta']>0),('Reference-agreement regression / 参考匹配退步',lambda r:r['delta']<0)]:
        pool=sorted((r for r in records if predicate(r)),key=lambda r:r['case']['case_id'])[:2]
        chosen.extend((label,r) for r in pool)
    text=['# Restricted evidence-intervention case studies / 受限证据干预病例',
      'These are outcome-stratified illustrations from the 48-case development set, not independent clinical validation. Two selected corrections and two regressions are shown when available. Metadata and batches are held fixed; only label spans are removed. No rule is selected from these outcomes. / 以下按结果类别展示开发集中的改善与退步，非独立临床验证，未据此挑选规则。',
      'Reference agreement records actions, not a unique optimal prescription. A quote can be authentic but irrelevant to this future-order task. / GT 是记录行为；引用真实不等于适合此处方时间窗口。']
    for i,(label,r) in enumerate(chosen,1):
        c=r['case'];a=r['with_evidence'];b=r['without_evidence']
        text.extend([f'## {i}. {label}',f"Local case key: `{c['case_id']}`. Drug F1: {100*r['before_f1']:.2f}% → {100*r['after_f1']:.2f}%.",
         '### Observed context / 当时可见信息','```json\n'+json.dumps(c['context'],ensure_ascii=False,indent=2)+'\n```',
         '### Recorded orders / 记录到的处方','```json\n'+json.dumps(c['gold'],ensure_ascii=False,indent=2)+'\n```',
         '### Paired outputs and traces / 成对输出与追踪','```json\n'+json.dumps({'with_evidence':{k:a[k] for k in ['orders','plan','assessment','checks','evidence']},'without_evidence':{k:b[k] for k in ['orders','plan','assessment','checks','evidence']}},ensure_ascii=False,indent=2)+'\n```'])
    target=PRIVATE/'EVIDENCE_CASE_STUDIES.bilingual.md';target.write_text('\n\n'.join(text)+'\n')
    save(HERE/'results/evidence_case_manifest.json',{'cases':len(cases),'illustrations':len(chosen),'improved_case_drug_f1':sum(r['delta']>0 for r in records),'regressed_case_drug_f1':sum(r['delta']<0 for r in records),'no_case_f1_change':sum(r['delta']==0 for r in records),
      'selection':'two stable-hash cases per improvement/regression category when available, not random',
      'restricted_artifact_sha256':sha(target),'patient_content_published':False,'clinical_appropriateness_adjudicated':False})
    print('Wrote private paired case studies:',len(chosen))
if __name__=='__main__':main()
